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
'''iOS WebKit Remote debug Protocol
'''

from __future__ import absolute_import, print_function

import json
import re
import struct
import socket
import subprocess
import uuid
from past.builtins import xrange
from six import BytesIO
from six import PY3
from six import PY2

from biplist import Data
from biplist import readPlist
from biplist import writePlist

from pymobiledevice.lockdown import LockdownClient
from qt4i.driver.tools.logger import get_logger
from qt4i.driver.tools.sched import PortManager
from qt4i.driver.tools.dt import DT


class EnumSelector(object):
    '''
    iOS Web Inspector消息类型（包含发送消息、接收消息）
    '''
    
    #发送消息类型
    SEND_REPORT_ID = "_rpc_reportIdentifier:"
    SEND_FORWARD_GET_LISTING = "_rpc_forwardGetListing:"
    SEND_FORWARD_SOCKET_SETUP = "_rpc_forwardSocketSetup:"
    SEND_FORWARD_SOCKET_DATA = "_rpc_forwardSocketData:"
    SEND_INDICATE_WEBVIEW = "_rpc_forwardIndicateWebView:"
    
    #接收消息类型
    ON_REPORT_SETUP = "_rpc_reportSetup:"
    ON_REPORT_DRIVER_LIST = "_rpc_reportConnectedDriverList:"
    ON_REPORT_CONNECTED_APP_LIST = "_rpc_reportConnectedApplicationList:"
    ON_APP_CONNECTED = "_rpc_applicationConnected:"
    ON_APP_UPDATED = "_rpc_applicationUpdated:"
    ON_APP_SENT_LISTING = "_rpc_applicationSentListing:"
    ON_APP_SENT_DATA = "_rpc_applicationSentData:"
    ON_APP_DISCONNECTED = "_rpc_applicationDisconnected:"


class WebInspectorError(Exception):
    pass


class WIPageUpdateError(Exception):
    """Web页面发生id更新"""
    pass


class WIPageNotFoundError(Exception):
    """Web页面未找到page id"""
    pass


class WebKitRemoteDebugProtocol(object):
    '''
    iOS WebKit 远程调试协议
    '''

    MAX_PLIST_LEN = 8192 - 512  # 7.5k
    FINAL_MSG = "WIRFinalMessageKey"
    PARTIAL_MSG = "WIRPartialMessageKey"

    def __init__(self, bundle_id, udid=None):
        self.app_bundle_id = bundle_id
        self.udid = udid
        if self.udid:
            self.logger = get_logger("driverserver_%s" % self.udid)
        else:
            self.logger = get_logger()
        self.seq = 0  # webkit调试命令的序号
        self.conn_id = str(uuid.uuid1()).upper()
        self.sender_key = str(uuid.uuid4()).upper()
        self.retry = 5  # 初始化消息的重试次数
        self.msgbuf = []
        self.cached_pages = []
        self.app_id = None
        self.page_id = None
        self.host_app_ids = []
    
    @property
    def is_complete_supported(self):
        raise NotImplementedError    
        
    def start(self):
        '''启动调试服务
        '''
        raise NotImplementedError
    
    def stop(self):
        '''停止调试服务
        '''
        if hasattr(self, '_sock'):
            self._sock.close()
        
    def send(self, data):
        total = 0
        while total < len(data):
            sent = self._sock.send(data[total:])
            if sent == 0:
                raise WebInspectorError("socket connection (send) error")
            total = total + sent
            
    def recv(self, size=4):
        data = ''
        if PY3:
            data = b''
        while len(data) < size:
            chunk = self._sock.recv(size-len(data))
            if not chunk or len(chunk) == 0:
                raise WebInspectorError("socket connection (recv) error")
            data = data + chunk
        return data     
    
    def _plist_to_bin(self, plist):
        f = BytesIO()
        writePlist(plist, f)
        return f.getvalue()
    
    def _plist_from_bin(self, data):
        f = BytesIO(data)
        return readPlist(f)
    
    def _init_app_id(self):
        request = {'__argument': {'WIRConnectionIdentifierKey': self.conn_id}, 
                   '__selector': EnumSelector.SEND_REPORT_ID}
        self.send_webkit_message(request)
        for _ in xrange(self.retry):
            response = self.recv_webkit_response()
            self.logger.info("wkrdp response:%s" % response)
            if response['__selector'] == EnumSelector.ON_REPORT_SETUP:
                continue
            elif response['__selector'] == EnumSelector.ON_REPORT_CONNECTED_APP_LIST:
                apps_dict = response['__argument']['WIRApplicationDictionaryKey']
                for k in apps_dict:
                    app_info = apps_dict[k]
                    app_bundle_id = app_info['WIRApplicationBundleIdentifierKey']
                    app_id = app_info['WIRApplicationIdentifierKey']
                    
                    if 'WIRHostApplicationIdentifierKey' in app_info: # web页面内嵌在一个app
                        host_app_id = app_info['WIRHostApplicationIdentifierKey']
                        host_app_bundle_id = apps_dict[host_app_id]['WIRApplicationBundleIdentifierKey']
                        if self.app_bundle_id == host_app_bundle_id :
                            self.host_app_ids.append(app_id)
                    if self.app_bundle_id == app_bundle_id:
                        self.app_id = app_id
                        self.app_name = app_info['WIRApplicationNameKey']
                if self.app_id:
                    return
            elif response['__selector'] == EnumSelector.ON_APP_CONNECTED: #单个app信息上报
                app_info = response['__argument']
                if self.app_bundle_id == app_info['WIRApplicationBundleIdentifierKey']:
                    self.app_id = app_info['WIRApplicationIdentifierKey']
                    self.app_name = app_info['WIRApplicationNameKey']
                    return 
        raise Exception('[bundle_id:%s] app id not found' % self.app_bundle_id)

    def _sort_page_ids(self, pages):
        '''排序规则--最新出现的pageID放到list末尾
        '''
        new_cached_pages = [p for p in self.cached_pages if p in pages]
        self.cached_pages = [p for p in pages.keys() if p not in new_cached_pages]
        new_cached_pages.extend(self.cached_pages)
        self.cached_pages = new_cached_pages

    def _get_default_page_id(self, pages):
        '''取最近更新的page作为当前page id
        '''
        new_cached_pages = [p for p in self.cached_pages if p in pages]
        self.cached_pages = [p for p in pages.keys() if p not in new_cached_pages]
        new_cached_pages.extend(self.cached_pages)
        self.cached_pages = new_cached_pages
        ################################ 排除同一个页面空的Webview
        for p in new_cached_pages:
            if 'WIRURLKey' not in pages[p].keys() or \
                (pages[p]['WIRURLKey'].startswith('applewebdata') and pages[p]['WIRTitleKey'] == ''):
                self.cached_pages.remove(p)
                self.cached_pages.insert(0, p) #仅将空page移到队列最前面，保证page列表后续不会进入循环更新
        ################################
        self.logger.info('cached_pages: %s'  %  self.cached_pages)
        page_id = self.cached_pages[-1]
        self.logger.info('page id: %s'  %  self.page_id)
        self.logger.info('new page id: %s'  %  page_id)
        self.title = pages[page_id]['WIRTitleKey']
        self.logger.info('title: %s'  % self.title.encode('utf-8'))
        self.url = pages[page_id]['WIRURLKey']
        self.logger.info('url: %s'  % self.url)
        return page_id
    
    def _get_page_id_by_title(self, pages, title):
        self.logger.info("wkrdp:get_page_id_by_title [%s] of pages" % title)
        self._sort_page_ids(pages)
        for page in pages:
            if 'WIRTitleKey' in pages[page].keys() and pages[page]['WIRTitleKey'] == title:
                self.url = pages[page]['WIRURLKey']
                return page

    def _get_page_id_by_url(self, pages, url):
        self.logger.info("wkrdp:get_page_id_by_url [%s] of pages" %url)
        self._sort_page_ids(pages)
        for page in pages:
            if 'WIRURLKey' in pages[page].keys() and re.search(url, pages[page]['WIRURLKey']):
                self.url = pages[page]['WIRURLKey']
                return page

    def request_current_page_id(self, title=None, url=None):
        if self.app_id not in self.host_app_ids:
            self.host_app_ids.insert(0, self.app_id)
        self.logger.debug('host apps:%s' % self.host_app_ids)
        for app_id in self.host_app_ids:
            for _ in xrange(3):
                request = {'__argument': {'WIRApplicationIdentifierKey': app_id, 
                                          'WIRConnectionIdentifierKey': self.conn_id}, 
                           '__selector': EnumSelector.SEND_FORWARD_GET_LISTING}
                self.send_webkit_message(request)
                try:
                    response = self.recv_webkit_response()
                except socket.timeout:
                    self.logger.error('_rpc_forwardGetListing: timeout')
                    continue
                self.logger.info("page response: %s" % response)
                if response['__selector'] == EnumSelector.ON_REPORT_DRIVER_LIST:
                    try:
                        response = self.recv_webkit_response()
                        self.logger.info("page multi-response: %s" % response)
                    except socket.timeout:
                        continue
                if response['__selector'] == EnumSelector.ON_APP_CONNECTED:  # appID发生变更
                    app_info = response['__argument']
                    if 'WIRHostApplicationIdentifierKey' in app_info and \
                        app_info['WIRHostApplicationIdentifierKey'] == self.app_id and \
                        app_info['WIRIsApplicationProxyKey'] :
                        new_app_id = app_info['WIRApplicationIdentifierKey']
                        if new_app_id not in self.host_app_ids:
                            self.logger.info("add new app id: %s" % new_app_id)
                            self.host_app_ids.append(new_app_id)
                elif response['__selector'] == EnumSelector.ON_APP_SENT_LISTING:
                    res_app_id = response['__argument']['WIRApplicationIdentifierKey']
                    pages = response['__argument']['WIRListingKey']
                    
                    if res_app_id in self.host_app_ids or title or url:
                        if not pages: continue
                        if title:
                            page_id = self._get_page_id_by_title(pages, title)
                        elif url:
                            page_id = self._get_page_id_by_url(pages, url)
                        else:
                            page_id = self._get_default_page_id(pages)
                        if page_id:
                            if res_app_id != self.app_id:
                                self.page_id = None
                            self.app_id = res_app_id
                            return page_id
                elif response['__selector'] == EnumSelector.ON_APP_UPDATED:
                    if response['__argument']['WIRApplicationBundleIdentifierKey'] == self.app_bundle_id:
                        self.app_id = response['__argument']['WIRApplicationIdentifierKey'] 
                elif response['__selector'] == EnumSelector.ON_APP_DISCONNECTED:
                    if self.app_id == response['__argument']['WIRApplicationIdentifierKey']:
                        break
        raise WIPageNotFoundError('[%s]' % self.app_id)

    def _setup_webkit_socket(self, page_id):
        self.page_id = page_id
        request = {'__argument': {'WIRAutomaticallyPause': False, 
                                  'WIRSenderKey': self.sender_key, 
                                  'WIRApplicationIdentifierKey': self.app_id, 
                                  'WIRConnectionIdentifierKey': self.conn_id, 
                                  'WIRPageIdentifierKey': int(page_id)
                                  }, 
                   '__selector': EnumSelector.SEND_FORWARD_SOCKET_SETUP}
        self.send_webkit_message(request)

    def _enable_inspector(self):
        '''打开web事件的通知开关(非必须)
        '''  
        data = {"method":"Inspector.enable"}
        self.send_webkit_socket_data(data, self.page_id)
        self.logger.info(self.recv_webkit_socket_data())
        
        data = {"method":"Console.enable"}
        self.send_webkit_socket_data(data, self.page_id)
        self.logger.info(self.recv_webkit_socket_data())  
        
    def init_inspector(self):
        self._init_app_id()
         
    def send_webkit_message(self, message): 
        self.logger.info('='*80)
        self.logger.info("request:%s" % message)
        data = self._plist_to_bin(message)
        data_len = len(data)
        if self.is_complete_supported:
            tmp_data = struct.pack('!L', len(data)) + data
            self.send(tmp_data)
            return
        for i in xrange(0, data_len, self.MAX_PLIST_LEN):
            is_partial = data_len - i > self.MAX_PLIST_LEN
            if is_partial:
                partial_msg = data[i:i + self.MAX_PLIST_LEN]
                if PY2:
                    partial_msg = Data(partial_msg)
                else:
                    partial_msg = partial_msg.encode()
                tmp_data = {self.PARTIAL_MSG: partial_msg}
            else:
                final_msg = data[i:data_len - i]
                if PY2:
                    final_msg = Data(final_msg)
                else:
                    final_msg = final_msg.encode()
                tmp_data = {self.FINAL_MSG: final_msg}
            tmp_data = self._plist_to_bin(tmp_data)
            tmp_data = struct.pack('!L', len(tmp_data)) + tmp_data
            self.send(tmp_data) 

    def recv_webkit_response(self):
        data = self.recv(4)
        if not data or len(data) != 4:
            raise Exception("WKDP header is invalid")
        l = struct.unpack('!L', data)[0]
        data = self.recv(l)
        data = self._plist_from_bin(data)
        if self.is_complete_supported:
            return data
        if self.FINAL_MSG in data:
            data = data[self.FINAL_MSG]
            if self.msgbuf:
                data = ''.join(self.msgbuf) + data
                self.msgbuf = []
            data = self._plist_from_bin(data)
            return data 
        else:
            data = data[self.PARTIAL_MSG]
            self.msgbuf.append(data)
            return self.recv_webkit_response()
    
    def send_webkit_socket_data(self, data, page_id):
        if page_id != self.page_id:
            self._setup_webkit_socket(page_id)
        self.seq += 1
        data["id"] = self.seq
        data = json.dumps(data)
        if PY2:
            wrapped_data = Data(data)
        else:
            wrapped_data = data.encode()
        data = {'__argument': {'WIRSenderKey': self.sender_key,
                               'WIRConnectionIdentifierKey': self.conn_id, 
                               'WIRApplicationIdentifierKey': self.app_id, 
                               'WIRSocketDataKey': wrapped_data,
                               'WIRPageIdentifierKey': int(page_id)
                               }, 
                '__selector': EnumSelector.SEND_FORWARD_SOCKET_DATA}
        self.send_webkit_message(data)
    
    def recv_webkit_socket_data(self, ignore_id=False):
        pages_changed = False
        while True:
            try:
                response = self.recv_webkit_response()
            except socket.timeout:
                if pages_changed:
                    raise WIPageUpdateError('Retry to get new page id.')
                else:
                    raise
            self.logger.info('response: %s' % response)
            selector = response['__selector']
            if selector == EnumSelector.ON_APP_SENT_LISTING:
                self.logger.info("Pages may change!")
                pages_changed = True
                continue
            elif selector != EnumSelector.ON_APP_SENT_DATA or \
                response['__argument']['WIRApplicationIdentifierKey'] != self.app_id:
                continue
            data = response['__argument']['WIRMessageDataKey']
            data = json.loads(data.decode('UTF-8'), encoding='UTF-8')
            if ('id' in data and (data['id'] == self.seq)) or ignore_id:
                return data


class RealDeviceProtocol(WebKitRemoteDebugProtocol): 
    '''
    iOS真机的远程调试协议实现（依赖usbmuxd通信）
    '''
    
    
    def __init__(self, bundle_id='com.apple.WebKit.WebContent', udid=None):
        super(RealDeviceProtocol, self).__init__(bundle_id, udid)
        self._partial_supported = True
        
    @property
    def is_complete_supported(self):
        return not self._partial_supported
        
    def start(self):
        lockdown = LockdownClient(self.udid)
        ios_version = lockdown.allValues['ProductVersion']
        if DT.compare_version(ios_version, '11.0') >= 0: # iOS11真机以上不支持数据分割
            self._partial_supported = False
        self.web_inspector = lockdown.startService("com.apple.webinspector")
        self._sock = self.web_inspector.s
        self._sock.setblocking(False)
        self._sock.settimeout(5)
        self.init_inspector()
        
    def __del__(self):
        self.stop()


class SimulatorProtocol(WebKitRemoteDebugProtocol):
    '''
    iOS模拟器的远程调试协议实现(本地socket通信)
    '''
    
    def __init__(self, bundle_id='com.apple.WebKit.WebContent', udid=None):
        super(SimulatorProtocol, self).__init__(bundle_id, udid)
        if DT.compare_xcode_version('9.3') >= 0:
            self._sock = self._get_webinspector_socket_above_xcode93(udid)
        else:
            self._sock = self._get_webinspector_socket_below_xcode93(udid)
        self._sock.setblocking(False)
        self._sock.settimeout(3)

    def _get_webinspector_socket_above_xcode93(self, udid):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        cmd = ["xcrun", "simctl", "getenv", udid, "RWI_LISTEN_SOCKET"]
        webinspector_unix_sock = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        if PY3:
            webinspector_unix_sock = webinspector_unix_sock.decode()
        webinspector_unix_sock = webinspector_unix_sock.strip('\n')
        self.logger.debug('webinspector socket:%s' % webinspector_unix_sock)
        #'/private/tmp/com.apple.launchd.aVC7CJkaJq/com.apple.webinspectord_sim.socket'
        sock.connect(webinspector_unix_sock)
        return sock

    def _get_webinspector_socket_below_xcode93(self, udid):
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        wi_port = PortManager.get_port('web', udid)
        if wi_port is None:
            wi_port = 27753
        self.logger.info('webport: %s'  %  wi_port)
        sock.connect(('::1', wi_port))
        return sock
        
    @property
    def is_complete_supported(self):
        return True
        
    def start(self):
        self.init_inspector()
        
    def __del__(self):
        self.stop()
