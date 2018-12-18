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
'''此模块用于归纳基础通用子模块
'''
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
import time, re, collections, threading
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

class Timer:
    '''等待计时器（此类被设计成动静混合结构，以期满足静态的需求）
    '''
    interval = 0.1  # (秒) 循环等待步长
    
    def __init__(self, timeout, interval=interval, callback=None, *callback_args):
        '''@param:
            timeout <str>            - 支持以下格式<字符串>，超出格式范围将抛出异常
                YYYY-mm-dd HH:MM:SS  - 阻塞至指定日期时间（常见场景：一次有效。）
                YYYY-mm-dd           - 阻塞至指定日期的零点（常见场景：一次有效。）
                HH:MM:SS             - 阻塞至当天指定时间（常见场景：当天一次有效。如果指定的时间已经在当天过时，那么自动递增一天。）
                D00                  - 阻塞多少天，等效于"H24"
                D0.0                 - 同上
                H00                  - 阻塞n小时（常见场景：持续有效），可大于24小时，向后推算。例如延迟三天可以传入: H72  注意H字头
                H0.0                 - 同上
                M00                  - 阻塞n分钟（常见场景：持续有效），可大于60分钟，向后推算。例如延迟三时可以传入：M180 注意M字头
                M0.0                 - 同上
                S00                  - 阻塞n秒钟（常见场景：持续有效）整数或浮点，可大于60秒钟，向后推算。例如延迟三分可以传入: S180或180或180.0)
                 00                  - 同上，等效于"S00"
                 0.0                 - 同上，等效于"S0.0"
            interval <int|float>     - 默认为0.1秒检测一次
            callback <function>      - 回调函数（如果有传入回调函数则回调）
            *callback_args <objects> - 回调函数的参数
        '''
        self.timeout = timeout
        self.interval = interval
        self.callback = callback
        self.callback_args = callback_args
        self.timeout_seconds = self.convert_timeout_to_seconds(self.timeout)
        self.__wait__(self.timeout_seconds, self.interval, self.callback, *self.callback_args)
    
    @classmethod
    def __convert_datetime_to_seconds__(cls, timeout):
        '''%Y-%m-%d %H:%M:%S
        '''
        return time.mktime(time.strptime(timeout, '%Y-%m-%d %H:%M:%S'))
    
    @classmethod
    def __convert_date_to_seconds__(cls, timeout):
        '''%Y-%m-%d
        '''
        return time.mktime(time.strptime(timeout, '%Y-%m-%d'))
    
    @classmethod
    def __convert_hour24_to_seconds__(cls, timeout):
        '''%H:%M:%S
        '''
        datatime = time.strftime('%Y-%m-%d', time.localtime()) + ' ' + timeout
        seconds = time.mktime(time.strptime(datatime, '%Y-%m-%d %H:%M:%S'))
        if seconds <= time.time() : seconds += (24 * 60 * 60)
        return seconds
    
    @classmethod
    def __convert_day_to_seconds__(cls, timeout):
        '''D00 or D0.0
        '''
        return time.time() + float(re.sub('[^\d\.]', '', timeout)) * (24 * 60 * 60)
    
    @classmethod
    def __convert_hour_to_seconds__(cls, timeout):
        '''H00 or H0.0
        '''
        return time.time() + float(re.sub('[^\d\.]', '', timeout)) * (60 * 60)
    
    @classmethod
    def __convert_minute_to_seconds__(cls, timeout):
        '''M00 or M0.0
        '''
        return time.time() + float(re.sub('[^\d\.]', '', timeout)) * 60
    
    @classmethod
    def __convert_seconds_to_seconds__(cls, timeout):
        '''S00 or S0.0 or 00 or 0.0
        '''
        return time.time() + float(re.sub('[^\d\.]', '', timeout))
    
    @classmethod
    def convert_timeout_to_seconds(cls, timeout):
        timeout = str(timeout)
        patterns = collections.OrderedDict()
        patterns['^\d{2,4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2}:\d{1,2}$'] = cls.__convert_datetime_to_seconds__;  # YYYY-mm-dd HH:MM:SS
        patterns['^\d{2,4}-\d{1,2}-\d{1,2}$'                        ] = cls.__convert_date_to_seconds__    ;  # YYYY-mm-dd
        patterns['^\d{1,2}:\d{1,2}:\d{1,2}$'                        ] = cls.__convert_hour24_to_seconds__  ;  # HH:MM:SS (如果过时则递增至第二天，常见于每天仅执行一次的任务)
        patterns['^D\d+\.?\d*$'                                     ] = cls.__convert_day_to_seconds__     ;  # Ddd or Dd.d
        patterns['^H\d+\.?\d*$'                                     ] = cls.__convert_hour_to_seconds__    ;  # Hhh or Hh.h
        patterns['^M\d+\.?\d*$'                                     ] = cls.__convert_minute_to_seconds__  ;  # Mmm or Mm.m
        patterns['^S?\d+\.?\d*$'                                    ] = cls.__convert_seconds_to_seconds__ ;  # Sss or Ss.s or ss or s.s
        if not re.match('|'.join(patterns.keys()), timeout) : raise Exception("不支持该格式：%s" % timeout)
        for key in patterns:
            if re.match(key, timeout):
                return patterns[key](timeout)
    
    @classmethod
    def __wait__(cls, timeout_seconds, interval=interval, callback=None, *callback_args):
        while(time.mktime(time.localtime()) - timeout_seconds < 0):time.sleep(interval)
        if callable(callback):callback(*callback_args)
    
    @classmethod
    def wait(cls, timeout, interval=interval, callback=None, *callback_args):
        timeout_seconds = cls.convert_timeout_to_seconds(timeout)
        cls.__wait__(timeout_seconds, interval, callback, *callback_args)

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

class ThreadTimer(threading.Thread):
    '''用于需要计时后回调的项目(可以取消)
    '''
    timeout = 30  # (秒) 30秒
    interval = 0.1  # (秒) 循环等待步长
    
    def __init__(self, timeout=timeout, interval=interval, callback=None, *callback_args):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.timeout = timeout
        self.interval = interval
        self.callback = callback
        self.callback_args = callback_args
        if callable(callback) == False : raise Exception('ThreadTimer callback is invalid.')
        self.canceled = False
        self.start()
    
    def cancel(self):
        self.canceled = True
    
    def run(self):
        timeout = Timer.convert_timeout_to_seconds(self.timeout)
        while self.canceled == False and time.time() < timeout : time.sleep(self.interval)
        if self.canceled == False : self.callback(*self.callback_args)
