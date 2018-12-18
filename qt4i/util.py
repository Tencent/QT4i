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
'''utility module
'''



from testbase.util import Timeout as BaseTimeout


class Rectangle(object):
    '''UI控件的矩形区域
    '''
    def __init__(self, left, top, right, bottom):
        self.top = top
        self.left = left
        self.bottom = bottom
        self.right = right
    
    @property
    def width(self):
        return self.right - self.left
    
    @property
    def height(self):
        return self.bottom - self.top
    
    def __repr__(self):
        return repr({'top'    : self.top,
                     'left'   : self.left,
                     'bottom' : self.bottom,
                     'right'  : self.right,
                     'width'  : self.width,
                     'height' : self.height})

class EnumDirect(object):
    '''方向
    '''
    Left, Right, Up, Down = ('Left', 'Right', 'Up', 'Down')


class Timeout(BaseTimeout):
    '''超时
    '''
    def __init__(self, timeout=1.8, interval=0.005):
        BaseTimeout.__init__(self, timeout, interval)
        self.timeout = float(timeout)
        self.interval = float(interval)

    def __repr__(self):
        return "%s" % {"timeout": self.timeout, "interval": self.interval}


class RegExpCompile(object):
    '''编译正则表达式
    当字符串变量中出现正则中的逻辑运算符时，该类将会自动处理转义。
    '''
    
    def __init__(self, source):
        self.source = source
        self.__compile__()
    
    def __compile__(self):
        self.regexp = ''
        for item in self.source:
            if item in '^$.*+?=!:|\\/()[]{}':
                self.regexp += '\\'
            self.regexp += item
    
    def __repr__(self):
        return self.regexp


def less_to(version_a, version_b):
    '''判断version_a是否小于version_b
    
    :returns: True if version_a less than version_b, False if not
    :rtype: boolean
    '''
    import re
    if not re.match('\d*\.\d*\.\d*', version_a):
        return True
    elif not re.match('\d*\.\d*\.\d*', version_b):
        return False
    a = version_a.split('.')
    b = version_b.split('.')
    length = min(len(a), len(b))
    for i in range(length):
        if int(a[i]) < int(b[i]):
            return True
    return False
