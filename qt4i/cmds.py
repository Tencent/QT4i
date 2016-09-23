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
'''QT4i命令
'''

import argparse
from testbase.management import Command
from qt4i._driver.driverserver import DriverManager

class StartDriver(Command):
    '''启动Driver
    '''
    name = 'restartdriver'
    parser = argparse.ArgumentParser("restart local QT4i driver daemon")
    
    def execute(self, args):
        '''执行过程
        '''
        DriverManager().restart()
