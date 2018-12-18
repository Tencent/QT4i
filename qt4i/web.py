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
'''iOS WebView
'''

from __future__ import absolute_import, print_function, division


import time
import traceback

from qt4i.icontrols import Element
from qt4w.util import JavaScriptError
from qt4w.webdriver.webkitwebdriver import WebkitWebDriver


class IOSWebDriver(WebkitWebDriver):
    '''iOS WebKit WebDrvier
    '''
    
    driver_script = WebkitWebDriver.driver_script + r'''
    window['qt4w_driver_lib']['getScale'] = function(){return 1;};
    '''


class IOSWebView(Element):
    '''
    iOS 内嵌WebView控件
    '''
    

    def __init__(self, root, locator, title=None, url=None,  **ext):
        Element.__init__(self, root, locator, **ext)
        self._scrollview = root
        self._device = self._app.device
        self._driver = self._device.driver
        self.bundle_id = self._app._bundle_id
        self.udid = self._device.udid
        self.is_simulator = self._device.simulator
        self.title = title
        self.url_key = url
        self.page_id = self._init_page_id()
        print("webview init page id:%s" % self.page_id)
            
    def _init_page_id(self):
        retry = 5
        for _ in range(retry):
            try:
                return self._driver.web.get_page_id(self.bundle_id, self.title, self.url_key)
            except Exception:
                err = traceback.format_exc()
                time.sleep(1)
        raise RuntimeError('Failed to init page id reason: %s'%err)
        
    @property
    def webdriver_class(self):
        '''WebView对应的WebDriver类
        '''
        return IOSWebDriver
    
    @property
    def rect(self):
        '''WebView控件的坐标
        '''
        root_rect = Window.rect.fget(self)   #webview相对native主窗口的坐标 # @UndefinedVariable
        return [root_rect.left, root_rect.top, root_rect.width, root_rect.height]
    
    @property
    def visible_rect(self):
        '''WebView控件可见区域的坐标信息
        '''
        rect = self._scrollview.rect  # webview相对native主窗口的可视区域的坐标
        visible_rect = [rect.left, rect.top, rect.width, rect.height]
        return visible_rect 
    
    def _coordinate_conversion(self, x, y, rel=True):
        '''WebView的坐标转换为native的坐标
        ''' 
        v_rect = self.visible_rect
        if x < 0 or x > v_rect[2] or \
           y < 0 or y > v_rect[3]:
            raise RuntimeError('[x:%s, y:%s]不在可见区域' % (x, y))
        x_abs = x + v_rect[0]
        y_abs = y + v_rect[1]
        if rel:
            dev_rect = self._device.rect
            x_rel = float('%.2f' % (x_abs / float(dev_rect.width)))
            y_rel = float('%.2f' % (y_abs / float(dev_rect.height)))
            return (x_rel, y_rel)
        else:
            return (x_abs, y_abs)   
         
    
    def click(self, x_offset, y_offset):
        coordinate = self._coordinate_conversion(x_offset, y_offset)
        self._device.click(coordinate[0], coordinate[1])
        
    def long_click(self, x_offset, y_offset, duration=2):
        coordinate = self._coordinate_conversion(x_offset, y_offset)
        self._device.long_click(coordinate[0], coordinate[1], duration)
     
    def double_click(self, x_offset, y_offset):
        coordinate = self._coordinate_conversion(x_offset, y_offset)
        self._device.double_click(coordinate[0], coordinate[1])
    
    def drag(self, x1, y1, x2, y2):
        coordinate1 = self._coordinate_conversion(x1, y1)
        coordinate2 = self._coordinate_conversion(x2, y2)
        self._device.drag(coordinate1[0], coordinate1[1], coordinate2[0], coordinate2[1])
          
    def eval_script(self, frame_xpaths, script):
        '''javascript脚本注入接口
        
        :param frame_xpaths: 保留，暂不使用
        :type frame_xpaths: str|None
        :param script: javascript脚本
        :type script: str
        '''
        result = None
        try:
            result = self._driver.web.eval_script(self.bundle_id, frame_xpaths, self.page_id, script)
        except Exception:
            err = traceback.format_exc()
            if 'WIPageUpdateError' in err:
                self.page_id = self._driver.web.get_page_id(self.bundle_id, self.title, self.url_key)
                return self.eval_script(frame_xpaths, script)
            else:
                raise
        if 'className' in result and (result['className'] == 'ReferenceError' or result['className'] == 'Error'):
            raise JavaScriptError(frame_xpaths, result['description'])
        elif 'type' in result and 'value' in result:
            return result['value']
        elif 'className' in result and result['className'] == 'Array' and 'preview' in result:
            if 'properties' in result['preview']:
                filter_result = []
                for p in result['preview']['properties']:
                    if p['type'] == 'number':
                        filter_result.append(int(p['value']))
                    else:
                        filter_result.append(p['value'])
                return filter_result    
            else:
                return result['preview']
        else:
            return result

    def send_keys(self, keys):
        self._driver.device.send_keys(keys)
