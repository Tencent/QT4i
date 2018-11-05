# -*- coding:utf-8 -*-
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
'''iOS真机抓包工具
'''

import re
import subprocess
import thread
import time
    
def start_rvictl(udid, sudo_pwd, pcap_path='dump.pcap'):
    try:
        result = False
        cmd = 'rvictl -s %s' % udid
        start_info = subprocess.check_output(cmd.split(' '), stderr = subprocess.STDOUT)
        start_info =start_info.strip('\n')
        print start_info
        matched = re.match(r'Starting device \w+ \[SUCCEEDED\] with interface (rvi\d+)', start_info)
        if matched:
            interface = matched.group(1)
            print 'interface:%s' % interface
            tcpdump = 'tcpdump -i %s -n -s 0 tcp -w %s' % (interface, pcap_path)
            thread.start_new_thread(_sudo, (sudo_pwd, tcpdump))
            time.sleep(1)
            print 'starting tcpdump...'
            result = True
    except subprocess.CalledProcessError, e:
        print e.output
    return result
    

def stop_rvictl(udid, sudo_pwd):
    try:
        result = False
        rvi_active = subprocess.check_output('rvictl -l'.split(' '), stderr = subprocess.STDOUT)
        interface = None
        for line in rvi_active.split('\n'):
            if udid in line:
                interface = re.match(r'.+(rvi\d+)', line).group(1)
                break
        print 'Inquire active interface:', interface
        grep = subprocess.check_output("ps ax | grep tcpdump | grep -v grep", shell=True)
        for line in grep.split('\n'):
            if 'tcpdump' in line and interface in line:
                pid = line.split(' ')[1]
                stop_tcpdump = 'kill -9 %s' % pid
                _sudo(sudo_pwd, stop_tcpdump)
        stop_rvi = 'rvictl -x %s' % udid
        info = subprocess.check_output(stop_rvi.split(' '), stderr = subprocess.STDOUT)
        matched = re.match(r'Stopping device \w+ \[SUCCEEDED\]', info)
        result = not matched 
    except subprocess.CalledProcessError, e:
        print e.output
    return result


def _sudo(sudo_pwd, cmd):
    proc = subprocess.Popen(['sudo', '-S'] + cmd.split(), stdin=subprocess.PIPE, 
            stderr=subprocess.PIPE, universal_newlines=True)
    proc.communicate(sudo_pwd + '\n')
