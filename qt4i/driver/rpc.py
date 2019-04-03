# -*- coding:utf-8 -*-
#
# Tencent is pleased to support the open source community by making QTA available.
# Copyright (C) 2016THL A29 Limited, a Tencent company. All rights reserved.
# Licensed under the BSD 3-Clause License (the "License"); you may not use this
# file except in compliance with the License. You may obtain a copy of the License at
#
# https://opensource.org/licenses/BSD-3-Clause
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" basis, WITHOUT WARRANTIES OR CONDITIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.
#
'''RPC Framework
'''

from __future__ import absolute_import, print_function

import json
import random
import re
import string
import six
from six.moves.socketserver import ThreadingMixIn
from six.moves.xmlrpc_server import SimpleXMLRPCServer
from six.moves.xmlrpc_server import SimpleXMLRPCRequestHandler
import six.moves.xmlrpc_client as xmlrpc_client
from six.moves.http_client import HTTPResponse
from six import StringIO
from six import PY2

if PY2:
    from urllib import splittype
    from urllib import splithost
else:
    from urllib.parse import splittype
    from urllib.parse import splithost

from qt4i.driver.tools import logger


try:
    import fcntl
except ImportError:
    fcntl = None

IDCHARS = string.ascii_lowercase+string.digits


def random_id(length=8):
    return_id = ''
    for _ in range(length):
        return_id += random.choice(IDCHARS)
    return return_id


class _RPCMethod(object):
    """RPC method decorator
    """
    def __init__(self, method, instance=None, owner=None ):
        self.method = method
        self.instance = instance
        self.owner = owner

    def __call__(self, *args, **kwargs ):
        if self.instance == None or self.owner == None:
            return self.method(*args, **kwargs)
        else:
            return self.method.__get__(self.instance, self.owner)(*args, **kwargs)

    def __get__(self, instance, owner):
        return _RPCMethod(self.method, instance, owner)

rpc_method = _RPCMethod


class RPCEndpoint(object):
    """RPC end point, subclass to define a RPC end point
    """
    rpc_name_prefix = ""

    def _dispatch(self, method, params):
        if not method.startswith(self.rpc_name_prefix):
            raise Exception('method "%s" is not supported by endpoint "%s"' % (method, type(self).__name__))
        try:
            m = getattr(self, method[len(self.rpc_name_prefix):])
        except AttributeError:
            raise Exception('method "%s" is not supported by endpoint "%s"' % (method, type(self).__name__))
        else:
            if not isinstance(m, _RPCMethod):
                raise Exception('method "%s" is not exposed by endpoint "%s"' % (method, type(self).__name__))
            return m(*params)

    def create_json_command(self, method, *params):
        '''serialize function to JSON Object
        '''
        return {"method": method, "params": list(params)}


class FakeSocket():
    def __init__(self, response_str):
        self._file = StringIO(response_str)
    def makefile(self, *args, **kwargs):
        return self._file


class RPCClientProxy(object):
    '''RPC Client,
    copy  ServerProxy 的源码， 在__request 方法中进行解码
    主要实现RPC客户端返回Unicode转换为UTF-8
    '''

    def __init__(self, uri, ws_uri=None,transport=None, encoding=None, verbose=0,
                 allow_none=0, use_datetime=0, context=None):
        # establish a "logical" server connection
        if PY2 and isinstance(uri, six.text_type):
            uri = uri.encode('ISO-8859-1')
        # get the url
        protocol, uri = splittype(uri)
        if protocol not in ("http", "https"):
            raise IOError("unsupported JSON-RPC protocol")
        self.__host, self.__handler = splithost(uri)
        if not self.__handler:
            self.__handler = "/RPC2"
        self.__ws_uri = ws_uri

        if transport is None:
            if protocol == "https":
                transport = SafeTransport(use_datetime=use_datetime, context=context)
            else:
                transport = Transport(use_datetime=use_datetime)
        self.__transport = transport

        self.__encoding = encoding
        self.__verbose = verbose
        self.__allow_none = allow_none

    def __close(self):
        self.__transport.close()

    def _parse_ws_response(self):
        http_response = self.__ws.recv()
        response = HTTPResponse(FakeSocket(http_response))
        response.begin()
        while response.length > len(http_response):
            http_response += self.__ws.recv()
        response = HTTPResponse(FakeSocket(http_response))
        self.__transport.verbose = 0
        response.begin()
        return self.__transport.parse_response(response)

    def _ws_request(self, request):
        import websocket
        self.__ws = websocket.WebSocket()
        self.__ws.connect(self.__ws_uri)
        header = "POST {abs_path} HTTP/1.1\r\n" \
                "Host: {host}\r\n"  \
                "User-Agent: jsonrpclib/0.1\r\n" \
                "Connection: close\r\n"  \
                "Accept-Encoding: gzip\r\n" \
                "Content-Type: application/json-rpc\r\n"  \
                "Content-Length: {len}\r\n" \
                "\r\n".format(abs_path=self.__handler, host=self.__host, len=len(request)).encode("UTF-8")
        self.__ws.send(header + request)
        return self._parse_ws_response()

    def __request(self, methodname, params):
        # call a method on the remote server
        request = {"jsonrpc": "2.0"}
        if len(params) > 0:
            request["params"] = params
        request["id"] = random_id()
        request["method"] = methodname
        request = json.dumps(request)
        if self.__ws_uri:
            response = self._ws_request(request)
        else:
            response = self.__transport.request(
                self.__host,
                self.__handler,
                request,
                verbose=self.__verbose
                )
        response = json.loads(response)
        if not isinstance(response, dict):
            raise TypeError('Response is not dict')
        if 'error' in response.keys() and response['error'] is not None:
            raise DriverApiError(response['error']['message'])
        else:
            response = response['result'][0]
            if isinstance(response, dict):
                return self.encode_dict(response, "UTF-8")
            elif isinstance(response, list):
                return self.encode_list(response, "UTF-8")
            elif PY2 and isinstance(response, six.text_type):
                return response.encode("UTF-8")
            return response

    def __repr__(self):
        return (
            "<ServerProxy for %s%s>" %
            (self.__host, self.__handler)
            )

    __str__ = __repr__

    def __getattr__(self, name):
        # magic method dispatcher
        return xmlrpc_client._Method(self.__request, name)

    # note: to call a remote object with an non-standard name, use
    # result getattr(server, "strange-python-name")(args)

    def __call__(self, attr):
        """A workaround to get special attributes on the ServerProxy
           without interfering with the magic __getattr__
        """
        if attr == "close":
            return self.__close
        elif attr == "transport":
            return self.__transport
        raise AttributeError("Attribute %r not found" % (attr,))

    def encode_dict(self, content, encoding="UTF-8"):
        '''将字典编码为指定形式

        :param content: 要编码内容
        :type content: dict
        :param encoding:编码类型
        :type encoding: str
        :returns: dict -- 编码后的字典
        '''
        for key in content:
            if isinstance(content[key], dict):
                content[key] = self.encode_dict(content[key], encoding)
            elif PY2 and isinstance(content[key], six.text_type):
                content[key] = content[key].encode(encoding)
            elif isinstance(content[key], list):
                content[key] = self.encode_list(content[key], encoding)
        return content

    def encode_list(self, content, encoding="UTF-8"):
        '''将列表编码为指定形式

        :param content: 要编码内容
        :type content: list
        :param encoding:编码类型
        :type encoding: str
        :returns: list -- 编码后的列表
        '''
        for ind, item in enumerate(content):
            if isinstance(item, dict):
                content[ind] = self.encode_dict(item, encoding)
            elif PY2 and isinstance(item, six.text_type):
                content[ind] = content[ind].encode(encoding)
            elif isinstance(item, list):
                content[ind] = self.encode_list(item, encoding)
        return content


class DriverApiError(Exception):
    '''Driver API Error
    '''


class Fault(object):
    '''JSON-RPC Error
    '''

    def __init__(self, code=-12306, message = None, rpcid=None):
        self.faultCode = code
        self.faultString = message
        self.rpcid = rpcid
        if not message:
            import traceback
            self.faultString = traceback.format_exc()

    def error(self):
        return {"code": self.faultCode, "message": self.faultString}

    def response(self):
        return json.dumps({"jsonrpc": "2.0", "error":self.error(), "id":self.rpcid})

    def __repr__(self):
        return '<Fault %s: %s>' % (self.faultCode, self.faultString)


class TransportMixIn(object):
    '''XMLRPC Transport extended API
    '''
    user_agent = "jsonrpclib/0.1"
    _connection = (None, None)
    _extra_headers = []

    def send_content(self, connection, request_body):
        connection.putheader("Content-Type", "application/json-rpc")
        connection.putheader("Content-Length", str(len(request_body)))
        connection.endheaders()
        if request_body:

            if not PY2 and isinstance(request_body, str):
                request_body = request_body.encode('utf-8')
            connection.send(request_body)

    def getparser(self):
        target = JSONTarget()
        return JSONParser(target), target


class JSONParser(object):

    def __init__(self, target):
        self.target = target

    def feed(self, data):
        self.target.feed(data)

    def close(self):
        pass


class JSONTarget(object):

    def __init__(self):
        self.data = []

    def feed(self, data):
        self.data.append(data)

    def close(self):
        if PY2:
            return ''.join(self.data)
        else:
            return b''.join(self.data)


class Transport(TransportMixIn, xmlrpc_client.Transport):

    def __init__(self, use_datetime):
        TransportMixIn.__init__(self)
        xmlrpc_client.Transport.__init__(self, use_datetime)


class SafeTransport(TransportMixIn, xmlrpc_client.SafeTransport):

    def __init__(self, use_datetime, context):
        TransportMixIn.__init__(self)
        xmlrpc_client.SafeTransport.__init__(self, use_datetime, context)


class SimpleJSONRPCRequestHandler(SimpleXMLRPCRequestHandler):
    '''JSON-RPC请求处理器
    '''
    def is_rpc_path_valid(self):
        return True

    def do_POST(self):
        '''处理HTTP的POST请求
        '''
        if not self.is_rpc_path_valid():
            self.report_404()
            return
        try:
            max_chunk_size = 10*1024*1024
            size_remaining = int(self.headers["content-length"])
            L = []
            while size_remaining:
                chunk_size = min(size_remaining, max_chunk_size)
                L.append(self.rfile.read(chunk_size))
                size_remaining -= len(L[-1])
            if PY2:
                data = ''.join(L)
            else:
                data = b''.join(L)
            response = self.server._marshaled_dispatch(
                    data, getattr(self, '_dispatch', None), self.path
                )
            self.send_response(200)
        except Exception:
            response = Fault().response()
            self.send_response(500, response)
            logger.get_logger().exception("ProtocolError:%s" % response)
        if response is None:
            response = ''
        self.send_header("Content-Type", "application/json-rpc")
        if self.encode_threshold is not None:
            if len(response) > self.encode_threshold:
                    q = self.accept_encodings().get("gzip", 0)
                    if q:
                        try:
                            if six.PY3 and isinstance(response, six.string_types):
                                response = response.encode('utf-8')
                            response = xmlrpc_client.gzip_encode(response)
                            self.send_header("Content-Encoding", "gzip")
                        except NotImplementedError:
                            pass
        self.send_header("Content-length", str(len(response)))
        self.end_headers()
        if six.PY3 and isinstance(response, six.string_types):
            response = response.encode('utf-8')
        self.wfile.write(response)


class SimpleJSONRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    """RPC Server
    """

    LOG_FILTERED_METHODS = [
                            'push_file_data',
                            'pull_file_data',
                            'device.get_log',
                            'device.get_crash_log',
                            'device.get_driver_log',
                            'device.get_element_tree',
                            'device.get_element_tree_and_capture_screen',
                            'device.capture_screen',
                            'element.get_element_tree',
                            ]

    def __init__(self, urls, addr):
        """Constructor

        :param urls: list of URL pattern and RPC end point class
        :param addr: listening address
        :type urls: list
        :type addr: tuple
        """
        SimpleXMLRPCServer.__init__(self, addr=addr,
                                                       requestHandler=SimpleJSONRPCRequestHandler,
                                                       allow_none=True,
                                                       encoding='UTF-8',
                                                       logRequests=False)

        self._dispatcher_patterns = []
        for url_pattern, method_pattern, endpoint_cls in urls:
            if method_pattern:
                method_c_pattern = re.compile(method_pattern)
            else:
                method_c_pattern = None
            self._dispatcher_patterns.append((re.compile(url_pattern),
                                              method_c_pattern,
                                              endpoint_cls))

    def _marshaled_dispatch(self, data, dispatch_method=None, path=None):
        origin_path = path
        path = path[1:] #remove /
        if not path.endswith('/'):
            path += '/'

        try:
            request = json.loads(data)
        except ValueError:
            fault = Fault(-32700, 'JSON parsing error')
            return fault.response()
        if not isinstance(request, dict):
            fault = Fault(-32600, 'Invalid request data type')
            return fault.response()
        rpcid = request.get('id', None)
        method = request.get('method', None)
        params = request.get('params', [])
        params_types = (list, dict, tuple)
        if not method or not isinstance(method, six.string_types) or not isinstance(params, params_types):
            return Fault(-32600, 'Invalid request method or parameters').response()

        tried_enpoint_clss = []
        for url_pattern, method_pattern, endpoint_cls in self._dispatcher_patterns:
            m = url_pattern.match(path)
            if m:
                try:
                    log_suffix = m.group(1)
                    log = logger.get_logger("driverserver_%s" % log_suffix)
                except:
                    log = logger.get_logger()

                tried_enpoint_clss.append(endpoint_cls)
                if (method_pattern is None) or method_pattern.match(method):
                    endpoint_params = m.groupdict()
                    try:
                        endpoint = endpoint_cls(self, **endpoint_params)
                    except:
                        fault = Fault()
                        log.exception(fault.error())
                        return fault.response()
                    else:
                        break
        else:
            if not tried_enpoint_clss:
                return Fault(-32601, "invalid URL: \"%s\"" % origin_path).response()
            else:
                return Fault(-32601, "invalid method: \"%s\", no matched end point, end point: %s tried" %
                    (method, ", ".join([ '"%s"'%it.__name__ for it in tried_enpoint_clss]))).response()

        try:
            log.debug('--- --- --- --- --- ---')
            log.debug('%s <<< %s' % (method, params))

            response = endpoint._dispatch(method, params)
            if method in self.LOG_FILTERED_METHODS:
                log.debug('%s >>> done' % method)
            else:
                log.debug('%s >>> %s' % (method, response))
            # wrap response in a singleton tuple
            if six.PY3 and isinstance(response, six.binary_type):
                response = response.decode('utf-8')
            response = (response,)
            response = json.dumps({"jsonrpc": "2.0", "result": response, "id": rpcid})
        except:
            fault = Fault()
            response = fault.response()
            log.error('%s >>> %s' % (method, fault.error()))
            log.exception(fault.error())
        return response
