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
'''资源的管理和分配调度工具
'''

from __future__ import absolute_import, print_function

import threading


MAX_PORT_NUM = 50

class PortManager(object):
    '''端口管理器基类
    '''
    _port_maps = {}  # 维护映射端口字典的集合，key为'agent'或'web'
    _lock = threading.Lock()
    EnumPortType = ['agent', 'web']

    @classmethod
    def set_port(cls, port_type, udid, port=None, base=8100):
        '''设置设备udid对应的端口
        
        :param port_type: 端口类型
        :type port_type: EnumPortType
        :param udid: 设备udid
        :type udid: str
        :param port: 端口号
        :type port: int
        :param base: 基准端口
        :type base: int
        '''
        if port_type not in PortManager.EnumPortType:
            raise Exception("端口类型%s异常，正确的类型有：%s" % (port_type,  str(cls.EnumPortType)))
        if port_type not in cls._port_maps:
            with cls._lock:
                cls._port_maps[port_type] = {}
        if not port:
            port = base
        if udid not in cls._port_maps[port_type]:
            hash_port = hash(udid) % MAX_PORT_NUM
            while 1:
                with cls._lock:
                    if port not in cls._port_maps[port_type].values():
                        cls._port_maps[port_type][udid] = port
                        break
                port = base + hash_port
                hash_port = (hash_port + 1) % MAX_PORT_NUM
    
    @classmethod
    def get_port(cls, port_type, udid):
        '''通过设备udid获取对应的端口
        
        :param port_type: 端口类型
        :type port_type: EnumPortType
        :param udid: 设备udid
        :type udid: str
        '''
        if port_type not in cls.EnumPortType:
            raise Exception("端口类型%s异常，正确的类型有：%s" % (port_type,  str(cls.EnumPortType)))
        if port_type not in cls._port_maps:
            with cls._lock:
                cls._port_maps[port_type] = {}
        if udid not in cls._port_maps[port_type]:
            if port_type == 'web':
                cls.set_port(port_type, udid, base=27753)
            else:
                cls.set_port(port_type, udid)
        return cls._port_maps[port_type][udid]
    
    @classmethod
    def exist(cls, port_type, udid):
        '''判断端口字典中是否已存在该设备
        
        :param port_type: 端口类型
        :type port_type: EnumPortType
        :param udid: 设备udid
        :type udid: str
        '''
        if port_type not in cls.EnumPortType:
            raise Exception("端口类型%s异常，正确的类型有：%s" % (port_type,  str(cls.EnumPortType)))
        if port_type not in cls._port_maps:
            with cls._lock:
                cls._port_maps[port_type] = {}
        return udid in cls._port_maps[port_type]
    
    @classmethod
    def del_port(cls, port_type, udid):
        '''从字典中删除设备及端口
        
        :param port_type: 端口类型
        :type port_type: EnumPortType
        :param udid: 设备udid
        :type udid: str
        '''
        if port_type not in cls.EnumPortType:
            raise Exception("端口类型%s异常，正确的类型有：%s" % (port_type,  str(cls.EnumPortType)))
        if port_type not in cls._port_maps:
            with cls._lock:
                cls._port_maps[port_type] = {}
        if udid in cls._port_maps[port_type]:
            with cls._lock:
                cls._port_maps[port_type].pop(udid)
    
    @classmethod
    def ports(cls, port_type):
        '''返回端口字典
        
        :param port_type: 端口类型
        :type port_type: EnumPortType
        '''
        if port_type not in cls.EnumPortType:
            raise Exception("端口类型%s异常，正确的类型有：%s" % (port_type,  str(cls.EnumPortType)))
        if port_type not in cls._port_maps:
            with cls._lock:
                cls._port_maps[port_type] = {}
        return cls._port_maps[port_type]