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
'''qt4i.driver.tools的单元测试用例
'''


import unittest
from qt4i.driver.tools.sched import PortManager

class SchedTest(unittest.TestCase):
    '''sched test
    '''
    
    def test_port_manager(self):
        port_type = "agent"
        udid1 = "aaaaaaaaaaaa"
        udid2 = "bbbbbbbbbbbb"
        PortManager.set_port(port_type, udid1)
        port1 = PortManager.get_port(port_type, udid1)
        port2 = PortManager.get_port(port_type, udid2)
        self.assertEqual(port1, 8100, 'PortManager分配端口错误')
        self.assertNotEqual(port1, port2, 'PortManager分配端口重复')
        PortManager.del_port(port_type, udid1)
        self.assertTrue(udid1 not in PortManager.ports(port_type), 'PortManager清理端口失败')