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
'''QT4i 2.5 - Driver
'''
# 2014/08/30    cherry    创建
# 2014/11/28    cherry    挪入DriverManager
# 2015/10/15    jerry   支持远程Driver
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
import sys
import os
import time
import datetime
import urllib
import xmlrpclib
import threading
import SocketServer
import SimpleXMLRPCServer
import socket
import subprocess
import thread
import base64
import traceback

import pkg_resources
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
from _logger  import Logger
from _args    import Args
from _process import Process
from _print   import print_msg, print_err
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
import ios_driver_api
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
#CurrentDirectoryPath = os.path.abspath(os.path.dirname(__file__))
#LogPath = os.path.join(CurrentDirectoryPath, 'driverserver.log')
LogPath = os.path.join('/tmp', 'driverserver.log')
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

DRIVER_DEFAULT_ADDRESS = socket.gethostbyname(socket.gethostname())

DRIVER_DEFAULT_PORT = 11516

class XMLRPCServer(SocketServer.ThreadingMixIn, SimpleXMLRPCServer.SimpleXMLRPCServer):
    
    LOG_FILTERED_METHODS = ['get_log', 'get_binary_data', 'ins.get_log', 'uia.target.get_element_tree', 'uia.element.get_element_tree']
    
    def __init__(self, addr):
        SimpleXMLRPCServer.SimpleXMLRPCServer.__init__(self, addr=addr, logRequests=False, allow_none=True, encoding='UTF-8')
        self.address, self.port = addr
        self._start_work_time = datetime.datetime.fromtimestamp(time.time())
        self._last_interactive_time = None
        self.register_introspection_functions()
        self.register_function(self.get_start_work_time , 'get_start_work_time')
        self.register_function(self.get_last_interactive_time , 'get_last_interactive_time')
        self.register_function(self.get_pid, 'get_pid')
        self.register_function(self.get_log, 'get_log')
        self.register_function(self.get_binary_data, 'get_binary_data')
        self.register_function(self.send_binary_data, 'send_binary_data')
        self.register_function(self.is_working, 'is_working')
        self.register_function(self.shutdown_driver, 'shutdown_driver')
        self.register_package()
        print_msg('Server(%s:%s) - Started' % (self.address, self.port))
    
    def get_start_work_time(self):
        return '%s' % self._start_work_time
    
    def get_last_interactive_time(self):
        return '%s' % self._last_interactive_time
    
    def get_pid(self):
        return os.getpid()

    def get_log(self):
        try    : return urllib.quote(file(LogPath, "r").read())
        except : return urllib.quote('获取Log失败')
        
    def get_binary_data(self, filename):
        '''拷贝Server端的文件到client端
        '''
        if os.path.exists(filename):
            data = None
            with open(filename, "rb") as fd:
                data = fd.read()
                return xmlrpclib.Binary(base64.encodestring(data))  
        else:
            raise Exception('[%s] does not exist' % filename)

    def send_binary_data(self, binary, filename):
        '''拷贝client端的文件到Server端
        '''
        if os.path.exists(filename):
            os.remove(filename)
        with open(filename, "wb") as fd:
            fd.write(binary.data) 
        return os.path.isfile(filename) 
    
    def is_working(self):
        return True
    
    def _shutdown(self):
        self.shutdown()
    
    def shutdown_driver(self):
        thread.start_new_thread(self._shutdown, ())
    
    def register_package(self):
        ios_driver_api.register_package(self)
    
    def _dispatch(self, method, params):
        _result = None
        print_msg('--- --- --- --- --- ---')
        print_msg('%s <<< %s' % (method, params))
        try: 
            _result = SimpleXMLRPCServer.SimpleXMLRPCServer._dispatch(self, method, params)
        except Exception, e: 
            print_err('%s - Error: %s' % (method, e))
            print_err('%s - Traceback:\n%s' % (method, traceback.format_exc()))
            raise
        if method in XMLRPCServer.LOG_FILTERED_METHODS:
            print_msg('%s >>> Binary Data' %  method)
        else:
            print_msg('%s >>> %s' % (method, _result))
        self._last_interactive_time = datetime.datetime.fromtimestamp(time.time())
        return _result


class ThreadXMLRPCServer(threading.Thread):
    
    def __init__(self, address, port):
        threading.Thread.__init__(self)
        self.address = address
        self.port = port
        self.rpc = xmlrpclib.ServerProxy('http://%s:%s' % (self.address, self.port), allow_none=True, encoding='UTF-8')
        self.start()
    
    def server_is_working(self):
        try: return self.rpc.is_working()
        except: return False
    
    def run(self):
        if not self.server_is_working():
            server = XMLRPCServer((self.address, self.port))
            server.serve_forever()
        else: print_err("Server(%s:%s) - IsWorking" % (self.address, self.port))


def daemonize():
    if os.fork() != 0: sys.exit(0)
    os.setsid()
    os.umask(0)
    if os.fork() != 0: sys.exit(0)
    si = file('/dev/null', 'r')
    so = file('/dev/null', 'w')
    se = file('/dev/null', 'w')
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())


def main(**args):
    daemonize()
    Logger(LogPath)
    global DRIVER_DEFAULT_ADDRESS
    global DRIVER_DEFAULT_PORT
    Process().kill_process_by_port(args.get('port', DRIVER_DEFAULT_PORT))
    os.system('killall -9 "ScriptAgent" "instruments" "Instruments"')
    args.update({'address': args.get('address', DRIVER_DEFAULT_ADDRESS)})
    args.update({'port': args.get('port', DRIVER_DEFAULT_PORT)})
    print_msg('Server(%(address)s:%(port)s) - StartWorking' % args)
    print_msg('--- --- --- --- --- ---')
    ThreadXMLRPCServer(**args).join()
    print_msg('--- --- --- --- --- ---')
    print_msg('Server(%(address)s:%(port)s) - StopWorking' % args)

class DriverManager(object):
    '''QT4i 2.5 DriverManager, 仅供Drun管理Driver Server使用
    '''
    global DRIVER_DEFAULT_ADDRESS
    global DRIVER_DEFAULT_PORT

    def __init__(self, address = DRIVER_DEFAULT_ADDRESS, port = DRIVER_DEFAULT_PORT):
        '''构造（原则：Driver的配置只在此处配置）
        '''
        self._driver_path = pkg_resources.resource_filename("qt4i._driver", "driverserver.py")
        self._driver_address = address
        self._driver_port = port
        self._driver_xmlrpc_url = 'http://%s:%s' % (self._driver_address, self._driver_port)
        self._driver = xmlrpclib.ServerProxy(self._driver_xmlrpc_url, allow_none=True)
    
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):cls._instance = super(DriverManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    
    @property
    def is_working(self):
        try    : return self._driver.is_working()
        except : return False

    @property
    def driver(self):
        if not self.is_working : raise Exception('Server not started.')
        return self._driver
    
    def wait_for_started(self, _timeout=10):
        _begin_time = time.time()
        while time.time() - _begin_time <= _timeout:
            print_msg('wait_for_started...')
            if self.is_working:
                return True
            time.sleep(0.2)
        #return False
        raise Exception('Server failed to start.')
    
    def wait_for_stopped(self, _timeout=10):
        _begin_time = time.time()
        while time.time() - _begin_time <= _timeout:
            if not self.is_working:
                return True
            time.sleep(0.2)
        raise Exception('Server failed to stop.')
    
    def start(self):
        if self.is_working : 
            print 'driver is working'
            return True
        else: 
            subprocess.Popen(['python', self._driver_path, '-address', self._driver_address, '-port',  '%s' % self._driver_port])
        return self.wait_for_started()

    def restart(self):
        retry = 3
        res = False
        for _ in xrange(1, retry+1):
            try:
                self.shutdown()
                res = self.start()
            except:
                print_err('Failed to start driver: %s time!' % _)
            if res:
                return True
        raise Exception('Server failed to start.')
        
    def shutdown(self):
        if self.is_working:
            try:
                self._driver.shutdown_driver()
                self.wait_for_stopped()
            except:
                return self.force_shutdown()
        return True

    def force_shutdown(self):
        Process().kill_process_by_name("driverserver.py")
        return self.wait_for_stopped()
   

class DriverWrapper(object):
    '''Driver的包装类，用于生成Driver client使用
    '''
    global DRIVER_DEFAULT_ADDRESS
    global DRIVER_DEFAULT_PORT

    def __init__(self, address = DRIVER_DEFAULT_ADDRESS, port = DRIVER_DEFAULT_PORT):
        xmlrpc_url = 'http://%s:%s' % (address, port)
        self._driver = xmlrpclib.ServerProxy(xmlrpc_url, allow_none=True, encoding='UTF-8')
    
    @property
    def driver(self):
        return self._driver
    

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

if __name__ == '__main__':
    # ***** ***** ***** ***** ***** ***** ***** ***** *****
    # 命令行调用: server.py -address 127.0.0.1 -port 8080
    #      参数: -address  通信IP地址
    #      参数: -port     通信端口
    # ***** ***** ***** ***** ***** ***** ***** ***** *****
    main(**Args())
