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

import time
import datetime

from testbase import logger


class App(object):
    '''iOS App基类
    '''
    
    def __init__(self, device, bundle_id, trace_template=None, trace_output=None, **params):
        '''构造函数
        
        :param device: Device的实例对象
        :type device: Device
        :param bundle_id: APP的BundleID（例如：com.tencent.demo）
        :type bundle_id: str
        :param trace_template: trace模板（专项测试使用，功能测试默认为None即可）
        :type trace_template: str
        :param trace_output: trace存储路径（专项测试使用，功能测试默认为None即可）
        :type trace_output: str
        :param params: app启动参数，默认为空
        :type params: dict
        '''
        self._device = device
        self._driver = device.driver
        self._bundle_id = bundle_id
        self._trace_template = trace_template
        self._trace_output = trace_output
        self._app_params = params
        self._rules_of_alert_auto_handle = []
        self._flag_alert_auto_handled = False
        self._app_started = False

    def start(self):
        '''启动APP
        '''
        begin_time = time.time()
        env = {
            'rules_of_alert_auto_handle' : self._rules_of_alert_auto_handle,
            'flag_alert_auto_handled'    : not self._flag_alert_auto_handled
        }
        self._driver.web.release_app_session(self._bundle_id) #重启app后app_id会发生变化,需要重新获取app_id
        self._app_started = self._device.start_app(self._bundle_id, self._app_params, env, self._trace_template, self._trace_output)
        if not self._app_started: raise Exception('APP-StartError')
        logger.info('[%s] APP - Start - %s - 启动耗时%s秒' % (datetime.datetime.fromtimestamp(time.time()), self._bundle_id, round(time.time() - begin_time, 3)))
    
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
        raise NotImplementedError
    
    @property
    def driver(self):
        '''返回app所使用的driver
        
        :rtype: RPCClientProxy
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
            self._driver.device.set_alert_auto_handling_rules(rules)

    def add_rule_of_alert_auto_handle(self, message_text, button_text):
        '''自动处理Alert规则，新增一项
        
        :param message_text: Alert内文本片段，支持正则表达式（范围是所谓文本，每个元素的label/name/value为文本段）
        :type message_text: str
        :param button_text: Alert内按钮的文本，支持正则表达式（元素的label/name/value）
        :type button_text: str
        '''
        self._rules_of_alert_auto_handle.append({'message_text': message_text, 'button_text': button_text})
        if self._app_started:
            self._driver.device.add_alert_auto_handling_rule(message_text, button_text)

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
                self._driver.device.enable_auto_close_handling(self._device.udid)
        if not flag and self._flag_alert_auto_handled:
            self._flag_alert_auto_handled = False
            if self._app_started:
                self._driver.device.disable_auto_alert_handling(self._device.udid)
    
    def release(self):
        '''终止APP
        '''
        logger.info('[%s] APP - Release - %s' % (datetime.datetime.fromtimestamp(time.time()), self._bundle_id))
        self._app_started = False
        
        
class Safari(App):
    '''Safari浏览器
    '''
    
    
    def __init__(self, device):
        App.__init__(self, device, 'com.apple.safari', app_name='Safari')
        self._init_window()
        
    def _init_window(self):
        from qt4i.icontrols import Element, Window
        from qt4i.qpath import QPath
        self._win = Window(self)
        self._win.updateLocator({
            'Safari':{'type':Element, 'root':self, 'locator':"Safari"},       
            'url输入框.未激活键盘': {'type':Element, 'root':self, 'locator':QPath("/name='URL' & maxdepth=9 & instance=1")},
            'url输入框': {'type':Element, 'root':self, 'locator':QPath("/name~='地址|Address|URL' & maxdepth=9 & instance=1")},
            '打开url': {'type':Element, 'root':self, 'locator':QPath("/name~='^打开$|^Open$' & maxdepth=15")},
        })
        self._win.Controls['Safari'].click()
    
    def open_url(self, url, timeout=1):
        '''打开Safari浏览器，跳转指定网页
        
        :param url: url地址
        :type url: str
        '''
        if self._win.Controls['url输入框.未激活键盘'].wait_for_exist(timeout, 0.05):
            self._win.Controls['url输入框.未激活键盘'].click()
        self._win.Controls['url输入框'].value = url
        self._win.Controls['url输入框'].send_keys('\n')
        if self._win.Controls['打开url'].exist():
            open_btn = self._win.Controls['打开url']
            open_btn.click()
            if open_btn.exist(): # 补充点击防止点击不生效
                self.device.click2(open_btn)
        else:
            raise Exception("Safari没有出现\"打开\"的对话框")


class NLCType(object):
    '''模拟弱网络类型
    '''
    
    NONE = "None"
    LOSS = "100%Loss"
    DSL = "DSL"
    _3G = "3G"
    EDGE = "Edge"
    DNS = "High Latency DNS"
    LTE = "LTE"
    BADNET = "Very Bad Network"
    WIFI = "Wi-Fi"
    WIFI802 = "WI-Fi 802.11ac"
    ADD = "ADD"
    

class Preferences(App):
    '''系统app 设置
    '''
    
    
    def __init__(self, device):
        App.__init__(self, device, 'com.apple.Preferences', app_name='设置')
        self._init_window()
        
    def _init_window(self):
        from qt4i.icontrols import Element, Window
        from qt4i.qpath import QPath
        self._win = Window(self)
        self._win.updateLocator({
            '无线局域网':{'type':Element, 'root':self, 'locator':QPath("/classname='Cell' && name='无线局域网' && maxdepth=8")},
            '无线开关':{'type':Element, 'root':self, 'locator':QPath("/classname='Switch' && name='无线局域网' && maxdepth=12")},
            '设置':{'type':Element, 'root':self, 'locator':QPath("/classname='Button' && name='设置' && maxdepth=5")},
            '蜂窝移动网络':{'type':Element, 'root':self, 'locator':QPath("/classname='Cell' && name='蜂窝移动网络' && maxdepth=8")},
            '蜂窝开关':{'type':Element, 'root':self, 'locator':QPath("/classname='Switch' && name='蜂窝移动数据' && maxdepth=12")},
            '飞行开关':{'type':Element, 'root':self, 'locator':QPath("/classname='Switch' && name='飞行模式' && maxdepth=9")},
            
            '开发者':{'type':Element, 'root':self, 'locator':QPath("/classname='Cell' && name='开发者' && maxdepth=8")},
            'status':{'type':Element, 'root':self, 'locator':QPath("/classname='Cell' && name='Status' && maxdepth=11")},
            'Enable':{'type':Element, 'root':self, 'locator':QPath("/classname='Switch' && name='Enable' && maxdepth=12")},
            '100%Loss':{'type':Element, 'root':self, 'locator':QPath("/classname='Cell' && name='100% Loss' && maxdepth=11")},
            '3G':{'type':Element, 'root':self, 'locator':QPath("/classname='Cell' && name='3G' && maxdepth=11")},
            'DSL':{'type':Element, 'root':self, 'locator':QPath("/classname='Cell' && name='DSL' && maxdepth=11")},
            'Edge':{'type':Element, 'root':self, 'locator':QPath("/classname='Cell' && name='Edge' && maxdepth=11")},
            'High Latency DNS':{'type':Element, 'root':self, 'locator':QPath("/classname='Cell' && name='High Latency DNS' && maxdepth=11")},
            'LTE':{'type':Element, 'root':self, 'locator':QPath("/classname='Cell' && name='LTE' && maxdepth=11")},
            'Very Bad Network':{'type':Element, 'root':self, 'locator':QPath("/classname='Cell' && name='Very Bad Network' && maxdepth=11")},
            'Wi-Fi':{'type':Element, 'root':self, 'locator':QPath("/classname='Cell' && name='Wi-Fi' && maxdepth=11")},
            'WI-Fi 802.11ac':{'type':Element, 'root':self, 'locator':QPath("/classname='Cell' && name='Wi-Fi 802.11ac' && maxdepth=11")},
            'ADD':{'type':Element, 'root':self, 'locator':QPath("/classname='Cell' && name='ADD' && maxdepth=11")},
            '返回':{'type':Element, 'root':self, 'locator':QPath("/classname='Button' && name='返回' && maxdepth=5 && instance=1")},      
            #ios10  
            '手动':{'type':Element, 'root':self, 'locator':"手动"},   
            '关闭':{'type':Element, 'root':self, 'locator':"关闭"},  
            '服务器':{'type':Element, 'root':self, 'locator':QPath("/classname = 'TextField' & label = '服务器' & maxdepth = 11")},
            '端口':{'type':Element, 'root':self, 'locator':QPath("/classname = 'TextField' & label = '端口'  & maxdepth = 11")},              
            #ios11
            '配置代理':{'type':Element, 'root':self, 'locator':"配置代理"},         
            '存储':{'type':Element, 'root':self, 'locator':"存储"},   
            '返回.无线局域网':{'type':Element, 'root':self, 'locator':"无线局域网"},     
            'Conditioner':{'type':Element, 'root':self, 'locator':"Network Link Conditioner"}, 
        })
        self.start()
             
    def _switch_wifi(self, network_type, timeout=1):
        '''wifi切换
        '''
        #进入无线网络
        self._win.Controls['无线局域网'].click()
        #拨动开关按钮        
        if int(self._win.Controls['无线开关'].value) == 1:
            if network_type == 0 or network_type == 1:
                self._win.Controls['无线开关'].click()
        else:
            if network_type == 2 or network_type == 3:
                self._win.Controls['无线开关'].click()
        #返回设置页面
        self._win.Controls['设置'].click()
        
    def _switch_xG(self, network_type, timeout=1):
        '''xG网络切换
        '''
        #进入蜂窝移动网络
        self._win.Controls['蜂窝移动网络'].click()
        #拨动开关按钮               
        if int(self._win.Controls['蜂窝开关'].value) == 1:
            if network_type == 0 or network_type == 2:
                self._win.Controls['蜂窝开关'].click()
        else:
            if network_type == 1 or network_type == 3:
                self._win.Controls['蜂窝开关'].click()
        #返回设置页面
        self._win.Controls['设置'].click()     
        
    def _switch_nlc(self, nlc_type=NLCType.NONE, timeout=1):
        '''弱网络模拟器切换
        '''
        #进入开发者模式
        self._win.Controls['开发者'].click()
        #获得版本号
        version = int(self._device.ios_version[0])
        if version == 1 :
            version = int(self._device.ios_version[:2])  
        #进入状态选择 
        if version == 11 :
            self._win.Controls['Conditioner'].click()
        else :
            self._win.Controls['status'].click()
        status = self._win.Controls['Enable']
        if nlc_type == NLCType.NONE:
            if int(status.value) == 1:
                status.click()
        else :
            if int(status.value) == 0:
                status.click()
            self._win.Controls[nlc_type].click()
        if version == 11 :
            pass
        else :
            self._win.Controls['返回'].click()
            self._win.Controls['设置'].click()           
         
    def switch_network(self, network_type, nlc_type=NLCType.NONE, timeout=1):
        '''网络切换
        
        :param network_type: 网络类型，如下：
                                     0:无WIFI无4G
                                     1:无WIFi有4G
                                     2:有WIFI无4G
                                     3:有WIFI有4G
                                     4:飞行模式
                                     5:保持不变,仅设置弱网
        :type network_type: int
        :param nlc_type: 模拟弱网络类型
        :type nlc_type: NLCType
        '''
        if network_type == 4:
            value = int(self._win.Controls['飞行开关'].value)
            if value == 0 :
                self._win.Controls['飞行开关'].click()
        elif network_type == 5:
            value = int(self._win.Controls['飞行开关'].value)
            if value == 1 :
                self._win.Controls['飞行开关'].click()
            self._switch_nlc(nlc_type, timeout)
        else:
            if self._win.Controls['飞行开关'].value == True:
                self._win.Controls['飞行开关'].click()
            self._switch_wifi(network_type, timeout)
            self._switch_xG(network_type, timeout)
            self._switch_nlc(nlc_type, timeout)
        
    def set_host_proxy(self, server, port, wifi_name): 
        '''设置host代理
        
        :param server: 服务器名
        :type server: str
        :param port: 端口号
        :type port: int
        :param wifi: wifi名
        :type wifi: str
        '''
        #ios版本
        version = int(self._device.ios_version[0])
        if version == 1 :
            version = int(self._device.ios_version[:2])   
        time.sleep(1)                            #添加保护
        #进入无线局域网
        if self._win.Controls['无线局域网'].wait_for_exist(2,0.05):
            self._win.Controls['无线局域网'].click()
        time.sleep(1)                            #添加保护
        from qt4i.icontrols import Element
        from qt4i.qpath import QPath
        self._win.updateLocator({
            'wifi_name':{'type':Element, 'root':self, 'locator':wifi_name},       
            'wifi_title':{'type':Element, 'root':self, 
                'locator':QPath("/classname='NavigationBar' & maxdepth=4 & name='%s'" % wifi_name)},       
            })
        self._win.Controls['wifi_name'].click()
        time.sleep(1)                            #添加保护
        if self._win.Controls['wifi_title'].exist():
            logger.info('已经是%s, 无需切换WiFi' % wifi_name)
        else:
            #再点击一次进入代理设置
            self._win.Controls['wifi_name'].click()
        
        if version == 11 :
            self._win.Controls['配置代理'].click()
            
        self._win.Controls['手动'].click()
        #服务器框
        server_text_field = self._win.Controls['服务器']
        server_text_field.click()
        server_text_field.value = server + '\n'
        #端口框
        port_text_field = self._win.Controls['端口']
        port_text_field.value = port
    
        if version == 11 :
            self._win.Controls['存储'].click()    
            if self._win.Controls['wifi_name'].wait_for_exist(2,0.05):
                self._win.Controls['wifi_name'].click()
        self._win.Controls['返回.无线局域网'].click()
        self._win.Controls['设置'].click()
        
    def reset_host_proxy(self):   
        '''关闭host代理
        ''' 
        #ios版本
        version = int(self._device.ios_version[0])
        if version == 1 :
            version = int(self._device.ios_version[:2])  
        time.sleep(1)                            #添加保护
        #进入无线局域网
        if self._win.Controls['无线局域网'].wait_for_exist(2,0.05):
            self._win.Controls['无线局域网'].click()
        time.sleep(1)                            #添加保护
        from qt4i.icontrols import Element
        self._win.updateLocator({
            'wifi_name':{'type':Element, 'root':self, 'locator':self._device.wifi},       
            })
        self._win.Controls['wifi_name'].click()
        time.sleep(1)                            #添加保护
        #再点击一次进入代理设置
        self._win.Controls['wifi_name'].click()
        
        if version == 11 :
            self._win.Controls['配置代理'].click()
        
        self._win.Controls['关闭'].click()
        if version == 11 :
            self._win.Controls['存储'].click()    
            if self._win.Controls['wifi_name'].wait_for_exist(2,0.05):
                self._win.Controls['wifi_name'].click()
        self._win.Controls['返回.无线局域网'].click()
        self._win.Controls['设置'].click()
        