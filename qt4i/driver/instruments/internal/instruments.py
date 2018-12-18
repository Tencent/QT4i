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
'''ios_driver
'''
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
from __future__ import absolute_import, print_function

import os, re, time, urllib
from qt4i.driver.instruments.internal._xcode   import Xcode
from qt4i.driver.instruments.internal._timer   import ThreadTimer
from qt4i.driver.util import Args
from qt4i.driver.util import FileManager
from qt4i.driver.instruments.internal._jsonp import Json
from qt4i.driver.util import Process
from qt4i.driver.util import Task
from qt4i.driver.tools import logger

from qt4i.driver.rpc import RPCClientProxy
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

class Instruments(object):
    
    CurrentDirectoryPath = os.path.abspath(os.path.dirname(__file__))
    PythonPath = Task('which python').execute()
    
    def _clean_instrumentscli_n_trace(self, trace_output=None, dir_path=CurrentDirectoryPath):
        if trace_output:
            FileManager(trace_output).force_delete(trace_output)
        items = FileManager(path=dir_path).get_children()
        for item in items:
            if re.match('^instrumentscli\d+.trace$', os.path.basename(item)):
                FileManager(path=item).force_delete()
    
    def _clean_uia_results_path(self):
        manager = FileManager(self.environment.get('uia_results_path'))
        if manager.exists():manager.force_delete()
    
    def _renew_output_path(self):
        for item in ['uia_results_path', 'screen_shot_path']:
            manager = FileManager(self.environment.get(item))
            if manager.exists():manager.force_delete()
            manager.repair_path()
    
    def _update_environment_file(self):
        with open(os.path.join(self.CurrentDirectoryPath, '_environment.js'), 'wb') as fd:
            fd.write('var Environment = %s;' % Json().dumps(self.environment, indent=4))
    
    def _find_instruments_uia_result_path(self):
        if os.path.exists(self.environment.get('uia_results_path')):
            items = FileManager(path=self.environment.get('uia_results_path')).get_children(sort_by_ctime=True)
            if len(items) > 0 : return items[-1]
            else:self.logger.error('Warning: instruments_uia_result_path not found.')
    
    def _copy_instrumentscli_n_trace(self, dir_path=CurrentDirectoryPath):
        dst = self.environment.get('trace_output')
        if dst:
            items = FileManager(path=dir_path).get_children()
            for item in items:
                if re.match('^instrumentscli\d+.trace$', os.path.basename(item)):
                    fm = FileManager(path=item)
                    fm.force_copy_to(dst)
                    fm.force_delete()
    
    def __init__(self, **args):
#         self.logger = Logger(os.path.join('/tmp', 'instruments.log'))
        self.logger = logger.get_logger("instruments")
        self.args = args
        if self.args.get('device_udid') is None: raise Exception('device_udid is None.')
        if self.args.get('device_udid') is None: raise Exception('bundle_id is None.')
        self.device_udid = self.args['device_udid']
        self.environment = {'device_udid'                 : self.args['device_udid'],
                            'device_simulator'            : self.args.get('device_simulator', False),
                            'bundle_id'                   : self.args['bundle_id'],
                            'trace_template'              : self.args.get('trace_template'),
                            'trace_output'                : self.args.get('trace_output'),
                            'uia_script'                  : os.path.abspath(self.args.get('uia_script', os.path.join(self.CurrentDirectoryPath, '_bootstrap.js'))),
                            'uia_results_path'            : os.path.join('/tmp', '_uiaresults'),
                            'screen_shot_path'            : os.path.join('/tmp', '_screenshot'),
                            'cwd'                         : self.CurrentDirectoryPath,
                            'timeout'                     : self.args.get('timeout', 20 * 60),
                            'xmlrpc_uri'                  : self.args.get('xmlrpc_uri', '/'.join(['http://0.0.0.0:12306', 'device', '%s'%self.device_udid])),
                            'cmd_fetch_delegate'          : os.path.join(self.CurrentDirectoryPath, '_cmd_fetch_delegate.py'),
                            'cmd_fetch_delegate_timeout'  : self.args.get('cmd_fetch_delegate_timeout', 10),
                            'ignore_cmd_error'            : self.args.get('ignore_cmd_error', True),
                            'python_path'                 : self.PythonPath}
        self.environment.update(eval(urllib.unquote(self.args.get('environment'))))
        self.args.update(self.environment)
        self.args.update({'started_callback': self.__started_callback__, 'stdout_line_callback': self.__stdout_line_callback__, 'stderr_line_callback': self.__stderr_line_callback__, 'return_code_callback': self.__return_code_callback__})
        self._clean_instrumentscli_n_trace(self.environment.get('trace_output'))
        self._renew_output_path()
        self._update_environment_file()
        self.out = list()
        self.err = list()
        self.rpc = RPCClientProxy(self.environment.get('xmlrpc_uri'), allow_none=True)
        self.instruments = Xcode().start_instruments(**self.args)
        self.logger.info(self.instruments.command)
        self.instruments_uia_result_path = None
        self.logger.info("Instruments timeout %d"%self.environment.get('timeout'))
        self.instruments_timeout_daemon = ThreadTimer(timeout=self.environment.get('timeout'), callback=self.__timeout_kill_instruments__)
        self.instruments_pid = self.instruments.pid
        self.instruments_trace_complete = False
        self.instruments.wait()
    
    def _get_out(self):
        if len(self.out) > 0:
            return ''.join(self.out)
    
    def _get_err(self):
        if len(self.err) > 0:
            return ''.join(self.err)
    
    def _repair_datetime_prefix(self, line):
        datetime_string, line = None, line
        datetime_pattern = '^\d{4}\-\d{2}\-\d{2} \d{2}\:\d{2}\:\d{2}'
        datetime_format = '%Y-%m-%d %H:%M:%S'
        datetime_timezone = 60 * 60 * 8
        if re.search('%s \+0{4} ' % datetime_pattern, line):
            datetime_string, line = re.split('(?<=%s) \+0{4} \w+\: |(?<=%s) \+0{4} ' % (datetime_pattern, datetime_pattern), line, maxsplit=1)
            datetime_string = time.strftime(datetime_format, time.localtime(time.mktime(time.strptime(datetime_string, datetime_format)) + datetime_timezone))
        return datetime_string, line
    
    def __notify__(self, method):
        self.logger.info(method)
        try: self.rpc.ins.notify(Json().dumps({"method": "%s" % method, "params": [{'pid': self.instruments_pid, 'environment': self.environment, 'error': self._get_err()}]}))
        except Exception as e: self.logger.error(str(e))
    
    def __timeout_kill_instruments__(self):
        self.instruments.stop()
        Process().kill_child_processes_by_ppid(os.getpid())
        self.__notify__('InstrumentsTimeout')
    
    def __started_callback__(self, pid):
        self.instruments_pid = pid
        self.__notify__('InstrumentsStarted')
    
    def __stdout_line_callback__(self, line):
        datetime, line = self._repair_datetime_prefix(line)
        if datetime : self.logger.info('[%s][%s] %s' % (datetime, os.getpid(), line)),
        else        : self.logger.info(line),
        self.out.append(line)
        self.__excavate__(line)
        if self.instruments_timeout_daemon : self.instruments_timeout_daemon.cancel()
        self.instruments_timeout_daemon = ThreadTimer(timeout=self.environment.get('timeout'), callback=self.__timeout_kill_instruments__)
    
    def __stderr_line_callback__(self, line):
        datetime, line = self._repair_datetime_prefix(line)
        if datetime : self.logger.info('[%s][%s] %s' % (datetime, os.getpid(), line)),
        else        : self.logger.info(line),
        self.err.append(line)
        self.__excavate__(line)
    
    def __return_code_callback__(self, pid, returncode):
        self.instruments_pid = pid
#         self._copy_instrumentscli_n_trace()  #直接在指定目录生成trace，无需拷贝
        self._clean_instrumentscli_n_trace()
        self._clean_uia_results_path()
        self.__notify__('InstrumentsTerminated')
    
    def __excavate__(self, line):
        if self.instruments_trace_complete == False and re.match('^ScreenshotCaptured:.+$', line):
            if self.instruments_uia_result_path is None:
                self.instruments_uia_result_path = self._find_instruments_uia_result_path()
            if self.instruments_uia_result_path is not None:
                data = Json().loads(re.sub('^ScreenshotCaptured:', '', line))
                src = os.path.join(self.instruments_uia_result_path, data['name'])
                dst = data['path']
                start_time = time.time()
                while time.time() - start_time < 10:
                    if os.path.exists(src):
                        FileManager(src).force_copy_to(dst)
                        if os.path.exists(dst): return
                    time.sleep(0.03)
                self.logger.error('Warning: screenshot failed [ %s ]' % src)
                return
        if self.instruments_trace_complete == False and re.match('^TORPC:.+$', line):
            try: self.rpc.ins.send_result(re.sub('^TORPC:', '', line))
            except Exception as e: self.logger.error(str(e))
            return
        if self.instruments_trace_complete == False and re.match('^Instruments Usage Error : The specified template .+$', line, re.I):
            self.__notify__('TraceTemplateInvalid')
            self.instruments_trace_complete = True
            return
        if self.instruments_trace_complete == False and re.match('^Instruments Usage Error : Specified target process is invalid: .+$', line, re.I):
            self.__notify__('TargetAppBundleIDInvalid')
            self.instruments_trace_complete = True
            return
        if self.instruments_trace_complete == False and re.match('^Instruments Trace Error : Target failed to run: Device is currently locked with a passcode.  Please unlock the device and try again.$', line, re.I):
            self.__notify__('DeviceIsCurrentlyLockedWithAPasscode')
            self.instruments_trace_complete = True
            return
        if self.instruments_trace_complete == False and re.match('^Instruments Trace Error : Target failed to run: Permission to debug com.tencent.qq.dailybuild.test.gn was denied.  The app must be signed with a development identity \(e.g. iOS Developer\).$', line, re.I):
            self.__notify__('TheAppMustBeSignedWithADevelopmentIdentity')
            self.instruments_trace_complete = True
            return
        if self.instruments_trace_complete == False and re.match('^Could not start script, target application is not frontmost.$', line, re.I):
            self.__notify__('TargetAppIsNotFrontmost')
            self.instruments_trace_complete = True
            return
        if self.instruments_trace_complete == False and re.match('^The target application appears to have died$', line, re.I):
            self.__notify__('TargetAppDied')
            self.instruments_trace_complete = True
            return
        if self.instruments_trace_complete == False and re.match('^.+WebKit Threading Violation - initial use of WebKit from a secondary thread.$', line, re.I):
            self.__notify__('DeviceDisabled')
            return
        if self.instruments_trace_complete == False and re.match('^Instruments Usage Error :.+$', line, re.I):
            self.__notify__('InstrumentsError')
            self.instruments_trace_complete = True
            return
        if self.instruments_trace_complete == False and re.match('^Instruments Trace Complete.+$', line, re.I):
            self.instruments.keep_running = False
            self.instruments_trace_complete = True
            return

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

if __name__ == '__main__':

    # ***** ***** ***** ***** ***** ***** ***** *****
    # 参数命令:（参数名不区分大小写，参数值区分大小写）
    #   device_udid                 - 设备UUID
    #   device_simulator            - 设备是否模拟器
    #   bundle_id                   - APP的BundleID
    #   uia_script                  - 脚本
    #   # 以下参数无特殊情况可不传入
    #   trace_template              - 定制化的trace_template
    #   trace_output                - 定制化的trace_output
    #   timeout                     - 闲置超时（单位:秒。默认为1200秒=20分钟），如果持续长时间无运行状态，达到执行的超时值则终止持续运行
    #   xmlrpc_uri                  - XmlRpcServer的uri（默认值: http://0.0.0.0:11516）
    #   cmd_fetch_delegate_timeout  - 请求命令的超时值（单位：秒。只有特殊情况才修改该值）
    #   ignore_cmd_error            - cmd执行异常后，输出异常但不终止程序，默认为True（由应用方判定是否终止程序）
    # ***** ***** ***** ***** ***** ***** ***** *****

    Instruments(**Args())
