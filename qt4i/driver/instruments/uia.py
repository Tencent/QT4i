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
'''UIAutomation API driver
'''

from __future__ import absolute_import, print_function

import base64
import os
import time
import urllib
import uuid

from qt4i.driver.instruments.ins import Instruments
from qt4i.driver.rpc import rpc_method
from qt4i.driver.rpc import RPCEndpoint
from qt4i.driver.tools import mobiledevice
from qt4i.driver.tools.dt import DT
from qt4i.driver.tools.logger import rotate_logger_by_name, get_logger_path_by_name
from qt4i.driver.util.uimap import xctest2instruments


class Device(RPCEndpoint):
    '''UIATarget/UIAApplication API
    '''
    rpc_name_prefix = "device."

    def __init__(self, rpc_server, device_id):
        self.udid = device_id
        RPCEndpoint.__init__(self)
        self._instruments = Instruments(device_id)
        self.rpc_server = rpc_server
    
    @rpc_method
    def stop_agent(self):
        '''空操作(此方法只用于xctest关闭Agent)
        '''
        pass
    
    @rpc_method
    def call_primitive_function(self, method, *params):
        '''执行UIATarget的方法(此方法保留，以期应对苹果升级或调整UIA框架)
        
        :param _method      : 方法名
        :type _method       : str
        :param _params      : 参数列表(参数_method之后的任意个数参数直接转传)
        :type _params       : []
        :returns            : 方法的输出
        '''
        command = self.create_json_command('uia.target.function', method, list(params))
        return self._instruments.exec_command(command)
    
    @rpc_method
    def install(self, ipa_path):
        '''在设备上安装制定路径下的APP
        
        :param ipa_path: 要安装的app的路径
        :type ipa_path: str
        :returns: boolean -- True if successfully installed, False if not
        '''
        dt = DT()
        return dt.install(ipa_path, self.udid)
    
    @rpc_method
    def uninstall(self, bundle_id):
        '''卸载设备上的APP
        
        :param bundle_id: 要卸载的APP的Bundle_ID, 例如"tencent.com.sng.test.gn"
        :type bundle_id: str
        :returns: boolean -- if uninstall app successfully, False if not
        '''
        dt = DT()
        return dt.uninstall(bundle_id, self.udid)
    
    @rpc_method
    def reboot(self):
        '''重启手机
        '''
        mobiledevice.reboot(self.udid)
    
    @rpc_method
    def start_app(self, bundle_id, app_params, env, trace_template=None, trace_output=None, retry=3, timeout=55):
        '''启动设备上的指定APP
        
        :param bundle_id: 要启动的APP的Bundle ID
        :type bundle_id: str
        :param app_params: APP 使用的参数
        :type app_params: dict
        :param trace_template: 专项测试使用trace_template的路径
        :type trace_template: str
        :param trace_output: 专项测试使用trace_output
        :type trace_output: str
        :param retry: 启动失败重试次数
        :type retry: int
        :param timeout: 单次启动超时 (秒)
        :type timeout: int
        :returns: boolean -- True if start successfully, False if not
        ''' 
        addr = self.rpc_server.server_address
        base_uri = "http://"+addr[0]+":"+str(addr[1])
        xmlrpc_uri = '/'.join([base_uri, "device", self.udid])
        return self._instruments.start(bundle_id, app_params, env, xmlrpc_uri, trace_template, trace_output, retry, timeout)
    
    @rpc_method
    def stop_app(self, bundle_id):
        '''停止指定的app
        
        :param bundle_id: 要停止的APP的Bundle ID
        :type bundle_id: str
        :returns: boolean -- True if stop successfully, False if not
        '''
        return self._instruments.release()

    
    @rpc_method
    def get_rect(self):
        '''获取设备屏幕大小
        
        :returns: 坐标和高宽
        '''
        command = self.create_json_command('uia.target.get_rect')
        return self._instruments.exec_command(command)
    
    @rpc_method
    def get_model(self):
        '''获取设备模型
        
        :returns: str
        '''
        command = self.create_json_command('uia.target.get_model')
        return self._instruments.exec_command(command)
    
    @rpc_method
    def get_name(self):
        '''获取设备名
        
        :returns: str
        '''
        command = self.create_json_command('uia.target.get_name')
        return self._instruments.exec_command(command)
    
    @rpc_method
    def get_system_name(self):
        '''获取系统名
        
        :returns : str
        '''
        command = self.create_json_command('uia.target.get_system_name')
        return self._instruments.exec_command(command)
    
    @rpc_method
    def get_system_version(self):
        '''获取系统版本
        
        :returns: str
        '''
        command = self.create_json_command('uia.target.get_system_version')
        return self._instruments.exec_command(command)
    
    @rpc_method
    def capture_screen(self):
        '''截屏
        :returns: str -- base64编码后截图数据
        '''
        try:
            filename = '/tmp/%s.png' % uuid.uuid1()
            command = self.create_json_command('uia.target.capture_screen', filename)
            self._instruments.exec_command(command)
        except:
            device = DT().get_device_by_udid(self.udid)
            if device["simulator"]:
                raise Exception("instruments screenshot error")
            if not mobiledevice.get_screenshot(self.udid, filename):
                raise Exception("mobiledevice screenshot error")
        start_time = time.time()
        while time.time() - start_time < 15:
            if os.path.isfile(filename):
                break
            time.sleep(0.05)
        else:
            raise Exception('capture_screen error')
        
        with open(filename, "rb") as fd:
            base64_img = base64.b64encode(fd.read())
        return base64_img

    @rpc_method
    def get_element_tree(self):
        '''从顶层开始获取UI树（输出的JSON字符串数据需要URL解码）
        
        :returns: dict
        '''
        command = self.create_json_command('uia.target.get_element_tree')
        result = urllib.unquote(self._instruments.exec_command(command))
        result = result.replace('\r', '\\r')
        result = result.replace('\n', '\\n')
        result = result.replace('\\', '\\\\')
        result = eval(result)
        return result
    
    @rpc_method
    def get_element_tree_and_capture_screen(self, filepath=None):
        '''获取UI树并截屏(该接口仅限UISpy使用)
        
        :param filepath: 将图片存储至该路径（png格式）
        :type filepath: str
        :returns: dict : { element_tree: {}, capture_screen: file_path }
        '''
        command = self.create_json_command('uia.target.get_element_tree_and_capture_screen', filepath)
        result_str = urllib.unquote(self._instruments.exec_command(command))
        return result_str

    @rpc_method
    def set_alert_auto_handling_rules(self, rules):
        '''设置自动处理Alert规则
        
                    当message_text匹配到Alert框内的任意文本，则点击button_text指定的按钮。
                    文本以段为单元，元素的label、name、value分为三段文本。规则匹配范围是Alert框内的所有元素的文本。
        :param rules: 规则集合
        :type rules: list - [ {"message_text": "message_text", "button_text": "button_text"}, ... ]
        '''
        command = self.create_json_command('uia.target.set_rules_of_alert_auto_handle', rules)
        self._instruments.exec_command(command)

    @rpc_method
    def get_alert_auto_handling_rules(self):
        '''获取已设置的自动处理Alert规则
        
        :returns: list - [ {"message_text": "message_text", "button_text": "button_text"}, ... ]
        '''
        command = self.create_json_command('uia.target.get_rules_of_alert_auto_handle')
        return self._instruments.exec_command(command)

    @rpc_method
    def add_alert_auto_handling_rule(self, message_text, button_text):
        '''自动处理Alert规则，添加一项规则
        
        :param message_text: Alert内文本片段，支持正则表达式（范围是所谓文本，每个元素的label/name/value为文本段）
        :type message_text: str
        :param button_text: Alert内按钮的文本，支持正则表达式（元素的label/name/value）
        :type button_text: str
        '''
        command = self.create_json_command('uia.target.add_rule_of_alert_auto_handle', message_text, button_text)
        self._instruments.exec_command(command)

    @rpc_method
    def clear_alert_auto_handling_rules(self):
        '''自动处理Alert规则，清空所有规则
        '''
        command = self.create_json_command('uia.target.clean_rules_of_alert_auto_handle')
        self._instruments.exec_command(command)

    @rpc_method
    def disable_auto_alert_handling(self):
        '''关闭自动关闭alert框
        '''
        command = self.create_json_command('uia.target.turn_off_auto_close_alert')
        self._instruments.exec_command(command)
    
    @rpc_method
    def enable_auto_close_handling(self):
        '''打开自动关闭alert框(优先级低于set_alert_auto_handling_rules所设置的策略)
        '''
        command = self.create_json_command('uia.target.turn_on_auto_close_alert')
        self._instruments.exec_command(command)
    
    @rpc_method
    def background_app(self, seconds=3):
        '''将App置于后台一定时间
        
        :param seconds: 秒
        :type seconds: int
        '''
        command = self.create_json_command('uia.target.deactivate_app_ror_duration', seconds)
        self._instruments.exec_command(command)
    
    @rpc_method
    def click(self, x, y, options=None):
        '''单击（全局操作）
        
        :param x: 横向坐标（从左向右，屏幕百分比）
        :type x: float
        :param y: 纵向坐标（从上向下，屏幕百分比）
        :type y: float
        :param options: 屏幕操作扩展参数
        :type options: dict: {
                            : tapCount    : 1, 几次，默认1次
                            : touchCount  : 1, 几点，默认1个点（例如两个手指则为2）
                            : duration    : 0  按住的时间，默认是0
                            }
        '''
        if options == None:
            command = self.create_json_command('uia.target.tap', {'x':x, 'y':y})
        else:
            command = self.create_json_command('uia.target.tap_with_option', {'x':x, 'y':y}, options)
        self._instruments.exec_command(command)
    
    @rpc_method
    def double_click(self, x, y):
        '''双击（全局操作）
        
        :param x: 横向坐标（从左向右，屏幕百分比）
        :type x: float
        :param y: 纵向坐标（从上向下，屏幕百分比）
        :type y: float
        '''
        command = self.create_json_command('uia.target.double_tap', {'x':x, 'y':y})
        self._instruments.exec_command(command)
    
    @rpc_method
    def long_click(self, x, y, seconds=3):
        '''长按
        
        :param x: 横向坐标（从左向右，屏幕百分比）
        :type x: float
        :param y: 纵向坐标（从上向下，屏幕百分比）
        :type y: float
        :param seconds: 秒
        :type seconds: int
        '''
        command = self.create_json_command('uia.target.touch_and_hold', {'x':x, 'y':y}, seconds)
        self._instruments.exec_command(command)
    
    @rpc_method
    def drag(self, x0, y0, x1, y1, duration=0.5):
        '''拖拽（全局操作）
        
        :param x0: 起始横向坐标（从左向右，屏幕百分比）
        :type x0: float
        :param y0: 起始纵向坐标（从上向下，屏幕百分比）
        :type y0: float
        :param x1: 终止横向坐标（从左向右，屏幕百分比）
        :type x1: float
        :param y1: 终止纵向坐标（从上向下，屏幕百分比）
        :type y1: float
        :param duration: 起始坐标按下的时间（秒）
        :type duration: float
        '''
        if duration == 0:
            command = self.create_json_command('uia.target.flick_from_to', {'x':x0, 'y':y0}, {'x':x1, 'y': y1})
        else:
            command = self.create_json_command('uia.target.drag_from_to_for_duration', {'x':x0, 'y':y0}, {'x':x1, 'y': y1}, duration)
        self._instruments.exec_command(command)
    
    @rpc_method
    def pinch(self, x0, y0, x1, y1, opposing=True, seconds=1):
        '''捏合/展开
        
        :param x0: 起始横向坐标（从左向右，屏幕百分比）
        :type x0: float
        :param y0: 起始纵向坐标（从上向下，屏幕百分比）
        :type y0: float
        :param x1: 终止横向坐标（从左向右，屏幕百分比）
        :type x1: float
        :param y1: 终止纵向坐标（从上向下，屏幕百分比）
        :type y1: float
        :param opposing: True为展开；False为捏合
        :type opposing: boolean
        :param seconds: 秒
        :type seconds: int
        '''
        if opposing:
            command = self.create_json_command('uia.target.pinch_open_from_to_for_duration', {'x':x0, 'y':y0}, {'x':x1, 'y':y1}, seconds)
        else:
            command = self.create_json_command('uia.target.pinch_close_from_to_for_duration', {'x':x0, 'y':y0}, {'x':x1, 'y':y1}, seconds)
        self._instruments.exec_command(command)
    
    
    @rpc_method
    def rotate(self, x, y, options=None):
        '''旋转
        
        :param x: 横向坐标（从左向右，屏幕百分比）
        :type x: float
        :param y: 纵向坐标（从上向下，屏幕百分比）
        :type y: float
        :param options: 自定义项
        :type options: dict : {
                            : duration    : 1,    持续的时间（秒）
                            : radius      : 50,   半径
                            : rotation    : 100,  圆周，默认是圆周率PI
                            : touchCount  : 2     触摸点数量 2 - 5
                            }
        '''
        command = self.create_json_command('uia.target.rotate_with_options', {'x':x, 'y':y}, options)
        self._instruments.exec_command(command)
    
    @rpc_method
    def set_location(self, coordinates, options=None):
        '''设置设备的GPS坐标
        
        :param coordinates: 经纬度
        :type coordinates: dict : {
                            : latitude    : 100, // 以度为单位的纬度。正值表示纬度赤道以北。负值表示纬度赤道以南。
                            : longitude   : 100  // 以度为单位的经度。测量是相对于零子午线，用正值向东延伸的经络及经络的负值西侧延伸。
                            }
        :param options: 自定义项
        :type options: options : {
                        : altitude            : 50, // 海拔高度，以米为单位，相对于海平面。正值表示海拔高度。负值表示低于海平面的高度。
                        : horizontalAccuracy  : 10, // 水平半径，不确位置时的范围内，以米为单位。负的值是无效的。
                        : verticalAccuracy    : 10, // 垂直半径，不确位置时的范围内，以米为单位。负的值是无效的。
                        : course              : 1,  // 设备是移动的，不确定移动方向
                        : speed               : 1   // 移动速度（米/秒）
                        }
        '''
        if options == None:
            command = self.create_json_command('uia.target.set_location', coordinates)
        else:
            command = self.create_json_command('uia.target.set_location_with_options', coordinates, options)
        self._instruments.exec_command(command)
    
    @rpc_method
    def shake(self):
        '''摇晃设备
        '''
        command = self.create_json_command('uia.target.shake')
        self._instruments.exec_command(command)
    
    @rpc_method
    def unlock(self):
        '''解锁设备
        '''
        command = self.create_json_command('uia.target.unlock')
        self._instruments.exec_command(command)
    
    @rpc_method
    def lock(self, seconds=0):
        '''锁定设备
        :param seconds: 秒, 0表示锁定设备；大于0表示锁定一段时间后解锁
        :type seconds: int
        '''
        if seconds == 0:
            command = self.create_json_command('uia.target.lock')
        else:
            command = self.create_json_command('uia.target.lock_for_duration', seconds)
        self._instruments.exec_command(command)
        
    @rpc_method
    def send_keys(self, keys):
        '''键盘输入
        
        :param keys        : 键入的字符串
        :type keys         : str
        '''
        command = self.create_json_command('uia.keyboard.sent_keys', keys)
        self._instruments.exec_command(command)
    
    @rpc_method
    def get_driver_log(self):
        driver_log_path = self._instruments.get_driver_log()
        log = None
        if driver_log_path and os.path.isfile(driver_log_path):
            with open(driver_log_path, "rb") as fd:
                log = fd.read().decode("utf-8")
        return log
        
    @rpc_method
    def get_crash_log(self, procname):
        '''通过设备的udid的获取指定进程的最新的crash日志
        
        :param proc_name: app的进程名，可通过xcode查看
        :type proc_name: str        
        :returns: str
        '''
        return DT().get_crash_log(self.udid, procname)
    
    @rpc_method
    def get_log(self):
        '''获取日志信息
        '''
        log = ''
        log_path = get_logger_path_by_name('driverserver_%s' % self.udid)
        if log_path and os.path.isfile(log_path):
            with open(log_path, "rb") as fd:
                log = fd.read().decode("utf-8")
        return log
    
    @rpc_method
    def cleanup_log(self):
        '''清理日志
        '''
        rotate_logger_by_name('driverserver_%s' % self.udid)
    
    @rpc_method
    def push_file(self, bundle_id, localpath, remotepath):
        '''拷贝Mac本地文件到手机中sandbox的指定目录地
        
        :param bundle_id: app的bundle id
        :type bundle_id: str   
        :param localpath: Mac上的文件路径
        :type localpath: str
        :param remotepath: sandbox上的目录或者文件，例如：/Library/Caches/test/
        :type remotepath: str        
        :returns: boolean
        '''
        return DT().push_file(self.udid, bundle_id, localpath, remotepath)

    @rpc_method
    def pull_file(self, bundle_id, remotepath, localpath='/tmp', is_dir=False, is_delete = False):
        '''拷贝手机中sandbox指定目录的文件到Mac本地
        
        :param bundle_id: app的bundle id
        :type bundle_id: str   
        :param remotepath: sandbox上的目录或者文件，例如：/Library/Caches/test/
        :type remotepath: str        
        :param localpath: 本地的目录
        :type localpath: str
        :param device_udid: 设备的udid
        :type device_udid: str
        :param is_dir: remotepath是否为目录，默认为单个文件
        :type is_dir: bool
        :param is_delete: 是否删除
        :type is_delete: bool
        :returns: list or None
        '''        
        return DT().pull_file(self.udid, bundle_id, remotepath, localpath, is_dir, is_delete)    

    @rpc_method
    def remove_files(self, bundle_id, file_path):
        '''删除手机上指定app中的文件或者目录
        
        :param bundle_id: app的bundle id
        :type bundle_id: str 
        :param file_path: 待删除的文件或者目录，例如: /Documents/test.log
        :type file_path: str  
        '''
        return DT().remove_files(self.udid, bundle_id, file_path) 
       
    @rpc_method
    def get_screen_orientation(self):
        command = self.create_json_command('uia.application.get_interface_orientation')
        return self._instruments.exec_command(command)
    @rpc_method
    def stop_all_agents(self):    
        pass           

class Application(RPCEndpoint):
    '''UIAApplication API
    '''
    rpc_name_prefix = "app."
    
    def __init__(self, rpc_server, device_id):
        self.udid = device_id
        RPCEndpoint.__init__(self)
        self._instruments = Instruments(device_id)
    
    @rpc_method
    def call_primitive_function(self, method, *params):
        '''执行UIAApplication的方法(此方法保留，以期应对苹果升级或调整UIA框架)
        
        :param _method: 方法名
        :type _method: str
        :param _params: 参数列表(参数_method之后的任意个数参数直接转传)
        :type _params: []
        :returns: 方法的输出
        '''
        command = self.create_json_command('uia.application.function', method, list(params))
        return self._instruments.exec_command(command)

    @rpc_method
    def get_app_bundle_id(self):
        '''获取当前App的BundleID
        
        :returns: str -- App的Bundle ID
        '''
        command = self.create_json_command('uia.application.get_app_bundle_id')
        return self._instruments.exec_command(command)
    
    @rpc_method
    def get_app_version(self):
        '''获取App的Version
        
        :returns: str
        '''
        command = self.create_json_command('uia.application.get_app_version')
        return self._instruments.exec_command(command)

    @rpc_method
    def has_crashed(self): 
        '''当前App是否发生crash
        
        :returns: boolean
        '''
        return self._instruments.get_crash_flag()
    

class Element(RPCEndpoint):
    '''UIAElement API
    '''
    rpc_name_prefix = "element."
    
    def __init__(self, rpc_server, device_id):
        self.udid = device_id
        RPCEndpoint.__init__(self)
        self._instruments = Instruments(device_id)
        
    def decode_find_result(self, result):
        '''js 返回值解码
        
        :returns : dict -- 解码结果
        '''
        path              = urllib.unquote(result.get('path', ''))
        valid_path_part   = urllib.unquote(result.get('valid_path_part', ''))
        invalid_path_part = urllib.unquote(result.get('invalid_path_part', ''))
        elements          = result.get('elements', [])
        for i, item in enumerate(elements): 
            elements[i]['attributes'] = urllib.unquote(item.get('attributes'))
        result.update({'path':path, 'valid_path_part':valid_path_part, 'invalid_path_part':invalid_path_part, 'elements':elements})
        return result
    
    @rpc_method
    def call_primitive_function(self, method, *params):
        '''执行UIAElement的方法(此方法保留，以期应对苹果升级或调整UIA框架)
        :param method      : 方法名
        :type method       : str
        :param params      : 参数列表(参数_method之后的任意个数参数直接转传)
        :type params       : []
        :returns: 方法的输出
        '''
        command = self.create_json_command('uia.element.function', method, list(params))
        return self._instruments.exec_command(command)
    
    @rpc_method
    def find_element(self, locator, timeout=3, interval=0.005, strategy='qpath', parent_id=None):
        '''查找单个element对象，返回查找到的element对象的缓存id，不指定parent_id则从Application下开始搜索。
        
        :param locator: 定位element的字符串，例如: "/classname='UIAWindow'"
        :type locator: str
        :param timeout: 查找element的超时值（单位: 秒）
        :param interval: 在查找element的超时范围内，循环的间隔（单位: 秒）
        :type interval: float
        :param strategy: locator的类型，例如: "qpath"
        :type strategy: str
        :param parent_id: 父element的id，如不指定则从UIAApplication下查找
        :type parent_id: str
        :returns: dict : {'element': id, 'path': <encode str>, 'valid_path_part': <encode str>, 'invalid_path_part': <encode str>, 'find_count': <int>, "find_time": int}
        '''
        if strategy == "id":
            locator = "/name='%s' & maxdepth=20" % locator
            strategy = "qpath"
        locator = xctest2instruments(locator)
        command = self.create_json_command('uia.element.find', locator, timeout, interval, strategy, parent_id)
        result = self._instruments.exec_command(command)
        result = self.decode_find_result(result)
        return result
    
    @rpc_method
    def find_elements(self, locator, timeout=3, interval=0.005, strategy='qpath', parent_id=None):
        '''查找单个element对象，返回查找到的element对象的缓存id。不指定parent_id则从UIAApplication下开始搜索。
        
        :param locator: 定位element的字符串，例如: "/classname='UIAWindow'"
        :type locator: str
        :param timeout: 查找element的超时值（单位: 秒）
        :type timeout: float
        :param interval: 在查找element的超时范围内，循环的间隔（单位: 秒）
        :type interval: float
        :param strategy: locator的类型，例如: "qpath"
        :type strategy: str
        :param parent_id: 父element的id，如不指定则从UIAApplication下查找
        :type parent_id: str
        :returns: list : {'elements': [{'element':id, 'attributes':<encode str>}], 'path': <encode str>, 'valid_path_part': <encode str>, 'invalid_path_part': <encode str>, 'find_count': <int>, "find_time": int}
        '''
        if strategy == "id":
            locator = "/name='%s' & maxdepth=20" % locator
            strategy = "qpath"
        start_time = time.time()
        result = None
        find_count = 0
        find_time = 0
        locator = xctest2instruments(locator)
        while True:
            before_step_time = time.time()
            command = self.create_json_command('uia.element.find_elements', locator, 0.5, interval, strategy, parent_id)
            result = self._instruments.exec_command(command)
            result = self.decode_find_result(result)
            after_step_time = time.time()
            step_time = after_step_time - before_step_time
            find_count += result['find_count']
            find_time += step_time
            if result['elements'] or after_step_time - start_time >= timeout:
                break
            if interval > 0:
                sleep_time = interval - step_time
                if sleep_time > 0:
                    time.sleep(sleep_time)
        result['find_count'] = find_count
        result['find_time'] = find_time
        return result

    @rpc_method
    def find_element_with_predicate(self, element_id, predicate):
        '''通过predicate文本获取第一个匹配的子element(UIAutomation API专用)
        
        :param element_id: element的id
        :type element_id: int
        :param predicate: 预期子element的predicate （例如：“name beginswith 'xxx'”）
        :type predicate: str
        :returns: int
        '''
        command = self.create_json_command('uia.element.first_with_predicate', element_id, predicate)
        return self._instruments.exec_command(command)

    @rpc_method
    def find_element_with_value_for_key(self, element_id, key, value):
        '''通过匹配指定key的value，获取第一个匹配的子element
        
        :param element_id: element的id
        :type element_id: int
        :param key: key （例如：label、name、value）
        :type key: str
        :param value: 对应key的value值
        :type value: str
        :returns: int
        '''
        command = self.create_json_command('uia.element.first_with_value_for_key', element_id, key, value)
        return self._instruments.exec_command(command)
    
    @rpc_method
    def find_elements_with_value_for_key(self, element_id, key, value):
        '''通过匹配指定key的value，获取第一个匹配的子element
        
        :param element_id: element的id
        :type element_id: int
        :param key: key （例如：label、name、value）
        :type key: str
        :param value: 对应key的value值
        :type value: str
        :returns: int
        '''
        command = self.create_json_command('uia.element.with_value_for_key', element_id, key, value)
        return self._instruments.exec_command(command)
    
    @rpc_method
    def get_element_tree(self, element_id, max_depth=0):
        '''获取指定element的所有子孙element树
        
        :param element_id: element的id
        :type element_id: int
        :param max_depth: 树的深度, 默认为0，获取所有子孙控件树
        :type max_depth: int
        :returns: dict
        '''
        command = self.create_json_command('uia.element.get_element_tree', element_id)
        result = urllib.unquote(self._instruments.exec_command(command))
        result = result.replace('\r', '\\r')
        result = result.replace('\n', '\\n')
        result = eval(result)
        return result
    
    @rpc_method
    def get_parent_element(self, element_id):
        '''获取指定element的父element的id
        
        :param element_id: element的id
        :type element_id: int
        :returns: int
        '''
        command = self.create_json_command('uia.element.get_parent', element_id)
        return self._instruments.exec_command(command)
    
    @rpc_method
    def get_children_elements(self, element_id):
        '''获取指定element的子elements集合
        
        :param element_id: element的id
        :type element_id: int
        :returns: list : [int, ...]
        '''
        command = self.create_json_command('uia.element.get_children', element_id)
        return self._instruments.exec_command(command)
    
    @rpc_method
    def get_rect(self, element_id):
        '''获取指定element的坐标和长宽
        
        :param element_id: element的id
        :type element_id: int
        :returns: dict : 坐标和长宽
        '''
        command = self.create_json_command('uia.element.get_rect', element_id)
        return self._instruments.exec_command(command)
    
    @rpc_method
    def capture(self, element_id, filepath=None):
        '''截图（截取指定element的图片，并将图片输出至指定的路径）
        
        :param element_id: element的id
        :type element_id: int
        :param filepath: 将图片存储至该路径（png格式），不传路径 或 路径仅含文件名，则截图后存储至默认路径。
        :type filepath: str
        :returns: str
        '''
        command = self.create_json_command('uia.element.capture', element_id, filepath)
        return self._instruments.exec_command(command)
    
    @rpc_method
    def click(self, element_id, x=None, y=None, options=None):
        '''点击指定的element
        
        :param element_id: element的id
        :type element_id: int
        :param x: x坐标（相对于当前element），可不传入该参数
        :type x: float
        :param y: y坐标（相对于当前element），可不传入该参数
        :type y: float
        '''
        if options == None:
            command = self.create_json_command('uia.element.tap', element_id, x, y)
        else:
            command = self.create_json_command('uia.element.tap_with_options', element_id, options)
        self._instruments.exec_command(command)
            
    
    @rpc_method
    def double_click(self, element_id, x=None, y=None):
        '''双击指定的element
        
        :param element_id: element的id
        :type element_id: int
        :param x: x坐标（相对于当前element），可不传入该参数
        :type x: float
        :param y: y坐标（相对于当前element），可不传入该参数
        :type y: float
        '''
        command = self.create_json_command('uia.element.double_tap', element_id, x, y)
        self._instruments.exec_command(command)
    
    @rpc_method
    def drag(self, element_id,  from_x, from_y, to_x, to_y, duration):
        '''拂去/拖拽等自定义操作
        
        :param element_id: element的id
        :type element_id: int
        :param from_x: 起点 x偏移百分比（从左至右为0.0至1.0）
        :type from_x: float
        :param from_y: 起点 y偏移百分比（从上至下为0.0至1.0）
        :type from_y: float
        :param to_x: 终点 x偏移百分比（从左至右为0.0至1.0）
        :type to_x: float
        :param to_y: 终点 y偏移百分比（从上至下为0.0至1.0）
        :type to_y: float
        :param touchCount: 触摸点（iPhone最多4个手指，iPad可以五个手指）
        :type touchCount: int
        :param duration: 持续时间（秒）
        :type duration: float
        :param repeat: 重复该操作
        :type repeat: int
        :param interval: 重复该操作的间隙时间（秒）
        :type interval: float
        :param options : 自定义项
        :type options : dict : {
                            : touchCount   : 1,                    // 触摸点
                            : duration     : 0.5,                  // 时间
                            : startOffset  : { x: 0.0, y: 0.1},    // 偏移百分比
                            : endOffset    : { x: 1.0, y: 0.1 },   // 偏移百分比
                            : repeat       : 1                     // 重复该操作
                            : interval     : 0                     // 重复该操作的间隙时间（秒）
                            }
        '''
        options = {"touchCount":1, "duration":duration, "startOffset":{"x":from_x, "y":from_y}, \
                    "endOffset":{"x":to_x, "y":to_y}, "repeat":1, "interval":0}
        if duration == 0:
            command = self.create_json_command('uia.element.flick_inside_with_options', element_id, options)
        else:    
            command = self.create_json_command('uia.element.drag_inside_with_options', element_id, options)
        self._instruments.exec_command(command)
    
    @rpc_method
    def rotate(self, element_id, options):
        '''旋转
        
        :param element_id: element的id
        :type element_id: int
        :param _options: 自定义项
        :type _options: dict : {
                            : centerOffset : {x:0.0, y:0.0},   // 中心点
                            : duration     : 1.5,              // 持续时间
                            : radius       : 100,              // 半径
                            : rotation     : 100,              // 旋转弧度的长度，默认为圆周率PI
                            : touchCount   : 2                 // 触摸点（最大5个点，这里默认2个）
                            }
        '''
        command = self.create_json_command('uia.element.rotate_with_options', element_id, options)
        self._instruments.exec_command(command)
    
    @rpc_method
    def scroll_to_visible(self, element_id):
        '''自动滚动到该element为可见
        
        :param element_id: element的id
        :type element_id: int
        '''
        command = self.create_json_command('uia.element.scroll_to_visible', element_id)
        self._instruments.exec_command(command)
    
    @rpc_method
    def long_click(self, element_id, seconds=3):
        '''持续按住
        
        :param element_id: element的id
        :type element_id: int
        :param seconds: 秒
        :type seconds: int
        '''
        command = self.create_json_command('uia.element.touch_and_hold', element_id, seconds)
        self._instruments.exec_command(command)
    
    @rpc_method
    def wait_for_invalid(self, element_id, seconds=5):
        '''等待当前element直到无效
        
        :param element_id: element的id
        :type element_id: int
        :param seconds: 秒
        :type seconds: int
        :returns: boolean -- True if invalid, False if not
        '''
        command = self.create_json_command('uia.element.wait_for_invalid', element_id, seconds)
        return self._instruments.exec_command(command)
    
    @rpc_method
    def set_value(self, element_id, value):
        '''设置指定element的value
        
        :param element_id: element的id
        :type element_id: int
        :param value: 值
        :type value: str
        '''
        command = self.create_json_command('uia.element.set_value', element_id, value)
        self._instruments.exec_command(command)
    
    @rpc_method
    def drag_to_value(self, element_id, value):
        '''slider滑到指定位置(0-1之间)
        :param element_id: element的id
        :type element_id: int
        :param value: 值
        :type value: str
        '''
        command = self.create_json_command('uia.element.drag_to_value', element_id, value)
        self._instruments.exec_command(command)
        
    @rpc_method
    def send_keys(self, element_id, keys):
        '''在指定element中键盘输入
        :param element_id: element的id
        :type element_id: int
        :param keys: 键入的字符串
        :type keys: str
        '''
        command = self.create_json_command('uia.element.sent_keys', element_id, keys)
        self._instruments.exec_command(command)
    
    @rpc_method
    def get_element_attrs(self, element_id):
        '''获取指定element的属性信息
        
        :param element_id: element的id
        :type element_id: int
        :returns: str: dict
        '''
        command = self.create_json_command('uia.element.get_element_dict', element_id)
        result = urllib.unquote(self._instruments.exec_command(command))
        result = result.replace('\r', '\\r')
        result = result.replace('\n', '\\n')
        result = eval(result)
        return result
    
    @rpc_method
    def get_element_attr(self, element_id, attr_name):
        '''获取指定element的属性信息
        
        :param element_id: element的id
        :type element_id: int
        :param attr_name: 属性名
        :type attr_name: str
        :returns: str
        '''
        command = self.create_json_command('uia.element.get_attr', element_id, attr_name)
        return self._instruments.exec_command(command) 
    
    @rpc_method
    def find_elements_with_predicate(self, element_id, predicate):
        '''通过predicate文本获取所有匹配的子element(UIAutomation API专用)
        
        :param element_id: element的id
        :type element_id: int
        :param predicate: 预期子element的predicate （例如：“name beginswith 'xxx'”）
        :type predicate: str
        :returns: list - [id1, id2, id3...]
        '''
        command = self.create_json_command('uia.element.with_predicate', element_id, predicate)
        return self._instruments.exec_command(command)
    
