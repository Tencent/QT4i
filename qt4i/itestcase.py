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
'''qt4i测试用例基类模块
'''
# 2014/05/11    celery      搬迁自Windows版QTA
# 2014/07/15    cherry    调整iTestCase: __init__; initTest; cleanTest;
# 2014/11/16    cherry    提炼DriverManager，面向接口，不要重度污染TestCase
# 2014/11/28    cherry    减肥，去除不应该存在的代码
# 2015/02/13    cherry    重建
# 2015/05/08    olive        适配QTAF5

import os
import time
import urllib


from testbase.testcase import TestCase
from device import DeviceManager
from device import Device
from qt4i._driver.driverserver import DriverManager

class iTestCase(TestCase):
    '''QT4i测试用例基类
    '''
    
    crash_flag = False
    attachments_path = '/tmp/_attachments'
    
    def init_test(self, testresult):
        '''测试用例初始化
        '''
        super(iTestCase, self).init_test(testresult)
        if not os.path.exists(self.attachments_path):
            os.makedirs(self.attachments_path)
        self._device_manager = DeviceManager()

    initTest = init_test    #兼容驼峰式命名和下划线式命名
    
    def clean_test(self):
        '''测试用例清理
        '''
        Device.release_all()
        self._device_manager.release_drivers()
        DriverManager().shutdown()  #兼容本地设备的运行模式
    
    cleanTest = clean_test  #兼容驼峰式命名和下划线式命名

    def get_extra_fail_record(self):
        '''当错误发生时，获取需要额外添加的日志记录和附件信息
        
        :return: dict,dict - 日志记录，附件信息
        '''
        #（instruments截屏失败后 则会使用libimobiledevice截屏）
        attachments = {}
        for device in Device.Devices:
            log_path = os.path.join(self.attachments_path, "%s_%s.log" % (type(self).__name__, time.time()))
            with open(log_path, 'w') as fd:
                fd.write(urllib.unquote(device.driver.ins.get_log()))
                attachments['driver日志(%s)' % device.name] = log_path
            
            #记录当前是否发生crash,在具体的测试基类中（根据进程名称过滤）上传crash日志
            self.crash_flag = device.driver.ins.get_crash_flag()
        
            image_path = os.path.join(self.attachments_path, "%s_%s.png" % (type(self).__name__, time.time()))
            if device.screenshot(image_path):
                attachments['设备截图(%s)' % device.name] = image_path
                
        return {}, attachments
    
    def get_crash_log(self, procname):
        '''获取应用程序的crash日志
        
        :param procname: app的进程名，可通过xcode查看
        :type procname: str
        :return: string or None - crash日志路径
        '''
        crash_logs = {}
        for device in Device.Devices:
            crash_log = device.get_crash_log(procname)
            if crash_log:
                crash_logs['crash日志(%s)' % device.name] = crash_log
        return crash_logs 
