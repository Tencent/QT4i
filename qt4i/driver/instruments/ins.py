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
'''Instruments Manager driver
'''

from __future__ import absolute_import, print_function

import os
import threading
import time 
import urllib

from qt4i.driver.rpc import rpc_method
from qt4i.driver.rpc import RPCEndpoint
from qt4i.driver.tools import logger

from qt4i.driver.instruments.internal._command import DeviceCommandDelegator
from qt4i.driver.instruments.internal._jsonp import Json
from qt4i.driver.util import Process
from qt4i.driver.util import Task
from qt4i.driver.util import ThreadTask

CurrentDirectoryPath = os.path.abspath(os.path.dirname(__file__))


class Instruments(object):
    '''Instrument API
    '''
    
    instances= {}  #保存Instruments的实例,key为设备的udid
    CommandTimeout = 90
    if os.path.exists("/tmp/instruments.log"):
        os.remove("/tmp/instruments.log")
    
    device_command_delegator = DeviceCommandDelegator()
    PythonPath = Task("which python").execute()
    InstrumentDriverPath = os.path.join(CurrentDirectoryPath,"internal","instruments.py")
    TasksPID = {}
    TasksLastError = {}
    TasksBoostrapStandBy = {}
    TasksEnvironment = {}
    TasksStartedEvents = {}
    TasksStoppedEvents = {}
    LastExecCommandDeviceUdid = None
    
    def __init__(self, device_id):
        self.log = logger.get_logger("instruments")
        self.udid = device_id
        if self.udid not in self.instances:
            self.instances[self.udid] = self
        self.crash_flag = False


    def notify(self, json_data):
        '''notify
        
        :param json_data: 要通知的内容
        :type json_data: Json
        '''
        dict_data = Json().loads(json_data)
        method = dict_data["method"]
        params = dict_data["params"]
        device_udid = params[0]["environment"]["device_udid"]
        instruments_pid = params[0]["pid"]
        
        if method == "InstrumentsStarted":
            self.log.info(method)
        if method in ['TraceTemplateInvalid', 'TargetAppBundleIDInvalid', 'DeviceIsCurrentlyLockedWithAPasscode',
               'TheAppMustBeSignedWithADevelopmentIdentity', 'TargetAppIsNotFrontmost', 'TargetAppDied',
               'DeviceDisabled', 'InstrumentsError', 'InstrumentsTimeout']:
            if method == "TargetAppDied":
                self.crash_flag = True
            self.device_command_delegator.clean_all(device_udid, method)
            self.TasksLastError.update({device_udid:method})
            self.dispatch_stopped_events()
            Process().kill_process_tree_by_pid(instruments_pid)
            self.log.error(method)
        
        if method == "InstrumentsTerminated":
            self.device_command_delegator.clean_all(device_udid, method)
            self.TasksEnvironment.pop(device_udid, None)
            self.TasksBoostrapStandBy.pop(device_udid, None)
            self.TasksPID.pop(device_udid, None)
            self.LastExecCommandDeviceUdid = None
            self.dispatch_stopped_events()
            self.log.info(method)
         
    def send_result(self, result):
        '''发送结果给指定的设备
        
        :param result: 要发送的结果
        :type result: str or dict
        '''
        result = Json().loads(result)
        self.device_command_delegator.set_command_result(self.udid, result)
    
    def send_result_and_get_next(self, result, timeout=CommandTimeout):
        '''发送结果给指定设备，并获取下一条指令
        
        :param result: 要发送的结果
        :type result: list or dict
        :param timeout: 指令执行超时 (秒)
        :type timeout: int
        :returns : Json -- 下一条执行的指令
        '''
        self.LastExecCommandDeviceUdid = self.udid
        result = Json().loads(result)
        if result.get('id') is None or result.get('id') < 0:
            if result.get('result') == "BootstrapStandBy":
                self.TasksBoostrapStandBy.update({self.udid:True})
                self.dispatch_started_events()
        else:
            self.device_command_delegator.set_command_result(self.udid, result)
        command = self.device_command_delegator.get_next_command(self.udid, timeout)
        if command:
            return Json().dumps(command, indent=None)
        
    def start(self, bundle_id, app_params, env, xmlrpc_uri, trace_template=None, trace_output=None, retry=3, timeout=55):
        '''用指定设备启动指定APP在后台运行
        
        :param bundle_id: 要启动的APP的Bundle ID
        :type bundle_id: str
        :param app_params: APP 使用的参数
        :type app_params: dict
        :param env: 任务设备的环境
        :type env: dict
        :param trace_template: 专项测试使用trace_template的路径
        :type trace_template: str
        :param trace_output: 专项测试使用trace_output
        :type trace_output: str
        :param retry: 启动失败重试次数
        :type retry: int
        :param timeout: 单次启动超时 (秒)
        :type timeout: int
        :returns : boolean -- True if start successfully, False if not
        ''' 
        if timeout < 10:
            raise Exception("timeout must be longer than 10 seconds")
        if self.is_working(): 
            self.release()
        if env == None:
            env = {}
        self.TasksEnvironment.update({self.udid:env})
        params = ''
        if app_params:
            params_list = []
            for k in app_params:
                params_list.append("-%s" % k)
                params_list.append("%s" % app_params[k])
            params = ' '.join(params_list)
        for i in range(retry):
            self.log.info("ins start app retry %d of %d times"%(i+1, retry))
            ins_py_cmd = ' '.join([self.PythonPath, '"%s"'%self.InstrumentDriverPath,
                                '-device_udid "%s"' % self.udid,
                                '-device_simulator %s' % False,
                                '-bundle_id "%s"' % bundle_id,
                                '-params "%s"' % params if params else '',
                                '-trace_template "%s"' % trace_template,
                                '-trace_output "%s"' % trace_output,
                                '-xmlrpc_uri "%s"' % xmlrpc_uri,
                                '-timeout %s' % (20*60),
                                '-cmd_fetch_delegate_timeout %s' % 10,
                                '-environment "%s"' % urllib.quote("%s"%env)
                                ])
            self.log.info(ins_py_cmd)
            task = ThreadTask(ins_py_cmd, stdout_line_callback=self.log.info, stderr_line_callback=self.log.error)
            if self.wait_for_start(timeout):
                self.TasksPID.update({self.udid: task.pid})
                self.log.info("ins start app successfully")
                return True
            Process().kill_child_processes_by_ppid(task.pid)
            time.sleep(3)
        error = self.TasksLastError.pop(self.udid,None)
        if error:
            raise Exception("[InstrumentsManager] %s"%error)
        return False
    
    def is_working(self):
        '''检查当前app是否在工作
        
        :returns : boolean True if it is working, False if not
        '''
#         return self.udid in self.instances
        return bool(self.TasksBoostrapStandBy.get(self.udid))
      
    def exec_command(self, command, timeout = CommandTimeout):
        '''执行指令
        
        :param command: 指令，包含方法和参数
        :type command: json 例如 {"method": func, "params": list(params)}
        :param timeout: 指令执行超时等待时常
        :type timeout: int 
        :returns : 执行结果 
        '''
        if not self.is_working():
            raise Exception("[Instruments] The app is not working")
        result = self.device_command_delegator.exec_command(self.udid, command, timeout)
        error = result.get("error")
        if error:
            raise Exception(error)
        return result.get("result")

    def dispatch_started_events(self):
        '''去除已经开始的事件
        '''
        events = self.TasksStartedEvents.pop(self.udid, [])
        for event in events:
            event.set()
            events.remove(event)
            
    def dispatch_stopped_events(self):
        '''去除已经停止的事件
        '''
        events = self.TasksStoppedEvents.pop(self.udid, [])
        for event in events:
            event.set()
            events.remove(event)
            
    def wait_for_start(self, timeout = CommandTimeout):
        '''等待设备开始
        
        :param timeout: 等待超时 (秒)
        :type timeout: int
        :returns : boolean -- True if start successfully, False if not
        '''
        event = threading.Event()
        if self.udid in self.TasksStartedEvents:
            self.TasksStartedEvents[self.udid].append(event)
        else:
            self.TasksStartedEvents[self.udid] = [event]
        event.wait(timeout)
        return self.is_working()
    
    def wait_for_stop(self, timeout=CommandTimeout):
        '''等待设备停止
        
        :param timeout: 执行超时时长
        :type timeout: int
        :returns : boolean -- True if stop successfully, False if not
        '''
        event = threading.Event()
        if self.udid in self.TasksStoppedEvents:
            self.TasksStoppedEvents[self.udid].append(event)
        else:
            self.TasksStoppedEvents[self.udid] = [event]
        event.wait(timeout)
        return self.is_working() == False
    
    def release(self, timeout=CommandTimeout):
        '''释放某个设备的instrument
        
        :param timeout: 等待超时 (秒)
        :type timeout: int
        :returns : boolean -- True if release successfully, False if not
        '''
        _begin_time = time.time()
        if self.is_working():
            self.device_command_delegator.clean_all(self.udid, "InstrumentsRelease")
            self.device_command_delegator.send_command(self.udid, {"method": "release"}, timeout-(time.time()-_begin_time))
            if not self.wait_for_stop(timeout-(time.time()-_begin_time)):
                Process().kill_child_processes_by_ppid(self.TasksPID.get(self.udid))
            if self.is_working():
                Process().kill_process_by_name("_fetch_cmd_delegate.py")
                Process().kill_process_by_name("instruments.py")
                os.system('killall -9 "instruments" "Instruments"')
                self.TasksBoostrapStandBy.pop(self.udid, None)
                self.instances.pop(self.udid)
        time.sleep(3)
        return self.is_working() == False
    
    @classmethod
    def release_all(cls):
        '''释放当前使用的所有设备的instrument
        '''
        for device_udid in cls.instances:
            cls.instances(device_udid).release()
        
    def get_crash_flag(self):
        '''获取app是否crash的标识
        
        :returns : boolean -- True if app crashed, False if not
        '''
        return self.crash_flag
    
    def set_command_timeout(self, timeout=CommandTimeout):
        '''设置指令执行超时
        
        :param timeout: 指令执行超时
        :type timeout: int
        '''
        self.__class__.CommandTimeout = timeout

    def get_driver_log(self):
        driver_log_path = None
        for h in self.log.handlers:
            attr_name = 'baseFilename'
            if hasattr(h, attr_name):
                driver_log_path = getattr(h, attr_name)
                break
        return driver_log_path

class InstrumentsCallBacker(RPCEndpoint):
    '''Instruments callback API (调用上面的Instruments的方法实现)
    '''

    rpc_name_prefix = "ins."
    CommandTimeout = 90 
       
    def __init__(self, rpc_server, device_id):
        self.server = rpc_server
        self.udid = device_id
        self.instruments = Instruments(self.udid)
      
    @rpc_method
    def notify(self, json_data):
        '''notify
        
        :param json_data: 要通知的内容
        :type json_data: Json
        '''
        self.instruments.notify(json_data)
    
    @rpc_method
    def send_result(self, result):
        '''发送结果给指定的设备
        
        :param device_udid: 设备的udid标识
        :type device_udid: str
        :param result: 要发送的结果
        :type result: str or dict
        '''
        self.instruments.send_result(result)
    
    @rpc_method
    def send_result_and_get_next(self, result, timeout=CommandTimeout):
        '''发送结果给指定设备，并获取下一条指令
        
        :param result: 要发送的结果
        :type result: list or dict
        :param timeout: 指令执行超时 (秒)
        :type timeout: int
        :returns : Json -- 下一条执行的指令
        '''
        return self.instruments.send_result_and_get_next(result, timeout)

    @rpc_method
    def set_command_timeout(self, timeout=CommandTimeout):
        '''设置指令执行超时
        
        :param timeout: 指令执行超时
        :type timeout: int
        '''
        self.__class__.CommandTimeout = timeout
        
    @rpc_method
    def is_working(self):
        '''判断instrument是否在工作
        
        '''
        return self.instruments.is_working()