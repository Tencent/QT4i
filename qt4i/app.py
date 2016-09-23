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
'''iOS App
'''
# 2014/11/16    cherry    创建
import time, datetime

from testbase import logger

class App(object):
    '''iOS App基类
    '''
    
    def __init__(self, device, app_name, trace_template=None, trace_output=None, **params):
        '''构造函数
        
        :param device: Device的实例对象
        :type device: Device
        :param app_name: APP的BundleID（例如：com.tencent.qq.dailybuild.test）
        :type app_name: str
        :param trace_template: trace模板（专项测试使用，功能测试默认为None即可）
        :type trace_template: str
        :param trace_output: trace存储路径（专项测试使用，功能测试默认为None即可）
        :type trace_output: str
        :param params: app启动参数，默认为空
        :type params: dict
        '''
        self._device = device
        self._driver = device.driver
        self._app_name = app_name
        self._trace_template = trace_template
        self._trace_output = trace_output
        self._app_params = params
        self._rules_of_alert_auto_handle = []
        self._flag_alert_auto_handled = False
        self._app_started = False

    def __set_environment__(self):
        self._driver.ins.set_environment(self._device.udid, {
            'rules_of_alert_auto_handle' : self._rules_of_alert_auto_handle,
            'flag_alert_auto_handled'    : not self._flag_alert_auto_handled
        })

    def start(self):
        '''启动APP
        '''
        self.__set_environment__()
        begin_time = time.time()
        self._app_started = self._device.start_app(self._app_name, self._app_params, self._trace_template, self._trace_output)
        if not self._app_started: raise Exception('APP-StartError')
        logger.info('[%s] APP - Start - %s - 启动耗时%s秒' % (datetime.datetime.fromtimestamp(time.time()), self._app_name, round(time.time() - begin_time, 3)))
    
    def get_text(self, text):
        '''获取text对应的本地语言文本
        
        :param text: 标准文本，不随语言环境发生变化的唯一标识
        :type text: str
        :return: str - 本地语言的文
        '''
        # 目前未拿到国际化语言对照表的范本，暂未实现解析步骤，用户可在子类中重载实现
        raise Exception('该函数暂未实现，请在子类中重载实现')
    
    @property
    def device(self):
        '''返回app所在的设备
        
        :rtype: qt4i.device.Device
        '''
        return self._device
    
    @property
    def language(self):
        '''app的当前语言
        
        :rtype: str
        '''
        if self._app_started:
            return self._driver.uia.application.function(self._device.udid, "preferencesValueForKey", "AppleLanguages")
        else:
            raise Exception('APP-StartError')
    
    @property
    def driver(self):
        '''返回app所使用的driver
        
        :rtype: xmlrpclib.ServerProxy
        '''
        return self._driver
    
    @property
    def rules_of_alert_auto_handle(self):
        '''获取已设置的自动处理Alert规则
        
        :rtype: list - [ {"message_text": "message_text", "button_text": "button_text"}, ... ]
        '''
        return self._rules_of_alert_auto_handle

    @rules_of_alert_auto_handle.setter
    def rules_of_alert_auto_handle(self, rules=list()):
        '''设置自动处理Alert规则
        
        当message_text匹配到Alert框内的任意文本，则点击button_text指定的按钮。
        文本以段为单元，元素的label、name、value分为三段文本。规则匹配范围是Alert框内的所有元素的文本。
        :param rules: 规则
        :type rules: list - [ {"message_text": "message_text", "button_text": "button_text"}, ... ]
        '''
        self._rules_of_alert_auto_handle = rules
        if self._app_started:
            self._driver.uia.target.set_rules_of_alert_auto_handle(self._device.udid, rules)

    def add_rule_of_alert_auto_handle(self, message_text, button_text):
        '''自动处理Alert规则，新增一项
        
        :param message_text: Alert内文本片段，支持正则表达式（范围是所谓文本，每个元素的label/name/value为文本段）
        :type message_text: str
        :param button_text: Alert内按钮的文本，支持正则表达式（元素的label/name/value）
        :type button_text: str
        '''
        self._rules_of_alert_auto_handle.append({'message_text': message_text, 'button_text': button_text})
        if self._app_started:
            self._driver.uia.target.add_rule_of_alert_auto_handle(self._device.udid, message_text, button_text)

    @property
    def flag_alert_auto_handled(self):
        '''自动关闭Alert框
        :rtype: boolean
        '''
        return self._flag_alert_auto_handled
    
    @flag_alert_auto_handled.setter
    def flag_alert_auto_handled(self, flag):
        '''自动关闭Alert框
        
        :param flag: True为自动关闭|False为不自动处理
        :type  flag: boolean
        '''
        if flag and not self._flag_alert_auto_handled:
            self._flag_alert_auto_handled = True
            if self._app_started:
                self._driver.uia.target.turn_on_auto_close_alert(self._device.udid)
        if not flag and self._flag_alert_auto_handled:
            self._flag_alert_auto_handled = False
            if self._app_started:
                self._driver.uia.target.turn_off_auto_close_alert(self._device.udid)
    
    def release(self):
        '''终止APP
        '''
        logger.info('[%s] APP - Release - %s' % (datetime.datetime.fromtimestamp(time.time()), self._app_name))
        self._device.release()
        self._app_started = False

    # 上层对象如果多处引用，会带来问题
    # def __del__(self):
    #     self.release()

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
