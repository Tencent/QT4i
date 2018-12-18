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
'''Process扩展
'''


import os
import re
import signal
import subprocess
import six


class Process(object):

    def get_processes_by_port(self, port, state="LISTEN"):
        items = []
        
        if isinstance(port, int):
            cmd = r"lsof -nP -iTCP:%s  -sTCP:%s | awk -s '{print  $2}'" % (port, state)
            items = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            if six.PY3:
                items = items.decode()
            items = items.split('\n')
            items = [item for item in items if re.match(r"^\d+$", item)]
        return items

    def get_processes_by_grep(self, grep=''):
        items = []
        stdout = os.popen('ps -ef').read()
        if len(stdout) > 0:
            lines = stdout.split('\n')
            top_line = re.sub('^ +| $', '', lines[0])
            top_line = re.sub(' +', ' ', top_line)
            keys = top_line.split(' ')
            if len(keys) != 8: raise Exception('KeysError')
            lines = lines[1:]
            if isinstance(grep, six.string_types): lines = os.popen('ps -ef|grep "%s" | grep -v grep' % grep).read().split('\n')
            for line in lines:
                if len(line) > 0:
                    line = re.sub('^ +| $', '', line)
                    line = re.sub(' +', ' ', line)
                    values = re.split(' ', line, len(keys) - 1)
                    if len(values) != 8: raise Exception('ValuesError')
                    _dict = {}
                    for i in range(8):
                        key = keys[i]
                        value = values[i]
                        if re.match('^\d+$', value):
                            value = int(value)
                        _dict.update({key: value})
                    items.append(_dict)
        return items

    def get_process_by_pid(self, pid, grep=''):
        if isinstance(pid, int):
            processes = self.get_processes_by_grep(grep)
            for process in processes:
                if process.get('PID') == pid: return process

    def get_child_processes_by_ppid(self, ppid, grep=None):
        children = []
        if isinstance(ppid, int):
            processes = self.get_processes_by_grep(grep)
            for process in processes:
                if process.get('PPID') == ppid: children.append(process)
        return children

    def kill_process_by_pid(self, pid):
        if isinstance(pid, int):
            try:
                os.kill(pid, signal.SIGKILL)
            except:
                pass
        return self.get_process_by_pid(pid) is None

    def kill_process_tree_by_pid(self, pid, grep=None):
        result = True
        if isinstance(pid, int):
            processes = self.get_child_processes_by_ppid(pid, grep)
            for process in processes:
                if self.kill_process_tree_by_pid(process.get('PID')) is False:
                    result = False
            if (self.kill_process_by_pid(pid) and len(self.get_child_processes_by_ppid(pid, grep))==0) is False:
                result = False
        return result

    def kill_child_processes_by_ppid(self, ppid, grep=None):
        if isinstance(ppid, int):
            processes = self.get_child_processes_by_ppid(ppid, grep)
            for process in processes:
                self.kill_process_tree_by_pid(process.get('PID'))
        return len(self.get_child_processes_by_ppid(ppid, grep)) == 0

    def kill_process_by_port(self, port):
        pids = self.get_processes_by_port(port)
        current_pid = os.getpid()
        for pid in pids:
            try:
                if pid != str(current_pid):
                    os.kill(int(pid), signal.SIGKILL)
            except:
                pass
                    
    def kill_process_by_name(self, script_name): 
        cmd = "ps ax | grep '%s' | grep -v grep | awk -s '{print $1}'" % script_name
        result = True
        try:
            data = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            if data:
                if six.PY3:
                    data = data.decode()
                pids = data.strip().split("\n")
                for pid in pids:
                    os.kill(int(pid), signal.SIGKILL)
        except:
            result = False
        return result