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
# 2014/11/17    cherry    全面重构

import re, urllib, xmlrpclib
from testbase.util    import LazyInit
from tuia.qpathparser import QPathParser
from qt4i.exceptions  import ControlNotFoundError
from qt4i.app         import App
from qt4i.qpath       import QPath
from qt4i.util        import Rectangle, EnumDirect, Timeout

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

class ControlContainer(object):
    '''控件集合接口
    
当一个类继承本接口，并设置Locator属性后，该类可以使用Controls属于获取控件。如下::

    class SysSettingWin(gf.GFWindow, ControlContainer)
        def __init__(self):
            locators={'基本设置Tab': {'type':gf.Button, 'root':self, 'locator'='Finger_Btn'},
                      '常规页': {'type':gf.Control, 'root':self, 'locator'='PageBasicGeneral'},
                      '退出程序单选框': {'type':gf.RadioBox, 'root':'@常规页','locator'=QPath("/name='ExitPrograme_RI' && maxdepth='10'")}
            }
            self.updateLocator(locators)
    
则SysSettingWin().Controls['基本设置Tab']返回设置窗口上基本设置Tab的gf.Button实例,
而SysSettingWin().Controls['退出程序单选框']，返回设置窗口的常规页下的退出程序单选框实例。
其中'root'='@常规页'中的'@常规页'表示参数'root'的值不是这个字符串，而是key'常规页'指定的控件。
    '''
    
    def __init__(self):
        self._locators = {}  # 对象定义
        # self._controls = {}  # 对象缓存（回避没必要的重新实例化）
    
    def __getitem__(self, key):
        '''操作符"[]"重载
        
        :param key: 控件名
        :type key: str
        :return: object
        :raises: Exception
        '''
        if not isinstance(key, basestring) or not self._locators.has_key(key): raise Exception('子控件名错误: %s' % key)
        params = self._locators.get(key)
        # -*- -*- -*- -*- -*- -*-
        # print 'key     : [%s]' % key
        # old_obj = self._controls.get(key, None)
        # if old_obj:
        #    if old_obj.is_valid():
        #        print 'element.locator       : %s' % old_obj._locator
        #        print 'element.id            : %s' % old_obj._id
        #        print '-' * 10
        #        return old_obj
        #    else:
        #        del self._controls[key]
        # -*- -*- -*- -*- -*- -*-
        if isinstance(params, basestring):
            new_obj = Element(self, params)
            # self._controls.update({key:new_obj})
            return new_obj
        # -*- -*- -*- -*- -*- -*-
        if isinstance(params, dict):
            cls = params.get('type')
            root = params.get('root')
            locator = params.get('locator')
            params = {'root': root, 'locator': locator}
            while True:
                if not isinstance(root, basestring): break
                if re.match('^@', root):
                    root_key = re.sub('^@', '', root)
                    if not self._locators.has_key(root_key):
                        raise ControlNotFoundError('未找到父控件: %s' % root_key)
                    root_params = self._locators.get(root_key)
                    params = {'root'    : root_params.get('root'),
                              'locator' : str(root_params.get('locator')) + str(params.get('locator'))}
                    root = root_params.get('root')
            new_obj = cls(**params)
            # self._controls.update({key:new_obj})
            return new_obj
        # -*- -*- -*- -*- -*- -*-
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
        :return: boolean
        '''
        return self._locators.has_key(control_key)
    
    def updateLocator(self, locators):
        '''更新控件定位参数
        
        :param locators: 定位参数，格式是 {'控件名':{'type':控件类, 控件类的参数dict列表}, ...}
        :type locators: dict
        '''
        self._locators.update(locators)

    # -*- -*- -*- -*- -*- -*- -*- -*- -*-
    # 此接口要被废弃，请使用 Element(...).wait_for_exist(10)
    def isChildCtrlExist(self, childctrlname, timeout=Timeout(2, 0.005)):
        '''判断子控件是否存在
        
        :param childctrlname: 控件名
        :type childctrlname: str
        :return: boolean
        '''
        print '*' * 30
        print '提示: isChildCtrlExist 接口已过时，请使用 Element(...).wait_for_exist()'
        print '*' * 30
        old_timeout = Element.timeout
        Element.timeout = timeout
        result = self.Controls[childctrlname].exist()
        Element.timeout = old_timeout
        return result

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

class _Element(object):

    def __init__(self, _id):
        self._id = _id

    @property
    def id(self):
        return self._id

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

class Element(ControlContainer):
    '''控件（UI框架是由各种控件组合而成）
    '''
    
    timeout = Timeout(2, 0.005)
    
    def __init__(self, root, locator):
        '''构造函数
        
        :param root: 父对象(多态：最顶层是App实例对象)
        :type root: App | Element
        :param locator: 定位描述（多态：可以直接是element的id），如果为None则指向_root对象
        :type locator: QPath | str(QPath) | int已定位到的element的ID
        '''
        ControlContainer.__init__(self)
        self._app = None
        self._root = root
        self._locator = locator
        # -*- -*- -*-
        if not isinstance(self._root, (App, Element)):
            raise Exception('element.root is invalid')
        if self._locator is not None and not isinstance(self._locator, (QPath, basestring, int)):
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
        pass
        if isinstance(_locator, (QPath, basestring)):
            parsed_qpath, _ = QPathParser().parse(_locator)
            # -*-
            # locators = []
            # for locator in parsed_qpath:
            #     props = []
            #     for propname in locator:
            #         prop = locator[propname]
            #         props.append('%s%s\'%s\''%(propname, prop[0], prop[1]))
            #     locators.append(' && '.join(props))
            # print locators

    def _decode_find_result(self, result):
        path              = urllib.unquote(result.get('path', ''))
        valid_path_part   = urllib.unquote(result.get('valid_path_part', ''))
        invalid_path_part = urllib.unquote(result.get('invalid_path_part', ''))
        elements          = result.get('elements', [])
        for i, item in enumerate(elements): elements[i]['attributes'] = urllib.unquote(item.get('attributes'))
        result.update({'path':path, 'valid_path_part':valid_path_part, 'invalid_path_part':invalid_path_part, 'elements':elements})
        return result

    def _find(self, parent_id=None):
        print '--- ' * 9
        print 'locator : %s' % self._locator
        print 'timeout : %s' % self.timeout.timeout
        # --- --- --- --- --- --- --- --- ---
        result = self._decode_find_result(self._app.driver.uia.element.find_elements(self._app.device.udid, (str(self._locator) if self._locator else None), self.timeout.timeout, self.timeout.interval, 'qpath', parent_id))
        elements = result.get('elements', [])
        element = elements[0].get('element') if len(elements)>0 else None
        # --- --- --- --- --- --- --- --- ---
        if element: print 'element : 耗时[%s]毫秒尝试了[%s]次查找到[ element id: %s ]' % (result.get('find_time'), result.get('find_count'), element)
        # --- --- --- --- --- --- --- --- ---
        if element is None:
            err_msg  = '\n未找到控件 : 耗时[%s]毫秒尝试了[%s]次查找 [%s]' % (result.get('find_time'), result.get('find_count'), self._locator)
            err_msg += '\n有效Path  : %s' % result.get('valid_path_part')
            err_msg += '\n无效Path  : %s' % result.get('invalid_path_part')
            err_msg += '\nControlNotFoundError 建议用 device.print_uitree() 重新分析UI树'
            raise ControlNotFoundError(err_msg)
        # --- --- --- --- --- --- --- --- ---
        # 有较多脚本中的父窗口封装 /classname='UIAWindow' 没有使用 instance，暂不启用 --- cherry
        # if len(elements) > 1 :
        #     err_msg = '\n找到多个控件: 耗时[%s]毫秒尝试了[%s]次查找，找到[%s]个控件' % (result.get('find_time'), result.get('find_count'), len(elements))
        #     for item in elements: err_msg += '\n  %s' % item.get('attributes')
        #     err_msg += '\nControlAmbiguousError 建议用 device.print_uitree() 重新分析UI树'
        #     raise ControlAmbiguousError(err_msg)
        # --- --- --- --- --- --- --- --- ---
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
        
        :return: boolean
        '''
        try                           : return bool(self._init_element())
        except xmlrpclib.Fault as err : raise err
        except Exception as err       : return False
        return False

    def wait_for_exist(self, timeout, interval):
        '''控件是否存在
        
        :param timeout: 超时值（秒），例如对象需要等待网络拉取10秒才出现
        :type timeout: float
        :param interval: 轮询值（秒），轮询值建议 0.005 秒
        :type interval: float
        :return: boolean
        '''
        self.timeout = Timeout(timeout, interval)
        return self.exist()
    
    def find_elements(self, locator):
        '''通过相对于当前父对象的Path搜索子孙控件（建议用此方法解决动态Path的场景）
        
        :param locator: 相对当前对象的 - 子Path对象 或 子Path字符串 （搜索的起点为当前父对象）
        :type locator: QPath | str
        :return: list: [Element, ...]
        '''
        if not isinstance(locator, (QPath, basestring)): raise Exception('find_elements(path) path is invalid')
        self._check_locator(locator)
        elements = []
        result = self._decode_find_result(self._app.driver.uia.element.find_elements(self._app.device.udid, str(locator), self.timeout.timeout, self.timeout.interval, 'qpath', self._element.id))
        found_elements = result.get('elements', [])
        for item in found_elements: elements.append(Element(root=self, locator=item.get('element')))
        return elements

    def first_with_name(self, name):
        '''通过name文本获取第一个匹配的子element
        
        :param name: 子控件的name
        :type name: str
        :return: Element or None
        '''
        _id = self._app.driver.uia.element.first_with_name(self._app.device.udid, self._element.id, name)
        if isinstance(_id, int): return Element(root=self, locator=_id)

    def with_name(self, name):
        '''通过name文本获取匹配的子elements
        
        :param name: 子控件的name
        :type name: str
        :return: list
        '''
        children = []
        children_id = self._app.driver.uia.element.with_name(self._app.device.udid, self._element.id, name)
        for child_id in children_id: children.append(Element(root=self, locator=child_id))
        return children

    def first_with_predicate(self, predicate):
        '''通过predicate文本获取第一个匹配的子element
        
        :param predicate: 预期子element的predicate （例如：“name beginswith 'xxx'”）
        :type predicate: str
        :return: Element or None
        '''
        _id = self._app.driver.uia.element.first_with_predicate(self._app.device.udid, self._element.id, predicate)
        if isinstance(_id, int): return Element(root=self, locator=_id)

    def with_predicate(self, predicate):
        '''通过predicate文本获取第一个匹配的子element
        :param predicate: 预期子element的predicate （例如：“name beginswith 'xxx'”）
        :type predicate: str
        :return: Element or None
        '''
        children = []
        children_id = self._app.driver.uia.element.with_predicate(self._app.device.udid, self._element.id, predicate)
        for child_id in children_id: children.append(Element(root=self, locator=child_id))
        return children

    def first_with_value_for_key(self, key, value):
        '''通过匹配指定key的value，获取第一个匹配的子element

        :param key: key （例如：label、name、value）
        :type key: str
        :param value: 对应key的value值
        :type value: value
        :return: Element or None
        '''
        _id = self._app.driver.uia.element.first_with_value_for_key(self._app.device.udid, self._element.id, key, value)
        if isinstance(_id, int): return Element(root=self, locator=_id)

    def with_value_for_key(self, key, value):
        '''通过匹配指定key的value，获取第一个匹配的子element
        
        :param key: key （例如：label、name、value）
        :type key: str
        :param value: 对应key的value值
        :type value: value
        :return: Element or None
        '''
        children = []
        children_id = self._app.driver.uia.element.with_value_for_key(self._app.device.udid, self._element.id, key, value)
        for child_id in children_id: children.append(Element(root=self, locator=child_id))
        return children

    @property
    def children(self):
        '''获取子控件（仅含相对本控件的第二层子控件，不含第三层以及更深层的子控件，建议用此方法解决动态Path的场景）
        
        :return: list: [Element, ...]
        '''
        children = []
        children_id = self._app.driver.uia.element.get_children(self._app.device.udid, self._element.id)
        for child_id in children_id:
            children.append(Element(root=self, locator=child_id))
        return children
    
    def _get_attr(self, attr_name):
        '''获取控件的属性
        '''
        return self._app.driver.uia.element.get_attr(self._app.device.udid, self._element.id, attr_name)
    
    def get_attr_dict(self):
        '''获取元素的属性信息，返回字典
        
        :return: dict
        '''
        _data = urllib.unquote(self._app.driver.uia.element.get_element_dict(self._app.device.udid, self._element.id))
        _data = _data.replace('\r', '\\r')
        _data = _data.replace('\n', '\\n')
        _data = eval(_data)
        return _data
    
    @property  
    def label(self):
        '''控件的label(可能有特殊字符超出Python解码为UTF-8的范围)
        
        :rtype: None | str
        '''
        label = self.get_attr_dict()['label']
        return label
    
    @property  
    def name(self):
        '''控件的name(可能有特殊字符超出Python解码为UTF-8的范围)
        
        :rtype: None | str
        '''
        name = self.get_attr_dict()['name']
        return name
    
    @property  
    def value(self):
        '''控件的value(可能有特殊字符超出Python解码为UTF-8的范围)
        
        :rtype: None | str
        '''
        value = self.get_attr_dict()['value']
        return value
    
    @value.setter
    def value(self, value):
        '''设置value(输入，支持中文)
        '''
        self._app.driver.uia.element.set_value(self._app.device.udid, self._element.id, value)
    
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
    def valid(self):
        '''控件是否有效（此接口会抛出异常，暂时不处理，以上层应用为主）
        
        :rtype: boolean
        '''
        return self._get_attr('valid')
        
    @property  
    def focused(self):
        '''控件的焦点状态
        
        :rtype: boolean
        '''
        return self._get_attr('focus')
    
    @property
    def rect(self):
        '''控件的矩形信息
        
        :rtype: Rectangle
        '''
        rect = self._app.driver.uia.element.get_rect(self._app.device.udid, self._element.id)
        origin = rect['origin']
        size = rect['size']
        return Rectangle(origin['x'], origin['y'], origin['x'] + size['width'], origin['y'] + size['height'])
    
    def send_keys(self, keys):
        '''输入字符串
        :param keys: 字符串内容
        :type keys: str        
        :attention: 该接口不支持中文，中文输入请使用value='中文'
        '''
        self._app.driver.uia.element.sent_keys(self._app.device.udid, self._element.id, keys)
    
    def scroll_to_visible(self):
        '''自动滚动到元素可见（技巧: Path中不写visible=true，当对象在屏幕可视范围之外，例如底部，调用此方法可以自动滚动到该元素为可见）
        '''
        self._app.driver.uia.element.scroll_to_visible(self._app.device.udid, self._element.id)
        if not self.visible:  #兼容UIAutomation框架中scrollToVisible失效的场景
            if self.rect.top < 0:
                d = (0.5, 0.42, 0.5 ,0.6)
            else:
                d = (0.5, 0.6, 0.5 ,0.42)
            for _ in xrange(10):
                self._app.device.flick(d[0], d[1], d[2], d[3])
                if self.visible:
                    break
            else:
                raise Exception('该控件不可见，请检查控件的位置[%s]和可见属性是否正常' % self.rect)
    
    def click(self, offset_x=None, offset_y=None):
        '''点击控件
        
        :param offset_x: 相对于该控件的坐标offset_x，百分比( 0 -> 1 )，不传入则默认该控件的中央
        :type offset_x: float|None
        :param offset_y: 相对于该控件的坐标offset_y，百分比( 0 -> 1 )，不传入则默认该控件的中央
        :type offset_y: float|None
        '''
        self._app.driver.uia.element.click(self._app.device.udid, self._element.id, offset_x, offset_y)
    
    def double_click(self):
        '''双击控件
        '''
        self._app.driver.uia.element.double_click(self._app.device.udid, self._element.id)
    
    def long_click(self, duration=3):
        '''单指长按
        
        :param duration: 持续时间（秒）
        :type duration: int
        '''
        options = {'tapCount'     : 1,
                   'touchCount'   : 1,
                   'duration'     : duration,
                   'tapOffset'    : {'x':  0.5, 'y':  0.5}}
        self._tap_with_options(options)
    
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
        self._app.driver.uia.element.tap_with_options(self._app.device.udid, self._element.id, options)
    
    def _touch_and_hold(self, duration):
        '''按住
        
        :param duration: 秒
        :type duration: int
        '''
        self._app.driver.uia.element.touch_and_hold(self._app.device.udid, self._element.id, duration)
    
    def _drag_inside_with_options(self, options):
        '''在控件体内拖拽（注意：如有过场动画，需要等待动画完毕）
           建议使用drag或drag2
        '''
        options = {'touchCount'  : options.get('touchCount', 1),  # 触摸点（iPhone最多4个手指，iPad可以五个手指）
                   'duration'    : options.get('duration', 0.5),  # 时间
                   'startOffset' : {'x': options.get('startOffset', {}).get('x'),
                                    'y': options.get('startOffset', {}).get('y')},
                   'endOffset'   : {'x': options.get('endOffset', {}).get('x'),
                                    'y': options.get('endOffset', {}).get('y')},
                   'repeat'      : options.get('repeat', 1),
                   'interval'    : options.get('interval', 0)}
        self._app.driver.uia.element.drag_inside_with_options(self._app.device.udid, self._element.id, options)
    
    def drag(self, from_x=0.9, from_y=0.5, to_x=0.1, to_y=0.5, touchCount=1, duration=0.5, repeat=1, interval=0):
        '''回避控件边缘，在控件体内拖拽（默认在控件内从右向左拖拽）
        
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
        '''
        self._drag_inside_with_options({
            'touchCount'    : touchCount or 1,
            'duration'      : duration or 0.5,
            'startOffset'   : {'x': from_x, 'y': from_y},
            'endOffset'     : {'x': to_x,   'y': to_y},
            'repeat'        : repeat or 1,
            'interval'      : interval or 0})
    
    def drag2(self, direct=EnumDirect.Left):
        '''回避边缘在控件体内拖拽
        
        :param direct: 拖拽的方向
        :type  direct: EnumDirect.Left|EnumDirect.Right|EnumDirect.Up|EnumDirect.Down
        '''
        if direct == EnumDirect.Left  : self._app.driver.uia.element.drag_inside_right_to_left(self._app.device.udid, self._element.id)
        if direct == EnumDirect.Right : self._app.driver.uia.element.drag_inside_left_to_right(self._app.device.udid, self._element.id)
        if direct == EnumDirect.Up    : self._app.driver.uia.element.drag_inside_down_to_up(self._app.device.udid, self._element.id)
        if direct == EnumDirect.Down  : self._app.driver.uia.element.drag_inside_up_to_down(self._app.device.udid, self._element.id)
    
    def _flick_inside_with_options(self, options):
        '''滑动/拂去，该接口比drag的滑动速度快，如果滚动距离大，建议用此接口
           除非多手指操作，建议使用flick方法或flick2方法
        '''
        options = {'touchCount'  : options.get('touchCount', 1),  # 触摸点（iPhone最多4个手指，iPad可以五个手指）
                   'startOffset' : {'x': options.get('startOffset', {}).get('x', 0.9),
                                    'y': options.get('startOffset', {}).get('y', 0.5)},
                   'endOffset'   : {'x': options.get('endOffset', {}).get('x', 0.1),
                                    'y': options.get('endOffset', {}).get('y', 0.5)},
                   'repeat'      : options.get('repeat', 1),
                   'interval'    : options.get('interval', 0)}
        self._app.driver.uia.element.flick_inside_with_options(self._app.device.udid, self._element.id, options)
    
    def flick(self, from_x=0.9, from_y=0.5, to_x=0.1, to_y=0.5, touchCount=1, repeat=1, interval=0):
        '''滑动/拂去（默认从右向左回避边缘进行滑动/拂去）该接口比drag的滑动速度快，如果滚动距离大，建议用此接口
        
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
        :param repeat: 重复该操作
        :type repeat: int
        :param interval: 重复该操作的间隙时间（秒）
        :type interval: float
        '''
        self._flick_inside_with_options({
            'touchCount'    : touchCount or 1,
            'startOffset'   : {'x': from_x, 'y': from_y},
            'endOffset'     : {'x': to_x,   'y': to_y},
            'repeat'        : repeat or 1,
            'interval'      : interval or 0})
    
    def flick2(self, direct=EnumDirect.Left):
        '''回避边缘在控件体内滑动/拂去
        
        :param direct: 滑动/拂去的方向
        :type  direct: EnumDirect.Left|EnumDirect.Right|EnumDirect.Up|EnumDirect.Down
        '''
        if direct == EnumDirect.Left  : self._app.driver.uia.element.flick_inside_right_to_left(self._app.device.udid, self._element.id)
        if direct == EnumDirect.Right : self._app.driver.uia.element.flick_inside_left_to_right(self._app.device.udid, self._element.id)
        if direct == EnumDirect.Up    : self._app.driver.uia.element.flick_inside_down_to_up(self._app.device.udid, self._element.id)
        if direct == EnumDirect.Down  : self._app.driver.uia.element.flick_inside_up_to_down(self._app.device.udid, self._element.id)
    
    def capture(self):
        '''截图（范围是该控件，可用于发送图片校验MD5或二维码）
        
        :attention: 所有截图统一只支持png格式
        :return: 截图后存储至默认路径（默认路径内存储的图片每次重启都会被清空，请在用例生命周期内取走或完成图片的使用）。
        '''
        return self._app.driver.uia.element.capture(self._app.device.udid, self._element.id)
    
    def wait_for_invalid(self, timeout=5):
        '''等待对象到无效
        
        :param timeout: 等待时间（秒）
        :type timeout: int
        :return: boolean - True表示对象还有效 | False表示对象已无效（如再进行任何操作则抛出异常）
        '''
        return self._app.driver.uia.element.wait_for_invalid(self._app.device.udid, self._element.id, timeout)

    def print_uitree(self):
        '''打印当前控件的UI树
        '''
        _ui_tree = urllib.unquote(self._app.driver.uia.element.get_element_tree(self._app.device.udid, self._element.id))
        _ui_tree = _ui_tree.replace('\r', '\\r')
        _ui_tree = _ui_tree.replace('\n', '\\n')
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

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

class Window(Element):
    '''Window概念
    '''
    def __init__(self, root, locator=None):
        Element.__init__(self, root, (locator if locator else 1))

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

class Alert(Window):
    '''弹出框
    
    由于弹出框在iOS不同版本中的UI逻辑不一致（QPath不同），但业务逻辑相对统一（确定/取消），故单独封装成一个类
    默认是iPhone最新版本的处理逻辑
    '''
    #
    # 20150504 cherry 重构Alert
    #
    def __init__(self, root, locator=QPath("/classname='UIAWindow'/classname='UIAAlert'")):
        Window.__init__(self, root=root, locator=locator)
        self._ios_version = self._app.device.ios_version
        self._ios_type = self._app.device.ios_type
        self._title = None
        self._buttons = []

    @property
    def title(self):
        '''提示文本内容
        '''
        # -*- iOS6
        if re.search('^6', self._ios_version) : self._title = Element(root=self, locator=QPath("/classname='UIAStaticText' && visible=true"))
        else                                  : self._title = Element(root=self, locator=QPath("/classname='UIAScrollView'/classname='UIAStaticText' && visible=true"))
        # -*-
        if self._title is not None            : return self._title
        # -*-
        raise Exception('未找到有效标题，请检查Alert类内的子对象是否正确的QPath')

    @property
    def buttons(self):
        '''Alert控件上的所有按钮
        '''
        # -*- iOS8
        if re.search('^[8|9]', self._ios_version):
            self._buttons = self.find_elements(QPath("/classname='UIACollectionView'/classname='UIACollectionCell'/classname='UIAButton' && visible=true"))
            if len(self._buttons) == 0: self._buttons = self.find_elements(QPath("/classname='UIACollectionView'/classname='UIACollectionCell' && visible=true"))
            # 避免性能测试使用libimobiledevice
            # if self._ios_type == Device.EnumDeviceType.iPad : self._buttons = self.find_elements(QPath("/classname='UIACollectionView'/classname='UIACollectionCell'/classname='UIAButton' && visible=true"))
            # else                                            : self._buttons = self.find_elements(QPath("/classname='UIACollectionView'/classname='UIACollectionCell' && visible=true"))
        # -*- iOS7
        if re.search('^7', self._ios_version)               : self._buttons = self.find_elements(QPath("/classname='UIATableView'/classname='UIATableCell' && visible=true"))
        # -*- iOS6
        if re.search('^6', self._ios_version)               : self._buttons = self.find_elements("/classname='UIAButton' && visible=true")
        # -*-
        if len(self._buttons) > 0                           : return self._buttons
        # -*-
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

    
class Slider(Window):
    '''进度条
    '''
    def __init__(self, root, locator=QPath("/classname='UIAWindow'/classname='UIAImage'/classname='UIASlider' && visible=true")):
        Window.__init__(self, root=root, locator=locator)
        self._ios_version = self._app.device.ios_version
    
    @Window.value.setter
    def value(self, value):
        '''设置进度条的值(取值0~1之间)
        '''
        self._app.driver.uia.element.drag_to_value(self._app.device.udid, self._element.id, value)
        
class ActionSheet(Window): 
    '''UIActionSheet弹出框
    '''
    def __init__(self, root, locator=QPath("/classname='UIAWindow'/classname='UIAActionSheet'")):
        Window.__init__(self, root=root, locator=locator)
        self._ios_version = self._app.device.ios_version  
        self._buttons = []
    
    @property
    def buttons(self):  
        '''ActionSheet上面的所有按钮
        '''
        if re.search('^7', self._ios_version):
            self._buttons = self.find_elements(QPath("/classname='UIAButton' && visible=true"))
        else:
            self._buttons = self.find_elements(QPath("/classname='UIACollectionView'/classname='UIACollectionCell'/classname='UIAButton' && visible=true"))
            other_buttons = self.find_elements(QPath("/classname='UIAButton' && visible=true"))
            if other_buttons:
                self._buttons.extend(other_buttons)
        
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
          

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

if __name__ == '__main__':

    # Demo
    # -*- -*- -*- -*- -*- -*-

    class LoginWin(Window):
        '''登录窗口
        '''
        def __init__(self, root, locator=QPath("/classname='UIAWindow'")):
            Window.__init__(self, root=root, locator=locator)
            self.updateLocator({
                'UIATableCell': {'type':Element, 'root': self,            'locator':QPath("/classname='UIATableCell'")},
                '帐号框'       : {'type':Element, 'root': '@UIATableCell', 'locator':QPath("/classname='UIATextField' && name~='QQ号' && visible=true")},
                "密码框"       : {'type':Element, 'root': '@UIATableCell', 'locator':QPath("/classname='UIASecureTextField' && label~='密码' && visible=true")},
                "登陆按钮"     : {'type':Element, 'root': self,            'locator':QPath("/classname='UIAButton' && label='登陆QQ' && visible=true")},
            })

    # 输入帐号密码
    # -*- -*- -*- -*- -*- -*-

    from qt4i.device import Device

    device = Device()
    app = App(device, 'com.tencent.qq.dailybuild.test.gn')
    app.start()

    # window = Window(app)
    # items = window.find_elements(QPath("/classname='UIAWindow'"))
    # for item in items:
    #     print item.get_attr_dict()

    loginwin = LoginWin(app)
    elem_uid = loginwin.Controls['帐号框']
    elem_pwd = loginwin.Controls['密码框']
    elem_uid.wait_for_exist(5, 0.01)
    elem_pwd.wait_for_exist(5, 0.01)
    elem_uid.value = ""
    elem_uid.send_keys('1002000505')
    elem_pwd.value = ""
    elem_pwd.send_keys('QtaTest123')
    app.release()
