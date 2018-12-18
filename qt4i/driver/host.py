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
'''RPC Server Host Driver
'''

from __future__ import absolute_import, print_function

import os
import base64
from qt4i.driver.rpc import rpc_method
from qt4i.driver.rpc import RPCEndpoint
from qt4i.driver.tools.dt import DT
from qt4i.driver.xctest.agent import XCUITestAgentManager

BUFFER_SIZE = 1024*1024*100


class RPCServerHost(RPCEndpoint):
    """RPC Server Host API
    """
    agent_manager = XCUITestAgentManager()
    
    def __init__(self, rpc_server):
        self.rpc_server = rpc_server
        RPCEndpoint.__init__(self)
    
    @rpc_method
    def pull_file_data(self, filepath, seek_index, buffer_size=BUFFER_SIZE):
        '''copy file from rpc server
        
        :param filepath: file path of rpc server
        :type filename: str
        :returns: six.xmlrpc_client.Binary
        '''
        if os.path.exists(filepath):
            with open(filepath, "rb") as fd:
                seek = seek_index * buffer_size
                if seek <= os.path.getsize(filepath):
                    fd.seek(seek)
                    data = base64.b64encode(fd.read(buffer_size))
                    return data
                return None
        else:
            raise Exception('file(%s) does not exist' % filepath)

    @rpc_method
    def push_file_data(self, data, filepath):
        '''copy file to rpc server
        
        :param data: file data
        :type data: str
        :param filepath: file path of rpc server
        :type filepath: str
        :returns: boolean
        '''
        if os.path.exists(filepath):
            os.remove(filepath)
        with open(filepath, "wb") as fd:
            fd.write(base64.decodestring(data))
        return os.path.isfile(filepath)
  
    @rpc_method
    def list_devices(self):
        '''list all devices of rpc server host
        
        :return: list
        '''
        return DT().get_devices()
    
    @rpc_method
    def list_real_devices(self):
        '''list all real iOS devices of rpc server host
        
        :returns: list
        '''
        return DT().get_real_devices()
    
    @rpc_method
    def list_simulators(self):
        '''list all iOS simulators of rpc server host
        
        :returns: list
        '''
        return DT().get_simulators()
    
    @rpc_method
    def start_simulator(self, udid=None):
        '''start iOS simulator of rpc server host
        
        :param udid: udid of iOS simulator
        :type udid: str
        :returns: boolean
        '''
        return DT().start_simulator(udid)
    
    @rpc_method
    def get_device_by_udid(self, udid):
        '''inquire device by udid
        
        :param udid: udid of device
        :type udid: str
        :returns: dict or None
        '''
        return DT().get_device_by_udid(udid)
    
    @rpc_method
    def echo(self):
        '''test xmlrpc server started
        
        :returns: boolean
        '''
        return True
    
    @rpc_method
    def stop_all_agents(self):
        '''
        stop all agents
        '''
        XCUITestAgentManager.stop_all_agents()
