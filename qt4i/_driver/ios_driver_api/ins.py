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
'''driver-instruments-api
'''
# 2014/11/02    cherry    创建
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
import os, time, urllib, threading

from _base import Register
from _command import DeviceCommandDelegator
from tools import DT
from qt4i._driver._jsonp import Json
from qt4i._driver._process import Process
from qt4i._driver._task import Task
from qt4i._driver._task import ThreadTask
from qt4i._driver._print import print_err
from qt4i._driver._print import print_msg
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
CurrentDirectoryPath = os.path.abspath(os.path.dirname(__file__))
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

class Instruments(Register):
    PythonPath = Task('which python').execute()
    DeviceCommandDelegator = DeviceCommandDelegator()
    InstrumentsDriverPath = os.path.join(CurrentDirectoryPath, '..', 'ios_driver', 'instruments.py')
    #InstrumentsLogPath = os.path.join(CurrentDirectoryPath, '..', 'ios_driver', 'instruments.log')
    InstrumentsLogPath = os.path.join('/tmp', 'instruments.log')
    TasksPID = {}
    TasksEnvironment = {}
    TasksStartedEvents = {}
    TasksStoppedEvents = {}
    TasksBootstrapStandBy = {}
    TasksLastError = {}
    LastExecCommandDeviceUdid = None
    CommandTimeout = 90
    crash_flag = False

    def register(self):
        self._register_functions('ins')

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'): cls._instance = super(cls, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, _server=None):
        Register.__init__(self, _server)
        self._server = _server

    def _dispatch_started_events(self, _device_udid):
        _events = self.TasksStartedEvents.pop(_device_udid, [])
        for _event in _events:
            _event.set()
            _events.remove(_event)

    def _dispatch_stopped_events(self, _device_udid):
        _events = self.TasksStoppedEvents.pop(_device_udid, [])
        for _event in _events:
            _event.set()
            _events.remove(_event)

    def is_working(self, _device_udid):
        return bool(self.TasksBootstrapStandBy.get(_device_udid))

    def wait_for_started(self, _device_udid, _timeout=None):
        _event = threading.Event()
        if self.TasksStartedEvents.has_key(_device_udid):
            self.TasksStartedEvents[_device_udid].append(_event)
        else:
            self.TasksStartedEvents[_device_udid] = [_event]
        _event.wait(_timeout)
        return self.is_working(_device_udid) == True

    def wait_for_stopped(self, _device_udid, _timeout=None):
        _event = threading.Event()
        if self.TasksStoppedEvents.has_key(_device_udid):
            self.TasksStoppedEvents[_device_udid].append(_event)
        else:
            self.TasksStoppedEvents[_device_udid] = [_event]
        _event.wait(_timeout)
        return self.is_working(_device_udid) == False

    def notify(self, _json_data):
        _dict = Json().loads(_json_data)
        _method = _dict['method']
        _params = _dict['params']
        _device_udid = _params[0]['environment']['device_udid']
        _instruments_pid = _params[0]['pid']
        # -*- -*- -*-
        if _method == 'InstrumentsStarted' : print_msg(_method)
        # -*- -*- -*-
        if _method in ['TraceTemplateInvalid', 'TargetAppBundleIDInvalid', 'DeviceIsCurrentlyLockedWithAPasscode',
                       'TheAppMustBeSignedWithADevelopmentIdentity', 'TargetAppIsNotFrontmost', 'TargetAppDied',
                       'DeviceDisabled', 'InstrumentsError', 'InstrumentsTimeout']:
            if _method == 'TargetAppDied':
                self.crash_flag = True
            self.DeviceCommandDelegator.clean_all(_device_udid, _method)
            self.TasksLastError.update({_device_udid: _method})
            self._dispatch_started_events(_device_udid)
            Process().kill_process_tree_by_pid(_instruments_pid)
            print_err(_method)
        # -*- -*- -*-
        if _method == 'InstrumentsTerminated':
            self.DeviceCommandDelegator.clean_all(_device_udid, _method)
            self.TasksEnvironment.pop(_device_udid, None)
            self.TasksBootstrapStandBy.pop(_device_udid, None)
            self.TasksPID.pop(_device_udid, None)
            self.LastExecCommandDeviceUdid = None
            self._dispatch_stopped_events(_device_udid)
            print_msg(_method)

    def set_environment(self, _device_udid, _environment={}):
        self.TasksEnvironment.update({_device_udid: _environment})

    def start(self, _device_udid, _device_simulator, _bundle_id, app_params, _trace_template=None, _trace_output=None, _retry=3, _timeout=55, _instruments_timeout=20 * 60, _cmd_fetch_delegate_timeout=10, _force_release=True):
        _device = DT().get_device_by_udid(_device_udid)
        if _device is None                                  : raise Exception('The device_udid is invalid: %s' % _device_udid)
        if _timeout < 10                                    : raise Exception('The _timeout value must be greater than 10 seconds')
        if _force_release and self.is_working(_device_udid) : self.release(_device_udid)
        if self.is_working(_device_udid)                    : raise Exception('The app is working')
        params = ''
        if app_params:
            params_list = []
            for k in app_params:
                params_list.append("-%s" % k)
                params_list.append("%s" % app_params[k])
            params = ' '.join(params_list)
        for i in xrange(_retry):
            _task = ThreadTask(' '.join([self.PythonPath, '"%s"' % self.InstrumentsDriverPath,
                    '-device_udid "%s"' % _device_udid,
                    '-device_simulator %s' % _device_simulator,
                    '-bundle_id "%s"' % _bundle_id,
                    '-params "%s"' % params if params else '',
                    '-trace_template "%s"' % _trace_template,
                    '-trace_output "%s"' % _trace_output,
                    '-xmlrpc_uri "http://%s:%s"' % (self._server.address, self._server.port),
                    '-timeout %s' % _instruments_timeout,
                    '-cmd_fetch_delegate_timeout %s' % _cmd_fetch_delegate_timeout,
                    '-environment "%s"' % urllib.quote("%s" % self.TasksEnvironment.get(_device_udid, {}))]))
            if self.wait_for_started(_device_udid, _timeout):
                self.TasksPID.update({_device_udid: _task.pid})
                return True
            print_err('ins.start -> retry [%s]' % (i+1))
            Process().kill_child_processes_by_ppid(_task.pid)
            time.sleep(3)
        _error = self.TasksLastError.pop(_device_udid, None)
        if _error: raise Exception('%s' % _error)
        return False

    def set_command_timeout(self, _timeout=CommandTimeout):
        self.__class__.CommandTimeout = _timeout

    def send_result(self, _device_udid, _result):
        _result = Json().loads(_result)
        self.DeviceCommandDelegator.set_command_result(_device_udid, _result)

    def send_result_and_get_next(self, _device_udid, _result, _timeout=CommandTimeout):
        self.LastExecCommandDeviceUdid = _device_udid
        _result = Json().loads(_result)
        if _result.get('id') is None or _result.get('id') < 0:
            if _result.get('result') == 'BootstrapStandBy':
                self.TasksBootstrapStandBy.update({_device_udid: True})
                self._dispatch_started_events(_device_udid)
        else:
            self.DeviceCommandDelegator.set_command_result(_device_udid, _result)
        _command = self.DeviceCommandDelegator.get_next_command(_device_udid, _timeout)
        if _command: return Json().dumps(_command, indent=None)

    def exec_command(self, _device_udid, _command, _timeout=CommandTimeout):
        if not self.is_working(_device_udid):
            raise Exception('The app is not working')
        _result = self.DeviceCommandDelegator.exec_command(_device_udid, _command, _timeout)
        _error = _result.get('error')
        if _error:
            raise Exception(_error)
        return _result.get('result')

    def release(self, _device_udid, _timeout=CommandTimeout):
        _begin_time = time.time()
        if self.is_working(_device_udid):
            self.DeviceCommandDelegator.clean_all(_device_udid, 'InstrumentsRelease')
            self.DeviceCommandDelegator.send_command(_device_udid, {"method": "release"}, _timeout - (time.time() - _begin_time))
            if not self.wait_for_stopped(_device_udid, _timeout - (time.time() - _begin_time)):
                Process().kill_child_processes_by_ppid(self.TasksPID.get(_device_udid))
            if self.is_working(_device_udid):
                Process().kill_process_by_name("_cmd_fetch_delegate.py")
                Process().kill_process_by_name("instruments.py")
                os.system('killall -9 "instruments" "Instruments"')
                self.TasksBootstrapStandBy.pop(_device_udid, None) 
                
        time.sleep(3)
        return self.is_working(_device_udid) == False

    def release_all(self):
        for _device_udid in self.TasksBootstrapStandBy.keys():
            self.release(_device_udid)

    def capture_screen(self, _device_udid, _path=None, _timeout=CommandTimeout):
        if self.is_working(_device_udid) is False: raise Exception('The app is not working')
        _begin_time = time.time()
        _command = {'method': 'uia.target.capture_screen', "params": [_path]}
        _path = self.exec_command(_device_udid, _command, _timeout)
        while time.time() - _begin_time < _timeout:
            if os.path.exists(_path): return urllib.quote(_path)
            time.sleep(0.05)
        raise Exception('ins.capture_screen failed')

    def last_exec_command_device_capture_screen(self, _path=None, _timeout=CommandTimeout):
        if self.LastExecCommandDeviceUdid is None: raise Exception('The app is not working')
        return self.capture_screen(self.LastExecCommandDeviceUdid, _path, _timeout)

    def get_log(self):
        try    : return urllib.quote(file(self.InstrumentsLogPath, 'r').read())
        except : return urllib.quote('获取Log失败')
        
    def get_crash_flag(self): 
        return self.crash_flag
       

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-