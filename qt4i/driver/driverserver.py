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
'''QT4i Driver Server
'''

from __future__ import absolute_import, print_function

import argparse
import atexit
import os
import signal
import sys
import time
from six import string_types
    
from qt4i.driver.rpc import SimpleJSONRPCServer
from qt4i.driver.tools import logger as logging 
from qt4i.driver.util import Process

DEFAULT_IP = '0.0.0.0'
DEFAULT_PORT = 12306
DEFAULT_AGENT_PORT = 8100
DEFAULT_PID_FILE = '/tmp/driverserver.pid'

logger = logging.get_logger()

class ArgumentParser(argparse.ArgumentParser):
    '''Argument parser, automatically display help while error
    '''
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2) 
CMD_HELP = {
    "start": "start driver server daemon",
    "stop" :  "stop driver server daemon",
    "restart": "stop driver server daemon and start it again",
    "debug": "try to start driver server as a normal process for debug",
}

#参数解析器
main_parser = ArgumentParser(description='QT4i 3.0 driver program',
                                 formatter_class=argparse.RawDescriptionHelpFormatter )
main_parser.add_argument('--host', '-H', metavar='HOST', dest='host', default=DEFAULT_IP,
                         help='listening address of driver server, local address<%s> is used by default' % DEFAULT_IP)
main_parser.add_argument('--port', '-p', metavar='PORT', dest='port', default=DEFAULT_PORT,
                         help='listening port of driver server, port %s is used by default' % DEFAULT_PORT)
main_parser.add_argument('--type', '-t', metavar='TYPE', dest='driver_type', default="instruments",
                         help='driver type of driver server(instruments or xctest), "instruments" is used by default')
main_parser.add_argument('--pidfile', '-f', metavar='PIDFILE', dest='pidfile', default=DEFAULT_PID_FILE,
                         help='the path of pid file, %s is used by default' % DEFAULT_PID_FILE)
main_parser.add_argument('--udid', '-u', metavar='UDID', dest='udid', default=None,
                         help='udid of device')
main_parser.add_argument('--agent_port', '-a', metavar='AGENTPORT', dest='agent_port', default=DEFAULT_AGENT_PORT,
                         help='listening port of xctest agent, port %s is used by default' % DEFAULT_AGENT_PORT)
main_parser.add_argument('--web_port', '-w', metavar='WEBPORT', dest='web_port', default=None,
                         help='listening port of simulator for webview testing')
main_parser.add_argument('--register', '-r', dest='endpoint_clss', default=None,
                         help='the endpoint classes registered to driverserver, for example, "perflib.ios.fps.FPSMonitor,perflib.ios.leaks.LeaksMonitor"')
     
subparser_dict = {}
subparsers = main_parser.add_subparsers(title='List of Commands', metavar='COMMAND')
for command in CMD_HELP:
    subparser_dict[command] = subparsers.add_parser(command, help=CMD_HELP[command])
    subparser_dict[command].set_defaults(func=command)

subparser_dict['stop'].add_argument('--force', '-f', action='store_true', default=False, 
                                    help='force stop driver server')

class Daemon(object):
    """
    A generic daemon class.
    Usage: subclass the Daemon class and override the run() method
    """

    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile

    def daemonize(self):
        """
        do the UNIX double-fork magic, see Stevens' "Advanced 
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        # Do first fork
        self.fork()

        # Decouple from parent environment
        self.dettach_env()

        # Do second fork
        self.fork()

        # Flush standart file descriptors
        sys.stdout.flush()
        sys.stderr.flush()

        # 
        self.attach_stream('stdin', mode='r')
        self.attach_stream('stdout', mode='a+')
        self.attach_stream('stderr', mode='a+')
       
        # write pidfile
        self.create_pidfile()

    def attach_stream(self, name, mode):
        """
        Replaces the stream with new one
        """
        stream = open(getattr(self, name), mode)
        os.dup2(stream.fileno(), getattr(sys, name).fileno())

    def dettach_env(self):
        os.chdir("/")
        os.setsid()
        os.umask(0)

    def fork(self):
        """
        Spawn the child process
        """
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as e:
            sys.stderr.write("Fork failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

    def create_pidfile(self):
        atexit.register(self.delpid)
        pid = str(os.getpid())
        open(self.pidfile,'w+').write("%s\n" % pid)

    def delpid(self):
        """
        Removes the pidfile on process exit
        """
        os.remove(self.pidfile)

    def start(self, is_daemon = True):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        pid = self.get_pid()

        if pid:
            if Process().get_process_by_pid(pid, 'driverserver.py'):
                message = "pidfile %s already exist. Daemon already running?\n"
                logger.warning(message % self.pidfile)
                return
            else:
                os.remove(self.pidfile)

        # Start the daemon
        if is_daemon:
            self.daemonize()
        self.run()

    def get_pid(self):
        """
        Returns the PID from pidfile
        """
        try:
            pf = open(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except (IOError, TypeError):
            pid = None
        return pid

    def stop(self, silent=False):
        """
        Stop the daemon
        """
        # Get the pid from the pidfile
        pid = self.get_pid()

        if not pid:
            if not silent:
                message = "pidfile %s does not exist. Daemon not running?\n"
                logger.error(message % self.pidfile)
            return 

        # Try killing the daemon process    
        try:
            while True:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
        except OSError as err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                logger.error(str(err))
                sys.exit(1)

    def restart(self):
        """
        Restart the daemon
        """
        self.stop(silent=True)
        self.start()

    def run(self):
        """
        You should override this method when you subclass Daemon. It will be called after the process has been
        daemonized by start() or restart().
        """
        raise NotImplementedError

class DriverManager(Daemon):
    
    def __init__(self, pidfile, urls, address, port, udid, agent_port, web_port):
        '''构造（原则：Driver的配置只在此处配置）
        '''
        Daemon.__init__(self, pidfile)
        self._urls = urls
        self._driver_address = address
        self._driver_port = port
        self._driver_url = 'http://%s:%d' % (self._driver_address, self._driver_port)
        self._udid = udid
        self._agent_port = agent_port
        if isinstance(web_port, string_types):
            web_port = int(web_port)
        self._web_port = web_port
    
    @property
    def driver_url(self):
        return self._driver_url
    
    def start(self, is_daemon = True):
        '''启动driver
        '''
        # Check for a pidfile to see if the daemon already runs
        pid = self.get_pid()

        if pid:
            process = Process().get_process_by_pid(pid, 'driverserver.py')
            if process:
                args = process['CMD'].split(' ')
                if len(args) > 3:
                    args = main_parser.parse_args(args[2:])
                    logger.info('Driverserver info:%s' % args)
                    if int(args.agent_port) == self._agent_port and int(args.port) == self._driver_port:
                        return
                Process().kill_process_by_pid(pid)
                logger.warning('Kill old driver server process %d'  % pid)
                logger.warning('old_params: driver_port: %d, agent_port: %d' % (int(args.port), int(args.agent_port)))
                logger.warning('new_params: driver_port: %d, agent_port: %d' % (self._driver_port, self._agent_port))
            else:
                os.remove(self.pidfile)

        # Start the daemon
        if is_daemon:
            self.daemonize()
        self.run()
        
    def run(self):
        if self._udid:
            if self._web_port:
                # 单例类PortManager，设置WebInspector端口
                from qt4i.driver.tools.sched import PortManager
                PortManager.set_port(port_type='web', udid=self._udid, port=self._web_port, base=27753)
            # 单例类XCUITestAgentManager，启动XCUITestAgent
            from qt4i.driver.xctest.agent import XCUITestAgentManager
            agent_manager = XCUITestAgentManager()
            agent_manager.start_agent(device_id=self._udid, server_port=self._agent_port, retry=1)
        
        server = SimpleJSONRPCServer(urls=urls, addr=(self._driver_address, self._driver_port))
        logger.info('DriverServer(%s:%s) - started' % (self._driver_address, self._driver_port))
        server.serve_forever()
        
    def cleanup(self):
        '''清理环境
        device中的stop_all_agents接口需要udid，请使用host中的对应接口
        '''
        from qt4i.driver.rpc import RPCClientProxy
        if self._udid:
            driver = RPCClientProxy('%s/device/%s/' % (self._driver_url, str(self._udid)), allow_none=True, encoding='UTF-8')
            driver.device.stop_all_agents()
        else:
            host = RPCClientProxy('%s/host/' % (self._driver_url), allow_none=True, encoding='UTF-8')
            host.stop_all_agents()
    
    def stop(self, silent=False):
        '''停止driver
        '''
        try:
            self.cleanup()
        except:
            logger.exception('Stop Driver Server')
        Daemon.stop(self, silent)
    
def load(cls_name):
    '''加载对应的对象
    
    :param cls_name: 注册rpc类名，例如：perflib.ios.fps.FPSMonitor
    :type cls_name: string
    :returns - Type/ModuleType
    '''
    try:
        parts = cls_name.split('.')
        module = None
        parts_imp = parts[:]
        while parts_imp:
            try:
                modulename = '.'.join(parts_imp)
                __import__(modulename)   #__import__得到的是最外层模块的object
                module = sys.modules[modulename]
                break
            except ImportError:
                del parts_imp[-1]
            except:
                del parts_imp[-1]
                break
        if parts_imp == parts: #为一个包或模块
            raise RuntimeError(" %s 是一个包或模块，请注册一个类" %cls_name)
        elif parts_imp == parts[0:-1] and hasattr(module, parts[-1]): #为一个类
            endpoint_cls = getattr(module, parts[-1]) 
            return endpoint_cls
        else: #触发异常
            if parts_imp:
                modulename = '.'.join(parts_imp)
                modulename += '.'
            else:
                modulename = ''
            modulename += parts[len(parts_imp)]
            __import__(modulename)
    except:
        logger.exception('load %s' %cls_name)
        raise

if __name__ == '__main__':
    args = main_parser.parse_args()
    urls = []
    if args.driver_type == 'instruments':
        from qt4i.driver.instruments.uia import Device, Application, Element #@UnusedImport
        from qt4i.driver.instruments.ins import InstrumentsCallBacker 
        urls = [
            ("^device/(?P<device_id>[\w\-]+)/$", "^ins\..*", InstrumentsCallBacker)
        ]
    else:
        from qt4i.driver.xctest.wda import Device, Application, Element 
    
    from qt4i.driver.host import RPCServerHost
    from qt4i.driver.web.web import WebInspector
    urls.extend([("^host/$", None, RPCServerHost),
            ("^device/(?P<device_id>[\w\-]+)/$", "^web\..*", WebInspector),
            ("^device/(?P<device_id>[\w\-]+)/$", "^device\..*", Device),
            ("^device/(?P<device_id>[\w\-]+)/$", "^app\..*", Application),
            ("^device/(?P<device_id>[\w\-]+)/$", "^element\..*", Element),])
    
    if args.endpoint_clss:
        endpoint_clss = args.endpoint_clss.split(",")
        for cls in endpoint_clss:
            if cls:
                endpoint_cls = load(cls)
                cls_name = endpoint_cls.__name__
                urls.append(("^device/(?P<device_id>[\w\-]+)/$", "^%s\..*" % cls_name.lower(), endpoint_cls))

    dm = DriverManager(args.pidfile, urls, args.host, int(args.port), args.udid, int(args.agent_port), args.web_port)
    if args.func == 'start':
        dm.start()
          
    elif args.func == 'stop':
        dm.stop()
          
    elif args.func == 'restart':
        dm.restart()
              
    elif args.func == 'debug':
        dm.start(False)
          
    else:
        main_parser.print_help()
        sys.exit(1)
