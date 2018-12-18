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
'''命令'''
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
from __future__ import absolute_import, print_function

import time, threading
from qt4i.driver.tools import logger
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
log = logger.get_logger("instruments")

class __DeviceCommandId__(threading.Thread):
    
    Id = 0
    Lock = threading.Lock()
    
    def __init__(self):
        threading.Thread.__init__(self)
        self._id = None
    
    def get_id(self):
        return self._id
    
    def run(self):
        __DeviceCommandId__.Lock.acquire()
        __DeviceCommandId__.Id += 1
        self._id = __DeviceCommandId__.Id
        __DeviceCommandId__.Lock.release()
    
    @classmethod
    def create_id(cls):
        obj = cls()
        obj.start()
        obj.join()
        return obj.get_id()

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

class __DeviceCommand__(threading.Thread):
    
    StandbyStatus = 0
    ExecuteStatus = 1
    ExecutedStatus = 2
    DiscardStatus = 3
    TimeoutStatus = 4
    FinishedStatus = 5
    
    def __init__(self, _udid, _command, _standby_timeout, _execute_timeout, _print=False):
        '''@desc: 构造函数
        # -*- -*- -*- -*- -*- -*-
        # ---> _command = { "id": <int>(内部自动维护id),  "method": <str>,         "params": [<base-object>,...] }
        # <--- _result  = { "id": <int>（命令的id）,     "result": <base-object>,  "error" : <None>|<str>        }
        # -*- -*- -*- -*- -*- -*-
        @param _udid            : 命令关联的设备
        @type _udid             : <str>
        @param _command         : 命令的实体数据（Python的dict对象）
        @type _command          : <dict>
        @param _standby_timeout : 命令等待执行超时值
        @type _standby_timeout  : <int>|<float>
        @param _execute_timeout : 命令执行超时值
        @type _execute_timeout  : <int>|<float>
        @param _print           : 内部是否跟踪打印命令交互的信息（用于调试）
        @type _print            : <bool>
        '''
        if False == isinstance(_command, dict)  : raise Exception("__DeviceCommand__.__init__(..., _command, ...): The _command is not an instance of the <dict>.")
        if None == _command.get('method', None) : raise Exception("__DeviceCommand__.__init__(..., _command, ...): The _command hasn't [method].")
        threading.Thread.__init__(self)
        self._execute_event = threading.Event()
        self._executed_event = threading.Event()
        _command['id'] = __DeviceCommandId__.create_id()
        self._command_id = _command['id']
        self._udid = _udid
        self._command = _command
        self._standby_timeout = _standby_timeout
        self._execute_timeout = _execute_timeout
        self._print = _print
        self._result = None
        self._standby_timestamp = time.time()
        self._execute_timestamp = None
        self._executed_timestamp = None
        self._discard_timestamp = None
        self._timeout_timestamp = None
        self._finished_timestamp = None
        self._status = self.StandbyStatus
    
    def __get_result_struct__(self, _result=None, _error=None):
        return {"id": self._command_id, "result": _result, "error": _error}
    
    @property
    def standby_timestamp(self):
        return self._standby_timestamp
    
    @property
    def finished_timestamp(self):
        return self._finished_timestamp
    
    @property
    def udid(self):
        return self._udid
    
    @property
    def command_id(self):
        return self._command_id
    
    @property
    def status(self):
        return self._status
    
    @property
    def command(self):
        self._execute_timestamp = time.time()
        self._status = self.ExecuteStatus
        self._execute_event.set()
        if True == self._print : log.info('DeviceCommand-%s: Execute - Standby = %ss' % (self._command_id, round(self._execute_timestamp - self._standby_timestamp, 3)))
        return self._command
    
    @property
    def result(self):
        if self._status != self.FinishedStatus:
            self._finished_timestamp = time.time()
            self._status = self.FinishedStatus
        if True == self._print : log.info('DeviceCommand-%s: Finished - Standby = %ss' % (self._command_id, round(self._finished_timestamp - self._standby_timestamp, 3)))
        return self._result
    
    @result.setter
    def result(self, _result={}):
        if False == isinstance(_result, dict) : raise Exception("__DeviceCommand__.result = _result: The _result is not an instance of the <dict>.")
        self._executed_timestamp = time.time()
        self._status = self.ExecutedStatus
        self._result = self.__get_result_struct__()
        self._result.update(_result)
        self._executed_event.set()
        if True == self._print : log.info('DeviceCommand-%s: Executed - Execute = %ss' % (self._command_id, round(self._executed_timestamp - self._execute_timestamp, 3)))
    
    def discard(self, _error='CommandDiscard'):
        self._discard_timestamp = time.time()
        self._status = self.DiscardStatus
        self._result = self.__get_result_struct__(_error=_error)
        self._executed_event.set()
        if True == self._print : log.info('DeviceCommand-%s: Discarded - Standby = %ss' % (self._command_id, round(self._discard_timestamp - self._standby_timestamp, 3)))
    
    def run(self):
        if True == self._print :
            log.info('DeviceCommand-%s: %s' % (self._command_id, '-' * 60))
            log.info('DeviceCommand-%s: Command  = %s' % (self._command_id, self._command))
        if self._standby_timeout > 0 : self._execute_event.wait(self._standby_timeout)
        if self._execute_timeout > 0 : self._executed_event.wait(self._execute_timeout)
        if self._execute_timeout > 0 and self._status not in [self.ExecutedStatus, self.DiscardStatus, self.FinishedStatus]:
            self._timeout_timestamp = time.time()
            self._status = self.TimeoutStatus
            self._result = self.__get_result_struct__(_error="CommandTimeout")
        if self._status == self.ExecutedStatus:
            self._finished_timestamp = time.time()
            self._status = self.FinishedStatus
        if True == self._print :
            log.info('DeviceCommand-%s: Result   = %s' % (self._command_id, self._result))
            log.info('DeviceCommand-%s: Duration = %ss' % (self._command_id, time.time() - self._standby_timestamp))

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

class __NewDeviceCommandEvent__(threading.Thread):
    
    def __init__(self, _udid, _timeout):
        threading.Thread.__init__(self)
        self._udid = _udid
        self._timeout = _timeout
        self._standby_timestamp = time.time()
        self._finished_timestamp = None
        self._event = threading.Event()
    
    @property
    def udid(self):
        return self._udid
    
    @property
    def timeout(self):
        return self._timeout
    
    @property
    def standby_timestamp(self):
        return self._standby_timestamp
    
    @property
    def finished_timestamp(self):
        return self._finished_timestamp
    
    def notify(self):
        self._event.set()
    
    def run(self):
        self._event.wait(self._timeout)
        self._finished_timestamp = time.time()

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

class __NewDeviceCommandEventDelegator__(threading.Thread):
    
    def __init__(self, _events_buffer_time=1, _events_clean_buffer_interval=0.3):
        threading.Thread.__init__(self)
        self._events = list()
        self._events_lock = threading.Lock()
        self._events_buffer_time = _events_buffer_time
        self._events_clean_buffer_interval = _events_clean_buffer_interval
        self.setDaemon(True)
        self.start()
    
    def create_event_and_waiting(self, _udid, _timeout):
        self._events_lock.acquire()
        _event = __NewDeviceCommandEvent__(_udid, _timeout)
        self._events.append(_event)
        _event.start()
        self._events_lock.release()
        _event.join()
    
    def notify_event(self, _udid):
        self._events_lock.acquire()
        for _event in self._events:
            if _event.is_alive() and _event.udid == _udid:
                _event.notify()
                self._events.remove(_event)
                break
        self._events_lock.release()
    
    def run(self):
        while True:
            time.sleep(self._events_clean_buffer_interval)
            self._events_lock.acquire()
            for _event in self._events:
                if _event.is_alive() == False and _event.finished_timestamp != None and time.time() - _event.finished_timestamp >= self._events_buffer_time:
                    self._events.remove(_event)
            self._events_lock.release()

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

class DeviceCommandDelegator(threading.Thread):
    
    Timeout = 30
    
    def __init__(self, _command_buffer_time=3, _command_clean_buffer_interval=0.5):
        threading.Thread.__init__(self)
        self._command_list = list()
        self._new_command_lock = threading.Lock()
        self._get_next_command_lock = threading.Lock()
        self._new_command_event_delegator = __NewDeviceCommandEventDelegator__(_command_buffer_time, _command_clean_buffer_interval)
        self._last_get_next_command_id = 0
        self._command_buffer_time = _command_buffer_time
        self._command_clean_buffer_interval = _command_clean_buffer_interval
        self.setDaemon(True)
        self.start()
    
    def run(self):
        while True:
            time.sleep(self._command_clean_buffer_interval)
            self._new_command_lock.acquire()
            for _command in self._command_list:
                if _command.is_alive() == False and _command.finished_timestamp != None and time.time() - _command.finished_timestamp >= self._command_buffer_time:
                    self._command_list.remove(_command)
            self._new_command_lock.release()
    
    def __exec_command__(self, _udid, _command, _standby_timeout=Timeout, _execute_timeout=Timeout, _print=False):
        '''@desc: 执行命令
        @param _udid            : 命令关联的设备
        @type _udid             : <str>
        @param _command         : 命令体: {"method": <str>,  "params": <list>}
        @type _command          : <dict>
        @param _standby_timeout : 命令等待执行超时值（秒，默认为30秒）
        @type _standby_timeout  : <int>|<float>
        @param _execute_timeout : 命令执行超时值（秒，默认为30秒）
        @type _execute_timeout  : <int>|<float>
        @param _print           : 是否print命令的过程信息（默认为False）
        @type _print            : <bool>
        @return                 : <dict> : {"id": <int>, "result": <object>, "error": "error"}
        '''
        self._new_command_lock.acquire()
        _command = __DeviceCommand__(_udid, _command, _standby_timeout, _execute_timeout, _print)
        self._command_list.append(_command)
        _command.start()
        self._new_command_event_delegator.notify_event(_udid)
        self._new_command_lock.release()
        _command.join()
        return _command.result
    
    def exec_command(self, _udid, _command, _timeout=Timeout, _print=False):
        '''@desc: 执行命令(阻塞至命令执行完毕或超时)'''
        return self.__exec_command__(_udid, _command, 0, _timeout, _print)
    
    def send_command(self, _udid, _command, _timeout=Timeout, _print=False):
        '''@desc: 执行命令(阻塞至设备接收命令，不需要返回值。如超时未被接收则被抛弃)'''
        self.__exec_command__(_udid, _command, _timeout, 0, _print)
    
    def __get_next_command__(self, _udid):
        self._get_next_command_lock.acquire()
        _next_command = None
        for _command in self._command_list:
            if _command.udid == _udid and _command.status == _command.StandbyStatus and _command.command_id > self._last_get_next_command_id:
                _next_command = _command.command
                self._last_get_next_command_id = _command.command_id
                break
        self._get_next_command_lock.release()
        return _next_command
    
    def get_next_command(self, _udid, _timeout=Timeout):
        '''@desc: 获取某设备的下一条待执行的命令
        @param _udid    : 设备的UUID（iOS、Android、Windows、Mac、Server自己）
        @type _udid     : <str> - 理论上不局限类型
        @param _timeout : 超时（秒） - 当一定时间后，没有对应的命令时则超时
        @type _timeout  : <int> or <float>
        @return         : <dict> : {"id": <int>, "method": <str>,  "params": <list>}
        '''
        _start_timestamp = time.time()
        _next_command = self.__get_next_command__(_udid)
        if _next_command == None and _timeout > 0:
            self._new_command_event_delegator.create_event_and_waiting(_udid, (_timeout - (time.time() - _start_timestamp)))
            return self.get_next_command(_udid, (_timeout - (time.time() - _start_timestamp)))
        return _next_command
    
    def set_command_result(self, _udid, _result):
        '''@desc: 返回结果给指定的命令
        @param _udid   : 设备的UUID（iOS、Android、Windows、Mac、Server自己）
        @type _udid    : <str> - 理论上不局限类型
        @param _result : 命令的结果
        @type _result  : <dict> : {"id": <int>, "result": <object>, "error": "error"}
        '''
        for _command in self._command_list:
            if _udid == _command.udid and _result.get('id') == _command.command_id:
                _command.result = _result
                return
    
    def clean_all(self, _udid, _error):
        '''@desc: 清除所有命令，统一设置结果（例如Crash了取消所有命令）
        @param _udid: 设备的UUID（iOS、Android、Windows、Mac、Server自己）
        @type _udid: <str> - 理论上不局限类型
        @param _error: 命令的结果，主要含清除命令的原因（命令不能无故清除，导致上层无法定位问题）
        @type _error: <dict> = <JSONRPC-Result>
        '''
        for _command in self._command_list:
            if _command.is_alive() and _command.udid == _udid and _command.status not in [_command.ExecutedStatus, _command.DiscardStatus, _command.TimeoutStatus, _command.FinishedStatus]:
                _command.discard(_error)

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

if __name__ == '__main__':
    
    cmds = 2000
    udid = 'iPhone'
    deviceCommandDelegator = DeviceCommandDelegator()
    
    class Driver(threading.Thread):
        def __init__(self, _cmds=cmds):
            threading.Thread.__init__(self)
            self._cmds = _cmds
            self.start()
        def exec_command(self, i):
            _cmd = deviceCommandDelegator.get_next_command(udid)
            if _cmd:
                log.info('Driver - %s <<< cmd : %s' % (i, _cmd))
                _rst = {"id": _cmd['id'], "result": "%s" % _cmd['method'], "error": _cmd['method']}
                deviceCommandDelegator.set_command_result(udid, _rst)
                log.info('Driver - %s >>> rst : %s' % (i, _rst))
            else:
                import sys
                sys.stderr.write('%s\n' % '无命令')
        def run(self):
            for i in range(self._cmds):
                self.exec_command(i)
    
    class Case(threading.Thread):
        def __init__(self, _cmds=cmds):
            threading.Thread.__init__(self)
            self._cmds = _cmds
            self.start()
        def run(self):
            _exec_command_times = list()
            for i in range(self._cmds):
                _cmd = {"method": "%s" % i, "params": ["%s" % i]}
                log.info('-' * 60)
                log.info('Case   - %s cmd --> : %s' % (i, _cmd))
                _start_timestamp = time.time()
                _rst = deviceCommandDelegator.exec_command(udid, _cmd)
                _exec_command_times.append(time.time() - _start_timestamp)
                log.info('Case   - %s rst <-- : %s' % (i, _rst))
            log.info('-' * 60)
            _all_exec_command_time = 0
            for item in _exec_command_times:
                _all_exec_command_time += item
            log.info('执行命令开销: %s\n' % (_all_exec_command_time / len(_exec_command_times)))
    
    for i in range(6):
        case1 = Case()
        driver1 = Driver()
        driver2 = Driver()
        case2 = Case()
    
    while threading.active_count() > 3:
        time.sleep(1)
        log.info('Waitting... [count: %s]' % threading.active_count())
    
    for item in threading.enumerate():
        log.info(item)
    
    while len(deviceCommandDelegator._command_list) > 0:
        log.info('命令队列残留: %s' % len(deviceCommandDelegator._command_list))
        time.sleep(1)
    log.info('命令队列残留: %s' % len(deviceCommandDelegator._command_list))
    log.info('Finished...')
