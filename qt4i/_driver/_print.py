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
'''带时间戳的Print（单纯的Print）
'''
# 2014/09/16    cherry    创建
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
import os, sys, time, datetime
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

def __print__(_std, _str):
    _std.write('[%s][PID:%s] %s\n' % (datetime.datetime.fromtimestamp(time.time()), os.getpid(), _str))

def print_msg(_str):
    '''@desc: 打印输出常规信息'''
    __print__(sys.stdout, _str)

def print_err(_str):
    '''@desc: 打印输出异常信息'''
    __print__(sys.stderr, _str)

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
