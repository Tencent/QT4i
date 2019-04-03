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
'''iOS设备模块
'''

from __future__ import absolute_import, print_function, division

import base64
import datetime
import os
import pkg_resources
import subprocess
import sys
import time
import uuid
import socket
import traceback
import six
from six import PY3
from six import PY2

from testbase import context
from testbase.conf import settings
from testbase.resource import LocalResourceHandler
from testbase.resource import LocalResourceManagerBackend
from testbase.resource import TestResourceManager
from testbase import logger
from qt4i.util import EnumDirect, Rectangle

from qt4i.driver.rpc import RPCClientProxy
from qt4i.driver.util import Process


QT4i_LOGS_PATH = os.path.abspath('_attachments')
if not os.path.exists(QT4i_LOGS_PATH):
    os.makedirs(QT4i_LOGS_PATH)

Encoding = 'UTF-8'
DEFAULT_ADDR = '127.0.0.1'
DEFAULT_PORT = 12306
DEFAULT_AGENT_PORT = 8100
DEFAULT_ALERT_RULE =  settings.get('QT4I_ALERT_RULES', [{'button_text':'^确定$|^好$|^允许$|^OK$|^Allow$'}])


class DeviceServer(object):
    '''设备服务器
    '''
    def __init__(self, addr, port, udid=None, agent_port=DEFAULT_AGENT_PORT, driver_type=settings.get('IOS_DRIVER', 'xctest'), endpoint_clss=''):
        '''初始化

        :param addr: 设备主机ip
        :type addr: str
        :param port: 设备主机端口号
        :type port: int
        :param udid: 设备UDID
        :type udid: str or None
        :param agent_port: agent端口号
        :type agent_port: int
        :param driver_type: driver类型，xctest or instruments
        :type driver_type: str
        :param endpoint_clss: 注册远程调用类集，多个以";"间隔
        :type endpoint_clss: str
        '''
        unzip_path = pkg_resources.resource_filename("qt4i", "driver")  # @UndefinedVariable
        self._script = os.path.join(unzip_path,'driverserver.py')
        self._addr = addr
        self._port = port
        self._udid = udid
        self._agent_port = agent_port
        self._driver_type = driver_type
        self._endpoint_clss = endpoint_clss
        self._python = "python3" if PY3 else "python"
        if self._udid:
            self.pidfile = '/tmp/driverserver_%s.pid' % self._udid
        else:
            self.pidfile = '/tmp/driverserver.pid'
        if hasattr(settings, 'QT4i_ENDPOINT_CLSS'): # 兼容小写配置项
            self._endpoint_clss = ','.join([self._endpoint_clss, settings.QT4i_ENDPOINT_CLSS])
        elif hasattr(settings, 'QT4I_ENDPOINT_CLSS'):
            self._endpoint_clss = ','.join([self._endpoint_clss, settings.QT4I_ENDPOINT_CLSS])

    def _wait_for_started(self, timeout=60):
        begin_time = time.time()
        while time.time() - begin_time <= timeout:
            try:
                server = RPCClientProxy('/'.join(["http://%s:%s" % (self._addr, self._port), 'host/']), allow_none=True, encoding=Encoding)
                if server.echo():
                    print('server is ready')
                    return True
            except:
                print('server is not ready...')
            time.sleep(0.2)
        raise Exception('DeviceServer failed to start.')

    def start(self):
        '''启动
        '''

        if self._udid:
            if self._endpoint_clss:
                cmd = '%s %s -t %s --pidfile %s -p %d -u %s -a %d -r %s start' % (self._python,
                                                                                  self._script,
                                                                                  self._driver_type,
                                                                                  self.pidfile,
                                                                                  self._port,
                                                                                  self._udid,
                                                                                  self._agent_port,
                                                                                  self._endpoint_clss)
            else:
                cmd = '%s %s -t %s --pidfile %s -p %d -u %s -a %d start' % (self._python,
                                                                            self._script,
                                                                            self._driver_type,
                                                                            self.pidfile,
                                                                            self._port,
                                                                            self._udid,
                                                                            self._agent_port)
        else:
            if self._endpoint_clss:
                cmd = '%s %s -t %s -p %d -r %s start' % (self._python, self._script, self._driver_type, self._port, self._endpoint_clss)
            else:
                cmd = '%s %s -t %s -p %d start' % (self._python, self._script, self._driver_type, self._port)
                print(cmd)

        subprocess.Popen(cmd, shell=True)
        self._wait_for_started()

    def stop(self):
        '''停止
        '''
        if self._udid:
            subprocess.Popen('%s %s --pidfile %s -p %d -u %s stop' % (self._python, self._script, self.pidfile, self._port, self._udid), shell=True)
        else:
            subprocess.Popen('%s %s --pidfile %s -p %d stop' % (self._python, self._script, self.pidfile, self._port), shell=True)

    def restart(self):
        '''重启
        '''
        if self._udid:
            if self._endpoint_clss:
                cmd = '%s %s -t %s --pidfile %s -p %d -u %s -a %d -r %s restart' % (self._python,
                                                                                    self._script,
                                                                                    self._driver_type,
                                                                                    self.pidfile,
                                                                                    self._port,
                                                                                    self._udid,
                                                                                    self._agent_port,
                                                                                    self._endpoint_clss)
            else:
                cmd = '%s %s -t %s --pidfile %s -p %d -u %s -a %d restart' % (self._python,
                                                                              self._script,
                                                                              self._driver_type,
                                                                              self.pidfile,
                                                                              self._port,
                                                                              self._udid,
                                                                              self._agent_port)
        else:
            if self._endpoint_clss:
                cmd = '%s %s -t %s -p %d -r %s restart' % (self._python,
                                                           self._script,
                                                           self._driver_type,
                                                           self._port,
                                                           self._endpoint_clss)
            else:
                cmd = '%s %s -t %s -p %d restart' % (self._python,
                                                     self._script,
                                                     self._driver_type,
                                                     self._port)

        subprocess.Popen(cmd, shell=True)
        self._wait_for_started()

    def debug(self):
        '''调试模式启动driverserver
        '''
        if self._udid:
            if self._endpoint_clss:
                cmd = '%s %s -t %s --pidfile %s -p %d -u %s -a %d -r %s debug' % (self._python,
                                                                                  self._script,
                                                                                  self._driver_type,
                                                                                  self.pidfile,
                                                                                  self._port,
                                                                                  self._udid,
                                                                                  self._agent_port,
                                                                                  self._endpoint_clss)
            else:
                cmd = '%s %s -t %s --pidfile %s -p %d -u %s -a %d debug' % (self._python,
                                                                            self._script,
                                                                            self._driver_type,
                                                                            self.pidfile,
                                                                            self._port,
                                                                            self._udid,
                                                                            self._agent_port)
        else:
            if self._endpoint_clss:
                cmd = '%s %s -t %s -p %d -r %s debug' % (self._python,
                                                         self._script,
                                                         self._driver_type,
                                                         self._port,
                                                         self._endpoint_clss)
            else:
                cmd = '%s %s -t %s -p %d debug' % (self._python, self._script, self._driver_type, self._port)

        subprocess.Popen(cmd, shell=True)
        self._wait_for_started()

    def get_pid(self):
        """
        Returns the PID from pidfile
        """
        try:
            if self.pidfile and os.path.exists(self.pidfile):
                with open(self.pidfile, 'r') as pf:
                    pid = int(pf.read().strip())
            else:
                pid = None
        except (IOError, TypeError):
            pid = None
        return pid

    def exist(self):
        '''driverserver进程是否存在
        '''
        pid = self.get_pid()
        if pid:
            if Process().get_process_by_pid(pid, 'driverserver.py'):
                return True
        return False


class DeviceResource(object):
    '''设备资源
    '''

    def __init__(self, host, port, udid, is_simulator, name, version, csst_uri=None, resource_id=None):
        if host == socket.gethostbyname(socket.gethostname()):
            host = DEFAULT_ADDR
        self._host = host
        self._port = port
        self._udid = udid
        self._name = name
        self._version = version
        if csst_uri:
            self._ws_uri = "ws://%s/proxy/control-%s" % (csst_uri, udid)
        else:
            self._ws_uri = None
        self._driver_url = 'http://%s:%d' % (host, port)
        self._is_sim = is_simulator
        self._resource_id = resource_id

    def __getitem__(self, key):
        if key == 'id':
            return self._resource_id
        else:
            return getattr(self, key)

    @property
    def driver_url(self):
        return self._driver_url

    @property
    def ws_uri(self):
        return self._ws_uri

    @property
    def resource_id(self):
        return self._resource_id

    @property
    def host(self):
        return self._host

    @property
    def udid(self):
        return self._udid

    @property
    def is_simulator(self):
        return self._is_sim

    @property
    def name(self):
        return self._name

    @property
    def version(self):
        return self._version

    def __eq__(self, other):
        '''通过IP+UDID判断是否为同一个设备
        '''
        return self._host == other._host and self._udid == other._udid

    def __str__(self):
        return "udid:%s, ip:%s" % (self._udid, self._host)


class IOSDeviceResourceHandler(LocalResourceHandler):
    '''iOS设备资源的本地管理
    '''

    def iter_resource(self, res_group=None, condition=None):
        DeviceManager.update_local_devices()
        if isinstance(condition, six.string_types):
            condition = {'udid': condition}
        for dev in DeviceManager.devices:
            if condition:
                for k in condition:
                    if condition[k] == dev[k]:
                        break
                else:
                    if condition:
                        continue
            yield dev

LocalResourceManagerBackend.register_resource_type('ios', IOSDeviceResourceHandler())


class DeviceManager(object):
    '''设备管理类，用于多个设备的申请、查询和管理（此类仅用于Device内部，测试用例中请勿直接使用）
    '''

    devices = []


    @staticmethod
    def get_devices_from_driver(driver_ip, driver_port=12306):
        driver = RPCClientProxy('http://%s:%d/host/' % (driver_ip, driver_port), allow_none=True, encoding=Encoding)
        driver_devices = driver.list_devices()
        devices = []
        index = 0
        for dev in driver_devices:
            dev['id'] = dev['udid']
            dev['host'] = driver_ip
            dev['port'] = driver_port
            dev['is_simulator'] = dev['simulator']
            dev.pop('simulator', None)
            dev['version'] = dev['ios']
            dev.pop('ios', None)
            if dev['is_simulator']:
                devices.append(dev)
            else:
                devices.insert(index, dev)
                index += 1
        return devices

    @staticmethod
    def update_local_devices():
        '''更新本地设备列表
        '''
        devices = []
        if sys.platform == 'darwin':
            DeviceServer(DEFAULT_ADDR, DEFAULT_PORT).start()
            devices.extend(DeviceManager.get_devices_from_driver(DEFAULT_ADDR))
        if hasattr(settings, 'QT4I_REMOTE_DRIVERS'):
            remote_drivers = settings.QT4I_REMOTE_DRIVERS
            for driver in remote_drivers:
                if driver['ip'] == '127.0.0.1':
                    continue
                devices.extend(DeviceManager.get_devices_from_driver(driver['ip'], driver['port']))
        DeviceManager.devices = devices


class Device(object):
    '''iOS设备基类（包含基于设备的UI操作接口）
    '''
    Devices = []

    @classmethod
    def release_all(cls):
        devices = cls.Devices[:]
        for device in devices:
            device.release()
        del cls.Devices[:]

    @classmethod
    def cleanup_all_log(cls):
        for device in cls.Devices:
            device.cleanup_log()

    def __init__(self, attrs={}, devicemanager=None):
        '''Device构造函数

        :param attrs: 设备UDID字符串｜设备属性字典
                                    keys: udid            - 设备UDID
                                          host            - 设备主机ip
                                          is_simulator    - 是否为模拟器
        :type attrs: str|dict
        :param devicemanager: 设备管理类
        :type devicemanager: DeviceManager
        '''
        cond = {}
        if isinstance(attrs, six.string_types):
            cond['udid'] = attrs
        elif isinstance(attrs, dict):
            cond = attrs.copy()
        else:
            raise Exception('Device attributes type error: %s' % type(attrs))
        ct = None
        if devicemanager:
            self._device_resource = devicemanager.acquire_device(cond)
        else:
            ct = context.current_testcase()
            if ct is None:
                self._test_resources = TestResourceManager(LocalResourceManagerBackend()).create_session()
            else:
                self._test_resources = ct.test_resources
            self._device_resource = self._test_resources.acquire_resource("ios", condition=cond)

        if self._device_resource is None:
            raise Exception('无可用的真机和模拟器: %s' % str(cond))

        props = self._device_resource
        if 'properties' in self._device_resource: # online mode
            devprops = self._device_resource['properties']
            props = { p['name'].encode(Encoding): p['value'].encode(Encoding) for p in devprops }
            props['id'] = self._device_resource['id']

        if 'csst_uri' not in props or props['csst_uri'] == 'None':
            props['csst_uri'] = None

        self._device_resource = DeviceResource(props['host'], int(props['port']), props['udid'],
                props['is_simulator'], props['name'], props['version'], props['csst_uri'], props['id'])

        self._base_url = self._device_resource.driver_url
        self._ws_uri = self._device_resource.ws_uri
        self._host = RPCClientProxy('/'.join([self._base_url, 'host/']), self._ws_uri, allow_none=True, encoding=Encoding)
        self._device_udid = self._device_resource.udid
        self._device_name = self._device_resource.name
        self._device_ios = self._device_resource.version
        if isinstance(self._device_resource.is_simulator, bool):
            self._device_simulator = self._device_resource.is_simulator
        else:
            self._device_simulator = self._device_resource.is_simulator == str(True)

        if self._device_simulator:
            self._host.start_simulator(self._device_udid)
        self._app_started = False
        Device.Devices.append(self)
        url = '/'.join([self._base_url, 'device', '%s/' % self._device_udid])
        self._driver = RPCClientProxy(url, self._ws_uri, allow_none=True, encoding=Encoding)
        self._keyboard = Keyboard(self)
        logger.info('[%s] Device - Connect - %s - %s (%s)' % (datetime.datetime.fromtimestamp(time.time()), self.name, self.udid, self.ios_version))
        # 申请设备成功后，对弹窗进行处理
        rule = settings.get('QT4I_ALERT_DISMISS', DEFAULT_ALERT_RULE)
        if rule :
            try :
                self._dismiss_alert(rule)
            except :
                logger.exception('dismiss alert %s' % rule)

    @property
    def driver(self):
        '''设备所在的driver

        :rtype: RPCClientProxy
        '''
        return self._driver

    @property
    def udid(self):
        '''设备的udid

        :rtype: str
        '''
        result = self._device_udid
        if PY2 and isinstance(result, six.text_type):
            return result.encode(Encoding)
        return result

    @property
    def name(self):
        '''设备名

        :rtype: str
        '''
        result = self._device_name
        if PY2 and isinstance(result, six.text_type):
            return result.encode(Encoding)
        return result

    @property
    def ios_version(self):
        '''iOS版本

        :rtype: str
        '''
        result = self._device_ios
        if PY2 and isinstance(result, six.text_type):
            return result.encode(Encoding)
        return result

    @property
    def simulator(self):
        '''是否模拟器

        :rtype: boolean
        '''
        return self._device_simulator

    @property
    def rect(self):
        '''屏幕大小

        :rtype: Rectangle
        '''
        rect   = self._driver.device.get_rect()
        origin = rect['origin']
        size   = rect['size']
        return Rectangle(origin['x'], origin['y'], origin['x'] + size['width'], origin['y'] + size['height'])

    @property
    def keyboard(self):
        '''获取键盘
        '''
        return self._keyboard

    def start_app(self, bundle_id, app_params, env, trace_template=None, trace_output=None, retry=5, timeout=55):
        '''启动APP

        :param bundle_id: APP Bundle ID
        :type bundle_id: str
        :param app_params: app启动参数
        :type app_params: dict
        :param env: app的环境变量
        :type env: dict
        :param trace_template: 专项使用trace_template路径，或已配置的项
        :type trace_template: str
        :param trace_output: 专项使用trace_output路径
        :type trace_output: str
        :param retry: 重试次数（建议大于等于2次）
        :type retry: int
        :param timeout: 单次启动超时（秒）
        :type timeout: int
        :param instruments_timeout: 闲置超时（秒）
        :type instruments_timeout: int
        :rtype: boolean
        '''
        if not self._app_started:
            if self._driver.device.start_app(bundle_id, app_params, env, trace_template, trace_output, retry, timeout):
                self._app_started = True
                self.bundle_id = bundle_id
        elif 'app_name' in app_params and self.get_foreground_app_name() != app_params['app_name']:
            try:
                elements = self._driver.element.find_elements(app_params['app_name'], 2, 0.05, 'id')
                element_id = elements['elements'][-1]['element']
                self._driver.element.click(element_id)
                self.bundle_id = bundle_id
                self._app_started = True
            except:
                raise Exception('未找到名为[%s]的App' % app_params['app_name'])
        return self._app_started == True

    def stop_app(self):
        '''终止APP

        :rtype: boolean
        '''
        if self._app_started:
            if self._driver.device.stop_app(self.bundle_id):
                self._app_started = False
        return self._app_started == False

    def release(self):
        '''释放设备
        '''
        try:
            self.stop_app()
            self._driver.web.release()
            if hasattr(self, 'nlc_flag') and self.nlc_flag: #恢复网络设置
                from qt4i.app import NLCType
                self.switch_network(5, NLCType.NONE)
            if hasattr(self, 'wifi') and self.wifi: #关闭host代理
                self.reset_host_proxy()
        except Exception:
            traceback.print_exc()
        finally:
            try:
                self._test_resources.release_resource("ios", self._device_resource.resource_id)
            except:
                pass
            Device.Devices.remove(self)
            logger.info('[%s] Device - Release - %s - %s (%s)' % (datetime.datetime.fromtimestamp(time.time()), self.name, self.udid, self.ios_version))

    def get_foreground_app_name(self):
        '''获取前台app的名称
        '''
        return self._driver.device.get_foreground_app_name()

    def get_foreground_app_pid(self):
        '''获取前台app的PID
        '''
        return self._driver.device.get_foreground_app_pid()

    def _check_app_started(self):
        '''检测APP是否已启动

        :raises: Exception
        '''
        if not self._app_started:
            raise Exception('app not started')

    def screenshot(self, image_path=None):
        '''截屏，返回元组：截屏是否成功，图片保存路径

        :param image_path: 截屏图片的存放路径
        :type image_path: str
        :rtype: tuple (boolean, str)
        '''
        try:
            base64_img = self._driver.device.capture_screen()
            if not image_path:
                image_path = os.path.join(QT4i_LOGS_PATH, "p%s_%s.png" %(os.getpid(), uuid.uuid1()))
            with open(os.path.abspath(image_path), "wb") as fd:
                if PY2:
                    fd.write(base64.decodestring(base64_img))
                else:
                    fd.write(base64.decodebytes(base64_img.encode('utf-8')))
            return os.path.isfile(image_path), image_path
        except:
            logger.error('screenshot failed: %s' % traceback.format_exc())
            return False, ""

    def print_uitree(self, need_back = False):
        '''打印界面树

        :param need_back: 是否需要返回UI Tree
        :type need_back: boolean
        :return: 控件树
        :rtype: dict or None
        '''
        self._check_app_started()
        _ui_tree = self._driver.device.get_element_tree()
        def _print(_tree, _spaces='', _indent='|---'):
            _line = _spaces + '{  ' + ',   '.join([
                'classname: "%s"' % _tree['classname'],
                'label: %s' % ('"%s"' % _tree['label'] if _tree['label'] else 'null'),
                'name: %s' % ('"%s"' % _tree['name' ] if _tree['name' ] else 'null'),
                'value: %s' % ('"%s"' % _tree['value'] if _tree['value'] else 'null'),
                'visible: %s' % ('true' if _tree['visible'] else 'false'),
                'enabled: %s' % ('true' if _tree['enabled'] else 'false'),
                'rect: %s' % _tree['rect'] if 'rect' in _tree else '']) + '  }'
            print(_line)
            for _child in _tree['children']: _print(_child, _spaces + _indent, _indent)
        _print(_ui_tree)
        if need_back:
            return _ui_tree

    def click(self, x=0.5, y=0.5):
        '''点击屏幕

        :param x: 横向坐标（从左向右，屏幕百分比）
        :type x: float
        :param y: 纵向坐标（从上向下，屏幕百分比）
        :type y: float
        '''
        self._check_app_started()
        self._driver.device.click(x, y)

    def click2(self, element):
        '''基于控件坐标点击屏幕（用于直接点击控件无效的场景,尽量少用）

        :param element: 控件对象
        :type element: Element
        '''
        self._check_app_started()
        element_rect = element.rect
        device_rect = self.rect
        x = (element_rect.left + element_rect.right) / (2.0 * device_rect.width)
        y = (element_rect.top + element_rect.bottom) / (2.0 * device_rect.height)
        self._driver.device.click(x, y)

    def long_click(self, x, y, duration=3):
        '''长按屏幕

        :param x: 横向坐标（从左向右，屏幕百分比）
        :type x: float
        :param y: 纵向坐标（从上向下，屏幕百分比）
        :type y: float
        :param duration: 持续时间（秒）
        :type duration: float
        '''
        self._check_app_started()
        self._driver.device.long_click(x, y, duration)

    def double_click(self, x, y):
        '''双击屏幕

        :param x: 横向坐标（从左向右计算，屏幕百分比）
        :type x: float
        :param y: 纵向坐标（从上向下计算，屏幕百分比）
        :type y: float
        '''
        self._check_app_started()
        self._driver.device.double_click(x, y)

    def _drag_from_to_for_duration(self, from_point, to_point, duration=0.5, repeat=1, interval=0):
        '''全屏拖拽

        :attention: 如有过场动画，需要等待动画完毕
        :param from_point  : 起始坐标偏移百分比
        :type from_point   : dict : { x: 0.5, y: 0.8 }
        :param to_point    : 结束坐标偏移百分比
        :type to_point     : dict : { x: 0.5, y: 0.1 }
        :param duration    : 持续时间（秒）
        :type duration     : float
        :param repeat      : 重复该操作
        :type repeat       : int
        :param interval    : 重复该操作的间隙时间（秒）
        :type interval     : float
        '''
        self._check_app_started()
        raise NotImplementedError

    def drag(self, from_x=0.9, from_y=0.5, to_x=0.1, to_y=0.5, duration=0.5):
        '''回避屏幕边缘，全屏拖拽（默认在屏幕中央从右向左拖拽）

        :param from_x: 起点 x偏移百分比(从左至右为0.0至1.0)
        :type from_x: float
        :param from_y: 起点 y偏移百分比(从上至下为0.0至1.0)
        :type from_y: float
        :param to_x: 终点 x偏移百分比(从左至右为0.0至1.0)
        :type to_x: float
        :param to_y: 终点 y偏移百分比(从上至下为0.0至1.0)
        :type to_y: float
        :param duration: 持续时间（秒）
        :type duration: float
        '''
        self._check_app_started()
        self._driver.device.drag(from_x, from_y, to_x, to_y, duration)

    def drag2(self, direct=EnumDirect.Left):
        '''回避屏幕边缘，全屏在屏幕中央拖拽

        :param direct: 拖拽的方向
        :type  direct: EnumDirect.Left|EnumDirect.Right|EnumDirect.Up|EnumDirect.Down
        '''
        self._check_app_started()
        if direct == EnumDirect.Left  : self._driver.device.drag(0.5, 0.5, 0.1, 0.5, 0.5)
        if direct == EnumDirect.Right : self._driver.device.drag(0.5, 0.5, 0.9, 0.5, 0.5)
        if direct == EnumDirect.Up    : self._driver.device.drag(0.5, 0.5, 0.5, 0.1, 0.5)
        if direct == EnumDirect.Down  : self._driver.device.drag(0.5, 0.5, 0.5, 0.9, 0.5)

    def flick(self, from_x=0.9, from_y=0.5, to_x=0.1, to_y=0.5):
        '''回避屏幕边缘，全屏滑动/拂去（默认从右向左滑动/拂去）
        该接口比drag的滑动速度快，如果滚动距离大，建议用此接口

        :param from_x: 起点 x偏移百分比（从左至右为0.0至1.0）
        :type from_x: float
        :param from_y: 起点 y偏移百分比（从上至下为0.0至1.0）
        :type from_y: float
        :param to_x: 终点 x偏移百分比（从左至右为0.0至1.0）
        :type to_x: float
        :param to_y: 终点 y偏移百分比（从上至下为0.0至1.0）
        :type to_y: float
        '''
        self._check_app_started()
        self._driver.device.drag(from_x, from_y, to_x, to_y, 0)

    def flick2(self, direct=EnumDirect.Left):
        '''回避屏幕边缘，全屏在屏幕中央滑动/拂去

        :param direct: 滑动/拂去的方向
        :type  direct: EnumDirect.Left|EnumDirect.Right|EnumDirect.Up|EnumDirect.Down
        '''
        self._check_app_started()
        if direct == EnumDirect.Left  : self._driver.device.drag(0.5, 0.5, 0.1, 0.5, 0)
        if direct == EnumDirect.Right : self._driver.device.drag(0.4, 0.5, 0.9, 0.5, 0)
        if direct == EnumDirect.Up    : self._driver.device.drag(0.5, 0.5, 0.5, 0.1, 0)
        if direct == EnumDirect.Down  : self._driver.device.drag(0.5, 0.5, 0.5, 0.9, 0)

    def flick3(self, from_x=0.5, from_y=0.8, to_x=0.5, to_y=0.2, repeat=1, interval=0.5, velocity=1000):
        '''全屏连续滑动（默认从下向滑动）
        该接口比flick2的滑动速度快，适用于性能测试

        :param from_x: 起点 x偏移百分比（从左至右为0.0至1.0）
        :type from_x: float
        :param from_y: 起点 y偏移百分比（从上至下为0.0至1.0）
        :type from_y: float
        :param to_x: 终点 x偏移百分比（从左至右为0.0至1.0）
        :type to_x: float
        :param to_y: 终点 y偏移百分比（从上至下为0.0至1.0）
        :type to_y: float
        :param repeat: 滑动的次数
        :type repeat: int
        :param interval: 滑动的间隔时间（秒）
        :type interval: double
        :param velocity: 滑动的速度
        :type velocity: double
        '''
        self._check_app_started()
        self._driver.device.drag(from_x, from_y, to_x, to_y, 0, repeat, interval, velocity)

    def deactivate_app_for_duration(self, seconds=3):
        '''将App置于后台一定时间

        :param seconds: 秒,若为-1，则模拟按Home键的效果，也即app切到后台后必须点击app才能再次唤起
        :type seconds: int
        :return: boolean
        '''
        return self._driver.device.background_app(seconds)

    def install(self, app_path):
        '''安装应用程序

        :param app_path: ipa或app安装包的路径(注意：真机和模拟器的安装包互不兼容)
        :type app_path: str
        :rtype: boolean
        '''
        begin_time = time.time()
        result = self._driver.device.install(app_path)
        count_time = time.time() - begin_time
        logger.info("安装被测应用耗时：%.3fs" % count_time)
        return result

    def uninstall(self, bundle_id):
        '''卸载应用程序

        :param bundle_id: APP的bundle_id，例如：com.tencent.qq.dailybuild.test
        :type bundle_id: str
        :rtype: boolean
        '''
        return self._driver.device.uninstall(bundle_id)

    def get_crash_log(self, procname):
        '''获取指定进程的最新的crash日志

        :param proc_name: app的进程名，可通过xcode查看
        :type proc_name: str
        :return: crash日志路径
        :rtype: string or None
        '''
        crash_log = self._driver.device.get_crash_log(procname)
        if crash_log:
            crash_log_path = os.path.join(QT4i_LOGS_PATH, "%s_%s.crash" %(procname, uuid.uuid1()))
            with open(os.path.abspath(crash_log_path), "wb") as fd:
                fd.write(crash_log)
            return crash_log_path
        else:
            return None

    def pull_file(self, bundle_id, remotepath, localpath=None, is_dir=False, is_delete=True):
        '''拷贝手机中sandbox指定目录的文件到Mac本地

        :param bundle_id: app的bundle id
        :type bundle_id: str
        :param remotepath: sandbox上的目录或者文件，例如：/Library/Caches/test/
        :type remotepath: str
        :param localpath: 本地的目录
        :type localpath: str
        :param is_dir: remotepath是否为目录，默认为单个文件
        :type is_dir: boolean
        :return: 拷贝到本地的文件列表
        :rtype: list or None
        '''
        if localpath is None:
            localpath = QT4i_LOGS_PATH
        filepaths = []
        if self._device_resource.host != DEFAULT_ADDR:
            files = self._driver.device.pull_file(bundle_id, remotepath, '/tmp', is_dir, is_delete)
            for f in files:
                filepath = os.path.join(localpath, os.path.basename(f))
                with open(filepath, "wb") as fd:
                    data = self._host.pull_file_data(f, 0)
                    index = 1
                    while data is not None:
                        if PY2:
                            fd.write(base64.decodestring(data))
                        else:
                            fd.write(base64.decodebytes(data.encode('utf-8')))
                        data = self._host.pull_file_data(f, index)
                        index += 1
                filepaths.append(filepath)
        else:
            filepaths = self._driver.device.pull_file(bundle_id, remotepath, localpath, is_dir, is_delete)
        return filepaths

    copy_to_local = pull_file

    def push_file(self, bundle_id, localpath, remotepath):
        '''拷贝Mac本地文件到手机中sandbox的指定目录地

        :param bundle_id: app的bundle id
        :type bundle_id: str
        :param localpath: 文件路径，支持本地文件路径和http路径
        :type localpath: str
        :param remotepath: iPhone上的目录或者文件，例如：/Documents/
        :type remotepath: str
        :rtype: boolean
        '''
        if localpath.startswith('http'):
            return self._driver.device.download_file_and_push(bundle_id, localpath, remotepath)
        else:
            if self._device_resource.host != DEFAULT_ADDR:
                with open(localpath, "rb") as fd:
                    data = base64.b64encode(fd.read())
                    if PY3:
                        data = data.decode('ascii')
                    filepath = os.path.join('/tmp', os.path.basename(localpath))
                    self._host.push_file_data(data, filepath)
                    localpath = filepath
            return self._driver.device.push_file(bundle_id, localpath, remotepath)

    def list_files(self, bundle_id, file_path):
        '''列出手机上app中的文件或者目录

        :param bundle_id: app的bundle id
        :type bundle_id: str
        :param file_path: sandbox上的目录或者文件，例如：/Library/Caches/test/
        :type file_path: str
        '''
        return self._driver.device.list_files(bundle_id, file_path)

    def download_file(self, file_url, dst_path):
        '''从网上下载指定文件到本地

        :param file_url: 文件的url路径，支持http和https路径, 需要对app插桩
        :type file_url: str
        :param dst_path: 文件在手机上的存储路径，例如：/Documents
        :type dst_path: str
        '''
        method = 'createFile:withPath:size:'
        params = [file_url, dst_path, 1]
        return self.call_qt4i_stub(method, params)

    def remove_files(self, bundle_id, file_path):
        '''删除手机上app中的文件或者目录(主要用于app的日志或者缓存的清理)

        :param bundle_id: app的bundle id
        :type bundle_id: str
        :param file_path: sandbox上的目录或者文件，例如：/Library/Caches/test/
        :type file_path: str
        '''
        self._driver.device.remove_files(bundle_id, file_path)

    remove_file = remove_files

    def reboot(self):
        '''重启手机
        '''
        self._driver.device.reboot()


    def get_driver_log(self, start_time=None):
        '''获取driver日志
        :param start_time 用例执行的开始时间
        :type str

        try-catch 说明：为了兼容client以及server端，对取失败用例日志的操作（后续接口更新可删除）
        '''
        try:
            return self._driver.device.get_driver_log(start_time)
        except:
            return self._driver.device.get_driver_log()

    def get_log(self, start_time=None):
        '''获取交互日志
        :param start_time 用例执行的开始时间
        :type str

        try-catch 说明：为了兼容client以及server端，对取失败用例日志的操作（后续接口更新可删除）
        '''
        try:
            return self._driver.device.get_log(start_time)
        except:
            return self._driver.device.get_log()

    def get_syslog(self, watchtime, process_name=None):
        '''获取手机系统日志
        '''
        return self._driver.device.get_syslog(watchtime, process_name)

    def cleanup_log(self):
        '''清理交互日志
        '''
        self._driver.device.cleanup_log()
        logger.info('[%s] Device - Clean Up Logger - %s - %s (%s)' % (datetime.datetime.fromtimestamp(time.time()), self.name, self.udid, self.ios_version))

    def get_app_list(self, app_type="user"):
        '''获取设备上的app列表

        :param app_type: app的类型(user/system/all)
        :type app_type: str
        :return: list
        :rtype: app列表，例如: [{'com.tencent.demo': 'Demo'}]
        '''
        return self._driver.device.get_app_list(app_type)

    def lock(self):
        '''锁定设备（灭屏）
        '''
        self._driver.device.lock()

    def unlock(self):
        '''解锁设备
        '''
        self._driver.device.unlock()

    def _volume(self, cmd):
        '''音量调节

        :param cmd: 音量调节命令
        :type str : 'up'|'down'|'silent'
        '''
        self._driver.device.volume(cmd)

    def _screen_direction(self, direct):
        '''设置屏幕方向

        :param direct: 屏幕调节命令
        :type str : 'up'|'down'|'left'|'right'
        '''
        self._driver.device.screen_direction(direct)

    def _siri(self, cmd):
        '''siri交互

        :param cmd: 与siri交互文本
        :type str : 譬如打开一个app，直接cmd='app名'
        '''
        self._driver.device.siri(cmd)

    def _dismiss_alert(self, rule):
        '''弹窗处理

        :param rule: 弹窗处理
        :type list: rules
        '''
        self._driver.device.dismiss_alert(rule)

    def switch_network(self, network_type, nlc_type):
        '''实现网络切换

        :param network_type: 网络类型，例如：
                            0:无WIFI无xG
                            1:无WIFi有xG
                            2:有WIFI无xG
                            3:有WIFI有xG
                            4:飞行模式
        :type network_type: int
        :param nlc_type: 模拟弱网络类型
        :type nlc_type: NLCType
        '''
        self.nlc_flag = True
        from qt4i.app import Preferences
        if self._app_started:
            self._active_app_name = self.get_foreground_app_name()
            self.deactivate_app_for_duration(-1)
        else:
            self._active_app_name = None
        pre = Preferences(self)
        pre.switch_network(network_type, nlc_type)
        if self._active_app_name:
            self.deactivate_app_for_duration(-1)
            self.start_app('', {'app_name':self._active_app_name}, None)
        else:
            self.stop_app()

    def set_host_proxy(self, server, port, wifi):
        '''设置host代理

        :param server: 服务器名
        :type server: str
        :param port: 端口号
        :type port: int
        :param wifi: wifi名
        :type wifi: str
        '''
        self.wifi = wifi
        from qt4i.app import Preferences
        if self._app_started:
            self._active_app_name = self.get_foreground_app_name()
            self.deactivate_app_for_duration(-1)
        else:
            self._active_app_name = None
        pre = Preferences(self)
        pre.set_host_proxy(server, port, wifi)
        if self._active_app_name:
            self.deactivate_app_for_duration(-1)
            self.start_app('', {'app_name':self._active_app_name}, None)
        else:
            self.stop_app()

    def reset_host_proxy(self):
        '''关闭host代理
        '''
        from qt4i.app import Preferences
        pre = Preferences(self)
        pre.reset_host_proxy()

    def upload_photo(self, photo_path, album_name, cleared=True):
        '''上传照片到系统相册

        :param photo_path: 本地照片路径
        :type photo_path: str
        :param album_name: 系统相册名
        :type album_name: str
        :param cleared: 是否清空已有的同名相册
        :type cleared: boolean
        :rtype: boolean
        '''
        with open(photo_path, 'rb') as fd:
            img_data = base64.b64encode(fd.read())
            return self._driver.device.upload_photo(img_data, album_name, cleared)

    def call_qt4i_stub(self, method, params, clazz=None):
        '''QT4i Stub通用接口

        :param method: 函数名
        :type method: str
        :param params: 函数参数
        :type params: list
        :param clazz: 类名
        :type clazz: str
        :return: 插桩接口返回值
        :rtype: str
        '''
        return self._driver.device.call_qt4i_stub(method, params, clazz)

    def get_device_detail(self):
        '''获取设备型号，颜色，内存大小等详细信息
        '''
        return self._driver.device.get_device_detail()

    def get_icon_badge(self, app_name):
        '''获取设备中app消息未读数
        '''
        if self._app_started:
            self._active_app_name = self.get_foreground_app_name()
            self.deactivate_app_for_duration(-1)
        else:
            self._active_app_name = None
        elements = self._driver.element.find_elements(app_name, 2, 0.05, 'id')
        element_id = elements['elements'][-1]['element']
        value = self._driver.element.get_element_attr(element_id, 'value')
        if value == None :
            value = 0
        else :
            value = value.split(' ')
            value = value[0]
        if self._active_app_name:
            self.deactivate_app_for_duration(-1)
            self.start_app('', {'app_name':self._active_app_name}, None)
        else:
            self.stop_app()
        return value


class Keyboard(object):
    '''键盘
    '''

    def __init__(self, device):
        self._device = device
        self._driver = device.driver

    def send_keys(self, keys):
        '''键盘输入

        :param keys: 要输入的字符串
        :type keys: str
        '''
        self._driver.device.send_keys(keys)
