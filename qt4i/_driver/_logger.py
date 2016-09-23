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
'''全局Log模块

设计目标：
    1、其它Log模块需要占用思维材料，引入复杂的log模块。
    2、标准化行输出，统一print接口，原本连print都不用顾虑（考虑到Python2.x与3.x，统一print接口有兼容的优势）。
    3、Log分级的劣势是需要增加代码和更多的思维材料（实际定位问题时，直接搜索挖掘关键信息更高效）。
'''
# 2014/09/16    cherry    搬迁至MacOSX后第2次重构简化
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
import sys, os
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

class __StdToIO__(object):
    '''Log输出至IO'''
    
    def __init__(self, _std_obj, _io_obj, _print=True):
        '''构造函数
        @param _std_obj : stderr or stdout
        @type _std_obj  : <stderr> or <stdout>
        @param _io_obj  : io对象（file's object or StringIO's object）
        @type _io_obj   : <file> or <StringIO>
        @param _print   : 是否屏幕打印
        @type _print    : <bool>
        '''
        self._std_obj = _std_obj
        self._io_obj = _io_obj
        self._print = _print
    
    def fileno(self):
        return self._io_obj.fileno()
    
    def flush(self):
        self._io_obj.flush()
    
    def close(self):
        self._io_obj.flush()
        self._io_obj.close()
    
    def write(self, *args):
        _line = ''.join(args)
        if self._print == True:
            self._std_obj.write(_line)
            self._std_obj.flush()
        if self._io_obj.closed == False:
            self._io_obj.write(_line)
            self._io_obj.flush()

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

class Logger(object):
    '''全局(stdout & stderr)重定向至指定的Log文件'''
    
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):cls._instance = super(cls, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    
    def __init__(self, _path='log.log', _mode='w', _print=True, _size=50):
        '''构造函数
        @param _path  : Log文件路径。
        @type _path   : <str>
        @param _mode  : Log文件的模式（默认为'w'模式，如果使用追加模式'a+'，请注意控制log的size）。
        @type _mode   : <str>
        @param _print : 是否屏幕打印。
        @type _print  : <bool>
        @param _size  : 记录Log文件的大小（单位: MB，默认50MB）（当再次实例化Log类时，如果存在的Log文件大于该值则会清除。如果需要保留，由使用方程序处理Log备份）。
        @type _size   : <int>
        '''
        self._path = os.path.abspath(_path)
        self._mode = _mode
        self._print = _print
        self._size = _size
        if os.path.exists(self._path) and os.path.getsize(self._path) / 1024 / 1024 > self._size:
            os.remove(self._path)
        self._log_io = file(self._path, self._mode)
        sys.stdout = __StdToIO__(sys.__stdout__, self._log_io, self._print)
        sys.stderr = __StdToIO__(sys.__stderr__, self._log_io, self._print)
    
    def release(self):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
    
    def fileno(self):
        return self._log_io.fileno()
    
    def flush(self):
        self._log_io.flush()
    
    def close(self):
        self.release()
        self._log_io.flush()
        self._log_io.close()
    
    def write(self, line):
        if self._log_io.closed == False:
            self._log_io.write(line)

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

