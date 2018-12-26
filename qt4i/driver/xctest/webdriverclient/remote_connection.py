# -*- coding: utf-8 -*-
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
'''连接远程WebDriverAgent服务
'''

from __future__ import absolute_import, print_function

import socket
import string
import base64
import json

try:
    import http.client as httplib
    from urllib import request as url_request
    from urllib import parse
except ImportError: # above is available in py3+, below is py2.7
    import httplib as httplib
    import urllib2 as url_request
    import urlparse as parse

from testbase.conf import settings
from qt4i.driver.tools import logger as logging
from qt4i.driver.xctest.webdriverclient.command import Command
from qt4i.driver.xctest.webdriverclient.errorhandler import ErrorCode
from qt4i.driver.xctest.webdriverclient.exceptions import XCTestAgentTimeoutException


class Request(url_request.Request):
    """Extends the url_request.Request to support all HTTP request types.
    """

    def __init__(self, url, data=None, method=None):
        """Initialise a new HTTP request.

        :param url: String for the URL to send the request to.
        :param data: Data to send with the request.
        """
        if method is None:
            method = data is not None and 'POST' or 'GET'
        elif method != 'POST' and method != 'PUT':
            data = None
        self._method = method
        url_request.Request.__init__(self, url, data=data)

    def get_method(self):
        """Returns the HTTP method used by this request.
        """
        return self._method


class Response(object):
    """Represents an HTTP response.
    """

    def __init__(self, fp, code, headers, url):
        """Initialise a new Response.

        :param fp: The response body file object.
        :param code: The HTTP status code returned by the server.
        :param headers: A dictionary of headers returned by the server.
        :param url: URL of the retrieved resource represented by this Response.
        """
        self.fp = fp
        self.read = fp.read
        self.code = code
        self.headers = headers
        self.url = url

    def close(self):
        """Close the response body file object.
        """
        self.read = None
        self.fp = None

    def info(self):
        """Returns the response headers.
        """
        return self.headers

    def geturl(self):
        """Returns the URL for the resource returned in this response.
        """
        return self.url


class HttpErrorHandler(url_request.HTTPDefaultErrorHandler):
    """
    A custom HTTP error handler.

    Used to return Response objects instead of raising an HTTPError exception.
    """

    def http_error_default(self, req, fp, code, msg, headers):
        """Default HTTP error handler.

        :param req: The original Request object.
        :param fp: The response body file object.
        :param code: The HTTP status code returned by the server.
        :param msg: The HTTP status message returned by the server.
        :param headers: The response headers.
        :returns: A new Response object.
        """
        return Response(fp, code, headers, req.get_full_url())


class RemoteConnection(object):
    """A connection with the Remote WebDriver server.

    Communicates with the server using the WebDriver wire protocol:
    https://github.com/SeleniumHQ/selenium/wiki/JsonWireProtocol"""

    _default_timeout = settings.get('QT4I_XCTAGENT_CMD_TIMEOUT', 90)
    if _default_timeout == -1:
        _default_timeout = socket._GLOBAL_DEFAULT_TIMEOUT
    _timeout = _default_timeout
#     _timeout = socket._GLOBAL_DEFAULT_TIMEOUT
    

    @classmethod
    def get_timeout(cls):
        """
        
        :returns: Timeout value in seconds for all http requests made to the Remote Connection
        """
        return None if cls._timeout == socket._GLOBAL_DEFAULT_TIMEOUT else cls._timeout

    @classmethod
    def set_global_timeout(cls, timeout):
        """Override the default timeout
 
        :param timeout: timeout value for http requests in seconds
        :type timeout: int
        """
        cls._timeout = timeout
        
    @classmethod
    def reset_global_timeout(cls):
        """Reset the http request timeout to socket._GLOBAL_DEFAULT_TIMEOUT
        """
#         cls._timeout = socket._GLOBAL_DEFAULT_TIMEOUT
        cls._timeout = cls._default_timeout
    
    def set_timeout(self, timeout):
        self._timeout = timeout
        
    def reset_timeout(self):
        self._timeout = self._default_timeout

    def __init__(self, remote_server_addr, keep_alive=False, resolve_ip=True, logger_name='RemoteConnection'):
        # Attempt to resolve the hostname and get an IP address.
        self.logger = logging.get_logger(logger_name)
        self.keep_alive = keep_alive
        parsed_url = parse.urlparse(remote_server_addr)
        addr = ""
        if parsed_url.hostname and resolve_ip:
            try:
                netloc = socket.gethostbyname(parsed_url.hostname)
                addr = netloc
                if parsed_url.port:
                    netloc += ':%d' % parsed_url.port
                if parsed_url.username:
                    auth = parsed_url.username
                    if parsed_url.password:
                        auth += ':%s' % parsed_url.password
                    netloc = '%s@%s' % (auth, netloc)
                remote_server_addr = parse.urlunparse(
                    (parsed_url.scheme, netloc, parsed_url.path,
                     parsed_url.params, parsed_url.query, parsed_url.fragment))
            except socket.gaierror:
                self.logger.info('Could not get IP address for host: %s' % parsed_url.hostname)

        self._url = remote_server_addr
        if keep_alive:
            self._conn = httplib.HTTPConnection(
                str(addr), str(parsed_url.port), timeout=self._timeout)

        self._commands = {
            Command.HEALTH: ('GET', '/health'),
            Command.DEACTIVATE_APP: ('POST', '/session/$sessionId/wda/deactivateApp'),
            Command.STATUS: ('GET', '/status'),
            Command.SESSION: ('POST', '/session'),
            Command.GET_ALL_SESSIONS: ('GET', '/sessions'),
            Command.QUIT: ('DELETE', '/session/$sessionId'),
            Command.GET: ('POST', '/session/$sessionId/url'),
            Command.EXECUTE_SCRIPT: ('POST', '/session/$sessionId/execute'),
            Command.GET_CURRENT_URL: ('GET', '/session/$sessionId/url'),
            Command.GET_TITLE: ('GET', '/session/$sessionId/title'),
            Command.GET_PAGE_SOURCE: ('GET', '/session/$sessionId/source'),
            Command.SCREENSHOT: ('GET', '/screenshot'),
            Command.ELEMENT_SCREENSHOT: ('GET', '/session/$sessionId/screenshot/$id'),
            Command.FIND_ELEMENT: ('POST', '/session/$sessionId/element'),
            Command.FIND_ELEMENTS: ('POST', '/session/$sessionId/elements'),
            Command.GET_ACTIVE_ELEMENT:
                ('POST', '/session/$sessionId/element/active'),
            Command.FIND_CHILD_ELEMENT:
                ('POST', '/session/$sessionId/element/$id/element'),
            Command.FIND_CHILD_ELEMENTS:
                ('POST', '/session/$sessionId/element/$id/elements'),
            Command.CLICK_ELEMENT: ('POST', '/session/$sessionId/element/$id/click'),
            Command.CLEAR_ELEMENT: ('POST', '/session/$sessionId/element/$id/clear'),
            Command.SUBMIT_ELEMENT: ('POST', '/session/$sessionId/element/$id/submit'),
            Command.GET_ELEMENT_TREE: ('GET', '/session/$sessionId/tree'),
            Command.GET_ELEMENT_TEXT: ('GET', '/session/$sessionId/element/$id/text'),
            Command.SEND_KEYS_TO_ELEMENT:
                ('POST', '/session/$sessionId/element/$id/value'),
            Command.SEND_KEYS_TO_ACTIVE_ELEMENT:
                ('POST', '/session/$sessionId/keys'),
            Command.GET_ELEMENT_VALUE:
                ('GET', '/session/$sessionId/element/$id/value'),
            Command.GET_ELEMENT_TAG_NAME:
                ('GET', '/session/$sessionId/element/$id/name'),
            Command.IS_ELEMENT_SELECTED:
                ('GET', '/session/$sessionId/element/$id/selected'),
            Command.SET_ELEMENT_SELECTED:
                ('POST', '/session/$sessionId/element/$id/selected'),
            Command.IS_ELEMENT_ENABLED:
                ('GET', '/session/$sessionId/element/$id/enabled'),
            Command.IS_ELEMENT_DISPLAYED:
                ('GET', '/session/$sessionId/element/$id/displayed'),
            Command.GET_ELEMENT_LOCATION:
                ('GET', '/session/$sessionId/element/$id/location'),
            Command.GET_ELEMENT_LOCATION_ONCE_SCROLLED_INTO_VIEW:
                ('GET', '/session/$sessionId/element/$id/location_in_view'),
            Command.GET_ELEMENT_SIZE:
                ('GET', '/session/$sessionId/element/$id/size'),
            Command.GET_ELEMENT_RECT:
                ('GET', '/session/$sessionId/element/$id/rect'),
            Command.GET_ELEMENT_ATTRIBUTE:
                ('GET', '/session/$sessionId/element/$id/attribute/$name'),
            Command.ELEMENT_EQUALS:
                ('GET', '/session/$sessionId/element/$id/equals/$other'),
            Command.SWITCH_TO_FRAME: ('POST', '/session/$sessionId/frame'),
            Command.SWITCH_TO_PARENT_FRAME: ('POST', '/session/$sessionId/frame/parent'),
            Command.SWITCH_TO_WINDOW: ('POST', '/session/$sessionId/window'),
            Command.CLOSE: ('DELETE', '/session/$sessionId/window'),
            Command.IMPLICIT_WAIT:
                ('POST', '/session/$sessionId/timeouts/implicit_wait'),
            Command.EXECUTE_ASYNC_SCRIPT: ('POST', '/session/$sessionId/execute_async'),
            Command.SET_SCRIPT_TIMEOUT:
                ('POST', '/session/$sessionId/timeouts/async_script'),
            Command.SET_TIMEOUTS:
                ('POST', '/session/$sessionId/timeouts'),
            Command.DISMISS_ALERT:
                ('POST', '/session/$sessionId/dismiss_alert'),
            Command.ACCEPT_ALERT:
                ('POST', '/session/$sessionId/accept_alert'),
            Command.SET_ALERT_VALUE:
                ('POST', '/session/$sessionId/alert_text'),
            Command.GET_ALERT_TEXT:
                ('GET', '/session/$sessionId/alert_text'),
            Command.SET_ALERT_CREDENTIALS:
                ('POST', '/session/$sessionId/alert/credentials'),
            Command.CLICK:
                ('POST', '/session/$sessionId/click'),
            Command.DOUBLE_CLICK:
                ('POST', '/session/$sessionId/doubleclick'),
            Command.MOUSE_DOWN:
                ('POST', '/session/$sessionId/buttondown'),
            Command.MOUSE_UP:
                ('POST', '/session/$sessionId/buttonup'),
            Command.MOVE_TO:
                ('POST', '/session/$sessionId/moveto'),
            Command.GET_WINDOW_SIZE:
                ('GET', '/session/$sessionId/window/size'),
            Command.SET_WINDOW_SIZE:
                ('POST', '/session/$sessionId/window/$windowHandle/size'),
            Command.GET_WINDOW_POSITION:
                ('GET', '/session/$sessionId/window/$windowHandle/position'),
            Command.SET_WINDOW_POSITION:
                ('POST', '/session/$sessionId/window/$windowHandle/position'),
            Command.MAXIMIZE_WINDOW:
                ('POST', '/session/$sessionId/window/$windowHandle/maximize'),
            Command.SET_SCREEN_ORIENTATION:
                ('POST', '/session/$sessionId/orientation'),
            Command.GET_SCREEN_ORIENTATION:
                ('GET', '/session/$sessionId/orientation'),
            Command.SINGLE_TAP:
                ('POST', '/session/$sessionId/touch/click'),
            Command.TOUCH_DOWN:
                ('POST', '/session/$sessionId/touch/down'),
            Command.TOUCH_UP:
                ('POST', '/session/$sessionId/touch/up'),
            Command.TOUCH_MOVE:
                ('POST', '/session/$sessionId/touch/move'),
            Command.TOUCH_SCROLL:
                ('POST', '/session/$sessionId/touch/scroll'),
            Command.DOUBLE_TAP:
                ('POST', '/session/$sessionId/touch/doubleclick'),
            Command.LONG_PRESS:
                ('POST', '/session/$sessionId/touch/longclick'),
            Command.FLICK:
                ('POST', '/session/$sessionId/touch/flick'),
            Command.EXECUTE_SQL:
                ('POST', '/session/$sessionId/execute_sql'),
            Command.GET_LOCATION:
                ('GET', '/session/$sessionId/location'),
            Command.SET_LOCATION:
                ('POST', '/session/$sessionId/location'),
            Command.GET_APP_CACHE:
                ('GET', '/session/$sessionId/application_cache'),
            Command.GET_APP_CACHE_STATUS:
                ('GET', '/session/$sessionId/application_cache/status'),
            Command.CLEAR_APP_CACHE:
                ('DELETE', '/session/$sessionId/application_cache/clear'),
            Command.GET_NETWORK_CONNECTION:
                ('GET', '/session/$sessionId/network_connection'),
            Command.SET_NETWORK_CONNECTION:
                ('POST', '/session/$sessionId/network_connection'),
            Command.GET_LOCAL_STORAGE_ITEM:
                ('GET', '/session/$sessionId/local_storage/key/$key'),
            Command.REMOVE_LOCAL_STORAGE_ITEM:
                ('DELETE', '/session/$sessionId/local_storage/key/$key'),
            Command.GET_LOCAL_STORAGE_KEYS:
                ('GET', '/session/$sessionId/local_storage'),
            Command.SET_LOCAL_STORAGE_ITEM:
                ('POST', '/session/$sessionId/local_storage'),
            Command.CLEAR_LOCAL_STORAGE:
                ('DELETE', '/session/$sessionId/local_storage'),
            Command.GET_LOCAL_STORAGE_SIZE:
                ('GET', '/session/$sessionId/local_storage/size'),
            Command.GET_SESSION_STORAGE_ITEM:
                ('GET', '/session/$sessionId/session_storage/key/$key'),
            Command.REMOVE_SESSION_STORAGE_ITEM:
                ('DELETE', '/session/$sessionId/session_storage/key/$key'),
            Command.GET_SESSION_STORAGE_KEYS:
                ('GET', '/session/$sessionId/session_storage'),
            Command.SET_SESSION_STORAGE_ITEM:
                ('POST', '/session/$sessionId/session_storage'),
            Command.CLEAR_SESSION_STORAGE:
                ('DELETE', '/session/$sessionId/session_storage'),
            Command.GET_SESSION_STORAGE_SIZE:
                ('GET', '/session/$sessionId/session_storage/size'),
            Command.CURRENT_CONTEXT_HANDLE:
                ('GET', '/session/$sessionId/context'),
            Command.CONTEXT_HANDLES:
                ('GET', '/session/$sessionId/contexts'),
            Command.SWITCH_TO_CONTEXT:
                ('POST', '/session/$sessionId/context'),
            Command.QTA_FIND_ELEMENTS:
                ('POST', '/session/$sessionId/qta/element/$id/elements'),
            Command.QTA_DEVICE_CLICK:
                ('POST', '/session/$sessionId/qta/click'),
            Command.QTA_ELEMENT_CLICK:
                ('POST', '/session/$sessionId/qta/element/$id/click'),
            Command.QTA_DEVICE_DOUBLE_CLICK:
                ('POST', '/session/$sessionId/qta/doubleclick'),
            Command.QTA_ELEMENT_DOUBLE_CLICK:
                ('POST', '/session/$sessionId/wda/element/$id/doubleTap'),
            Command.QTA_DEVICE_LONG_CLICK:
                ('POST', '/session/$sessionId/qta/longclick'),
            Command.QTA_ELEMENT_LONG_CLICK:
                ('POST', '/session/$sessionId/wda/element/$id/touchAndHold'),
            Command.QTA_DEVICE_SENDKEYS:
                ('POST', '/session/$sessionId/qta/sendkeys'),
            Command.QTA_ELEMENT_SENDKEYS:
                ('POST', '/session/$sessionId/qta/element/$id/sendkeys'),
            Command.QTA_DEVICE_DRAG:
                ('POST', '/session/$sessionId/qta/drag'),
            Command.QTA_ELEMENT_DRAG:
                ('POST', '/session/$sessionId/qta/element/$id/drag'),
            Command.QTA_GET_PARENT_ELEMENT:
                ('POST', '/session/$sessionId/qta/element/$id/parent'),
            Command.QTA_GET_CHILDREN_ELEMENTS:
                ('POST', '/session/$sessionId/qta/element/$id/children'),
            Command.QTA_SCROLL_TO_VISIBLE:
                ('POST', '/session/$sessionId/qta/element/$id/scroll'),
            Command.QTA_DRAG_TO_VALUE:
                ('POST', '/session/$sessionId/qta/element/$id/slider'),
            Command.QTA_GET_ELEMENT_ATTRS:
                ('POST', '/session/$sessionId/qta/element/$id/attrs'),
            Command.QTA_ALERT_RULES_UPDATE:
                ('POST', '/qta/alertrules/update'),
            Command.QTA_ELEMENT_SETVALUE:
                ('POST', '/session/$sessionId/qta/element/$id/value'),
            Command.QTA_ELEMENT_TREE:
                ('POST', '/session/$sessionId/qta/element/$id/tree'),
            Command.QTA_STOP_AGENT:
                ('POST', '/qta/stop'),
            Command.QTA_GET_FOREGROUND_APP_NAME:
                ('GET', '/qta/appName'),
            Command.QTA_GET_FOREGROUND_APP_PID:
                ('GET', '/qta/appPid'),
            Command.QTA_GET_ELEMENT_WIN_INFO:
                ('GET', '/session/$sessionId/qta/element/$id/wininfo'),
            Command.QTA_ALERT_DISMISS:
                ('POST', '/qta/alert/dismiss'),
            Command.QTA_DEVICE_LOCK:
                ('POST', '/qta/device/lock'),    
            Command.QTA_DEVICE_UNLOCK:
                ('POST', '/qta/device/unlock'),  
            Command.QTA_SANDBOX_LIST:
                ('POST', '/qta/sandbox/list'),
            Command.QTA_SANDBOX_REMOVE:
                ('POST', '/qta/sandbox/remove'),
            Command.QTA_ALBUM_UPLOAD:
                ('POST', '/qta/album/upload'),
            Command.QTA_STUB_CALL:
                ('POST', '/qta/stub'),
            Command.QTA_DEVICE_VOLUME:
                ('POST', '/qta/device/volume'),     
            Command.QTA_DEVICE_SIRI:
                ('POST', '/qta/device/siri'),       
            Command.QTA_DEVICE_SCREEN_DIRECTION:
                ('POST', '/qta/device/screenDirection'), 
            Command.QTA_DEVICE_DETAIL_INFO:
                ('POST', '/qta/device/detailInfo'),
            Command.QTA_WHEEL_SELECT:
                ('POST', '/session/$sessionId/qta/element/$id/wheel/select'),
            Command.FORCE_TOUCH:
                ('POST', '/session/$sessionId/wda/element/forceTouch/$id'),
        }

    def execute(self, command, params):
        """Send a command to the remote server.
        Any path subtitutions required for the URL mapped to the command should be
        included in the command parameters.

        :param command: A string specifying the command to execute.
        :type command: str
        :param params: A dictionary of named parameters to send with the command as its JSON payload.
        :type params: dict
        :returns: dict 
        """
        command_info = self._commands[command]
        assert command_info is not None, 'Unrecognised command %s' % command
        data = json.dumps(params)
        path = string.Template(command_info[1]).substitute(params)
        url = '%s%s' % (self._url, path)
        return self._request(command_info[0], url, body=data)

    def _request(self, method, url, body=None):
        """Send an HTTP request to the remote server.

        :param method: A string for the HTTP method to send the request with.
        :type method: str
        :param url: A string for the URL to send the request to.
        :type url: str
        :param body: A string for request body. Ignored unless method is POST or PUT.
        :type body: str
        :returns: A dictionary with the server's parsed JSON response.
        """
        self.logger.debug('%s %s %s' % (method, url, body))
        
        for _ in range(3):
            try:
                parsed_url = parse.urlparse(url)
        
                if self.keep_alive:
                    headers = {"Connection": 'keep-alive', method: parsed_url.path,
                               "User-Agent": "Python http auth",
                               "Content-type": "application/json;charset=\"UTF-8\"",
                               "Accept": "application/json"}
                    if parsed_url.username:
                        auth = base64.standard_b64encode(('%s:%s' %
                               (parsed_url.username, parsed_url.password)).encode('ascii')).decode('ascii').replace('\n', '')
                        headers["Authorization"] = "Basic %s" % auth
                    if body and method != 'POST' and method != 'PUT':
                        body = None
                    try:
                        self._conn.request(method, parsed_url.path, body, headers)
                        resp = self._conn.getresponse()
                    except (httplib.HTTPException, socket.error):
                        self._conn.close()
                        raise
        
                    statuscode = resp.status
                else:
                    password_manager = None
                    if parsed_url.username:
                        netloc = parsed_url.hostname
                        if parsed_url.port:
                            netloc += ":%s" % parsed_url.port
                        cleaned_url = parse.urlunparse((parsed_url.scheme,
                                                           netloc,
                                                           parsed_url.path,
                                                           parsed_url.params,
                                                           parsed_url.query,
                                                           parsed_url.fragment))
                        password_manager = url_request.HTTPPasswordMgrWithDefaultRealm()
                        password_manager.add_password(None,
                                                      "%s://%s" % (parsed_url.scheme, netloc),
                                                      parsed_url.username,
                                                      parsed_url.password)
                        request = Request(cleaned_url, data=body.encode('utf-8'), method=method)
                    else:
                        request = Request(url, data=body.encode('utf-8'), method=method)
        
                    request.add_header('Accept', 'application/json')
                    request.add_header('Content-Type', 'application/json;charset=UTF-8')
        
                    if password_manager:
                        opener = url_request.build_opener(url_request.HTTPRedirectHandler(),
                                                          HttpErrorHandler(),
                                                          url_request.HTTPBasicAuthHandler(password_manager),
                                                          url_request.ProxyHandler({}))
                    else:
                        opener = url_request.build_opener(url_request.HTTPRedirectHandler(),
                                                          HttpErrorHandler(),
                                                          url_request.ProxyHandler({}))
                    resp = opener.open(request, timeout=self._timeout)
                    statuscode = resp.code
                    if not hasattr(resp, 'getheader'):
                        if hasattr(resp.headers, 'getheader'):
                            resp.getheader = lambda x: resp.headers.getheader(x)
                        elif hasattr(resp.headers, 'get'):
                            resp.getheader = lambda x: resp.headers.get(x)
        
                data = resp.read()
                try:
                    if 300 <= statuscode < 304:
                        return self._request('GET', resp.getheader('location'))
                    body = data.decode('utf-8').replace('\x00', '').strip()
                    if 399 < statuscode < 500:
                        return {'status': statuscode, 'value': body}
                    content_type = []
                    if resp.getheader('Content-Type') is not None:
                        content_type = resp.getheader('Content-Type').split(';')
                    if not any([x.startswith('image/png') for x in content_type]):
                        try:
                            data = json.loads(body.strip())
                        except ValueError:
                            if 199 < statuscode < 300:
                                status = ErrorCode.SUCCESS
                            else:
                                status = ErrorCode.UNKNOWN_ERROR
                            return {'status': status, 'value': body.strip()}
        
                        assert type(data) is dict, (
                            'Invalid server response body: %s' % body)
                        # Some of the drivers incorrectly return a response
                        # with no 'value' field when they should return null.
                        if 'value' not in data:
                            data['value'] = None
                        return data
                    else:
                        data = {'status': 0, 'value': body.strip()}
                        return data
                finally:
                    self.logger.debug("Finished Request")
                    resp.close()
                
            except socket.timeout:
                self.logger.error('Remote Connection timeout')
                raise XCTestAgentTimeoutException('XCTestAgent response is timed out')
            except Exception as e:
                self.logger.error('Remote Connection:%s' % str(e))
