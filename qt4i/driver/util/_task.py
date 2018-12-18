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
'''此模块用于归纳基础通用子模块
'''

import re
import sys
import time
import subprocess
import threading
from six import StringIO
from six import PY3

class Task(object):
    
    def __init__(self, command, cwd=None, env=None, print_enable=False):
        '''构造函数
        @param command: 命令行
        @type command: <str>
        @param cwd: 设置执行目录（默认为父进程目录）
        @type cwd: <str>
        @param env: 设置环境变量
        @type env: <dict>
        @param print_enable: 开启print
        @type print_enable: <bool>
        '''
        self.command = command
        self.bufsize = 1
        self.shell = True
        self.cwd = cwd
        self.env = env
        self.print_enable = print_enable
    
    def __execute__(self, out, err):
        '''使用subprocess模块执行
        '''
        process = subprocess.Popen(self.command, bufsize=self.bufsize, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    shell=self.shell, cwd=self.cwd, env=self.env)
        while True:
            out_line = process.stdout.readline()
            if PY3:
                out_line = out_line.decode()
            if out_line == '' and process.poll() != None    : break
            if out_line != '' and self.print_enable == True : sys.stdout.write(out_line)

            out.writelines([out_line])
            out.flush()
        while True:
            err_line = process.stderr.readline()
            if PY3:
                err_line = err_line.decode()
            if err_line == '' and process.poll() != None    : break
            if err_line != '' and self.print_enable == True : sys.stderr.write(err_line)
            err.writelines([err_line])
            err.flush()
        out.seek(0)
        err.seek(0)
        return out, err, process.returncode
    
    def execute1(self):
        '''执行命令
        @return: stdout and stderr<StringIO>
        '''
        out = StringIO()
        self.__execute__(out, out)
        return out
    
    def execute2(self):
        '''执行命令
        @return: (stdout<StringIO>, stderr<StringIO>)
        '''
        out, err = StringIO(), StringIO()
        self.__execute__(out, err)
        return out, err
    
    def execute3(self):
        '''执行命令
        @return: (stdout<StringIO>, stderr<StringIO>, returncode<int>)
        '''
        out, err = StringIO(), StringIO()
        returncode = self.__execute__(out, err)[-1]
        return out, err, returncode
    
    def execute(self):
        '''执行命令
        @return: stdout<str>
        '''
        out = self.execute1()
        return re.sub("\n+$", "", out.read())


class ThreadTask(threading.Thread):
    '''该线程类用于执行Shell
    '''
    
    def __init__(self, command, started_callback=None, stdout_line_callback=None, stderr_line_callback=None, return_code_callback=None, cwd=None, env=None, print_enable=False):
        '''构造函数
        @param command: 命令行
        @type command: <str>
        @param started_callback: started回调
        @type started_callback: <function> 
        @param stdout_line_callback: stdout行回调
        @type stdout_line_callback: <function>
        @param stderr_line_callback: stderr行回调
        @type stderr_line_callback: <function>
        @param return_code_callback: returncode回调
        @type return_code_callback: <function>
        @param cwd: 设置执行目录（默认为父进程目录）
        @type cwd: <str>
        @param env: 设置环境变量
        @type env: <dict>
        @param print_enable: 开启print
        @type print_enable: <bool>
        '''
        threading.Thread.__init__(self)
        self.command = command
        self.bufsize = 1
        self.shell = True
        self.started_callback = started_callback
        self.stdout_line_callback = stdout_line_callback
        self.stderr_line_callback = stderr_line_callback
        self.return_code_callback = return_code_callback
        self.cwd = cwd
        self.env = env
        self.print_enable = print_enable
        self.process = None
        self.keep_running = True
        self.setDaemon(True)
        self.start()
    
    def __call_started_callback__(self, pid):
        '''回调started
        '''
        if self.started_callback and callable(self.started_callback):
            self.started_callback(pid)
    
    def __call_stdout_Line_callback__(self, line):
        '''回调stdout
        '''
        if self.print_enable : sys.stdout.write(line)
        if PY3:
            line = line.decode()
        if self.stdout_line_callback and callable(self.stdout_line_callback):
            self.stdout_line_callback(line)
    
    def __call_stderr_line_callback__(self, line):
        '''回调stderr
        '''
        if self.print_enable : sys.stderr.write(line)
        if PY3:
            line = line.decode()
        if self.stderr_line_callback and callable(self.stderr_line_callback):
            self.stderr_line_callback(line)
    
    def __call_return_code_callback__(self, pid, returncode):
        '''回调returncode
        '''
        if self.return_code_callback and callable(self.return_code_callback):
            self.return_code_callback(pid, returncode)
    
    @property
    def pid(self):
        '''获取进程PID
        '''
        if self.process: return self.process.pid
    
    def poll(self):
        '''进程是否执行完毕
        '''
        if self.process: return self.process.poll()
    
    def is_alive(self):
        '''进程是否还存在
        '''
        if hasattr(self.process, 'returncode'):
            return self.process.returncode == None
        return False
    
    def terminate(self):
        '''终止进程
        '''
        if self.is_alive(): self.process.terminate()
    
    def kill(self):
        '''杀进程
        '''
        if self.is_alive(): self.process.kill()
    
    def run(self):
        '''线程开始执行（该方法自动执行无需调用start）
        '''
        self.process = subprocess.Popen(self.command, bufsize=self.bufsize, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=self.shell, cwd=self.cwd, env=self.env)
        self.__call_started_callback__(self.process.pid)
        while self.keep_running:
            out_line = self.process.stdout.readline()
            if out_line == '' and self.process.poll() != None : break
            if out_line != '' : self.__call_stdout_Line_callback__(out_line)
        while self.keep_running:
            err_line = self.process.stderr.readline()
            if err_line == '' and self.process.poll() != None : break
            if err_line != '' : self.__call_stderr_line_callback__(err_line)
        self.__call_return_code_callback__(self.process.pid, self.process.returncode)
    
    def stop(self):
        '''终止执行
        '''
        self.keep_running = False
        self.terminate()
    
    def wait(self, timeout=0):
        '''等待至进程结束(外部不要使用join等待线程执行完毕)
        '''
        start_time = time.time()
        while self.poll() == None and self.keep_running:
            if timeout > 0 and time.time() - start_time > timeout : break
            time.sleep(0.3)
        time.sleep(1)
