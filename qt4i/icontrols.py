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
'''iOS基础UI控件模块
'''

from __future__ import absolute_import, print_function, division

import base64
import os
import re
import time
import traceback
import uuid
import hashlib
import six
from six import string_types
from six import StringIO
from six.moves.xmlrpc_client import Fault

from testbase.conf import settings
from testbase.util import LazyInit
from qt4i.exceptions import ControlAmbiguousError
from qt4i.exceptions import ControlNotFoundError
from qt4i.app import App
from qt4i.device import QT4i_LOGS_PATH
from qt4i.qpath import QPath
from qt4i.util import Rectangle, EnumDirect, Timeout


INS_IOS_DRIVER = True if settings.get('IOS_DRIVER', 'xctest') == 'instruments' else False
QTA_AI_SWITCH = settings.get('QT4I_AI_SWITCH', False)


class ControlContainer(object):
    '''控件集合接口
    '''
    
    def __init__(self):
        self._locators = {}  # 对象定义
        
    def __getitem__(self, key):
        '''操作符"[]"重载
        
        :param key: 控件名
        :type key: str
        :rtype: object
        :raises: Exception
        '''
        if not isinstance(key, string_types) or key not in self._locators: raise Exception('子控件名错误: %s' % key)
        params = self._locators.get(key)
        if isinstance(params, dict):
            cls = params.get('type')
            root = params.get('root')
            locator = params.get('locator')
            title = params.get('title')
            url = params.get('url')
            usr_name = params.get('name')
            mt_instance = params.get('instance')
            params = {'root': root, 'locator': locator}
            if INS_IOS_DRIVER:
                while True:
                    if not isinstance(root, string_types): break
                    if re.match('^@', root):
                        root_key = re.sub('^@', '', root)
                        if root_key not in self._locators:
                            raise ControlNotFoundError('未找到父控件: %s' % root_key)
                        root_params = self._locators.get(root_key)
                        params = {'root'    : root_params.get('root'),
                                  'locator' : str(root_params.get('locator')) + str(params.get('locator'))}
                        root = root_params.get('root')                
            else:
                if isinstance(root, string_types) and re.match('^@', root):
                    root_key = root[1:]
                    if root_key not in self._locators:
                        raise ControlNotFoundError('未找到父控件: %s' % root_key)
                    params['root'] = self[root_key]
            if usr_name:
                params['name'] = usr_name 
            params['id'] = key
            if title:
                params['title'] = title
            if url:
                params['url'] = url
            if mt_instance is not None:
                params['instance'] = mt_instance
            return cls(**params)
        raise Exception('控件定义的结构异常: [%s]' % key)
    
    @property
    def Controls(self):
        '''返回子控件集合 - 示例：XX_Window.Controls['XX_按钮'].click()
        '''
        return self
    
    def clearLocator(self):
        '''清空控件定位参数
        '''
        self._locators.clear()
        
    def hasControlKey(self, control_key):
        '''是否包含控件control_key
        
        :param control_key: 控件名
        :type control_key: str
        :rtype: boolean
        '''
        return control_key in self._locators
    
    def updateLocator(self, locators):
        '''更新控件定位参数
        
        :param locators: 定位参数，格式是 {'控件名':{'type':控件类, 控件类的参数dict列表}, ...}
        :type locators: dict
        '''
        self._locators.update(locators)

    # 此接口要被废弃，请使用 Element(...).wait_for_exist(10)
    def isChildCtrlExist(self, childctrlname, timeout=Timeout(2, 0.005)):
        '''判断子控件是否存在
        
        :param childctrlname: 控件名
        :type childctrlname: str
        :rtype: boolean
        '''
        print('*' * 30)
        print('提示: isChildCtrlExist 接口已过时，请使用 Element(...).wait_for_exist()')
        print('*' * 30)
        old_timeout = Element.timeout
        Element.timeout = timeout
        result = self.Controls[childctrlname].exist()
        Element.timeout = old_timeout
        return result


class _Element(object):

    def __init__(self, _id):
        self._id = _id

    @property
    def id(self):
        return self._id


class Element(ControlContainer):
    '''控件（UI框架是由各种控件组合而成）
    '''
    
    timeout = Timeout(5, 0.005)
    
    def __init__(self, root, locator, **ext):
        '''构造函数
        
        :param root: 父对象(多态：最顶层是App实例对象)
        :type root: App | Element
        :param locator: 定位描述（多态：可以直接是element的id），如果为None则指向_root对象
        :type locator: QPath | str(QPath) | int已定位到的element的ID
        '''
        ControlContainer.__init__(self)
        if ext:
            self.user_name = ext['id']
        self._app = None
        self._root = root
        self._locator = locator
        # -*- -*- -*-
        if not isinstance(self._root, (App, Element)):
            raise Exception('element.root is invalid')
        if self._locator is not None and not isinstance(self._locator, (QPath, string_types, int)):
            raise Exception('element.locator is invalid')
        # -*- -*- -*-
        root = self._root
        while True:
            if isinstance(root, App):
                self._app = root
                break
            root = root._root
        if not isinstance(self._app, App):
            raise Exception('element.app is invalid')
        # -*- -*- -*-
        self._check_locator(self._locator)
        # -*- -*- -*-
        self._element = LazyInit(self, '_element', self._init_element)
   
    def _check_locator(self, _locator):
        if isinstance(_locator, string_types) and not _locator.startswith('/'): #默认为_locator为id
            self.strategy = 'id'
        else:
            self.strategy = 'qpath'

    def _find(self, parent_id=None):
        print('--- ' * 9)
        print('locator : %s' % self._locator)
        print('timeout : %s' % self.timeout.timeout)
        # --- --- --- --- --- --- --- --- ---
        result = self._app.driver.element.find_elements((str(self._locator) if self._locator else None), self.timeout.timeout, self.timeout.interval, self.strategy, parent_id)
        elements = result.get('elements', [])
        element = elements[0].get('element') if len(elements)>0 else None
        # --- --- --- --- --- --- --- --- ---
        if element is None:
            if self.strategy == "id":
                err_msg  = '\n未找到控件 : 耗时[%s]毫秒尝试了[%s]次查找 [%s]' % (result.get('find_time'), result.get('find_count'), self._locator)
                err_msg += '\n无效控件ID : %s' % self._locator
                err_msg += '\nControlNotFoundError 建议用 device.print_uitree() 重新分析UI树'
            else:                
                err_msg  = '\n未找到控件 : 耗时[%s]毫秒尝试了[%s]次查找 [%s]' % (result.get('find_time'), result.get('find_count'), self._locator)
                err_msg += '\n有效Path  : %s' % result.get('valid_path_part')
                err_msg += '\n无效Path  : %s' % result.get('invalid_path_part')
                err_msg += '\nControlNotFoundError 建议用 device.print_uitree() 重新分析UI树'
            raise ControlNotFoundError(err_msg)
        if len(elements) > 1 and not INS_IOS_DRIVER:
            err_msg = '\n找到多个控件: 耗时[%s]毫秒尝试了[%s]次查找，找到[%s]个控件' % (result.get('find_time'), result.get('find_count'), len(elements))
            for e in elements: err_msg += '\n  %s' % e
            err_msg += '\nControlAmbiguousError 建议用 device.print_uitree() 重新分析UI树'
            raise ControlAmbiguousError(err_msg)
        print('element : 耗时[%s]毫秒尝试了[%s]次查找到[ element id: %s ]' % (result.get('find_time'), result.get('find_count'), element))
        return element

    def _init_element(self):
        if isinstance(self._locator, int): _id = self._locator
        else:
            if isinstance(self._root, Element) : _id = self._find(self._root._element.id)
            else                               : _id = self._find()
        if not isinstance(_id, int): raise Exception('element is invalid')
        self._element = _Element(_id)
        return self._element
    

    def exist(self):
        '''控件是否存在
        
        :rtype: boolean
        '''
        try:
            return bool(self._init_element())
        except Fault as err:
            raise err
        except Exception as err:
            print(err)
        return False

    def wait_for_exist(self, timeout, interval):
        '''控件是否存在
        
        :param timeout: 超时值（秒），例如对象需要等待网络拉取10秒才出现
        :type timeout: float
        :param interval: 轮询值（秒），轮询值建议 0.005 秒
        :type interval: float
        :rtype: boolean
        '''
        self.timeout = Timeout(timeout, interval)
        return self.exist()
    
    def find_elements(self, locator):
        '''通过相对于当前父对象的Path搜索子孙控件（建议用此方法解决动态Path的场景）
        
        :param locator: 相对当前对象的 - 子Path对象 或 子Path字符串 （搜索的起点为当前父对象）
        :type locator: QPath | str
        :return: [Element, ...]
        :rtype: list
        '''
        if not isinstance(locator, (QPath, string_types)): raise Exception('find_elements(path) path is invalid')
        strategy = 'qpath'
        if isinstance(locator, string_types) and not locator.startswith('/'):
            strategy = 'id'
        elements = []
        result = self._app.driver.element.find_elements(str(locator), self.timeout.timeout, self.timeout.interval, strategy, self._element.id)
        found_elements = result.get('elements', [])
        for item in found_elements: elements.append(Element(root=self, locator=item.get('element')))
        return elements

    def first_with_name(self, name):
        '''通过name文本获取第一个匹配的子element
        
        :param name: 子控件的name
        :type name: str
        :rtype: Element or None
        '''
        _id = self._app.driver.element.find_element_with_value_for_key(self._element.id, 'name', name)
        if isinstance(_id, int): return Element(root=self, locator=_id)

    def with_name(self, name):
        '''通过name文本获取匹配的子elements
        
        :param name: 子控件的name
        :type name: str
        :rtype: list
        '''
        children = []
        children_id = self._app.driver.element.find_elements_with_value_for_key(self._element.id, 'name', name)
        for child_id in children_id: children.append(Element(root=self, locator=child_id))
        return children

    def first_with_predicate(self, predicate):
        '''通过predicate文本获取第一个匹配的子element
        
        :param predicate: 预期子element的predicate （例如：“name beginswith 'xxx'”）
        :type predicate: str
        :rtype: Element or None
        '''
        _id = self._app.driver.element.find_element_with_predicate(self._element.id, predicate)
        if isinstance(_id, int): return Element(root=self, locator=_id)

    def with_predicate(self, predicate):
        '''通过predicate文本获取第一个匹配的子element
        :param predicate: 预期子element的predicate （例如：“name beginswith 'xxx'”）
        :type predicate: str
        :rtype: Element or None
        '''
        children = []
        children_id = self._app.driver.element.find_elements_with_predicate(self._element.id, predicate)
        for child_id in children_id: children.append(Element(root=self, locator=child_id))
        return children

    def first_with_value_for_key(self, key, value):
        '''通过匹配指定key的value，获取第一个匹配的子element

        :param key: key （例如：label、name、value）
        :type key: str
        :param value: 对应key的value值
        :type value: str or int
        :rtype: Element or None
        '''
        _id = self._app.driver.element.find_element_with_value_for_key(self._element.id, key, value)
        if isinstance(_id, int): return Element(root=self, locator=_id)

    def with_value_for_key(self, key, value):
        '''通过匹配指定key的value，获取所有匹配的子element
        
        :param key: key （例如：label、name、value）
        :type key: str
        :param value: 对应key的value值
        :type value: str or int
        :rtype: Element or None
        '''
        children = []
        children_id = self._app.driver.element.find_elements_with_value_for_key(self._element.id, key, value)
        for child_id in children_id: children.append(Element(root=self, locator=child_id))
        return children

    @property
    def children(self):
        '''获取子控件（仅含相对本控件的第二层子控件，不含第三层以及更深层的子控件，建议用此方法解决动态Path的场景）
        
        :return: [Element, ...]
        :rtype: list
        '''
        children = []
        children_id = self._app.driver.element.get_children_elements(self._element.id)
        for child_id in children_id:
            children.append(Element(root=self, locator=child_id))
        return children
    
    @property
    def parent(self):
        '''获取上一级的父控件
        
        :rtype: Element
        '''
        _id = self._app.driver.element.get_parent_element(self._element.id)
        if isinstance(_id, int): return Element(root=self, locator=_id)      
    
    def _get_attr(self, attr_name):
        '''获取控件的属性
        '''
        return self._app.driver.element.get_element_attr(self._element.id, attr_name)
    
    def get_attr_dict(self):
        '''获取元素的属性信息，返回字典
        
        :rtype: dict
        '''
        return self._app.driver.element.get_element_attrs(self._element.id)
    
    @property  
    def label(self):
        '''控件的label
        
        :rtype: str or None
        '''
        return self._get_attr('label')
    
    @property  
    def name(self):
        '''控件的name
        
        :rtype: str or None
        '''
        return self._get_attr('name')
    
    @property  
    def value(self):
        '''控件的value
        
        :rtype: None | str
        '''
        return self._get_attr('value')
    
    @value.setter
    def value(self, value):
        '''设置value(输入，支持中文)
        '''
        self._app.driver.element.set_value(self._element.id, value)
    
    @property  
    def visible(self):  
        '''控件是否可见
        
        :rtype: boolean
        '''
        return self._get_attr('visible')
    
    @property  
    def enabled(self): 
        '''控件是否开启
        
        :rtype: boolean
        ''' 
        return self._get_attr('enabled')
    
    @property
    def rect(self):
        '''控件的矩形信息
        
        :rtype: Rectangle
        '''
        rect = self._app.driver.element.get_rect(self._element.id)
        origin = rect['origin']
        size = rect['size']
        return Rectangle(origin['x'], origin['y'], origin['x'] + size['width'], origin['y'] + size['height'])

    def send_keys(self, keys):
        '''输入字符串

        :param keys: 字符串内容
        :type keys: str        
        :attention: 该接口不支持中文，中文输入请使用value='中文'
        '''
        self._app.driver.element.send_keys(self._element.id, keys)
    
    def scroll_to_visible(self, rate=1.0, drag_times=20):
        '''自动滚动到元素可见（技巧: Path中不写visible=true，当对象在屏幕可视范围之外，例如底部，调用此方法可以自动滚动到该元素为可见）
        
        :param drag_times: 最多尝试下滑次数，默认20次
        :type drag_times: int
        '''
        try:
            self._app.driver.element.scroll_to_visible(self._element.id, rate)
        except Exception:
                err = traceback.format_exc()
                if 'has no scrollable ancestor' not in err:
                    raise
        if not self.visible:  #兼容UIAutomation框架中scrollToVisible失效的场景
            for _ in range(drag_times):
                rate = self.rect.top / self._app.device.rect.height
                if rate > 1:
                    self._app.driver.device.drag(0.5, 0.6, 0.5 ,0.4)
                elif rate < -1:
                    self._app.driver.device.drag(0.5, 0.4, 0.5 ,0.6)
                elif rate >= -1 and rate < 0.5: 
                    self._app.driver.device.drag(0.5, 0.45, 0.5 ,0.55)
                elif rate >= 0.5 and rate <= 1: 
                    self._app.driver.device.drag(0.5, 0.55, 0.5 ,0.45)
                time.sleep(0.3)
                if self.visible:
                    break
            else:
                raise Exception('该控件不可见，请检查控件的位置[%s]和可见属性是否正常' % self.rect)
    
    def click(self, offset_x=None, offset_y=None):
        '''点击控件
        
        :param offset_x: 相对于该控件的坐标offset_x，百分比( 0 -> 1 )，不传入则默认该控件的中央
        :type offset_x: float or None
        :param offset_y: 相对于该控件的坐标offset_y，百分比( 0 -> 1 )，不传入则默认该控件的中央
        :type offset_y: float or None
        '''
        self._app.driver.element.click(self._element.id, offset_x, offset_y)
    
    def double_click(self, offset_x=0.5, offset_y=0.5):
        '''双击控件
        
        :param offset_x: 相对于该控件的坐标offset_x，百分比( 0 -> 1 )，不传入则默认该控件的中央
        :type offset_x: float
        :param offset_y: 相对于该控件的坐标offset_y，百分比( 0 -> 1 )，不传入则默认该控件的中央
        :type offset_y: float
        '''
        self._app.driver.element.double_click(self._element.id, offset_x, offset_y)
    
    def long_click(self, duration=3, offset_x=0.5, offset_y=0.5):
        '''单指长按
        
        :param duration: 持续时间（秒）
        :type duration: int
        :param offset_x: 相对于该控件的坐标offset_x，百分比( 0 -> 1 )，不传入则默认该控件的中央
        :type offset_x: float
        :param offset_y: 相对于该控件的坐标offset_y，百分比( 0 -> 1 )，不传入则默认该控件的中央
        :type offset_y: float
        '''
        self._app.driver.element.long_click(self._element.id, offset_x, offset_y, duration)
        
    def _tap_with_options(self, options={}):
        '''自定义点击(默认单指点击一次控件的中央)
        
        :param options : 自定义项
        :type options  : dict : {
                       :           tapCount     : 1,                    // 轻触次数
                       :           touchCount   : 1,                    // 触摸点
                       :           duration     : 1,                    // 持续时间
                       :           tapOffset    : { x: 0.5, y: 0.5 }    // 轻触偏移百分比
                       :          }
        '''
        options = {'tapCount'   : options.get('tapCount'  , 1),
                   'touchCount' : options.get('touchCount', 1),
                   'duration'   : options.get('duration'  , 0.1),
                   'tapOffset'  : {
                                   'x' : options.get('tapOffset', {}).get('x', 0.5),
                                   'y' : options.get('tapOffset', {}).get('y', 0.5)
                                  }}
        self._app.driver.element.click(self._element.id, None, None, options)
    
    def drag(self, from_x=0.9, from_y=0.5, to_x=0.1, to_y=0.5, duration=0.5):
        '''回避控件边缘，在控件体内拖拽（默认在控件内从右向左拖拽）
        
        :param from_x: 起点 x偏移百分比（从左至右为0.0至1.0）
        :type from_x: float
        :param from_y: 起点 y偏移百分比（从上至下为0.0至1.0）
        :type from_y: float
        :param to_x: 终点 x偏移百分比（从左至右为0.0至1.0）
        :type to_x: float
        :param to_y: 终点 y偏移百分比（从上至下为0.0至1.0）
        :type to_y: float
        :param duration: 持续时间（秒）
        :type duration: float
        '''
        self._app.driver.element.drag(self._element.id, from_x, from_y, to_x, to_y, duration)
    
    def drag2(self, direct=EnumDirect.Left):
        '''回避边缘在控件体内拖拽
        
        :param direct: 拖拽的方向
        :type  direct: EnumDirect.Left|EnumDirect.Right|EnumDirect.Up|EnumDirect.Down
        '''
        if direct == EnumDirect.Left  : self._app.driver.element.drag(self._element.id, 0.5, 0.5, 0.1, 0.5, 0.5)
        if direct == EnumDirect.Right : self._app.driver.element.drag(self._element.id, 0.5, 0.5, 0.9, 0.5, 0.5)
        if direct == EnumDirect.Up    : self._app.driver.element.drag(self._element.id, 0.5, 0.5, 0.5, 0.1, 0.5)
        if direct == EnumDirect.Down  : self._app.driver.element.drag(self._element.id, 0.5, 0.5, 0.5, 0.9, 0.5)
    
    def flick(self, from_x=0.9, from_y=0.5, to_x=0.1, to_y=0.5):
        '''滑动/拂去（默认从右向左回避边缘进行滑动/拂去）该接口比drag的滑动速度快，如果滚动距离大，建议用此接口
        
        :param from_x: 起点 x偏移百分比（从左至右为0.0至1.0）
        :type from_x: float
        :param from_y: 起点 y偏移百分比（从上至下为0.0至1.0）
        :type from_y: float
        :param to_x: 终点 x偏移百分比（从左至右为0.0至1.0）
        :type to_x: float
        :param to_y: 终点 y偏移百分比（从上至下为0.0至1.0）
        :type to_y: float
        '''
        self._app.driver.element.drag(self._element.id, from_x, from_y, to_x, to_y, 0)
    
    def flick2(self, direct=EnumDirect.Left):
        '''回避边缘在控件体内滑动/拂去
        
        :param direct: 滑动/拂去的方向
        :type  direct: EnumDirect.Left|EnumDirect.Right|EnumDirect.Up|EnumDirect.Down
        '''
        if direct == EnumDirect.Left  : self._app.driver.element.drag(self._element.id, 0.5, 0.5, 0.1, 0.5, 0)
        if direct == EnumDirect.Right : self._app.driver.element.drag(self._element.id, 0.5, 0.5, 0.9, 0.5, 0)
        if direct == EnumDirect.Up    : self._app.driver.element.drag(self._element.id, 0.5, 0.5, 0.5, 0.1, 0)
        if direct == EnumDirect.Down  : self._app.driver.element.drag(self._element.id, 0.5, 0.5, 0.5, 0.9, 0)
    
    def screenshot(self, image_path=None, image_type=None):
        '''截屏
        
        :attention: 裁剪图像使用了PIL库，使用该接口请安装Pillow，如下：pip install Pillow
        :param image_path: 截屏图片的存放路径
        :type image_path: str
        :param image_path: 截屏图片的存放路径
        :type image_path: str
        :return: 截屏结果和截屏文件的路径
        :rtype: tuple (boolean, str)
        '''
        base64_img = self._app.driver.device.capture_screen()
        device_img_data = base64.decodestring(base64_img)
        from PIL import Image
        image_fd = StringIO(device_img_data)
        img = Image.open(image_fd)
        scale_x = self._app.driver.device.get_rect()['size']['width']*1.0/img.size[0]
        scale_y = self._app.driver.device.get_rect()['size']['height']*1.0/img.size[1]
        rect = self.rect
        rect = (rect.left/scale_x, rect.top/scale_y, rect.right/scale_x, rect.bottom/scale_y)
        import math
        rect = (math.floor(rect[0]), math.floor(rect[1]), math.floor(rect[2]), math.floor(rect[3]))
        element_img = img.crop(rect)
        if image_type == 'Pil.Image':
            return element_img
        if not image_path:
            image_path = os.path.join(QT4i_LOGS_PATH, "p%s_%s.png" %(os.getpid(), uuid.uuid1()))
        element_img.save(os.path.abspath(image_path))
        return (os.path.isfile(image_path), image_path)

    def print_uitree(self):
        '''打印当前控件的UI树
        '''
        _ui_tree = self._app.driver.element.get_element_tree(self._element.id)
        def _print(_tree, _spaces='', _indent='|---'):
            _line = _spaces + '{  ' + ',   '.join([
                'classname: "%s"' % _tree['classname'],
                'label: %s' % ('"%s"' % _tree['label'] if _tree['label'] else 'null'),
                'name: %s' % ('"%s"' % _tree['name' ] if _tree['name' ] else 'null'),
                'value: %s' % ('"%s"' % _tree['value'] if _tree['value'] else 'null'),
                'visible: %s' % ('true' if _tree['visible'] else 'false'),
                'enabled: %s' % ('true' if _tree['enabled'] else 'false'),
                'rect: %s' % _tree['rect']]) + '  }'
            print(_line)
            for _child in _tree['children']: _print(_child, _spaces + _indent, _indent)
        _print(_ui_tree)
   
    def get_metis_view(self):
        '''返回MetisView
        '''
        return MetisView(self)
    
    def force_touch(self, pressure=1.0, duration=2.0):
        '''3D touch

        :param pressure: 按压力度（取值：0-1.0）
        :type pressure: float
        :param duration: 按压持续的时间（单位:秒）
        :type duration: float
        '''
        self._app.driver.element.force_touch(self._element.id, pressure, duration)


class Window(Element):
    '''窗口基类
    '''
    def __init__(self, root, locator=None, **ext):
        Element.__init__(self, root, (locator if locator else 1), **ext)
        

class Alert(Element):
    '''弹出框
    
    由于弹出框在iOS不同版本中的UI逻辑不一致（QPath不同），但业务逻辑相对统一（确定/取消），故单独封装成一个类
    '''
    
    def __init__(self, root, locator= QPath("/classname='UIAAlert' & maxdepth = 20"), **ext):
        Element.__init__(self, root=root, locator=locator, **ext)
        self._ios_version = self._app.device.ios_version
        self._title = None
        self._buttons = []

    @property
    def title(self):
        '''提示文本内容
        '''
        if INS_IOS_DRIVER:
            self._title = Element(root=self, locator=QPath("/classname='UIAScrollView'/classname='UIAStaticText' && visible=true"))
        else:
            self._title = Element(root=self, locator=QPath("/classname='StaticText' & visible=true & maxdepth=10"))
            
        if self._title is not None: 
            return self._title
        raise Exception('未找到有效标题，请检查Alert类内的子对象是否正确的QPath')

    @property
    def buttons(self):
        '''Alert控件上的所有按钮
        '''
        if INS_IOS_DRIVER:
            if re.search('^[8|9]', self._ios_version):
                self._buttons = self.find_elements(QPath("/classname='UIACollectionView'/classname='UIACollectionCell'/classname='UIAButton' && visible=true"))
            elif re.search('^7', self._ios_version):
                self._buttons = self.find_elements(QPath("/classname='UIATableView'/classname='UIATableCell' && visible=true"))
            if len(self._buttons) == 0: 
                self._buttons = self.find_elements(QPath("/classname='UIACollectionView'/classname='UIACollectionCell' && visible=true"))
        else:
            self._buttons = self.find_elements(QPath("/classname='Button' & visible=true & maxdepth=10"))
        if len(self._buttons) > 0                           : return self._buttons
        raise Exception('未找到有效按钮，请检查Alert类内的子对象是否正确的QPath')

    def click_button(self, text):
        '''点击指定文本的按钮
        
        :param text: 按钮上的文本
        :type text: str
        '''
        for button in self.buttons:
            text = str(text)
            attr = button.get_attr_dict()
            label = str(attr['label'])
            name = str(attr['name'])
            value = str(attr['value'])
            if text in [label, name, value]:
                button.click()
                return
        raise Exception('未有效匹配按钮，请检查指定的字符串是否命中预期')

    
class Slider(Element):
    '''进度条
    '''
    
    def __init__(self, root, locator=QPath("/classname='UIASlider' & maxdepth = 20"), **ext):
        Element.__init__(self, root=root, locator=locator, **ext)
        self._ios_version = self._app.device.ios_version
    
    @Window.value.setter
    def value(self, value):
        '''设置进度条的值(取值0~1之间)
        '''
        self._app.driver.element.drag_to_value(self._element.id, value)

        
class ActionSheet(Element): 
    '''UIActionSheet弹出框
    '''
    
    def __init__(self, root, locator=None, **ext):
        if locator is None:
            if INS_IOS_DRIVER:
                locator =  QPath("/classname='UIAWindow'/classname='UIAActionSheet'")    
            else:
                locator =  QPath("/classname='Sheet' & maxdepth = 20") 
        Element.__init__(self, root=root, locator=locator, **ext)
        self._ios_version = self._app.device.ios_version  
        self._buttons = []
    
    @property
    def buttons(self):  
        '''ActionSheet上面的所有按钮
        '''
        if INS_IOS_DRIVER:
            if re.search('^7', self._ios_version):
                self._buttons = self.find_elements(QPath("/classname='UIAButton' && visible=true"))
            else:
                self._buttons = self.find_elements(QPath("/classname='UIACollectionView'/classname='UIACollectionCell'/classname='UIAButton' && visible=true"))
                other_buttons = self.find_elements(QPath("/classname='UIAButton' && visible=true"))
                if other_buttons:
                    self._buttons.extend(other_buttons)
        else:
            self._buttons = self.find_elements(QPath("/classname='Button' & visible=true & maxdepth=10"))
        
        if len(self._buttons) > 0:
            return self._buttons
        raise Exception('未找到有效按钮，请检查ActionSheet类内的控件QPath是否正确')
    
    def click_button(self, text):
        '''点击text对应的按钮
        
        :param text: 按钮上的文本
        :type text: str
        '''
        for button in self.buttons:
            text = str(text)
            attr = button.get_attr_dict()
            label = str(attr['label'])
            name = str(attr['name'])
            value = str(attr['value'])
            if text in [label, name, value]:
                button.click()
                return
        raise Exception('未有效匹配按钮，请检查指定的字符串是否命中预期')            


class TableView(Element):
    '''TableView控件
    '''
    
    def __init__(self, root, locator=None, **ext):
        if locator is None:
            if INS_IOS_DRIVER:
                locator =  QPath("/classname='UIAWindow'/classname='UIATableView'")    
            else:
                locator =  QPath("/classname='Table' & maxdepth = 20")
        Element.__init__(self, root, locator, **ext)
        if isinstance(root, Window):
            for key, value in six.iteritems(root._locators):
                if value['root'] == '@%s' % self.user_name:
                    self.updateLocator({key:value})
        self._cells = []
        
    
    @property
    def cells(self):
        if INS_IOS_DRIVER:
            self._cells = self.find_elements("/classname='UIATableCell'")
        else:
            self._cells = self.find_elements("/classname='Cell'")
        
        if len(self._cells) > 0:
            return self._cells      
        raise RuntimeError('未找到有效TableCell，请检查TableView类内的控件QPath是否正确')
    
    def click_cell(self, text):
        for cell in self.cells:
            if text in cell.name: # 考虑效率问题，目前只查找name
                if not cell.visible:
                    cell.scroll_to_visible()
                cell.click()
                return 
        raise RuntimeError('未找到指定TableCell:%s' % text)
    
    def __iter__(self):
        for cell in self.cells:
            yield Cell(cell, self._locators)


class Cell(object):
    '''TableCell控件
    '''
    def __init__(self, element, locators={}):
        self._element = element
        for key in locators:
            locators[key]['root'] = self._element
        self._element.updateLocator(locators)
        
    def __getattr__(self, attr):
        return getattr(self._element, attr) 
    

class Button(Element):
    '''Button控件
    '''

    
class TextField(Element):
    '''文本输入框
    '''
    
    
class SecureTextField(Element):
    '''密码输入框
    '''
    
    
class PickerWheel(Element):
    '''滚轮选择框
    '''
    
    def select(self, value):
        self._app.driver.element.select_picker_wheel(self._element.id, value)

        
class MetisView(object):
    '''MetisView
    '''
    def __init__(self, element):
        self.element = element
        if isinstance(self.element, Element):
            img = self.element.screenshot(image_type='Pil.Image')
            real_width = img.size[0]
            real_height = img.size[1]
            rect = self.element.rect
            self._dx = real_width*1.0/rect.width
            self._dy = real_height*1.0/rect.height

    @property
    def rect(self):
        '''元素相对坐标(x, y, w, h)
        '''
        rect = self.element.rect
        if isinstance(self.element, Element):
            return (rect.top*self._dy, rect.left*self._dx, rect.width*self._dx, rect.height*self._dy)
        else:
            return (rect.top, rect.left, rect.width, rect.height)

    @property
    def os_type(self):
        '''系统类型，例如"android"，"ios"，"pc"
        '''
        return "ios"

    def screenshot(self):
        '''当前容器的区域截图
        '''
        return self.element.screenshot(image_type='Pil.Image')

    def click(self, offset_x=None, offset_y=None):
        '''点击
        
        :param offset_x: 相对于该控件的坐标offset_x，百分比( 0 -> 1 )，不传入则默认该控件的中央
        :type offset_x: float or None
        :param offset_y: 相对于该控件的坐标offset_y，百分比( 0 -> 1 )，不传入则默认该控件的中央
        :type offset_y: float or None
        '''
        self.element.click(offset_x, offset_y)

    def send_keys(self, text):
        self.element.send_keys(text)

    def double_click(self, offset_x=None, offset_y=None):
        if offset_x is None:
            offset_x = 0.5
        if offset_y is None:
            offset_y = 0.5
        self.element.double_click(offset_x, offset_y)

    def long_click(self, duration=3, offset_x=None, offset_y=None):
        if offset_x is None:
            offset_x = 0.5
        if offset_y is None:
            offset_y = 0.5
        self.element.long_click(duration, offset_x=offset_x, offset_y=offset_y)
    
    def drag(self, from_x=0.5, from_y=0.5, to_x=0.5, to_y=0.1, duration=0.5):
        '''拖拽
        
        :param from_x: 起点 x偏移百分比（从左至右为0.0至1.0）
        :type from_x: float
        :param from_y: 起点 y偏移百分比（从上至下为0.0至1.0）
        :type from_y: float
        :param to_x: 终点 x偏移百分比（从左至右为0.0至1.0）
        :type to_x: float
        :param to_y: 终点 y偏移百分比（从上至下为0.0至1.0）
        :type to_y: float
        :param duration: 持续时间（秒）
        :type duration: float
        '''
        self.element.drag(from_x, from_y, to_x, to_y, duration)