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
from qt4i.app import NLCType
from qt4i.util import EnumDirect


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
        self.device._host = mock.MagicMock()
    
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
        
    def test_stop_app(self):
        self._start_app()
        self.device.driver.device.stop_app.return_value = True
        result = self.device.stop_app()
        self.assertTrue(result, 'stop app failed')
        
    def test_get_foreground_app_name(self):
        expected_name = 'Safari'
        self.device.driver.device.get_foreground_app_name.return_value = expected_name
        app_name = self.device.get_foreground_app_name()
        self.assertEqual(app_name, expected_name, 'get_foreground_app_name failed')

    def test_get_foreground_app_pid(self):
        expected_pid = '2018'
        self.device.driver.device.get_foreground_app_pid.return_value = expected_pid
        app_pid = self.device.get_foreground_app_pid()
        self.assertEqual(app_pid, expected_pid, 'get_foreground_app_pid failed')

    def test_screenshot(self):
        data = 'base64 demo data'
        import base64
        encoded_data = base64.encodestring(data)
        self.device.driver.device.capture_screen.return_value = encoded_data
        result = self.device.screenshot()
        self.assertTrue(result[0], 'screenshot error:%s' % result[1])

    def test_print_uitree_with_return(self):
        self._start_app()
        self.device.driver.device.get_element_tree.return_value = \
            {"classname": "Application", "label": "7.8.5_gn", "name": "7.8.5_gn", "value":"",
             "visible":True, "enabled": True, "children":{}}
        result = self.device.print_uitree(True)
        self.assertIsInstance(result, dict, 'print_uitree should have a dict return')

    def test_print_uitree_without_resturn(self):
        self._start_app()
        self.device.driver.device.get_element_tree.return_value = \
            {"classname": "Application", "label": "7.8.5_gn", "name": "7.8.5_gn", "value":"",
             "visible":True, "enabled": True, "children":{}}
        result = self.device.print_uitree()
        self.assertIsNone(result, 'print_uitree should return None: %s' % type(result))

    def test_click(self):
        self._start_app()
        self.device.click() 
          
    def test_click2(self):
        app = App(self.device, 'com.tencent.demo')
        app.start()
        element = Element(app, 2)
        self.device.click2(element)
    
    def test_long_click(self):
        self._start_app()
        x = 0.5
        y = 0.5
        self.device.long_click(x, y)

    def test_double_click(self):
        self._start_app()
        x, y = 0.5, 0.5
        self.device.double_click(x, y)

    def test_drag(self):
        self._start_app()
        from_x = 0.9
        from_y = 0.5
        to_x = 0.1
        to_y = 0.5
        duration = 0.5
        self.device.drag(from_x, from_y, to_x, to_y, duration)

    def test_drag2(self):
        self._start_app()
        self.device.drag2(EnumDirect.Right)

    def test_flick(self):
        self._start_app()
        from_x = 0.9
        from_y = 0.5
        to_x = 0.1
        to_y = 0.5
        self.device.flick(from_x, from_y, to_x, to_y)

    def test_flick2(self):
        self._start_app()
        self.device.flick2(EnumDirect.Down)

    def test_flick3(self):
        self._start_app()
        from_x = 0.9
        from_y = 0.5
        to_x = 0.1
        to_y = 0.5
        repeat = 1
        interval = 0.5
        velocity = 1000
        self.device.flick3(from_x, from_y, to_x, to_y, repeat, interval, velocity)

    def test_deactivate_app_for_duration(self):
        self.device.deactivate_app_for_duration(5)

    def test_install(self):
        app_path = "/tmp/demoapp.zip"
        self.device.install(app_path)

    def test_uninstall(self):
        bundle_id = 'com.tencent.demo'
        self.device.uninstall(bundle_id)

    def test_get_crash_log(self):
        self.device.driver.device.get_crash_log.return_value = 'test1234567890'
        self._start_app()
        crash_file = self.device.get_crash_log('demo')
        self.assertTrue(os.path.isfile(crash_file), 'export crash log failed')

    def test_pull_file_from_localhost(self):
        files = ['/tmp/test.log']
        self.device._driver.device.pull_file.return_value = files
        bundle_id = 'com.tencent.demo'
        remotepath = '/Library/Caches/test.log'
        localpath = '/tmp'
        result = self.device.pull_file(bundle_id, remotepath, localpath)
        self.assertEqual(files, result, 'pull_file from localhost failed')

    def test_push_file_with_http_file(self):
        bundle_id = 'com.tencent.demo'
        localpath = 'http://test.com/files/test.png'
        remotepath = '/Documents'
        self.device.driver.device.download_file_and_push.return_value = True
        result = self.device.push_file(bundle_id, localpath, remotepath)
        self.assertTrue(result, 'push_file with http file failed')

    def test_push_file_with_local_file(self):
        bundle_id = 'com.tencent.demo'
        localpath = '/tmp/test.png'
        remotepath = '/Documents'
        self.device.driver.device.push_file.return_value = True
        result = self.device.push_file(bundle_id, localpath, remotepath)
        self.assertTrue(result, 'push_file with local file failed')

    def test_list_files(self):
        bundle_id = 'com.tencent.demo'
        file_path = '/Documents/caches'
        expected_files = ['/Documents/caches/1.png', '/Documents/caches/2.png']
        self.device.driver.device.list_files.return_value = expected_files
        result = self.device.list_files(bundle_id, file_path)
        self.assertEqual(expected_files, result, 'list files failed')

    def test_download_file(self):
        file_url = 'http://test.com/files/test.png'
        remotepath = '/Documents'
        self.device.download_file(file_url, remotepath)

    def test_remove_files(self):
        bundle_id = 'com.tencent.demo'
        file_path = '/Documents/caches/logs'
        self.device.remove_files(bundle_id, file_path)

    def test_reboot(self):
        self.device.reboot()

    def test_get_driver_log(self):
        self.device.get_driver_log()

    def test_get_log(self):
        self.device.get_log()

    def test_get_syslog(self):
        watch_time = 60
        process_name = 'QQ'
        self.device.get_syslog(60, process_name)

    def test_cleanup_log(self):
        self.device.cleanup_log()

    def test_get_user_app_list(self):
        expected_apps = [{'com.tencent.demo': 'Demo'}]
        self.device.driver.device.get_app_list.return_value = expected_apps
        result = self.device.get_app_list("user")
        self.assertEqual(expected_apps, result, 'get_app_list failed')

    def test_get_system_app_list(self):
        expected_apps = [{'com.apple.mobilesafari': 'Safari'}]
        self.device.driver.device.get_app_list.return_value = expected_apps
        result = self.device.get_app_list("system")
        self.assertEqual(expected_apps, result, 'get_app_list failed')

    def test_get_all_app_list(self):
        expected_apps = [{'com.tencent.demo': 'Demo'}, {'com.apple.mobilesafari': 'Safari'}]
        self.device.driver.device.get_app_list.return_value = expected_apps
        result = self.device.get_app_list("all")
        self.assertEqual(expected_apps, result, 'get_app_list failed')

    def test_lock(self):
        self.device.lock()

    def test_unlock(self):
        self.device.unlock()

    def test_volume(self):
        self.device._volume('up')
        self.device._volume('down')
        self.device._volume('silent')

    def test_screen_direction(self):
        self.device._screen_direction('up')
        self.device._screen_direction('down')
        self.device._screen_direction('left')
        self.device._screen_direction('right')

    def test_siri(self):
        self.device._siri('Maps')

    def test__dismiss_alert(self):
        rules = [{'button_text':'^确定$|^好$|^允许$|^OK$|^Allow$'}]
        self.device._dismiss_alert(rules)

    def test_switch_network(self):
        nlc_type = NLCType.EDGE
        import qt4i
        qt4i.app.Preferences = mock.MagicMock()
        self.device.switch_network(0, nlc_type)

    def test_set_host_proxy(self):
        server = '127.0.0.1'
        port = 12345
        wifi = 'Test-WiFi'
        import qt4i
        qt4i.app.Preferences = mock.MagicMock()
        self.device.set_host_proxy(server, port, wifi)

    def test_reset_host_proxy(self):
        import qt4i
        qt4i.app.Preferences = mock.MagicMock()
        self.device.reset_host_proxy()

    def test_upload_photo(self):
        img_file = os.path.join(os.path.dirname(__file__), 'hello.png')
        with open(img_file, 'w+') as fd:
            fd.write('hello world'*100)
        album_name = "QT4i"
        try:
            self.device.upload_photo(img_file, album_name)
        except:
            os.remove(img_file)
            raise

    def test_call_qt4i_stub(self):
        method = 'foo'
        params = [1, 2]
        self.device.call_qt4i_stub(method, params)

    def test_get_device_detail(self):
        device_detail = {u'color': 'black', u'model': 'iPhone 7 Plus', u'storage': '32GB'}
        self.device.driver.device.get_device_detail.return_value = device_detail
        result = self.device.get_device_detail()
        self.assertEqual(result, device_detail, 'get_device_detail failed')

    def test_get_icon_badge(self):
        num = '5'
        self.device.driver.element.get_element_attr.return_value = '5 '
        result = self.device.get_icon_badge('QQ')
        self.assertEqual(result, num, 'get_icon_badge failed')


class KeyBoardTest(unittest.TestCase):

    @mock.patch('qt4i.device.Device._dismiss_alert')
    @mock.patch('qt4i.driver.host.RPCServerHost.start_simulator')
    def setUp(self, dismiss_alert, start_simulator):
        udid = '6CA54461-A267-47FB-B473-554532E32D2D'
        devices = [{
            'id': udid,
            'udid': udid,
            'name': 'iPhoneX',
            'host': '127.0.0.1',
            'port': 12306,
            'is_simulator': True,
            'version': '12.0',
        }, ]
        IOSDeviceResourceHandler.iter_resource = mock.MagicMock(return_value=iter(devices))
        self.device = Device()
        self.device._driver = mock.MagicMock()
        self.device._host = mock.MagicMock()

    def tearDown(self):
        self.device.release()

    def test_send_keys(self):
        from qt4i.device import Keyboard
        Keyboard(self.device).send_keys('hello world')
