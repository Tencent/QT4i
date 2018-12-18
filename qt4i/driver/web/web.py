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
'''iOS WebInspector API Driver
'''

from __future__ import absolute_import, print_function

from qt4i.driver.rpc import rpc_method
from qt4i.driver.rpc import RPCEndpoint
from qt4i.driver.tools.dt import DT
from qt4i.driver.tools.logger import get_logger
from qt4i.driver.web.wkrdp import RealDeviceProtocol
from qt4i.driver.web.wkrdp import SimulatorProtocol


class WebInspector(RPCEndpoint):
    '''
    iOS Web Inpector API, 提供iOS的webview的javascript注入接口
    '''
    rpc_name_prefix = "web."
    WKRDP = {}
    WKRDP_SEPARATOR = ':'
    
    def __init__(self, rpc_server, device_id):
        self.udid = device_id
        self.logger = get_logger("driverserver_%s" % device_id)
        RPCEndpoint.__init__(self)

    @rpc_method
    def get_page_id(self, bundle_id, title, url):
        ub = self.WKRDP_SEPARATOR.join([self.udid,bundle_id])
        self.logger.info('current app sessions:%s' % WebInspector.WKRDP)
        if ub not in WebInspector.WKRDP:
            if not DT().is_simulator(self.udid):
                WebInspector.WKRDP[ub] = RealDeviceProtocol(bundle_id, self.udid)
            else:
                WebInspector.WKRDP[ub] = SimulatorProtocol(bundle_id, self.udid)
            self.logger.info('[%s] wkrdp session starting' % ub)
            WebInspector.WKRDP[ub].start()
        return WebInspector.WKRDP[ub].request_current_page_id(title, url)
    
    @rpc_method
    def eval_script(self, bundle_id, frame_id, page_id, script):
        ub = self.WKRDP_SEPARATOR.join([self.udid,bundle_id])
        data = {"method":"Runtime.evaluate","params":{"expression":script,"objectGroup":"console","includeCommandLineAPI":True,"doNotPauseOnExceptionsAndMuteConsole":False,"returnByValue":False,"generatePreview":True,"saveResult":False}}
        WebInspector.WKRDP[ub].send_webkit_socket_data(data, page_id)
        result = self.WKRDP[ub].recv_webkit_socket_data()
        return result['result']['result']
    
    @rpc_method
    def release(self):
        for ub in list(self.WKRDP.keys()):
            if ub.split(self.WKRDP_SEPARATOR)[0] == self.udid:
                self.WKRDP[ub].stop()
                del self.WKRDP[ub]
    
    @rpc_method
    def release_app_session(self, bundle_id):
        ub = WebInspector.WKRDP_SEPARATOR.join([self.udid,bundle_id])
        self.logger.info('release app session:%s' % ub)
        if ub in WebInspector.WKRDP:
            WebInspector.WKRDP[ub].stop()
            del WebInspector.WKRDP[ub]  
