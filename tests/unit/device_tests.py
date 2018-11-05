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
'''iOS Device接口的单元测试用例
'''


import unittest
import mock
import os

from qt4i.device import Device
from qt4i.device import IOSDeviceResourceHandler
from qt4i.icontrols import Element
from qt4i.app import App


class DeviceAcquirementTest(unittest.TestCase):
    '''acquire device test
    '''
    
    def test_no_device(self):
        devices = []
        IOSDeviceResourceHandler.iter_resource = mock.MagicMock(return_value=iter(devices))
        from testbase.resource import ResourceNotAvailable
        self.assertRaises(ResourceNotAvailable, lambda:Device())
        
    @mock.patch('qt4i.device.Device._dismiss_alert')
    @mock.patch('qt4i.driver.host.RPCServerHost.start_simulator')
    def test_single_device(self, dismiss_alert, start_simulator):
        udid = '6CA54461-A267-47FB-B473-554532E32D2D'
        devices = [{
            'id':udid,
            'udid':udid,
            'name':'iPhoneX',
            'host':'127.0.0.1',
            'port':12306,
            'is_simulator':True,
            'version':'12.0',
        },]
        IOSDeviceResourceHandler.iter_resource = mock.MagicMock(return_value=iter(devices))
        device = Device()
        self.assertEqual(device.udid, udid, 'acquire device failed')
        device.release()


class DeviceActionTest(unittest.TestCase):
    '''device action test
    '''
    
    @mock.patch('qt4i.device.Device._dismiss_alert')
    @mock.patch('qt4i.driver.host.RPCServerHost.start_simulator')
    def setUp(self, dismiss_alert, start_simulator):
        udid = '6CA54461-A267-47FB-B473-554532E32D2D'
        devices = [{
            'id':udid,
            'udid':udid,
            'name':'iPhoneX',
            'host':'127.0.0.1',
            'port':12306,
            'is_simulator':True,
            'version':'12.0',
        },]
        IOSDeviceResourceHandler.iter_resource = mock.MagicMock(return_value=iter(devices))
        self.device = Device()
        self.device._driver = mock.MagicMock()
    
    def tearDown(self):
        self.device.release()
        
    def _start_app(self):
        bundle_id = 'com.tencent.demo'
        app_params = None
        env = {
            'rules_of_alert_auto_handle' : [],
            'flag_alert_auto_handled'    : False
        }
        self.assertTrue(self.device.start_app(bundle_id, app_params, env), 'start app failed')       

    def test_start_app(self):
        self._start_app()
        
    def test_click(self):
        self._start_app()
        self.device.click() 
          
    def test_click2(self):
        app = App(self.device, 'com.tencent.demo')
        app.start()
        element = Element(app, 2)
        self.device.click2(element)
    
    def test_screenshot(self):
        data = 'base64 demo data'
        import base64
        encoded_data = base64.encodestring(data)
        self.device._driver.device.capture_screen.return_value = encoded_data
        result = self.device.screenshot()
        self.assertTrue(result[0], 'screenshot error:%s' % result[1])
        
    def test_get_crash_log(self):
        self.device._driver.device.get_crash_log.return_value = 'test1234567890'
        self._start_app()
        crash_file = self.device.get_crash_log('demo')
        self.assertTrue(os.path.isfile(crash_file), 'export crash log failed')
