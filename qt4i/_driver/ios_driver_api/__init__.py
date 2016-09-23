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
'''iOS Driver API
'''
# 2014/09/16    cherry    创建
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
from tools import DT, IMobileDevice
from ins   import Instruments
from uia   import UIATarget, UIAKeyboard, UIAApplication, UIAElement
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

classes = {DT:False, IMobileDevice:False, Instruments:False, UIATarget:False, UIAKeyboard:False, UIAApplication:False, UIAElement:False}

def register_package(server):
    for cls, value in classes.items():
        if value is False:
            cls(server).register()
            classes.update({cls:True})
