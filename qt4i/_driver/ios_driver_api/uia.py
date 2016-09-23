# coding: UTF-8
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
'''driver-instruments-api
'''
# 2014/11/02    cherry    创建
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

from _base import Register
from ins   import Instruments
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

class UIABase(object):
    '''基类
    '''
    def _create_json_rpc_command(self, _method, *_params):
        return {"method": _method, "params": list(_params)}

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

class UIATarget(Register, UIABase):
    '''UIATarget接口映射
    '''
    def register(self):
        self._register_functions('uia.target')

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):cls._instance = super(cls, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    
    def __init__(self, _server=None):
        Register.__init__(self, _server)
        UIABase.__init__(self)
        self._server = _server
        self._instruments = Instruments(_server)
    
    def function(self, _device_udid, _method, *_params):
        '''执行UIATarget的方法(此方法保留，以期应对苹果升级或调整UIA框架)
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _method      : 方法名
        :type _method       : str
        :param _params      : 参数列表(参数_method之后的任意个数参数直接转传)
        :type _params       : []
        :return             : 方法的输出
        '''
        _command = self._create_json_rpc_command('uia.target.function', _method, list(_params))
        return self._instruments.exec_command(_device_udid, _command)
    
    def get_rect(self, _device_udid):
        '''获取设备屏幕大小
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :return             : 高宽
        '''
        _command = self._create_json_rpc_command('uia.target.get_rect')
        return self._instruments.exec_command(_device_udid, _command)
    
    def get_model(self, _device_udid):
        '''获取设备模型
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :return             : str
        '''
        _command = self._create_json_rpc_command('uia.target.get_model')
        return self._instruments.exec_command(_device_udid, _command)
    
    def get_name(self, _device_udid):
        '''获取设备名
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :return             : str
        '''
        _command = self._create_json_rpc_command('uia.target.get_name')
        return self._instruments.exec_command(_device_udid, _command)
    
    def get_system_name(self, _device_udid):
        '''获取系统名
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :return             : str
        '''
        _command = self._create_json_rpc_command('uia.target.get_system_name')
        return self._instruments.exec_command(_device_udid, _command)
    
    def get_system_version(self, _device_udid):
        '''获取系统版本
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :return             : str
        '''
        _command = self._create_json_rpc_command('uia.target.get_system_version')
        return self._instruments.exec_command(_device_udid, _command)
    
    def capture_screen(self, _device_udid, _path=None):
        '''截屏(将输出图片至指定的路径)
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _path        : 将图片存储至该路径（png格式），例如：/Users/cherry/Desktop/test.png
                            : 不传路径 或 路径仅含文件名，则截图后存储至默认路径（默认路径内存储的图片每次重启都会被清空）。
        :type _path         : str
        :return             : str
        '''
        _command = self._create_json_rpc_command('uia.target.capture_screen', _path)
        return self._instruments.exec_command(_device_udid, _command)
    
    def capture_rect(self, _device_udid, _rect=None, _path=None):
        '''截图（指定区域截图，并将图片输出至指定的路径）
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _rect        : 指定区域
        :type _rect         : dict : {
                            :           origin : { x: xposition, y: yposition },
                            :           size   : { width: widthvalue, height: heightvalue}
                            :          }
        :param _path        : 将图片存储至该路径（png格式），例如：/Users/cherry/Desktop/test.png
                            : 不传路径 或 路径仅含文件名，则截图后存储至默认路径（默认路径内存储的图片每次重启都会被清空）。
        :type _path         : str
        :return             : str
        '''
        if _rect is None: return self.capture_screen(_device_udid, _path)
        _command = self._create_json_rpc_command('uia.target.capture_rect', _rect, _path)
        return self._instruments.exec_command(_device_udid, _command)
    
    def get_element_tree_and_capture_screen(self, _device_udid, _path=None):
        '''获取UI树并截屏（输出的JSON字符串数据需要URL解码）
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _path        : 将图片存储至该路径（png格式），例如：/Users/cherry/Desktop/test.png
                            : 不传路径 或 路径仅含文件名，则截图后存储至默认路径（默认路径内存储的图片每次重启都会被清空）。
        :type _path         : str
        :return             : dict : { element_tree: {}, capture_screen: file_path }
        '''
        _command = self._create_json_rpc_command('uia.target.get_element_tree_and_capture_screen', _path)
        _result_str = self._instruments.exec_command(_device_udid, _command)
        # _result = urllib.unquote(_result_str)
        # _result = _result.replace('\r', '\\r')
        # _result = _result.replace('\n', '\\n')
        # _result = eval(_result)
        return _result_str

    def set_rules_of_alert_auto_handle(self, _device_udid, _rules):
        '''设置自动处理Alert规则
        当message_text匹配到Alert框内的任意文本，则点击button_text指定的按钮。
        文本以段为单元，元素的label、name、value分为三段文本。规则匹配范围是Alert框内的所有元素的文本。
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _rules       : 规则集合
        :type _rules        : list - [ {"message_text": "message_text", "button_text": "button_text"}, ... ]
        '''
        _command = self._create_json_rpc_command('uia.target.set_rules_of_alert_auto_handle', _rules)
        self._instruments.exec_command(_device_udid, _command)

    def get_rules_of_alert_auto_handle(self, _device_udid):
        '''获取已设置的自动处理Alert规则
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :return             : list - [ {"message_text": "message_text", "button_text": "button_text"}, ... ]
        '''
        _command = self._create_json_rpc_command('uia.target.get_rules_of_alert_auto_handle')
        return self._instruments.exec_command(_device_udid, _command)

    def add_rule_of_alert_auto_handle(self, _device_udid, _message_text, _button_text):
        '''自动处理Alert规则，添加一项规则
        :param _device_udid  : 设备的UDID
        :type _device_udid   : str
        :param _message_text : Alert内文本片段，支持正则表达式（范围是所谓文本，每个元素的label/name/value为文本段）
        :type _message_text  : str
        :param _button_text  : Alert内按钮的文本，支持正则表达式（元素的label/name/value）
        :type _button_text   : str
        '''
        _command = self._create_json_rpc_command('uia.target.add_rule_of_alert_auto_handle', _message_text, _button_text)
        self._instruments.exec_command(_device_udid, _command)

    def clean_rules_of_alert_auto_handle(self, _device_udid):
        '''自动处理Alert规则，清空所有规则
        '''
        _command = self._create_json_rpc_command('uia.target.clean_rules_of_alert_auto_handle')
        self._instruments.exec_command(_device_udid, _command)

    def turn_off_auto_close_alert(self, _device_udid):
        '''关闭自动关闭alert框
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        '''
        _command = self._create_json_rpc_command('uia.target.turn_off_auto_close_alert')
        self._instruments.exec_command(_device_udid, _command)
    
    def turn_on_auto_close_alert(self, _device_udid):
        '''打开自动关闭alert框(优先级低于set_rules_of_alert_auto_handle所设置的策略)
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        '''
        _command = self._create_json_rpc_command('uia.target.turn_on_auto_close_alert')
        self._instruments.exec_command(_device_udid, _command)
    
    def get_last_alert_msg(self, _device_udid):
        '''获取最近一次alert框的提示内容(iOS6/7/8由于UI框架变更，可能会有Bug)
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :return             : str
        '''
        _command = self._create_json_rpc_command('uia.target.get_last_alert_msg')
        return self._instruments.exec_command(_device_udid, _command)
    
    def delay(self, _device_udid, _seconds=1):
        '''等待
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _seconds     : 秒
        :type _seconds      : int
        
        '''
        _command = self._create_json_rpc_command('uia.target.delay', _seconds)
        self._instruments.exec_command(_device_udid, _command)

    def get_element_tree(self, _device_udid):
        '''从顶层开始获取UI树（输出的JSON字符串数据需要URL解码）
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :return             : str
        '''
        _command = self._create_json_rpc_command('uia.target.get_element_tree')
        return self._instruments.exec_command(_device_udid, _command)

    def log_element_tree_ext(self, _device_udid):
        '''从顶层开始获取UI树（输出的JSON字符串数据需要URL解码）
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :return             : str
        '''
        _command = self._create_json_rpc_command('uia.target.log_element_tree_ext')
        return self._instruments.exec_command(_device_udid, _command)
    
    def click_volume_down(self, _device_udid):
        '''按下一次减少音量按键
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        '''
        _command = self._create_json_rpc_command('uia.target.click_volume_down')
        self._instruments.exec_command(_device_udid, _command)
    
    def click_volume_up(self, _device_udid):
        '''按下一次增加音量按键
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        '''
        _command = self._create_json_rpc_command('uia.target.click_volume_up')
        self._instruments.exec_command(_device_udid, _command)
    
    def hold_volume_down(self, _device_udid, _seconds=1):
        '''持续按住减少音量按键
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _seconds     : 秒
        :type _seconds      : int
        '''
        _command = self._create_json_rpc_command('uia.target.hold_volume_down', _seconds)
        self._instruments.exec_command(_device_udid, _command)
    
    def hold_volume_up(self, _device_udid, _seconds=1):
        '''持续按住增加音量按键
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _seconds     : 秒
        :type _seconds      : int
        '''
        _command = self._create_json_rpc_command('uia.target.hold_volume_up', _seconds)
        self._instruments.exec_command(_device_udid, _command)
    
    def deactivate_app_ror_duration(self, _device_udid, _seconds=3):
        '''将App置于后台一定时间
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _seconds     : 秒
        :type _seconds      : int
        '''
        _command = self._create_json_rpc_command('uia.target.deactivate_app_ror_duration', _seconds)
        return self._instruments.exec_command(_device_udid, _command)
    
    def get_device_orientation(self, _device_udid):
        '''获取设备的方向
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :return             : int
                            : UIA_DEVICE_ORIENTATION_UNKNOWN
                            : UIA_DEVICE_ORIENTATION_PORTRAIT
                            : UIA_DEVICE_ORIENTATION_PORTRAIT_UPSIDEDOWN
                            : UIA_DEVICE_ORIENTATION_LANDSCAPELEFT
                            : UIA_DEVICE_ORIENTATION_LANDSCAPERIGHT
                            : UIA_DEVICE_ORIENTATION_FACEUP
                            : UIA_DEVICE_ORIENTATION_FACEDOWN
        '''
        _command = self._create_json_rpc_command('uia.target.get_device_orientation')
        return self._instruments.exec_command(_device_udid, _command)
    
    def tap(self, _device_udid, _point=None):
        '''轻敲/单击（全局操作）
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _point       : 坐标
        :type _point        : dict : { x: 100, y: 100 }
        '''
        _command = self._create_json_rpc_command('uia.target.tap', _point)
        self._instruments.exec_command(_device_udid, _command)
    
    def double_tap(self, _device_udid, _point):
        '''轻敲/双击（全局操作）
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _point       : 坐标
        :type _point        : dict : { x: 100, y: 100 }
        '''
        _command = self._create_json_rpc_command('uia.target.double_tap', _point)
        self._instruments.exec_command(_device_udid, _command)
    
    def tap_with_options(self, _device_udid, _point, _options):
        '''自定义轻敲（全局操作）
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _point       : 坐标
        :type _point        : dict : { x: 100, y: 100 }
        :param _point       : 自定义
        :type _point        : dict : {
                            :           tapCount    : 1, 几次，默认1次
                            :           touchCount  : 1, 几点，默认1个点（例如两个手指则为2）
                            :           duration    : 0  按住的时间，默认是0
                            :          }
        '''
        _command = self._create_json_rpc_command('uia.target.tap_with_options', _point, _options)
        self._instruments.exec_command(_device_udid, _command)
    
    def touch_and_hold(self, _device_udid, _point, _seconds=3):
        '''轻敲/双击（全局操作）
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _point       : 坐标
        :type _point        : dict : { x: 100, y: 100 }
        :param _seconds     : 秒
        :type _seconds      : int
        '''
        _command = self._create_json_rpc_command('uia.target.touch_and_hold', _point, _seconds)
        self._instruments.exec_command(_device_udid, _command)
    
    def drag_from_to_for_duration(self, _device_udid, _from_point, _to_point, _seconds=0.5, _repeat=1, _interval=0):
        '''拖拽（全局操作）
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _from_point  : 起始坐标
        :type _from_point   : dict : { x: 100, y: 100 }
        :param _to_point    : 结束坐标
        :type _to_point     : dict : { x: 100, y: 100 }
        :param _seconds     : 持续时间（秒）
        :type _seconds      : float
        :param _repeat      : 重复该操作
        :type _repeat       : int
        :param _interval    : 重复该操作的间隙时间（秒）
        :type _interval     : float
        '''
        _command = self._create_json_rpc_command('uia.target.drag_from_to_for_duration', _from_point, _to_point, _seconds, _repeat, _interval)
        self._instruments.exec_command(_device_udid, _command)
    
    def drag_right_to_left(self, _device_udid):
        '''屏幕中央从右向左拖拽（回避屏幕边缘）
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        '''
        _command = self._create_json_rpc_command('uia.target.drag_right_to_left')
        self._instruments.exec_command(_device_udid, _command)
    
    def drag_left_to_right(self, _device_udid):
        '''屏幕中央从左向右拖拽（回避屏幕边缘）
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        '''
        _command = self._create_json_rpc_command('uia.target.drag_left_to_right')
        self._instruments.exec_command(_device_udid, _command)
    
    def drag_up_to_down(self, _device_udid):
        '''屏幕中央从上向下拖拽（回避屏幕边缘）
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        '''
        _command = self._create_json_rpc_command('uia.target.drag_up_to_down')
        self._instruments.exec_command(_device_udid, _command)
    
    def drag_down_to_up(self, _device_udid):
        '''屏幕中央从下向上拖拽（回避屏幕边缘）
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        '''
        _command = self._create_json_rpc_command('uia.target.drag_down_to_up')
        self._instruments.exec_command(_device_udid, _command)
    
    def flick_from_to(self, _device_udid, _from_point, _to_point, _repeat=1, _interval=0):
        '''弹去,拂去（全局操作）
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _from_point  : 起始坐标
        :type _from_point   : dict : { x: 100, y: 100 }
        :param _to_point    : 结束坐标
        :type _to_point     : dict : { x: 100, y: 100 }
        :param _repeat      : 重复该操作
        :type _repeat       : int
        :param _interval    : 重复该操作的间隙时间（秒）
        :type _interval     : float
        '''
        _command = self._create_json_rpc_command('uia.target.flick_from_to', _from_point, _to_point, _repeat, _interval)
        self._instruments.exec_command(_device_udid, _command)
    
    def flick_right_to_left(self, _device_udid):
        '''屏幕中央从右向左弹去/拂去
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        '''
        _command = self._create_json_rpc_command('uia.target.flick_right_to_left')
        self._instruments.exec_command(_device_udid, _command)
    
    def flick_left_to_right(self, _device_udid):
        '''屏幕中央从左向右弹去/拂去
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        '''
        _command = self._create_json_rpc_command('uia.target.flick_left_to_right')
        self._instruments.exec_command(_device_udid, _command)
    
    def flick_up_to_down(self, _device_udid):
        '''屏幕中央从上向下弹去/拂去
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        '''
        _command = self._create_json_rpc_command('uia.target.flick_up_to_down')
        self._instruments.exec_command(_device_udid, _command)
    
    def flick_down_to_up(self, _device_udid):
        '''屏幕中央从下向上弹去/拂去
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        '''
        _command = self._create_json_rpc_command('uia.target.flick_down_to_up')
        self._instruments.exec_command(_device_udid, _command)
    
    def lock_for_duration(self, _device_udid, _seconds=5):
        '''持续锁定一段时间
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _seconds     : 秒
        :type _seconds      : int
        '''
        _command = self._create_json_rpc_command('uia.target.lock_for_duration', _seconds)
        self._instruments.exec_command(_device_udid, _command)
    
    def pinch_close_from_to_for_duration(self, _device_udid, _from_point, _to_point, _seconds=1):
        '''捏合
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _from_point  : 起始坐标
        :type _from_point   : dict : { x: 100, y: 100 }
        :param _to_point    : 结束坐标
        :type _to_point     : dict : { x: 100, y: 100 }
        :param _seconds     : 秒
        :type _seconds      : int
        '''
        _command = self._create_json_rpc_command('uia.target.pinch_close_from_to_for_duration', _from_point, _to_point, _seconds)
        self._instruments.exec_command(_device_udid, _command)
    
    def pinch_open_from_to_for_duration(self, _device_udid, _from_point, _to_point, _seconds=1):
        '''展开
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _from_point  : 起始坐标
        :type _from_point   : dict : { x: 100, y: 100 }
        :param _to_point    : 结束坐标
        :type _to_point     : dict : { x: 100, y: 100 }
        :param _seconds     : 秒
        :type _seconds      : int
        '''
        _command = self._create_json_rpc_command('uia.target.pinch_open_from_to_for_duration', _from_point, _to_point, _seconds)
        self._instruments.exec_command(_device_udid, _command)
    
    def rotate_with_options(self, _device_udid, _location, _options):
        '''旋转
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _location    : 中心点
        :type _location     : dict : { x: 100, y: 100 }
        :param _options     : 自定义项
        :type _options      : dict : {
                            :           duration    : 1,    持续的时间（秒）
                            :           radius      : 50,   半径
                            :           rotation    : 100,  圆周，默认是圆周率PI
                            :           touchCount  : 2     触摸点数量 2 - 5
                            :          }
        '''
        _command = self._create_json_rpc_command('uia.target.rotate_with_options', _location, _options)
        self._instruments.exec_command(_device_udid, _command)
    
    def set_device_orientation(self, _device_udid, _orientation):
        '''设置设备的方向
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _orientation : 代表方向的数值
        :type _orientation  : int
                            : UIA_DEVICE_ORIENTATION_UNKNOWN
                            : UIA_DEVICE_ORIENTATION_PORTRAIT
                            : UIA_DEVICE_ORIENTATION_PORTRAIT_UPSIDEDOWN
                            : UIA_DEVICE_ORIENTATION_LANDSCAPELEFT
                            : UIA_DEVICE_ORIENTATION_LANDSCAPERIGHT
                            : UIA_DEVICE_ORIENTATION_FACEUP
                            : UIA_DEVICE_ORIENTATION_FACEDOWN
        '''
        _command = self._create_json_rpc_command('uia.target.set_device_orientation', _orientation)
        self._instruments.exec_command(_device_udid, _command)
    
    def set_location(self, _device_udid, _coordinates):
        '''设置设备的GPS坐标
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _coordinates : 经纬度
        :type _coordinates  : dict : {
                            :           latitude    : 100, // 以度为单位的纬度。正值表示纬度赤道以北。负值表示纬度赤道以南。
                            :           longitude   : 100  // 以度为单位的经度。测量是相对于零子午线，用正值向东延伸的经络及经络的负值西侧延伸。
                            :          }
        '''
        _command = self._create_json_rpc_command('uia.target.set_location', _coordinates)
        self._instruments.exec_command(_device_udid, _command)
    
    def set_location_with_options(self, _device_udid, _coordinates, _options):
        '''设置设备的GPS坐标
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _coordinates : 经纬度
        :type _coordinates  : dict : {
                            :           latitude    : 100, // 以度为单位的纬度。正值表示纬度赤道以北。负值表示纬度赤道以南。
                            :           longitude   : 100  // 以度为单位的经度。测量是相对于零子午线，用正值向东延伸的经络及经络的负值西侧延伸。
                            :          }
        :param _options     : 自定义项
        :type _options      : dict : {
                            :           altitude            : 50, // 海拔高度，以米为单位，相对于海平面。正值表示海拔高度。负值表示低于海平面的高度。
                            :           horizontalAccuracy  : 10, // 水平半径，不确位置时的范围内，以米为单位。负的值是无效的。
                            :           verticalAccuracy    : 10, // 垂直半径，不确位置时的范围内，以米为单位。负的值是无效的。
                            :           course              : 1,  // 设备是移动的，不确定移动方向
                            :           speed               : 1   // 移动速度（米/秒）
                            :          }
        '''
        _command = self._create_json_rpc_command('uia.target.set_location_with_options', _coordinates, _options)
        self._instruments.exec_command(_device_udid, _command)
    
    def shake(self, _device_udid):
        '''摇晃设备
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        '''
        _command = self._create_json_rpc_command('uia.target.shake')
        self._instruments.exec_command(_device_udid, _command)
    
    def unlock(self, _device_udid):
        '''解锁设备
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        '''
        _command = self._create_json_rpc_command('uia.target.unlock')
        self._instruments.exec_command(_device_udid, _command)
    
    def lock(self, _device_udid):
        '''锁定设备
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        '''
        _command = self._create_json_rpc_command('uia.target.lock')
        self._instruments.exec_command(_device_udid, _command)

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

class UIAKeyboard(Register, UIABase):
    '''Keyboard接口映射
    '''
    def register(self):
        self._register_functions('uia.keyboard')

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):cls._instance = super(cls, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, _server=None):
        Register.__init__(self, _server)
        UIABase.__init__(self)
        self._server = _server
        self._instruments = Instruments(_server)

    def sent_keys(self, _device_udid, _keys):
        '''键盘输入
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _keys        : 键入的字符串
        :type _keys         : str
        '''
        _command = self._create_json_rpc_command('uia.keyboard.sent_keys', _keys)
        self._instruments.exec_command(_device_udid, _command)

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

class UIAApplication(Register, UIABase):
    '''UIAApplication接口映射
    '''
    def register(self):
        self._register_functions('uia.application')

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):cls._instance = super(cls, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    
    def __init__(self, _server=None):
        Register.__init__(self, _server)
        UIABase.__init__(self)
        self._server = _server
        self._instruments = Instruments(_server)
    
    def function(self, _device_udid, _method, *_params):
        '''执行UIAApplication的方法(此方法保留，以期应对苹果升级或调整UIA框架)
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _method      : 方法名
        :type _method       : str
        :param _params      : 参数列表(参数_method之后的任意个数参数直接转传)
        :type _params       : []
        :return             : 方法的输出
        '''
        _command = self._create_json_rpc_command('uia.application.function', _method, list(_params))
        return self._instruments.exec_command(_device_udid, _command)
    
    def get_main_window(self, _device_udid):
        '''获取APP的MainWindow的ID
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :return             : int
        '''
        _command = self._create_json_rpc_command('uia.application.get_main_window')
        return self._instruments.exec_command(_device_udid, _command)
    
    def get_interface_orientation(self, _device_udid):
        '''获取接口方向(返回整数，不同数值表示不同方向)
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :return             : int
        '''
        _command = self._create_json_rpc_command('uia.application.get_interface_orientation')
        return self._instruments.exec_command(_device_udid, _command)
    
    def get_app_bundle_id(self, _device_udid):
        '''获取APP的BundleID
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :return             : str
        '''
        _command = self._create_json_rpc_command('uia.application.get_app_bundle_id')
        return self._instruments.exec_command(_device_udid, _command)
    
    def get_app_version(self, _device_udid):
        '''获取APP的Version
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :return             : str
        '''
        _command = self._create_json_rpc_command('uia.application.get_app_version')
        return self._instruments.exec_command(_device_udid, _command)
    

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

class UIAElement(Register, UIABase):
    '''UIAElement接口映射
    '''
    def register(self):
        self._register_functions('uia.element')
    
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):cls._instance = super(cls, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    
    def __init__(self, _server=None):
        Register.__init__(self, _server)
        UIABase.__init__(self)
        self._server = _server
        self._instruments = Instruments(_server)
        self._target = UIATarget(_server)
    
    def function(self, _device_udid, _method, *_params):
        '''执行UIAElement的方法(此方法保留，以期应对苹果升级或调整UIA框架)
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _method      : 方法名
        :type _method       : str
        :param _params      : 参数列表(参数_method之后的任意个数参数直接转传)
        :type _params       : []
        :return             : 方法的输出
        '''
        _command = self._create_json_rpc_command('uia.element.function', _method, list(_params))
        return self._instruments.exec_command(_device_udid, _command)
    
    def is_valid(self, _device_udid, _id):
        '''检测对象是否还有效
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _id          : element的id
        :type _id           : int
        :return             : bool
        '''
        _command = self._create_json_rpc_command('uia.element.is_valid', _id)
        return self._instruments.exec_command(_device_udid, _command)
    
    def find(self, _device_udid, _locator, _timeout=3, _interval=0.005, _strategy='qpath', _parent_id=None):
        '''查找单个element对象，返回查找到的element对象的缓存id。不指定parent_id则从UIAApplication下开始搜索。
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _locator     : 定位element的字符串，例如: "/classname='UIAWindow'"
        :type _locator      : str
        :param _timeout     : 查找element的超时值（单位: 秒）
        :type _timeout      : float
        :param _interval    : 在查找element的超时范围内，循环的间隔（单位: 秒）
        :type _interval     : float
        :param _strategy    : locator的类型，例如: "qpath"
        :type _strategy     : str
        :param _parent_id   : 父element的id，如不指定则从UIAApplication下查找
        :type _parent_id    : str
        :return             : dict : {'element': id, 'path': <encode str>, 'valid_path_part': <encode str>, 'invalid_path_part': <encode str>, 'find_count': <int>, "find_time": int}
        '''
        _command = self._create_json_rpc_command('uia.element.find', _locator, _timeout, _interval, _strategy, _parent_id)
        _result = self._instruments.exec_command(_device_udid, _command)
        return _result
    
    def find_elements(self, _device_udid, _locator, _timeout=3, _interval=0.005, _strategy='qpath', _parent_id=None):
        '''查找单个element对象，返回查找到的element对象的缓存id。不指定parent_id则从UIAApplication下开始搜索。
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _locator     : 定位element的字符串，例如: "/classname='UIAWindow'"
        :type _locator      : str
        :param _timeout     : 查找element的超时值（单位: 秒）
        :type _timeout      : float
        :param _interval    : 在查找element的超时范围内，循环的间隔（单位: 秒）
        :type _interval     : float
        :param _strategy    : locator的类型，例如: "qpath"
        :type _strategy     : str
        :param _parent_id   : 父element的id，如不指定则从UIAApplication下查找
        :type _parent_id    : str
        :return             : list : {'elements': [{'element':id, 'attributes':<encode str>}], 'path': <encode str>, 'valid_path_part': <encode str>, 'invalid_path_part': <encode str>, 'find_count': <int>, "find_time": int}
        '''
        _command = self._create_json_rpc_command('uia.element.find_elements', _locator, _timeout, _interval, _strategy, _parent_id)
        _result = self._instruments.exec_command(_device_udid, _command)
        return _result

    def first_with_name(self, _device_udid, _id, _name):
        '''通过name文本获取第一个匹配的子element
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _id          : element的id
        :type _id           : int
        :param _name        : 子控件的name
        :type _name         : str
        :return             : int
        '''
        _command = self._create_json_rpc_command('uia.element.first_with_name', _id, _name)
        return self._instruments.exec_command(_device_udid, _command)

    def with_name(self, _device_udid, _id, _name):
        '''通过name文本获取匹配的子elements
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _id          : element的id
        :type _id           : int
        :param _name        : 子控件的name
        :type _name         : str
        :return             : list
        '''
        _command = self._create_json_rpc_command('uia.element.with_name', _id, _name)
        return self._instruments.exec_command(_device_udid, _command)

    def first_with_predicate(self, _device_udid, _id, _predicate):
        '''通过predicate文本获取第一个匹配的子element
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _id          : element的id
        :type _id           : int
        :param _predicate   : 预期子element的predicate （例如：“name beginswith 'xxx'”）
        :type _predicate    : str
        :return             : int
        '''
        _command = self._create_json_rpc_command('uia.element.first_with_predicate', _id, _predicate)
        return self._instruments.exec_command(_device_udid, _command)

    def with_predicate(self, _device_udid, _id, _predicate):
        '''通过predicate文本获取匹配的子elements
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _id          : element的id
        :type _id           : int
        :param _predicate   : 预期子element的predicate （例如：“name beginswith ‘xxx'”）
        :type _predicate    : str
        :return             : int
        '''
        _command = self._create_json_rpc_command('uia.element.with_predicate', _id, _predicate)
        return self._instruments.exec_command(_device_udid, _command)

    def first_with_value_for_key(self, _device_udid, _id, _key, _value):
        '''通过匹配指定key的value，获取第一个匹配的子element
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _id          : element的id
        :type _id           : int
        :param _key         : key （例如：label、name、value）
        :type _key          : str
        :param _value       : 对应key的value值
        :type _value        : str
        :return             : int
        '''
        _command = self._create_json_rpc_command('uia.element.first_with_value_for_key', _id, _key, _value)
        return self._instruments.exec_command(_device_udid, _command)

    def with_value_for_key(self, _device_udid, _id, _key, _value):
        '''通过匹配指定key的value，获取匹配的子elements
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _id          : element的id
        :type _id           : int
        :param _key         : key （例如：label、name、value）
        :type _key          : str
        :param _value       : 对应key的value值
        :type _value        : str
        :return             : int
        '''
        _command = self._create_json_rpc_command('uia.element.with_value_for_key', _id, _key, _value)
        return self._instruments.exec_command(_device_udid, _command)
    
    def get_attr(self, _device_udid, _id, _name):
        '''获取指定element的属性
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _id          : element的id
        :type _id           : int
        :param _name        : 属性名，例如: name、lable、value
        :type _name         : str
        :return             : str
        '''
        _command = self._create_json_rpc_command('uia.element.get_attr', _id, _name)
        return self._instruments.exec_command(_device_udid, _command)
    
    def get_element_tree(self, _device_udid, _id):
        '''获取指定element的所有子孙element树
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _id          : element的id
        :type _id           : int
        :return             : str
        '''
        _command = self._create_json_rpc_command('uia.element.get_element_tree', _id)
        return self._instruments.exec_command(_device_udid, _command)
    
    def get_parent(self, _device_udid, _id):
        '''获取指定element的父element的id
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _id          : element的id
        :type _id           : int
        :return             : int
        '''
        _command = self._create_json_rpc_command('uia.element.get_parent', _id)
        return self._instruments.exec_command(_device_udid, _command)
    
    def get_children(self, _device_udid, _id):
        '''获取指定element的子elements集合
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _id          : element的id
        :type _id           : int
        :return             : list : [int, ...]
        '''
        _command = self._create_json_rpc_command('uia.element.get_children', _id)
        return self._instruments.exec_command(_device_udid, _command)
    
    def get_rect(self, _device_udid, _id):
        '''获取指定element的坐标和长宽
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _id          : element的id
        :type _id           : int
        :return             : dict : 坐标和长宽
        '''
        _command = self._create_json_rpc_command('uia.element.get_rect', _id)
        return self._instruments.exec_command(_device_udid, _command)
    
    def capture(self, _device_udid, _id, _path=None):
        '''截图（截取指定element的图片，并将图片输出至指定的路径）
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _id          : element的id
        :type _id           : int
        :param _path        : 将图片存储至该路径（png格式），例如：/Users/cherry/Desktop/test.png
                            : 不传路径 或 路径仅含文件名，则截图后存储至默认路径（默认路径内存储的图片每次重启都会被清空）。
        :type _path         : str
        :return             : str
        '''
        _command = self._create_json_rpc_command('uia.element.capture', _id, _path)
        return self._instruments.exec_command(_device_udid, _command)
    
    def tap(self, _device_udid, _id, _x=None, _y=None):
        '''点击指定的element
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _id          : element的id
        :type _id           : int
        :param _x           : x坐标（相对于当前element），可不传入该参数
        :type _x            : str
        :param _y           : y坐标（相对于当前element），可不传入该参数
        :type _y            : str
        '''
        _command = self._create_json_rpc_command('uia.element.tap', _id, _x, _y)
        self._instruments.exec_command(_device_udid, _command)
    
    def double_tap(self, _device_udid, _id, _x=None, _y=None):
        '''双击指定的element
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _id          : element的id
        :type _id           : int
        :param _x           : x坐标（相对于当前element），可不传入该参数
        :type _x            : str
        :param _y           : y坐标（相对于当前element），可不传入该参数
        :type _y            : str
        '''
        _command = self._create_json_rpc_command('uia.element.double_tap', _id, _x, _y)
        self._instruments.exec_command(_device_udid, _command)
    
    def tap_with_options(self, _device_udid, _id, _options):
        '''自定义点击
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _id          : element的id
        :type _id           : int
        :param _options     : 自定义项
        :type _options      : dict : {
                            :           tapCount     : 1,                    // 轻触次数
                            :           touchCount   : 1,                    // 触摸点
                            :           duration     : 1,                    // 持续时间
                            :           tapOffset    : { x: 1.0, y: 0.1 }    // 轻触偏移百分比
                            :          }
        '''
        _command = self._create_json_rpc_command('uia.element.tap_with_options', _id, _options)
        self._instruments.exec_command(_device_udid, _command)
    
    def click(self, _device_udid, _id, _x=None, _y=None):
        '''双击指定的element
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _id          : element的id
        :type _id           : int
        :param _x           : x坐标（相对于当前element），可不传入该参数
        :type _x            : str
        :param _y           : y坐标（相对于当前element），可不传入该参数
        :type _y            : str
        '''
        _command = self._create_json_rpc_command('uia.element.click', _id, _x, _y)
        self._instruments.exec_command(_device_udid, _command)
    
    def double_click(self, _device_udid, _id, _x=None, _y=None):
        '''双击指定的element
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _id          : element的id
        :type _id           : int
        :param _x           : x坐标（相对于当前element），可不传入该参数
        :type _x            : str
        :param _y           : y坐标（相对于当前element），可不传入该参数
        :type _y            : str
        '''
        _command = self._create_json_rpc_command('uia.element.double_click', _id, _x, _y)
        self._instruments.exec_command(_device_udid, _command)
    
    def drag_inside_with_options(self, _device_udid, _id, _options):
        '''拖拽
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _id          : element的id
        :type _id           : int
        :param _options     : 自定义项
        :type _options      : dict : {
                            :           touchCount   : 1,                    // 触摸点
                            :           duration     : 0.5,                  // 时间
                            :           startOffset  : { x: 0.0, y: 0.1},    // 偏移百分比
                            :           endOffset    : { x: 1.0, y: 0.1 },   // 偏移百分比
                            :           repeat       : 1                     // 重复该操作
                            :           interval     : 0                     // 重复该操作的间隙时间（秒）
                            :        }
        '''
        _command = self._create_json_rpc_command('uia.element.drag_inside_with_options', _id, _options)
        self._instruments.exec_command(_device_udid, _command)
    
    def drag_inside_right_to_left(self, _device_udid, _id):
        '''单指在控件的中央从右向左拖拽（回避控件边缘，拖拽过程使用1秒）
        '''
        _command = self._create_json_rpc_command('uia.element.drag_inside_right_to_left', _id)
        self._instruments.exec_command(_device_udid, _command)
    
    def drag_inside_left_to_right(self, _device_udid, _id):
        '''单指在控件的中央从左向右拖拽（回避控件边缘，拖拽过程使用1秒）
        '''
        _command = self._create_json_rpc_command('uia.element.drag_inside_left_to_right', _id)
        self._instruments.exec_command(_device_udid, _command)
    
    def drag_inside_up_to_down(self, _device_udid, _id):
        '''单指在控件的中央从上向下拖拽（回避控件边缘，拖拽过程使用1秒）
        '''
        _command = self._create_json_rpc_command('uia.element.drag_inside_up_to_down', _id)
        self._instruments.exec_command(_device_udid, _command)
    
    def drag_inside_down_to_up(self, _device_udid, _id):
        '''单指在控件的中央从下向上拖拽（回避控件边缘，拖拽过程使用1秒）
        '''
        _command = self._create_json_rpc_command('uia.element.drag_inside_down_to_up', _id)
        self._instruments.exec_command(_device_udid, _command)
    
    def flick_inside_with_options(self, _device_udid, _id, _options):
        '''弹去/拂去
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _id          : element的id
        :type _id           : int
        :param _options     : 自定义项
        :type _options      : dict : {
                            :           touchCount   : 1,                    // 触摸点
                            :           startOffset  : { x: 0.5, y: 0.9 },   // 偏移百分比
                            :           endOffset    : { x: 1.0, y: 0.9 }    // 偏移百分比
                            :           repeat       : 1                     // 重复该操作
                            :           interval     : 0                     // 重复该操作的间隙时间（秒）
                            :          }
        '''
        _command = self._create_json_rpc_command('uia.element.flick_inside_with_options', _id, _options)
        self._instruments.exec_command(_device_udid, _command)
    
    def flick_inside_right_to_left(self, _device_udid, _id):
        '''单指在控件中央从右向左弹去/拂去（回避控件边缘）
        '''
        _command = self._create_json_rpc_command('uia.element.flick_inside_right_to_left', _id)
        self._instruments.exec_command(_device_udid, _command)
    
    def flick_inside_left_to_right(self, _device_udid, _id):
        '''单指在控件中央从左向右弹去/拂去（回避控件边缘）
        '''
        _command = self._create_json_rpc_command('uia.element.flick_inside_left_to_right', _id)
        self._instruments.exec_command(_device_udid, _command)
    
    def flick_inside_up_to_down(self, _device_udid, _id):
        '''单指在控件中央从上向下弹去/拂去（回避控件边缘）
        '''
        _command = self._create_json_rpc_command('uia.element.flick_inside_up_to_down', _id)
        self._instruments.exec_command(_device_udid, _command)
    
    def flick_inside_down_to_up(self, _device_udid, _id):
        '''单指在控件中央从下向上弹去/拂去（回避控件边缘）
        '''
        _command = self._create_json_rpc_command('uia.element.flick_inside_down_to_up', _id)
        self._instruments.exec_command(_device_udid, _command)
    
    def rotate_with_options(self, _device_udid, _id, _options):
        '''旋转
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _id          : element的id
        :type _id           : int
        :param _options     : 自定义项
        :type _options      : dict : {
                            :           centerOffset : {x:0.0, y:0.0},   // 中心点
                            :           duration     : 1.5,              // 持续时间
                            :           radius       : 100,              // 半径
                            :           rotation     : 100,              // 旋转弧度的长度，默认为圆周率PI
                            :           touchCount   : 2                 // 触摸点（最大5个点，这里默认2个）
                            :          }
        '''
        _command = self._create_json_rpc_command('uia.element.rotate_with_options', _id, _options)
        self._instruments.exec_command(_device_udid, _command)
    
    def scroll_to_visible(self, _device_udid, _id):
        '''自动滚动到该element为可见
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _id          : element的id
        :type _id           : int
        '''
        _command = self._create_json_rpc_command('uia.element.scroll_to_visible', _id)
        self._instruments.exec_command(_device_udid, _command)
    
    def touch_and_hold(self, _device_udid, _id, _seconds=3):
        '''持续按住
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _id          : element的id
        :type _id           : int
        :param _seconds     : 秒
        :type _seconds      : int
        '''
        _command = self._create_json_rpc_command('uia.element.touch_and_hold', _id, _seconds)
        self._instruments.exec_command(_device_udid, _command)
    
    def two_finger_tap(self, _device_udid, _id):
        '''二指轻触
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _id          : element的id
        :type _id           : int
        '''
        _command = self._create_json_rpc_command('uia.element.two_finger_tap', _id)
        self._instruments.exec_command(_device_udid, _command)
    
    def wait_for_invalid(self, _device_udid, _id, _seconds=5):
        '''等待当前element直到无效
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _id          : element的id
        :type _id           : int
        :param _seconds     : 秒
        :type _seconds      : int
        :return             : bool
        '''
        _command = self._create_json_rpc_command('uia.element.wait_for_invalid', _id, _seconds)
        return self._instruments.exec_command(_device_udid, _command)
    
    def set_value(self, _device_udid, _id, _value):
        '''设置指定element的value
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _id          : element的id
        :type _id           : int
        :param _value       : 值
        :type _value        : str
        '''
        _command = self._create_json_rpc_command('uia.element.set_value', _id, _value)
        self._instruments.exec_command(_device_udid, _command)
    
    def drag_to_value(self, _device_udid, _id, _value):
        '''slider滑到指定位置(0-1之间)
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _id          : element的id
        :type _id           : int
        :param _value       : 值
        :type _value        : str
        '''
        _command = self._create_json_rpc_command('uia.element.drag_to_value', _id, _value)
        self._instruments.exec_command(_device_udid, _command)
        
    
    def sent_keys(self, _device_udid, _id, _keys):
        '''在指定element中键盘输入
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _id          : element的id
        :type _id           : int
        :param _keys        : 键入的字符串
        :type _keys         : str
        '''
        _command = self._create_json_rpc_command('uia.element.sent_keys', _id, _keys)
        self._instruments.exec_command(_device_udid, _command)
    
    def get_element_dict(self, _device_udid, _id):
        '''获取指定element的属性信息（需要解码）
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _id          : element的id
        :type _id           : int
        :return             : str : dict
        '''
        _command = self._create_json_rpc_command('uia.element.get_element_dict', _id)
        return self._instruments.exec_command(_device_udid, _command)
    
    def log_element_tree_ext(self, _device_udid, _id):
        '''从指定element开始获取UI树（需要解码）
        :param _device_udid : 设备的UDID
        :type _device_udid  : str
        :param _id          : element的id
        :type _id           : int
        :return             : str : dict
        '''
        _command = self._create_json_rpc_command('uia.element.log_element_tree_ext', _id)
        return self._instruments.exec_command(_device_udid, _command)

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
