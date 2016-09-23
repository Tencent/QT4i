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
# 2014/11/16    cherry    创建
# 2015/10/21    jerry   支持远程多终端
import time
import urllib
import datetime
import threading
import os
import xmlrpclib
import base64

from testbase import logger
from util import EnumDirect, Rectangle
from testbase.util import Singleton
from testbase.conf import settings
from _driver.driverserver import DriverManager
from _driver.driverserver import DriverWrapper

class DeviceManager(object):
    '''设备管理类，用于多个设备的申请、查询和管理（此类仅用于Device内部，测试用例中请勿直接使用）
    '''
    
    __metaclass__ = Singleton

    def __init__(self):
        self._index = 0
        self._lock = threading.Lock()
        self._drivers = {}  
        
    @property
    def drivers(self):
        return self._drivers
        
    def acquire_driver(self):
        '''申请本地设备或者协助设备，默认第一个申请的设备为本地设备，后续申请的设备均为协作设备
        
        :rtype: DriverWrapper or None
        '''  
        device = None
        driver = None
        with self._lock:
            self._index += 1
        if self._index == 1:
            DriverManager().start()
            driver = DriverWrapper()
        else:
            if hasattr(settings, 'QT4I_REMOTE_DRIVERS'):
                remote_drivers = settings.QT4I_REMOTE_DRIVERS
                index = self._index - 2
                if len(remote_drivers) - 1 == index:
                    driver = DriverWrapper(remote_drivers[index]['ip'])
                    device = 'debug'
                else:
                    raise RuntimeError("本地没有配置协作设备，请检查settings中的REMOTE_DRIVERS变量")
            else:
                from _driver._respool import DevicePool
                device = DevicePool().acquire(None)
                if device:
                    driver = DriverWrapper(device.host)
                else:
                    raise RuntimeError("协作设备申请失败")
        with self._lock:
            self._drivers[driver] = device
        return driver 
    
    def release_driver(self, driver):
        '''释放指定的远程协助设备
        
        :param driver: 远程协作设备
        :type driver: DriverWrapper
        '''  
        with self._lock:
            if driver in self._drivers:
                if not hasattr(settings, 'QT4I_REMOTE_DRIVERS'):
                    if self._drivers[driver]:
                        from _driver._respool import DevicePool
                        DevicePool().release(self._drivers[driver])
                del self._drivers[driver]
                self._index -= 1

    def release_drivers(self):
        '''释放所有占用的远程协助设备
        ''' 
        for driver in self._drivers.keys():
            self.release_driver(driver)


class Device(object):
    '''iOS设备基类（包含基于设备的UI操作接口）
    '''
    Encoding = 'UTF-8'
    Devices = []
    
    class EnumDeviceType(object):
        '''定义设备类型'''
        iPhone, iPad, iPod, Unknown = ('iPhone', 'iPad', 'iPod', 'Unknown')
    
    @classmethod
    def release_all(cls):
        for device in cls.Devices:
            device.release()
    
    def __init__(self, device_id=None):
        '''Device构造函数
        
        :param device_id: 本地设备的UDID
                           不指定UDID则获取已连接的真机，无真机连接则使用默认的模拟器
                           指定Simulator则使用默认的模拟器
                           指定UDID则使用指定的设备，如果是真机的UDID，真机不存在则异常，如果是模拟器的UDID，对不上号则异常（要注意每一台Mac的模拟器的UDID都不相同）。
        :type device_id: str|None
        '''
        self._device_manager = DeviceManager()
        self._driver_wrapper = self._device_manager.acquire_driver()
        self._driver = self._driver_wrapper.driver
        self._device = None
        # -*- -*- -*- -*- -*- -*-
        # 第一默认: 第一台连接的真机
        if device_id is None:
            _real_devices = self._driver.dt.get_real_devices()
            if len(_real_devices) > 0:
                self._device = _real_devices[0]
        # 第二默认: 默认模拟器
        if self._device is None and (device_id is None or str(device_id).lower() == 'simulator'):
            self._driver.dt.start_simulator()
            _simulators = self._driver.dt.get_simulators()
            for _simulator in _simulators:
                if _simulator['state'] == "Booted":
                    self._device = _simulator
                    break
        # 第三指定: 指定设备
        if self._device is None and device_id is not None and str(device_id).lower() != 'simulator':
            _device = self._driver.dt.get_device_by_udid(device_id)
            if _device is not None:
                self._device = _device
        # -*- -*- -*- -*- -*- -*-
        if self._device is None: raise Exception('无可用的真机和模拟器: device_udid=%s' % device_id)
        # -*- -*- -*- -*- -*- -*-
        self._device_udid = self._device['udid']
        self._device_name = self._device['name']
        self._device_ios = self._device['ios']
        self._device_type = self.EnumDeviceType.Unknown
        self._device_simulator = self._device['simulator']
        self._app_started = False
        self._keyboard = Keyboard(self)
        Device.Devices.append(self)
        logger.info('[%s] Device - Connect - %s - %s (%s)' % (datetime.datetime.fromtimestamp(time.time()), self.name, self.udid, self.ios_version))

    @property
    def driver(self):
        '''设备所在的driver
        
        :rtype: xmlrpclib.ServerProxy
        '''
        return self._driver

    @property
    def udid(self):
        '''设备的udid
        
        :rtype: str
        '''
        if isinstance(self._device_udid, basestring):
            return self._device_udid.encode(self.Encoding)
    
    @property
    def name(self):
        '''设备名
        
        :rtype: str
        '''
        if isinstance(self._device_name, basestring):
            return self._device_name.encode(self.Encoding)
    
    @property
    def ios_version(self):
        '''iOS版本
        
        :rtype: str
        '''
        if isinstance(self._device_ios, basestring):
            return self._device_ios.encode(self.Encoding)

    @property
    def ios_type(self):
        '''iOS设备类型
        
        :rtype: str
        '''
        if isinstance(self._device_type, basestring) and self._device_type != self.EnumDeviceType.Unknown:
            self._device_type = self._driver.imobiledevice.get_device_type_by_udid(self.udid)
            return self._device_type.encode(self.Encoding)

    @property
    def simulator(self):
        '''是否模拟器
        
        :rtype: boolean
        '''
        return self._device_simulator
    
    @property
    def rect(self):
        '''屏幕大小
        
        :rtype : Rectangle
        '''
        rect   = self._driver.uia.target.get_rect(self._device_udid)
        origin = rect['origin']
        size   = rect['size']
        return Rectangle(origin['x'], origin['y'], origin['x'] + size['width'], origin['y'] + size['height'])

    @property
    def keyboard(self):
        '''获取键盘
        '''
        return self._keyboard
    
    def start_app(self, app_name, app_params, trace_template=None, trace_output=None, retry=5, timeout=55, instruments_timeout=20 * 60):
        '''启动APP
        
        :param app_name: APP Bundle ID
        :type app_name: str
        :param app_params: app启动参数
        :type app_params: dict
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
        :return: boolean
        '''
        if not self._app_started:
            if self._driver.ins.start(self._device_udid, self._device_simulator, app_name, app_params, trace_template, trace_output, retry, timeout, instruments_timeout):
                self._app_started = True
        return self._app_started == True
    
    def _stop_app(self):
        '''终止APP
        
        :return: boolean
        '''
        if self._app_started:
            if self._driver.ins.release(self._device_udid):
                self._app_started = False
                Device.Devices.remove(self)
        return self._app_started == False
    
    def release(self):
        '''终止APP
        '''
        self._stop_app()
        self._device_manager.release_driver(self._driver_wrapper)
        logger.info('[%s] Device - Release - %s - %s (%s)' % (datetime.datetime.fromtimestamp(time.time()), self.name, self.udid, self.ios_version))

    # 上层对象如果多处引用，会带来问题
    # def __del__(self):
    #     '''析构
    #     '''
    #     self.release()
    
    def _check_app_started(self):
        '''检测APP是否已启动
        
        :raises: Exception
        '''
        if not self._app_started:
            raise Exception('app not started')
    
    def screenshot(self, image_path):
        '''截屏
        
        :param image_path: 截屏图片的存放路径 (默认存储路径为临时路径，在启动APP时被清空)
        :type image_path: str
        :return: boolean 
        '''
        result = True
        try:
            self._check_app_started()
            self._driver.ins.capture_screen(self._device_udid, image_path)
        except Exception:
            result = False
            if not self.simulator:
                result = self._driver.imobiledevice.get_screenshot_by_udid(image_path, self._device_udid)
        
        if result and self._device_manager.drivers[self._driver_wrapper]:
                with open(os.path.realpath(image_path), "wb") as fd:
                    data = self._driver.get_binary_data(image_path).data
                    fd.write(base64.decodestring(data))
        return os.path.isfile(image_path)
    
    def print_uitree(self):
        '''打印界面树
        '''
        self._check_app_started()
        _ui_tree = urllib.unquote(self._driver.uia.target.get_element_tree(self._device_udid))
        _ui_tree = _ui_tree.replace('\r', '\\r')
        _ui_tree = _ui_tree.replace('\n', '\\n')
        _ui_tree = _ui_tree.replace('\\', '\\\\')
        _ui_tree = eval(_ui_tree)
        def _print(_tree, _spaces='', _indent='|---'):
            _line = _spaces + '{  ' + ',   '.join([
                'classname: "%s"' % _tree['classname'],
                'label: %s' % ('"%s"' % _tree['label'] if _tree['label'] else 'null'),
                'name: %s' % ('"%s"' % _tree['name' ] if _tree['name' ] else 'null'),
                'value: %s' % ('"%s"' % _tree['value'] if _tree['value'] else 'null'),
                'visible: %s' % ('true' if _tree['visible'] else 'false'),
                'enabled: %s' % ('true' if _tree['enabled'] else 'false'),
                'valid: %s' % ('true' if _tree['valid'] else 'false'),
                'focus: %s' % ('true' if _tree['focus'] else 'false'),
                'rect: %s' % _tree['rect']]) + '  }'
            print _line
            for _child in _tree['children']: _print(_child, _spaces + _indent, _indent)
        _print(_ui_tree)
    
    def click(self, x=0.5, y=0.5):
        '''点击屏幕
        
        :param x: 横向坐标（从左向右，屏幕百分比）
        :type x: float
        :param y: 纵向坐标（从上向下，屏幕百分比）
        :type y: float
        '''
        self._check_app_started()
        self._driver.uia.target.tap(self._device_udid, {'x':x, 'y':y})
        
    def long_click(self, x, y, duration=3):
        '''长按屏幕
        
        :param x: 横向坐标（从左向右计算，绝对坐标值）
        :type x: float
        :param y: 纵向坐标（从上向下计算，绝对坐标值）
        :type y: float
        :param duration: 持续时间（秒）
        :type duration: float
        '''
        self._check_app_started()
        self._driver.uia.target.tap_with_options(self._device_udid, {'x':x, 'y':y}, {'duration':duration})
        
    def double_click(self, x, y):
        '''双击屏幕
        
        :param x: 横向坐标（从左向右计算，屏幕百分比）
        :type x: float
        :param y: 纵向坐标（从上向下计算，屏幕百分比）
        :type y: float
        '''
        self._check_app_started()
        x = x * self.rect.width
        y = y * self.rect.height
        self._driver.uia.target.double_tap(self._device_udid, {'x':x, 'y':y})
    
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
        self._driver.uia.target.drag_from_to_for_duration(self._device_udid, from_point, to_point, duration, repeat, interval)
    
    def drag(self, from_x=0.9, from_y=0.5, to_x=0.1, to_y=0.5, duration=0.5, repeat=1, interval=0):
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
        :param repeat: 重复该操作
        :type repeat: int
        :param interval: 重复该操作的间隙时间（秒）
        :type interval: float
        '''
        self._drag_from_to_for_duration({'x': from_x, 'y': from_y}, {'x': to_x, 'y': to_y}, duration, repeat, interval)
    
    def drag2(self, direct=EnumDirect.Left):
        '''回避屏幕边缘，全屏在屏幕中央拖拽
        
        :param direct: 拖拽的方向
        :type  direct: EnumDirect.Left|EnumDirect.Right|EnumDirect.Up|EnumDirect.Down
        '''
        if direct == EnumDirect.Left  : self._driver.uia.target.drag_right_to_left(self._device_udid)
        if direct == EnumDirect.Right : self._driver.uia.target.drag_left_to_right(self._device_udid)
        if direct == EnumDirect.Up    : self._driver.uia.target.drag_down_to_up(self._device_udid)
        if direct == EnumDirect.Down  : self._driver.uia.target.drag_up_to_down(self._device_udid)
    
    def _flick_from_to(self, from_point, to_point, repeat=1, interval=0):
        '''回避屏幕边缘，全屏滑动/拂去
        
        :attention: 如有过场动画，需要等待动画完毕
        :param from_point  : 起始坐标偏移百分比
        :type from_point   : dict : { x: 0.5, y: 0.8 }
        :param to_point    : 结束坐标偏移百分比
        :type to_point     : dict : { x: 0.5, y: 0.1 }
        :param repeat      : 重复该操作
        :type repeat       : int
        :param interval    : 重复该操作的间隙时间（秒）
        :type interval     : float
        '''
        self._check_app_started()
        self._driver.uia.target.flick_from_to(self._device_udid, from_point, to_point, repeat, interval)
    
    def flick(self, from_x=0.9, from_y=0.5, to_x=0.1, to_y=0.5, repeat=1, interval=0):
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
        self._flick_from_to({'x': from_x, 'y': from_y}, {'x': to_x, 'y': to_y}, repeat, interval)
    
    def flick2(self, direct=EnumDirect.Left):
        '''回避屏幕边缘，全屏在屏幕中央滑动/拂去
        
        :param direct: 滑动/拂去的方向
        :type  direct: EnumDirect.Left|EnumDirect.Right|EnumDirect.Up|EnumDirect.Down
        '''
        if direct == EnumDirect.Left  : self._driver.uia.target.flick_right_to_left(self._device_udid)
        if direct == EnumDirect.Right : self._driver.uia.target.flick_left_to_right(self._device_udid)
        if direct == EnumDirect.Up    : self._driver.uia.target.flick_down_to_up(self._device_udid)
        if direct == EnumDirect.Down  : self._driver.uia.target.flick_up_to_down(self._device_udid)

    def deactivate_app_ror_duration(self, seconds=3):
        '''将App置于后台一定时间
        
        :param seconds: 秒
        :type seconds: int
        :return: boolean
        '''
        return self._driver.uia.target.deactivate_app_ror_duration(self._device_udid, seconds)
    
    def install(self, app_path):
        '''安装应用程序
        
        :param app_path: ipa或app安装包的路径(注意：真机和模拟器的安装包互不兼容)
        :type app_path: str
        :return: boolean
        '''
        return self._driver.dt.install(app_path, self._device_udid)
    
    def uninstall(self, bundle_id):
        '''卸载应用程序
        
        :param bundle_id: APP的bundle_id，例如：com.tencent.qq.dailybuild.test
        :type bundle_id: str
        :return: boolean
        '''
        return self._driver.dt.uninstall(bundle_id, self._device_udid)
    
    def get_crash_log(self, procname):
        '''获取指定进程的最新的crash日志
        
        :param proc_name: app的进程名，可通过xcode查看
        :type proc_name: str  
        :return: string or None - crash日志路径
        '''
        if self.simulator:
            return None
        crash_log_path = self._driver.imobiledevice.get_crash_log(procname, self._device_udid)
        if self._device_manager.drivers[self._driver_wrapper]:
                with open(os.path.realpath(crash_log_path), "wb") as fd:
                    data = self._driver.get_binary_data(crash_log_path).data
                    fd.write(base64.decodestring(data))
        return crash_log_path if crash_log_path and os.path.isfile(crash_log_path) else None
    
    def copy_to_local(self, bundle_id, remotepath, localpath='/tmp',is_dir = False):
        '''拷贝手机中sandbox指定目录的文件到Mac本地
        
        :param bundle_id: app的bundle id
        :type bundle_id: str   
        :param remotepath: sandbox上的目录或者文件，例如：/Library/Caches
        :type remotepath: str        
        :param localpath: 本地的目录
        :type localpath: str
        :param is_dir: remotepath是否为目录，默认为单个文件
        :type is_dir: boolean
        :return: list or None
        '''
        if self.simulator:
            return None
        
        files = self._driver.imobiledevice.copy_to_local(bundle_id, remotepath, localpath, self._device_udid, is_dir)
        if self._device_manager.drivers[self._driver_wrapper]:
            for f in files:
                with open(os.path.realpath(f), "wb") as fd:
                    data = self._driver.get_binary_data(f).data
                    fd.write(base64.decodestring(data))
        return files if files and os.path.isfile(files[0]) else None

    def copy_to_remote(self, bundle_id, localpath, remotepath):
        '''拷贝Mac本地文件到手机中sandbox的指定目录地
        
        :param bundle_id: app的bundle id
        :type bundle_id: str   
        :param localpath: Mac上的文件路径
        :type localpath: str
        :param remotepath: iPhone上的目录或者文件，例如：/Documents/
        :type remotepath: str        
        :return: boolean
        '''
        if self.simulator:
            return False
        
        if self._device_manager.drivers[self._driver_wrapper]:
            with open(localpath, "rb") as fd:
                binary_data = xmlrpclib.Binary(fd.read())
                self._driver.send_binary_data(binary_data, localpath)
                
        return self._driver.imobiledevice.copy_to_remote(bundle_id, localpath, remotepath, self._device_udid)

    def remove_file(self, bundle_id, app_files):
        '''删除手机上app中的文件或者目录(主要用于app的日志或者缓存的清理)
        
        :param bundle_id: app的bundle id
        :type bundle_id: str   
        :param app_files: sandbox上的目录或者文件，例如：/Library/Caches/QQINI/
        :type app_files: str
        ''' 
        if self.simulator:
            return
        self._driver.imobiledevice.remove(bundle_id, app_files, self._device_udid)       

    def reboot(self):
        '''重启手机
        '''
        if self.simulator:
            return
        self._driver.imobiledevice.reboot(self._device_udid)
    

    
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
        self._driver.uia.keyboard.sent_keys(self._device.udid, keys)

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
if __name__ == '__main__':
    device_manager = DeviceManager()
    driver_wrapper = device_manager.acquire_driver()
    res = driver_wrapper.driver.is_working
    print 'driver is working: %s'  % res
