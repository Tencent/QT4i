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
'''logging日志模块的封装
'''

import os
import logging
import datetime
import time
import re

from logging.handlers import BaseRotatingHandler
from testbase.conf import settings

TMP_DIR_PATH = settings.get('QT4I_TMP_DIR_PATH', '/tmp')
LOG_MAX_BTYES = 1024*1024*10 #单份日志最大容量(byte)
LOG_BACKUP_COUNT = settings.get('QT4I_LOG_BACKUP_COUNT', 10) #setting获取count时默认值
LOG_DELAY_DAY = 2 #日志保留天数0.0015625
TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
USER_KEY_WORDS = settings.get('QT4I_AGENT_ERROR_KEY_WORDS', [])
DEFAULT_KEY_WORDS = ['requires a development team','invalid code signature','expired','Connection peer refused channel request']

class RotatingFileHandler(BaseRotatingHandler):
    '''文件滚动日志
    '''
    def __init__(self, filename, mode='a', encoding=None, delay=0):
        self._shouldRoller = False
        BaseRotatingHandler.__init__(self, filename, mode, encoding, delay)

    def doRollover(self):
        '''进行日志滚动
        '''
        if self.stream:
            self.stream.close()
            self.stream = None
        if os.path.exists(self.baseFilename):
            os.remove(self.baseFilename)
        if not self.delay:
            self.stream = self._open()
        self._shouldRoller = False

    def shouldRollover(self, record):
        '''决定是否进行日志滚动
        '''
        if self.stream is None:                 # delay was set...
            self.stream = self._open()
        if self._shouldRoller:                   # are we rolling over?
            return 1
        return 0
    
    def rotate(self):
        '''滚动日志
        '''
        self._shouldRoller = True

def get_logger(logger_name='driverserver'):
    '''通过日志名称获取日志对象
    
    :param logger_name: 日志名称
    :type logger_name: str
    :returns: logger_instance - 日志对象
    '''
    logger_instance = logging.getLogger(logger_name)
    
    if len(logger_instance.handlers) == 0:
        logger_instance.setLevel(logging.DEBUG)
        if not os.path.isdir(TMP_DIR_PATH):
            os.mkdir(TMP_DIR_PATH)
        log_path = os.path.join(TMP_DIR_PATH,"%s.log" % logger_instance.name)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)

        fmt = "[%(asctime)s][pid:%(process)d][tid:%(thread)d][%(levelname)s] %(message)s"
        formatter = logging.Formatter(fmt)
        formatter2 = logging.Formatter(fmt, TIME_FORMAT)
        console_handler.setFormatter(formatter2)
        
        hdlr = logging.handlers.RotatingFileHandler(log_path, maxBytes=LOG_MAX_BTYES, backupCount=LOG_BACKUP_COUNT)
        hdlr.setLevel(logging.DEBUG)
        hdlr.setFormatter(formatter)
        
        logger_instance.addHandler(console_handler)
        logger_instance.addHandler(hdlr)
        
    return logger_instance

def rotate_logger_by_name(logger_name):
    '''通过日志名称滚动日志，并返回日志对象
    
    :param logger_name: 日志名称
    :type logger_name: str
    :returns: logger_instance - 日志对象
    '''
    logger_instance = get_logger(logger_name)
    for handler in logger_instance.handlers:
        if type(handler) == RotatingFileHandler:
            handler.rotate()
    return logger_instance

def get_logger_path_by_name(logger_name):
    '''通过日志名称获取日志路径
    
    :param logger_name: 日志名称
    :type logger_name: str
    :returns: str or None - 日志路径
    '''
    logger_instance = logging.getLogger(logger_name)
    logger_path = None
    attr_name = 'baseFilename'
    for handler in logger_instance.handlers:
        if hasattr(handler, attr_name):
            logger_path = getattr(handler, attr_name)
            break
    return logger_path

def clean_expired_log(logger_name):
    '''
    根据LOG_DELAY_DAY来清理过期的日志
    
    :param logger_name :日志名称
    :type str
    :return None
    '''
    few_day_ago = (datetime.datetime.now() - datetime.timedelta(days = LOG_DELAY_DAY))
    expire_time = time.mktime(few_day_ago.timetuple())
    files = os.listdir(TMP_DIR_PATH)
    for f in files:
        logger_path = os.path.join(TMP_DIR_PATH, f)
        if os.path.exists(logger_path) and f.find(logger_name) != -1:
            c_time = os.path.getctime(logger_path) #获取文件创建时间
            if c_time < expire_time:
                os.remove(logger_path)

def str_to_time(str_time):
    '''
    str类型的时间转换成time
    '''
    return datetime.datetime.strptime(str_time,TIME_FORMAT)
           
def get_agent_error_log(error_log_name, start_time):
    '''
    Failed to start XCTestAgent情况下获取xctest日志中的关键错误信息
    
    :param error_log_name 日志文件名
    :type str
    :param start_time 启动agent日志开始时间
    :type str 时间戳
    :return agent_error_log 返回agent出错的信息
    :type str or ''
    '''
    
    key_word = list(set(USER_KEY_WORDS).union(set(DEFAULT_KEY_WORDS)))
    error_pattern = get_match_pattern(key_word)
    
    time_pattern = r'^\[(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})'
    flag = False #标记该时间段的日志是否已经取完
    start_time = str_to_time(time.strftime(TIME_FORMAT,time.localtime(float(start_time))))
    end_time = str_to_time(time.strftime(TIME_FORMAT, time.localtime()))
    files = os.listdir(TMP_DIR_PATH)
    
    for f in files:
        log_path = os.path.join(TMP_DIR_PATH, f)
        if not flag and os.path.exists(log_path) and f.find(error_log_name) != -1:
            with open(log_path, "rb") as fd:
                for line in fd:
                    line = line.decode("utf-8")
                    match = re.search(time_pattern, line)
                    if match:
                        cur_time = str_to_time(match.group(1))
                        if cur_time < start_time:
                            flag = True
                            continue
                        elif cur_time > end_time:
                            break
                        else:
                            if re.findall(error_pattern, line):
                                return line
    
    return 'No matches found, please check the \'QT4I_AGENT_ERROR_KEY_WORDS\' configuration item'
    
def get_match_pattern(key_word):
    '''
    获取setting文件中配置的对应内容（一个元组），生成正则表达式匹配形式
    :param error_logo setting文件中配置的标志名
    :type str
    :return pattern
    :type str
    '''
    pattern = ''
    
    for key in key_word:
        pattern += '.*' + key + '.*|'
    return pattern[0:len(pattern)-1]
