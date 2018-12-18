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
'''QT4i命令
'''

from __future__ import absolute_import, print_function

import argparse
import os
import logging
import shutil
import sys
import zipfile

from testbase.management import Command
from testbase.management import ArgumentParser
from qt4i.device import DeviceServer
from qt4i.util import less_to
from qt4i.driver.util import zip_decompress
from qt4i.version import version as qt4i_version

DEFAULT_IP = '0.0.0.0'
DEFAULT_PORT = 12306
DEFAULT_AGENT_PORT = 8100
DEFAULT_PID_FILE = '/tmp/driverserver.pid'


class StartDriver(Command):
    '''启动Driver
    '''
    name = 'restartdriver'
    parser = argparse.ArgumentParser("restart local QT4i driver daemon")
    parser.add_argument('--host', '-H', metavar='HOST', dest='host', default=DEFAULT_IP,
                         help='listening address of driver server, local address<%s> is used by default' % DEFAULT_IP)
    parser.add_argument('--port', '-p', metavar='PORT', dest='port', default=DEFAULT_PORT,
                         help='listening port of driver server, port %s is used by default' % DEFAULT_PORT)
    parser.add_argument('--type', '-t', metavar='TYPE', dest='driver_type', default="xctest",
                         help='driver type of driver server(instruments or xctest), "xctest" is used by default')
    parser.add_argument('--pidfile', '-f', metavar='PIDFILE', dest='pidfile', default=DEFAULT_PID_FILE,
                         help='the path of pid file, %s is used by default' % DEFAULT_PID_FILE)
    parser.add_argument('--udid', '-u', metavar='UDID', dest='udid', default=None,
                         help='udid of device')
    parser.add_argument('--agent_port', '-a', metavar='AGENTPORT', dest='agent_port', default=DEFAULT_AGENT_PORT,
                         help='listening port of xctest agent, port %s is used by default' % DEFAULT_AGENT_PORT)
    parser.add_argument('--register', '-r', dest='endpoint_clss', default='',
                         help='the endpoint classes registered to driverserver, for example, "register.demo.Demo,perflib.ios.fps.FPSMonitor"')

    def execute(self, args):
        '''执行过程
        '''
        DeviceServer(args.host, int(args.port), args.udid, int(args.agent_port), args.driver_type, args.endpoint_clss).restart()


class Installer(Command):
    '''安装命令
    '''
    name = 'install'
    parser = argparse.ArgumentParser("install app")
    parser.add_argument("product_path", help="product file path")
    parser.add_argument('-u', default=None, help="device udid", dest="device_udid")

    def execute(self, args):
        '''执行过程
        '''
        from qt4i.driver.tools.dt import DT
        DT().install(args.product_path, args.device_udid)


class Uninstaller(Command):
    '''卸载命令
    '''
    name = 'uninstall'
    parser = argparse.ArgumentParser("uninstall app")
    parser.add_argument("bundle_id", help="app bundle id")
    parser.add_argument('-u', default=None, help="device udid", dest="device_udid")

    def execute(self, args):
        '''执行过程
        '''
        from qt4i.driver.tools.dt import DT
        DT().uninstall(args.bundle_id, args.device_udid)


class DeviceList(Command):
    '''获取当前Mac机上的所有可用设备列表(含真机与模拟器，并产生缓存)
    '''
    name = 'listdevices'
    parser = argparse.ArgumentParser("list devices")

    def execute(self, args):
        '''执行过程
        '''
        from qt4i.driver.tools.dt import DT
        import pprint
        
        for device in DT().get_devices():
            pprint.pprint(device)

            
class Setup(Command):
    '''安装XCTestAgent
    '''
    name = 'setup'
    parser = argparse.ArgumentParser("setup XCTest Agent")

    def execute(self, args):
        '''执行过程
        '''
        egg_file = os.path.join(os.path.dirname(os.path.dirname(__file__)))
        agent_src_path = ""
        if zipfile.is_zipfile(egg_file):
            zip_decompress(egg_file, '/tmp')
            agent_src_path = '/tmp/qt4i/driver/xctest/xctestproj/XCTestAgent'
        else:
            qt4i_path = os.path.dirname(__file__)
            agent_src_path = os.path.join(qt4i_path, 'driver/xctest/xctestproj/XCTestAgent')

        proj_dir = os.path.join(os.path.expanduser('~'), 'XCTestAgent')
        if os.path.exists(proj_dir):
            shutil.rmtree(proj_dir)
        shutil.copytree(agent_src_path, proj_dir)

        proj_path = os.path.join(proj_dir, 'XCTestAgent.xcodeproj')
        os.popen('open %s' % proj_path)

        with open(os.path.join(proj_dir, 'version.txt'), 'w') as f:
            f.write(qt4i_version)

        if os.path.exists('/tmp/qt4i'):
            shutil.rmtree('/tmp/qt4i')


class Update(Command):
    '''更新XCTestAgent
    '''
    name = 'update'
    parser = argparse.ArgumentParser("update XCTest Agent")

    def execute(self, args):
        '''执行过程
        '''
        egg_file = os.path.join(os.path.dirname(os.path.dirname(__file__)))
        proj_dir = os.path.join(os.path.expanduser('~'), 'XCTestAgent')
        is_updated = False
        if zipfile.is_zipfile(egg_file):
            zip_decompress(egg_file, '/tmp')
            agent_src_path = '/tmp/qt4i/driver/xctest/xctestproj/XCTestAgent'
        else:
            qt4i_path = os.path.dirname(__file__)
            agent_src_path = os.path.join(qt4i_path, 'driver/xctest/xctestproj/XCTestAgent')
        if os.path.exists(proj_dir):
            with open(os.path.join(proj_dir, 'version.txt'), 'r') as f:
                version = f.read()
            if not less_to(version, qt4i_version):
                return
            else:
                lib_dir = os.path.join(proj_dir, 'third')
                shutil.rmtree(lib_dir)
                lib_src_path = os.path.join(agent_src_path, 'third')
                shutil.copytree(lib_src_path, lib_dir)
                is_updated = True
        else:
            shutil.copytree(agent_src_path, proj_dir)
            proj_path = os.path.join(proj_dir, 'XCTestAgent.xcodeproj')
            os.popen('open %s' % proj_path)
            is_updated = True

        if is_updated:
            with open(os.path.join(proj_dir, 'version.txt'), 'w') as f:
                f.write(qt4i_version)

            if os.path.exists('/tmp/qt4i'):
                shutil.rmtree('/tmp/qt4i')


class RebootDevice(Command):
    '''重启手机
    '''
    name = 'reboot'
    parser = argparse.ArgumentParser("reboot device")
    parser.add_argument('-u', default=None, help="device udid", dest="device_udid")

    def execute(self, args):
        '''执行过程
        '''
        from qt4i.driver.tools.dt import DT
        DT().reboot(args.device_udid)


class ListAppsOnDevice(Command):
    '''获取手机上的app列表
    '''

    name = 'listapps'
    parser = argparse.ArgumentParser("List applications of the specified device")
    parser.add_argument('-u', default=None, help="device udid", dest="device_udid")
    parser.add_argument('-t', default='user', help="app type(user/system/all)", dest="app_type")

    def execute(self, args):
        '''执行过程
        '''
        from qt4i.driver.tools.dt import DT
        import pprint
        pprint.pprint(DT().list_apps(args.device_udid, args.app_type))


class UpdateFbsimctl(Command):
    '''更新fbsimctl
    '''

    name = 'updatefbsimctl'
    parser = argparse.ArgumentParser("Update fbsimctl tool in /cores/fbsimctl")

    def execute(self, args):
        '''执行过程
        '''
        fbsimctl_path = '/cores/fbsimctl'
        if os.path.exists(fbsimctl_path):
            shutil.rmtree(fbsimctl_path)


def qt4i_manage_main():
    logging.root.addHandler(logging.StreamHandler())
    logging.root.level = logging.INFO
    cmds = [StartDriver, Installer, Uninstaller, DeviceList, Setup, Update, \
        RebootDevice, ListAppsOnDevice, UpdateFbsimctl]
    argparser = ArgumentParser(cmds)
    subcmd, args = argparser.parse_args(sys.argv[1:])
    subcmd.execute(args)
