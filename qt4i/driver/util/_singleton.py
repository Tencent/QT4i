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
'''单例实现
'''

import threading

class Singleton(type):
    """单实例元类，用于某个类需要实现单例模式。
    使用方式示例如下::
          
          class MyClass(object):
              __metaclass__ = Singleton
              def __init__(self, *args, **kwargs):
                  pass
    
    """
    _instances = {}
    def __init__(cls, name, bases, dic):
        super(Singleton, cls).__init__(name, bases, dic)
        cls._instances = {}
        
    def __call__(self, *args, **kwargs):
        if self not in self._instances:
            self._instances[self] = super(Singleton, self).__call__(*args, **kwargs)          
        return self._instances[self]
    
Singleton = Singleton

class ThreadSafetySingleton(object):
    '''单例实现，线程安全
    '''
    _instance = None
    _mutex = threading.Lock()
    
    def __init__(self):
        '''构造函数
        '''
        pass
    
    @staticmethod
    def get_instance():
        '''静态函数
        '''
        if ThreadSafetySingleton._instance == None:
            ThreadSafetySingleton._instance = ThreadSafetySingleton()
            
        with ThreadSafetySingleton._mutex: 
            return ThreadSafetySingleton._instance
        