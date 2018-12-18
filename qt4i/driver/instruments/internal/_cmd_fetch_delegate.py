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
'''用于与Server通信（xmlrpc）
'''
from __future__ import absolute_import, print_function

import os, re, sys, socket, six
from qt4i.driver.rpc import RPCClientProxy
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

class Args(dict):
    '''@desc: 命令行参数解析为字典（支持格式:  -key "value" -key=value --key "value" --key=value）
    '''
    RegPattern1 = '^\-{1,2}\w+\=.+$'
    RegPattern2 = '^\-{1,2}\w+$'
    RegPatternAll = '|'.join([RegPattern1, RegPattern2])
    
    def __init__(self, keys_to_lower=True):
        dict.__init__(self)
        self.keys_to_lower = keys_to_lower
        self.parse()
    
    def __convert__(self, item):
        if re.match('^\d+\.\d+$', item)                          : return float(item)
        if re.match('^\d+$', item)                               : return int(item)
        if re.match('|'.join(['^True$', '^False$']), item, re.I) : return bool(item)
        if re.match('|'.join(['^None$', '^NULL$']), item, re.I)  : return None
        return item
    
    def update(self, _dict):
        if self.keys_to_lower:
            for (key, value) in six.iteritems(_dict):
                self[key.lower()] = value
        else:super(self.__class__, self).update(_dict)
    
    def parse(self):
        for i, item in enumerate(sys.argv):
            if re.match(self.RegPatternAll, item):
                if re.match(self.RegPattern1, item):
                    item = re.sub('^-+', '', item)
                    key = re.sub('=.+$', '', item)
                    value = re.sub('^\w+=', '', item)
                    if self.keys_to_lower : key = key.lower()
                    self.update({key:self.__convert__(value)})
                    continue
                if re.match(self.RegPattern2, item):
                    key = re.sub('^-+', '', item)
                    value = sys.argv[i + 1]
                    if self.keys_to_lower : key = key.lower()
                    self.update({key:self.__convert__(value)})
                    continue

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

class Rpc(object):
    
    def __init__(self, xmlrpc_uri, rpc_method, device_udid, result, timeout):
        self.xmlrpc_uri = xmlrpc_uri
        self.rpc_method = rpc_method
        self.result = result
        self.timeout = timeout
        self.rpc = RPCClientProxy(self.xmlrpc_uri, allow_none=True, encoding='UTF-8')
        self.rpc_working = RPCClientProxy(''.join([self.xmlrpc_uri.split("device")[0],'host/']), allow_none=True, encoding='UTF-8')
        socket.setdefaulttimeout(self.timeout + 3)
    
    def rpc_is_working(self):
        try: return self.rpc_working.echo()
        except: return False
    
    def send_result(self):
        if self.rpc_is_working(): self.rpc.ins.send_result(self.result)
    
    def send_result_and_get_next(self):
        # //<-- return  : {"id": 1, "result": "JSON", "error": null}
        # //--> command : {"id": 1, "method": "echo", "params": ["Hello JSON"]}
        if self.rpc_is_working(): return self.rpc.ins.send_result_and_get_next(self.result, self.timeout)
        return '{"id": -1, "method": "release"}'
    
    def rpc_exec(self):
        if self.rpc_method == 'send_result_and_get_next' : return self.send_result_and_get_next()
        if self.rpc_method == 'send_result'              : self.send_result()


if __name__ == '__main__':
    try: sys.stdout.write(Rpc(**Args()).rpc_exec() or '') 
    except Exception as e:
        with open(os.path.join(os.path.dirname(__file__), '_cmd_fetch_delegate.error.log'), 'w') as fd:
            fd.write(repr(e))
        sys.stdout.write(repr(e))
        raise e
