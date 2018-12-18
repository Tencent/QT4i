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
'''XCUITest API driver
'''

from __future__ import absolute_import, print_function

import os
import time
import select
import threading
import pkg_resources
import traceback
import shutil
import subprocess
from six import with_metaclass

from qt4i.driver.tools.sched import PortManager
from qt4i.driver.tools import logger, dt
from qt4i.driver.util import Task
from qt4i.driver.util import ThreadTask
from qt4i.driver.util import Process
from qt4i.driver.xctest.webdriverclient.command import Command
from qt4i.driver.xctest.webdriverclient.errorhandler import ErrorHandler
from qt4i.driver.xctest.webdriverclient.exceptions import WebDriverException
from qt4i.driver.xctest.webdriverclient.exceptions import XCTestAgentDeadException
from qt4i.driver.xctest.webdriverclient.exceptions import XCTestAgentTimeoutException
from qt4i.driver.xctest.webdriverclient.exceptions import ApplicationCrashedException
from qt4i.driver.xctest.webdriverclient.remote_connection import RemoteConnection
from pymobiledevice.usbmux.tcprelay import ThreadedTCPServer, TCPRelay
from testbase.conf import settings
from testbase.util import Singleton

CurrentDirectoryPath = os.path.abspath(os.path.dirname(__file__))

MAX_PORT_NUM = 50
DEFAULT_IP = '127.0.0.1'
DEFAULT_PORT = 8100
AGENT_STORE_PATH = '/cores/xctestagent'


class EnumDevice():
    '''设备类型
    '''
    Device = "iOS"
    Simulator = "iOS Simulator"
    
class AgentStartError(Exception):
    '''Agent Start Error
    '''
    pass


class XCUITestAgentManager(with_metaclass(Singleton, object)):
    '''XCUITest Agent Manager 单例类
    '''
    
    _agents = {}  # 维护Agents的实例，key为设备的udid，value为Agent实例
    _lock = threading.Lock()
    
    @classmethod
    def stop_all_agents(cls):
        '''关闭全部Agent
        '''
        for device_id in cls._agents:
            cls._agents[device_id].stop()
            PortManager.del_port('agent', device_id)
            logger.get_logger("xctest_%s" % device_id).info('stop_agent')
        cls._agents = {}

    def start_agent(self, device_id, server_ip=DEFAULT_IP, server_port=DEFAULT_PORT, keep_alive=False, retry=3, timeout=60):
        '''启动Agent并返回
        
        :param device_id: 设备ID
        :type device_id: str
        :param server_ip: 设备IP地址
        :type server_ip: str
        :param server_port: 设备端口号
        :type server_port: int
        :param keep_alive: HTTP远程连接是否使用keep-alive，默认为False
        :type keep_alive: boolean
        :param retry: 启动尝试次数，默认3次
        :type retry: int
        :param timeout: 单次启动超时 (秒)
        :type timeout: int
        :returns: XCUITestAgent
        '''
        self.log = logger.get_logger("xctest_%s" % device_id)
        if device_id not in self._agents:
            try:
                PortManager.set_port('agent', device_id, server_port)
                server_port = PortManager.get_port('agent', device_id)
                self.log.info('start_agent, port: %d' %server_port)
                with self._lock:
                    self._agents[device_id] = XCUITestAgent(device_id, server_ip, server_port, keep_alive, retry, timeout)
            except:
                self.log.exception('start_agent')
                PortManager.del_port('agent', device_id)
                raise
        return self._agents[device_id]
        
    def restart_agent(self, device_id):
        '''重启Agent
        '''
        if device_id in self._agents:
            self._agents[device_id].stop()
            self._agents[device_id].start()
        else:
            self.start_agent(device_id)
        
    def stop_agent(self, device_id):
        '''关闭Agent
        '''
        if device_id in self._agents:
            self._agents[device_id].stop()
            PortManager.del_port('agent', device_id)
            self._agents.pop(device_id)
    
    def get_agent(self, device_id):
        '''根据udid获取Agent对象
        
        :param device_id: 设备udid
        :type device_id: str
        :returns: XCUITestAgent
        '''
        if device_id in self._agents:
            return self._agents[device_id]
        else:
            return self.start_agent(device_id)
    
    @property
    def agents(self):
        '''获取Agent列表
        
        :returns: list
        '''
        return self._agents.values()
    
    def has_agent(self, device_id):
        '''查询设备是否存在对应的agent
        
        :returns: boolean
        '''
        return device_id in self._agents


class XCUITestAgent(object):
    '''XCUITest Agent
    '''
    _process = None # Agent进程
    _relay_thread = None # 端口映射线程
    _agent_cmd = ''
    CommandTimeout = settings.get('QT4I_START_APP_TIMEOUT', 60)
    PythonPath = Task("which python").execute()
    
    LOG_FILTERED_METHODS = [
                            Command.SCREENSHOT, 
                            Command.QTA_STOP_AGENT,
                            Command.GET_PAGE_SOURCE,
                            Command.GET_ELEMENT_TREE,
                            Command.QTA_ELEMENT_TREE,
                            ]

    def __init__(self, device_id, server_ip=DEFAULT_IP, server_port=DEFAULT_PORT, keep_alive=False, retry=3, timeout=60):
        self.log_name = "xctest_%s" % device_id
        self.log = logger.get_logger(self.log_name)
        
        self.version = '0.0.0'
        version_file = os.path.join(os.path.expanduser('~'), 'XCTestAgent', 'version.txt')
        if os.path.exists(version_file):
            with open(version_file, 'r') as f:
                self.version = f.read()
        
        # XCTestAgent工程默认路径：~/XCTestAent/XCTestAgent.xcodeproj
        self.XCTestAgentPath = os.path.join(os.path.expanduser('~'), "XCTestAgent", "XCTestAgent.xcodeproj")
        if not os.path.exists(self.XCTestAgentPath):
            msg = 'XCTestAgent does not exist. Please use command line: "python manage.py qt4i.setup" to setup XCTestAgent.xcodeproj'
            self.log.error(msg)
            raise Exception(msg)
            
        self.udid = device_id
        self._server_ip = server_ip
        self._server_port = server_port
        self._server_url = 'http://%s:%d' % (server_ip, server_port)
        self.type = EnumDevice.Simulator if dt.DT().is_simulator(device_id) else EnumDevice.Device
        self._is_remote = True
        self.session_id = None
        self.crash_flag = False
        self.capabilities = {}
        self.mjpeg_port = 9100 + self._server_port - 8100
        self.stub_remote_port = 18123
        self.stub_port = 18123 + self._server_port - 8100
        self.stub_server_url = 'http://%s:%d' % (DEFAULT_IP, self.stub_port)
        self.stub_client = RemoteConnection(self.stub_server_url, keep_alive=False, logger_name=self.log_name)
        self.stub_client.set_timeout(0.01)
        self.error_handler = ErrorHandler()
        self._command_executor = RemoteConnection(self._server_url, keep_alive=keep_alive, logger_name=self.log_name)
        self._is_relay_quit = threading.Event()
        self.start(retry, timeout)
    
    def _tcp_relay(self):
        '''将设备8100端口映射到本地8100端口，虚拟机不需要映射
        '''
        if self.type == EnumDevice.Simulator:
            return
        if not self._relay_thread and self._server_ip == DEFAULT_IP:
            self._relay_error = None
            self._relay_thread = threading.Thread(target=self._forward_ports)
            self._relay_thread.daemon = True
            self.log.info("Start TCPRelay Thread")
            self._relay_thread.start()
            time.sleep(1)
            if self._relay_error:
                raise Exception(self._relay_error)
            if not self._relay_thread.is_alive():
                raise RuntimeError('_relay_thread failed to start')
            
    def _forward_ports(self):
        '''iOS真机设备的端口转发
        '''
        try:
            agent_port_pair = '%d:%d' % (8100, self._server_port)
            stub_port_pair = '%d:%d' %(self.stub_remote_port, self.stub_port)
            mjpeg_port_pair = '%d:%d' %(9100, self.mjpeg_port)
            pair_ports = [agent_port_pair, stub_port_pair, mjpeg_port_pair] # 端口对的数组，每对端口中前一个代表远程端口，后一个代表本地端口，例如：["8100:8100", "8200:8200"]
            self._tcp_servers=[]
            serverclass = ThreadedTCPServer
            for pair_port in pair_ports:
                rport, lport = pair_port.split(":")
                rport = int(rport)
                lport = int(lport)
                self.log.info("Forwarding local port %d to remote port %d" % (lport, rport))
                server = serverclass(("localhost", lport), TCPRelay)
                server.rport = rport
                server.bufsize = 128
                server.udid = self.udid
                self._tcp_servers.append(server)
                
            self._quit_relay_thread = False # 退出端口转发线程的标识位
            self._is_relay_quit.clear()
            while not self._quit_relay_thread:
                try:
                    rl, wl, xl = select.select(self._tcp_servers, [], []) #@UnusedVariable
                    for server in rl:
                        server.handle_request()
                except:
                    self.log.exception('Forward ports')
                    self._quit_relay_thread = True
            self.log.info("Forward ports: successfully quit select")
            for server in self._tcp_servers:
                server.server_close()
            self._is_relay_quit.set()
            self.log.info("Forward ports: successfully close socket")
            
        except Exception:
            self._relay_error = traceback.format_exc()
            self.log.exception('forward ports')

    def _build_agent_for_simulator(self, xcode_version):
        agent_dir = os.path.join(AGENT_STORE_PATH, xcode_version)
        agent_file = os.path.join(agent_dir, 'XCTestAgent-Runner.app')
        if not os.path.exists(agent_file):
            if not os.path.exists(agent_dir):
                os.makedirs(agent_dir)
            xctest_root = pkg_resources.resource_filename("qt4i", "driver/xctest/xctestproj") #@UndefinedVariable
            xctestproj = os.path.join(xctest_root, 'XCTestAgent','XCTestAgent.xcodeproj')
            build_for_test_cmd = ' '.join(['xcodebuild',
                'build-for-testing',
                '-project',
                '"%s"' % xctestproj,
                '-scheme',
                'XCTestAgent',
                '-destination',
                '"platform=%s,id=%s"' % (self.type, self.udid),
                'CONFIGURATION_BUILD_DIR=%s' % agent_dir])
            subprocess.call(build_for_test_cmd, shell=True)
            self.log.debug("build XCTestAgent:%s" % build_for_test_cmd)
        return agent_dir

    def _get_xcodebuild_agent_cmd_for_simulator(self, xcode_version):
        template_root = pkg_resources.resource_filename("qt4i", "driver/xctest/bin") #@UndefinedVariable
        xctestfile_template = os.path.join(template_root, "iphonesimulator-%s.xctestrun" % xcode_version)
        agent_dir = self._build_agent_for_simulator(xcode_version)
        xctestfile = os.path.join(agent_dir, "%s.xctestrun" % self.udid)
        if not os.path.isfile(xctestfile):
            shutil.copyfile(xctestfile_template, xctestfile)
        cmd = "/usr/libexec/PlistBuddy -c 'Set :XCTestAgent:EnvironmentVariables:USE_PORT %s' %s" % (self._server_port, xctestfile)
        subprocess.call(cmd, shell=True)
        derived_data_path = '/tmp/xctlog/%s' % self.udid
        if not os.path.exists(derived_data_path):
            os.makedirs(derived_data_path)
        return ' '.join(['xcodebuild',
                'test-without-building',
                '-xctestrun',
                xctestfile,
                '-destination',
                '"platform=%s,id=%s"' % (self.type, self.udid),
                '-derivedDataPath',
                derived_data_path])

    def _get_fbsimctl_agent_cmd_for_simulator(self, xcode_version):
        agent_dir = self._build_agent_for_simulator(xcode_version)
        xctest_path = os.path.join(agent_dir, 'XCTestAgent-Runner.app/PlugIns/XCTestAgent.xctest') 
        attached_app = settings.get('QT4I_SIM_ATTACHED_APP', 'com.apple.reminders')
        return ' '.join([dt.DT().fbsimctl,
                self.udid,
                'launch_xctest',
                xctest_path,
                attached_app,
                '--port %s -- listen' % self._server_port])
        
    def _stdout_line_callback(self, line):
        '''标准输出回调函数
        '''
        self.log.debug(line.strip(' '))
    
    def _stderr_line_callback(self, line):
        '''标准错误回调函数
        '''
        self.log.error(line.strip(' '))

    def start(self, retry=1, timeout=CommandTimeout):
        '''启动Agent，类初始化即调用
        
        :param retry: 启动尝试次数
        :type retry: int
        :param timeout: 单次启动超时 (秒)
        :type timeout: int
        '''
        if self.type == EnumDevice.Simulator:
            dt.DT().reboot(self.udid)
            xcode_version = dt.DT.get_xcode_version().split(".")[0]
            if int(xcode_version) >= 9:
                self._agent_cmd = self._get_xcodebuild_agent_cmd_for_simulator(xcode_version)
            else:
                self._agent_cmd = self._get_fbsimctl_agent_cmd_for_simulator(xcode_version)
        else:
            self._agent_cmd = ' '.join(['xcodebuild',
                '-project %s' % self.XCTestAgentPath,
                '-scheme %s' % 'XCTestAgent',
                '-destination "platform=%s,id=%s"' % (self.type, self.udid),
                'test'])
        # 清理遗留的xcodebuild进程
        Process().kill_process_by_name(self._agent_cmd.replace('"', ''))
        Process().kill_process_by_port(self._server_port)
        start_time = time.time()
        # 启动端口转发线程
        self._tcp_relay()
        for _ in range(retry):
            self.log.info("Start XCTestAgent: %s" %self._agent_cmd)
            self.log.info("XCTestAgent Version: %s" %self.version)
            self._process = ThreadTask(command=self._agent_cmd, 
                                       stdout_line_callback=self._stdout_line_callback, 
                                       stderr_line_callback=self._stderr_line_callback)
            
            time0 = time.time()
            while time.time() - time0 < timeout:
                if self.is_working():
                    exec_time = (time.time() - start_time) * 1000
                    self.log.info('[ %s ] consumed [ %dms ]' %('Start XCTestAgent', exec_time))
                    return
                time.sleep(3)
            
            _dt = dt.DT()
            self.log.info("Uninstall com.apple.test.XCTestAgent-Runner")
            result = _dt.uninstall("com.apple.test.XCTestAgent-Runner", self.udid)
            if not result:
                self.log.error(_dt.uninstall_error)
        
        self.stop()
        error_log_name = 'xctest_%s' % self.udid
        agent_error_log = logger.get_agent_error_log(error_log_name, start_time)
        raise AgentStartError("Failed to start XCTestAgent.\nDetails:%s" % agent_error_log)
    
    def stop(self, is_timeout=False):
        '''关闭Agent
        '''
        if not is_timeout:
            # 停止手机上Agent进程
            try:
                self._command_executor.set_timeout(2)
                self.execute(Command.QTA_STOP_AGENT)
            except:
                pass
        # 停止PC上端口转发线程
        if self._relay_thread:
            self._quit_relay_thread = True
            try:
                self._execute(Command.HEALTH) # 发送请求，退出select阻塞
            except:
                pass
            self._is_relay_quit.wait() # 等待端口转发线程退出
            self._relay_thread = None
        self._command_executor.reset_timeout()
        # 等待PC上xcodebuild进程停止
        time.sleep(10)
        self._process = None
        self.session_id = None
        self.log.info("Stop XCTestAgent successfully")
    
    def is_working(self):
        '''检查当前Agent是否在工作，如果Agent无法退到后台，重启手机
        
        :returns: boolean
        '''
        try:
            self._command_executor.set_timeout(1)
            response = self._execute(Command.HEALTH)
            self._command_executor.reset_timeout()
            return response['value'] == 'XCTestAgent is ready'
        except XCTestAgentDeadException:
            self.log.exception('XCTestAgentDead')
            # Agent无法退到后台，重启手机
            try:
                self.log.info('Reboot device %s' % self.udid)
                dt.DT().reboot(self.udid)
                for _ in range(20):
                    device = dt.DT().get_device_by_udid(self.udid)
                    if device is not None:
                        break
                else:
                    raise RuntimeError("after reboot, device disconnected!")
            except Exception:
                self.log.exception('device reboot error')
        
        except XCTestAgentTimeoutException:
            if self._relay_error:
                self.log.error("TcpRelay error:%s" % self._relay_error)
                self.stop()
    
        return False
    
    def has_session(self):
        '''检查是否存在会话
        
        :returns: boolean
        '''
        return self.session_id is not None
    
    def start_session(self, desired_capabilities, timeout=CommandTimeout):
        '''创建新会话
        
        :param desired_capabilities: 
         - bundleId - APP的bundle_id，例如：com.tencent.qq.dailybuild.test
         - app - APP路径，用于运行前安装APP.
        :type desired_capabilities: dict
        :param timeout: 检测启动app超时时间，启动超时则重启agent，单位：秒
        :type timeout: int
        :returns: 返回结果，dict
        '''
        while not self.is_working():
            self.start()
            
        while 1:
            time0 = time.time()
            response = self._execute(Command.SESSION, {
                'desiredCapabilities': desired_capabilities,
            })
            exec_time = int((time.time() - time0) * 1000) # 单位：毫秒
            if exec_time < (timeout*1000):
                break
            self.log.error('Restart XCTestAgent: [ %s ] consumed [ %dms ]' %('start app', exec_time))
            self.stop()
            self.start()
            
        self.session_id = response['sessionId']
        self.capabilities = response['value']['capabilities']
        return response
    
    def _execute(self, command, params={}):
        '''执行指令
        '''
        response = self._command_executor.execute(command, params)
        
        if response:
            if not command in self.LOG_FILTERED_METHODS:
                self.log.debug(response)
            # 检查返回结果
            try:
                self.error_handler.check_response(response)
            except ApplicationCrashedException:
                self.crash_flag = True
                raise
            return response
        # 如果服务器没有发送响应，认为指令执行成功
        return {'success': 0, 'value': None, 'sessionId': self.session_id}
    
    def capture_screen(self):
        try:
            return self.stub_client.execute(Command.SCREENSHOT, {})
        except XCTestAgentTimeoutException:
            return None    
    
    def execute(self, command, params={}, timeout=CommandTimeout):
        '''执行指令

        :param command: 指令名称
        :type command: str
        :param params: 指令参数集
        :type params: dict 例如 {bundleId: com.tencent.test}
        :param timeout: 指令执行超时等待时常
        :type timeout: int
        :returns: 返回结果，dict
        '''
        time0 = time.time()
        
        if not self.has_session():
            response = self._execute(Command.STATUS, {})
            self.session_id = response['sessionId']
        
        if self.has_session():
            if not params:
                params = {'sessionId': self.session_id}
            elif 'sessionId' not in params:
                params['sessionId'] = self.session_id
                
        if command == Command.START:
            if params is None:
                raise WebDriverException("Desired Capabilities can't be None")
            if not isinstance(params, dict):
                raise WebDriverException("Desired Capabilities must be a dictionary")
            response = self.start_session(params, timeout)
            
        elif command == Command.QUIT:
            if 'sessionId' in params:
                response = self._execute(command, params)
            else:
                response = {}
            self.session_id = None
            
        elif command == Command.STATUS:
            response = self._execute(command, params)
            if self.session_id is None:
                self.session_id = response['sessionId']
        else:
            response = self._execute(command, params)
            
        exec_time = int((time.time() - time0) * 1000)
        self.log.info('[ %s ] consumed [ %dms ]' %(command, exec_time))
        return response
        
    def get_crash_flag(self):
        '''获取app是否crash的标识
        
        :returns : boolean -- True if app crashed, False if not
        '''
        return self.crash_flag

    def get_driver_log(self):
        '''获取driver日志路径
        '''
        driver_log_path = None
        for h in self.log.handlers:
            attr_name = 'baseFilename'
            if hasattr(h, attr_name):
                driver_log_path = getattr(h, attr_name)
                break
        return driver_log_path
