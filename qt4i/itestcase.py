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

from __future__ import absolute_import, print_function

import os
import time
import traceback

from testbase.testcase import TestCase
from qt4i.device import Device, QT4i_LOGS_PATH


class iTestCase(TestCase):
    '''QT4i测试用例基类
    '''
    crash_flag = False
    attachments_path = QT4i_LOGS_PATH
    error_print_uitree = False
    
    def init_test(self, testresult):
        '''测试用例初始化
        '''
        super(iTestCase, self).init_test(testresult)
        self._start_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

    initTest = init_test    #兼容驼峰式命名和下划线式命名
    
    def clean_test(self):
        '''测试用例清理，以用例为单位清理日志，并释放所有设备
        '''
        try:
            super(iTestCase, self).clean_test()
            Device.cleanup_all_log()
        finally:
            Device.release_all()
    
    cleanTest = clean_test  #兼容驼峰式命名和下划线式命名

    def get_extra_fail_record(self):
        '''当错误发生时，获取需要额外添加的日志记录和附件信息
        
        :return: dict,dict - 日志记录，附件信息
        '''
        #（instruments截屏失败后 则会使用libimobiledevice截屏）
        attachments = {}
        try:
            for device in Device.Devices:
                #上传截图到报告
                image_path = os.path.join(self.attachments_path, "%s_%s.png" % (type(self).__name__, time.time()))
                if device.screenshot(image_path)[0]:
                    attachments['设备截图(%s)' % device.name] = image_path
    
                #上传日志到报告
                log_path = os.path.join(self.attachments_path, "%s_%s.log" % (type(self).__name__, time.time()))
                with open(log_path, 'w') as fd:
                    fd.write(device.get_log(self._start_time))
                    attachments['日志(%s)' % device.name] = log_path
                
                #打印发生error时的UI tree到报告中
                if self.error_print_uitree: 
                    self.log_info("error time ui tree: \n %s"%'\n'.join(device.print_uitree(self.error_print_uitree)))
    
                #记录当前是否发生crash,在具体的测试基类中（根据进程名称过滤）上传crash日志
                self.crash_flag = device.driver.app.has_crashed()
    
                #上传driver日志到报告
                driver_log_path = os.path.join(self.attachments_path, "driver%s_%s.log" % (type(self).__name__, time.time()))
                with open(driver_log_path, 'w') as fd:
                    fd.write(device.get_driver_log(self._start_time))
                    attachments['driver日志(%s)' % device.name] = driver_log_path
            self._start_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        except:
            self.log_info(traceback.format_exc())
        finally:
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
