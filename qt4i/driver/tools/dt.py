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
'''DeviceTools
'''

from __future__ import absolute_import, print_function

import fcntl 
import json
import os
import pkg_resources
import re
import subprocess
import shutil
import time
import datetime
import base64
from six.moves.http_client import HTTPConnection
from six import PY3
from six import with_metaclass
import six

from qt4i.driver.tools import mobiledevice
from qt4i.driver.tools.mobiledevice import InstallationProxy
from qt4i.driver.tools.sched import PortManager
from qt4i.driver.util import zip_decompress
from qt4i.driver.tools.mobiledevice import SandboxClient
from testbase.util import Singleton
from testbase.util import Timeout


# 挂载根路径
MOUNT_ROOT_PATH = os.path.expanduser('~')
TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

class Flock(object):
    
    def __init__(self, filepath='/cores/lock'):
        self._filepath = filepath
        self._fd = open(self._filepath, 'w')

    def __enter__(self):
        fcntl.flock(self._fd, fcntl.LOCK_EX)
        with open('/cores/pid','w+') as fd:
            fd.write("%s\n" % str(os.getpid()))
        return self

    def __exit__(self, *args):
        fcntl.flock(self._fd, fcntl.LOCK_UN)
        try:  
            self._fd.close()  
            os.unlink(self._filepath)
        except:  
            pass
        self._fd = None 
    
    
def func_retry_wrap(func):
    def _wrap_func(*args, **kwargs):
        '''
        '''
        for _ in range(3):
            try:
                return func(*args, **kwargs)
            except:
                time.sleep(10)
        else:
            raise
    return _wrap_func

class DT(with_metaclass(Singleton, object)):
    '''
    DeviceTools
    '''
    
    FBSIMCTL_DEFAULT_PATH = '/cores/fbsimctl/fbsimctl'
    
    def __init__(self):
        self.xcode_version = DT.get_xcode_version()
        self.udid = None
        self.bundle_id = None
        self.sc = None
        self._init_fbsimctl()
    
    def _init_fbsimctl(self):
        try:
            fbsimctl_zip = pkg_resources.resource_filename("qt4i", "driver/tools/fbsimctl/fbsimctl.zip") #@UndefinedVariable
            if not os.path.exists(fbsimctl_zip):
                raise Exception('fbsimctl not found')
            self.fbsimctl = DT.FBSIMCTL_DEFAULT_PATH
        except:
            try:
                os.environ['PATH'] += ':/usr/local/bin'
                result = subprocess.check_output("which fbsimctl", env=os.environ, shell=True, stderr=subprocess.STDOUT, )
                if PY3:
                    result = result.decode()
                self.fbsimctl = result.split('\n')[0]
            except subprocess.CalledProcessError: 
                raise Exception('fbsimctl not found, use brew install')
        if self.fbsimctl == DT.FBSIMCTL_DEFAULT_PATH and not os.path.exists(self.fbsimctl): # 解压fbsimctl到默认路径
            fbsimctl_root_path = os.path.split(DT.FBSIMCTL_DEFAULT_PATH)[0]
            zip_decompress(fbsimctl_zip, fbsimctl_root_path)
            os.chmod(self.fbsimctl, 0o755)
            fbsimctl_fmk_path = os.path.split(DT.FBSIMCTL_DEFAULT_PATH)[0]
            for root, dirs, _files in os.walk(fbsimctl_fmk_path):
                if root.endswith('.framework'):
                    if 'Headers' not in dirs: # 为Framework添加Headers/Modules/Resources的外链
                        framework_name = os.path.splitext(os.path.basename(root))[0]
                        for item in ['Headers', 'Modules', 'Resources', framework_name]:
                            item_path = os.path.join(root, item)
                            if os.path.exists(item_path) and not os.path.islink(item_path):
                                os.remove(item_path)
                            os.symlink('Versions/Current/%s' % item, item_path)
                if root.endswith('Versions'):
                    if 'Current' not in dirs:
                        current_path = os.path.join(root, 'Current')
                        if os.path.exists(current_path) and not os.path.islink(current_path):
                            os.remove(current_path)
                        os.symlink('A', current_path)

    @staticmethod
    def get_xcode_version():
        '''查询Xcode版本
        
        :returns: str
        '''
        version = "7.3"
        try:
            xcode_info = subprocess.check_output("xcodebuild -version", shell=True, stderr=subprocess.STDOUT)
            if PY3:
                xcode_info = xcode_info.decode()
            version = re.match(r'Xcode\s(\d+\.\d+)', xcode_info.split('\n')[0]).group(1)
        except subprocess.CalledProcessError as e:
            raise Exception('get_xcode_version error:%s' % e.output)
        return version 

    @staticmethod
    def compare_xcode_version(version):
        '''比较当前Mac上的Xcode版本和指定version的大小
        
        当前版本 > version return 1
        当前版本 = version return 0
        当前版本 < version return -1
        '''
        current_version = DT.get_xcode_version()
        return DT.compare_version(current_version, version)

    @staticmethod
    def compare_version(version_a, version_b):
        '''
        version_a > version_b return 1
        version_a = version_b return 0
        version_a < version_b return -1
        '''
        version_reg = r'^\d*\.\d*\.?\d*$'
        if not re.match(version_reg, version_a):
            raise Exception('version_a invalid:%s' % version_a)
        elif not re.match(version_reg, version_b):
            raise Exception('version_b invalid:%s' % version_b)
        a = version_a.split('.')
        b = version_b.split('.')
        length = min(len(a), len(b))
        for i in range(length):
            if int(a[i]) < int(b[i]):
                return -1
            if int(a[i]) > int(b[i]):
                return 1
        if len(a) > len(b):
            return 1
        elif len(a) < len(b):
            return -1
        else:
            return 0

    def get_real_devices(self):
        '''查询当前Mac机上已连接的真机设备（仅含真机，不含模拟器）
        
        :returns: list[dict] or None（意外情况）
        '''
        devices = self.get_devices()
        real_devices = []
        for dev in devices:
            if not dev['simulator']:
                real_devices.append(dev)
        return real_devices
    
    def _get_simulators_below_xcode_7(self):
        devices = []
        try:
            cmd = "xcrun simctl list devices"
            result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            if PY3:
                result = result.decode()            
            dev_flag = False
            for line in result.split("\n"):
                if line.startswith("-- "):
                    if line.startswith("-- iOS"):
                        dev_flag = True
                        dev_version = re.match(r'--\siOS\s(\d+\.\d)\s--', line).group(1)
                    else:
                        dev_flag = False
                    continue
                if dev_flag:
                    ret = re.match(r'\s{4}(.+)\s\(([0-9A-F\-]+)\)\s\((.+)\)', line)
                    if ret:
                        device = {}
                        device["udid"] = ret.group(2)
                        device["name"] = ret.group(1)
                        device["ios"] = dev_version
                        device["state"] = ret.group(3)
                        device["simulator"] = True
                        devices.append(device)
        except subprocess.CalledProcessError as e:
            raise Exception('_get_simulators_below_xcode_7 error:%s' % e.output)
        return devices
    
    def _get_simulators_above_xcode_7(self):
        devices = []
        try:
            cmd = "xcrun simctl list -j devices"   
            result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            if PY3:
                result = result.decode()            
            json_devices = json.loads(result, encoding='utf-8')["devices"]
            for k in json_devices:
                if k.startswith("iOS"):
                    ios_version = re.match(r'iOS\s(\d+\.\d+)', k).group(1)
                    for dev in json_devices[k]:
                        dev["ios"] = ios_version
                        dev["simulator"] = True
                        devices.append(dev)
        except subprocess.CalledProcessError as e:
            raise Exception('_get_simulators_above_xcode_7 error:%s' % e.output)
        return devices          
    
    def get_simulators(self):
        '''查询已安装的模拟器(如果没必要查询真机，仅查模拟器的性能更佳)
        
        :returns: list[dict] or None（意外情况）
        '''
        if self.xcode_version < "7.0":
            return self._get_simulators_below_xcode_7()
        else:
            return self._get_simulators_above_xcode_7()
    
    def _list_devices(self):
        '''获取设备列表进程
        '''
        self._list_devices_process = subprocess.Popen("instruments -s devices", 
                                                      shell=True, 
                                                      stdout=subprocess.PIPE, 
                                                      stderr=subprocess.PIPE, 
                                                      close_fds=True)
        self._dev_info, _ = self._list_devices_process.communicate()
    
    def get_devices(self):
        '''查询当前Mac机上的所有可用设备(含真机与模拟器，并产生缓存)
        
        :returns: list[dict]
        '''
        return self._get_device_by_fbsimctl()
    
    def get_device_by_name(self, _name):
        '''通过设备名查询当前Mac机上的可用设备(含真机与模拟器)
        
        :param _name: 设备名(支持正则表达式)，例如：iPhone 5s (8.1 Simulator)
        :type _name: str
        :returns: dict or None
        '''
        _devices = self.get_devices()
        for _item in _devices:
            if _name == _item["name"] or re.match(_name, _item["name"]):
                return _item
    
    def get_device_by_udid(self, _device_udid):
        '''通过设备的udid查询当前Mac机上的设备(含真机与模拟器)
        
        :param _device_udid: 设备的udid
        :type _device_udid: str
        :returns: dict or None
        '''
        _devices = self.get_devices()
        for _item in _devices:
            if _device_udid == _item["udid"]:
                return _item
    
    def is_simulator(self, udid):
        '''判断是否是模拟器
        '''
        device = self.get_device_by_udid(udid)
        if device:
            return device['simulator']
        return False
    
    def check_device_udid_is_valid(self, _device_udid):
        '''检测udid是否有效（含真机与模拟器）
        
        :param _device_udid: 真机或模拟器的udid
        :type _device_udid: str
        :returns: bool
        '''
        device = self.get_device_by_udid(_device_udid)
        return bool(device)
    
    def get_simulator_by_name(self, _name):
        '''通过模拟器名查询模拟器(如果没必要查询真机，仅查模拟器的性能极佳)
        
        :param _name: 模拟器名(支持正则表达式)，例如：iPhone 5s (8.1 Simulator)
        :type _name: str
        :returns: dict or None
        '''
        _simulators = self.get_simulators()
        if _simulators:
            for _item in _simulators:
                if _name == _item["name"] or re.match(_name, _item["name"]):
                    return _item
    
    def get_simulator_by_udid(self, _device_udid):
        '''通过模拟器udid查询模拟器(如果没必要查询真机，仅查模拟器的性能极佳)
        
        :param _device_udid: 模拟器的udid
        :type _device_udid: str
        :returns: dict or None
        '''
        _simulators = self.get_simulators()
        if _simulators:
            for _item in _simulators:
                if _device_udid == _item["udid"]:
                    return _item
    
    def get_default_simulator(self):
        '''查询默认的模拟器(由于模拟器只能有一个实例，所以有默认模拟器。真机不存在默认真机的情况)
        
        :returns: dict or None（意外情况）
        '''
        raise Exception("get_default_simulator unsupported")
    
    def set_default_simulator(self, _device_udid):
        '''设置默认模拟器
        
        :param _device_udid: 模拟器的udid
        :type _device_udid: str
        :returns: bool
        '''
        raise Exception("set_default_simulator unsupported")
    
    def app_info(self, _file_path):
        '''获取APP安装包的信息(IPA或APP均可)
        
        :param _file_path: IPA或APP安装包的路径(注意：当前Mac机必须能访问到该路径)
        :type _file_path: str
        :returns: dict or None
        '''
        raise Exception("app_info unsupported")
    
    def _modify_wi_port(self, udid):
        port = PortManager.get_port('web', udid)
        if self.xcode_version.startswith('9'):
            wi_plist_path = '/Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/Library/CoreSimulator/Profiles/Runtimes/iOS.simruntime/Contents/Resources/RuntimeRoot/System/Library/LaunchDaemons/com.apple.webinspectord.plist'
        else: 
            wi_plist_path = '/Applications/Xcode.app/Contents/Developer/Platforms/iPhoneSimulator.platform/Developer/SDKs/iPhoneSimulator.sdk/System/Library/LaunchDaemons/com.apple.webinspectord.plist'
        cmd = ['/usr/libexec/PlistBuddy', '-c', 'Set :Sockets:com.apple.webinspectord.socket:SockServiceName %s' % port, wi_plist_path]
        subprocess.call(cmd)
    
    def start_simulator(self, udid=None):
        #检查模拟器是否启动成功
        def check_started():
            for s in self.get_simulators():
                if s["state"] == "Booted" and (s["udid"] == udid or udid is None):
                    return True
            return False
        
        if check_started():
            return  True
        simulator = "Simulator"
        if self.compare_xcode_version("7.0") < 0:
            simulator = "iOS Simulator"
        if udid:
            cmd = [self.fbsimctl, udid, 'boot']
            if self.compare_xcode_version("9.0") >= 0:
                cmd = ['xcrun', 'simctl', 'boot', udid]
        else:
            cmd = "open -a \"%s\"" % simulator
        
        if self.compare_xcode_version("9.3") >=0:
            ret = subprocess.call(cmd, close_fds=True)
            if ret != 0:
                result = False
            else:
                result = Timeout(20, 0.05).check(check_started, True)
        else:
            with Flock():
                self._modify_wi_port(udid) 
                ret = subprocess.call(cmd, close_fds=True)
                if ret != 0:
                    result = False
                else:
                    result = Timeout(20, 0.05).check(check_started, True)
        return result
    
    @func_retry_wrap
    def _download_http_file(self, url, target_path):
        '''下载http文件 
        :param url: HTTP路径
        :type url: string
        :param target_path: 下载到目标路径
        :type target_path: string
        '''
        url0 = url
        if url[:7] == 'http://':
            url = url[7:]
        pos = url.find('/')
        host = url[:pos]
        page = url[pos:]
        conn = HTTPConnection(host, port=80, timeout=60)  # 60秒超时
        conn.request('GET', page)
        res = conn.getresponse()
        if res.status != 200: 
            raise RuntimeError('访问：%s 错误[HTTP错误码：%s]' % (url0, res.status))
        target_size = int(res.getheader('Content-Length'))
        data = res.read()
        conn.close()
        if len(data) != target_size:
            return self._download_http_file(url0, target_path)
        else:
            f = open(target_path, 'wb')
            f.write(data)
            f.close()
            
    def _download_package(self, src, dstdir):
        '''下载安装包
        
        :param src: 源路径
        :param dstdir: 本地目录
        :returns: filepath - 安装包路径
        '''
        http_prefix = u'http://'
        https_prefix = u'https://'
        
        if src.startswith(http_prefix) or src.startswith(https_prefix):
            '''源路径是http或https服务器路径
            '''
            filename = src[src.rfind('/')+1:]
            filepath = os.path.join(dstdir, filename)
            self._download_http_file(src, filepath)
        
        elif os.path.isfile(src):
            '''源路径是本地路径
            '''
            filepath = src
        
        else:
            raise RuntimeError("file path not supported, %s" % src.encode('utf8'))
        
        return filepath
            
    def _extract_tgz(self, filepath, dstpath):
        '''解压tgz包
        
        :param filepath: tgz包路径
        :type filepath: string
        :param dstpath: 解压后路径
        :type dstpath: string
        '''
        items = os.listdir(dstpath)
        #首先删除目录中已有的app文件，防止版本冲突
        for it in items:
            if it.endswith('.app'):
                shutil.rmtree(os.path.join(dstpath, it))
        zip_decompress(filepath, dstpath)
        items = os.listdir(dstpath)
        for it in items:
            if it.endswith('.app'):
                return os.path.join(dstpath, it)
    
    def _extract_zip(self, filepath, dstpath):
        '''解压zip包
        
        :param filepath: zip包路径
        :type filepath: string
        :param dstpath: 解压后路径
        :type dstpath: string
        '''
        items = os.listdir(dstpath)
        #首先删除目录中已有的app文件，防止版本冲突
        for it in items:
            if it.endswith('.app'):
                shutil.rmtree(os.path.join(dstpath, it))
        zip_decompress(filepath, dstpath)
        items = os.listdir(dstpath)
        for it in items:
            if it.endswith('.app'):
                return os.path.join(dstpath, it)
        
    def _prepare_package(self, _file_path, pkgcachedir):
        '''准备安装包
        
        :param _file_path: 安装包路径
        :type _file_path: string
        :param pkgcachedir: 包缓存目录
        :type pkgcachedir: string
        :returns: str - 安装包本地路径
        '''
        
        if not os.path.isdir(pkgcachedir):
            os.mkdir(pkgcachedir)
        
        if not isinstance(_file_path, six.text_type):
            try:
                _file_path = _file_path.decode('utf8')
            except:
                _file_path = _file_path.decode('gbk')
        
        filepath = self._download_package(_file_path, pkgcachedir)
        if filepath.endswith('.ipa'):
            return filepath
        elif filepath.endswith('.tar.gz'):
            return self._extract_tgz(filepath, pkgcachedir)
        elif filepath.endswith('.zip'):
            return self._extract_zip(filepath, pkgcachedir)
        else:
            raise RuntimeError('unknown type of package: %s' % _file_path.encode('utf8'))

    def _install_for_simulator(self, udid, app_path):
        try:
            cmd = "xcrun simctl install %s %s" % (udid, app_path)
            subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            return (True, "")
        except subprocess.CalledProcessError as e:
            return (False, e.output)

    def install(self, _file_path, _device_udid=None):
        '''通过udid指定真机安装IPA或模拟器安装APP(注意：真机所用IPA不能在模拟器上安装和使用，IPA与APP相互不兼容)
        
        :param _file_path: IPA或APP安装包的路径(注意：当前Mac机必须能访问到该路径)
        :type _file_path: str
        :param _device_udid: 设备的udid(当udid为None时，IPA包则安装到第一台连接上的真机上，APP包则安装到默认模拟器上)
        :type _device_udid: str
        :returns: bool
        '''
        self.install_error = ""
        from qt4i.driver.tools import logger
        log = logger.get_logger("task")
        
        if not _file_path:
            return True
        
        pkgcachedir = os.path.join(os.environ['HOME'],'pkg_cache')
        if not os.path.isdir(pkgcachedir):
            os.mkdir(pkgcachedir)
        pkgcachedir = os.path.join(pkgcachedir, str(_device_udid))
        file_path = self._prepare_package(_file_path, pkgcachedir)
        if os.path.exists(file_path) == False :
            self.install_error = 'file does not exist'
            return False
        if file_path.endswith("ipa"):
            if self.is_simulator(_device_udid):
                log.warn('Failed to install an ipa to a simulator.')
                return False
            ip = InstallationProxy(_device_udid)
            ret = ip.install(file_path)
            
        else:
            if not self.is_simulator(_device_udid):
                log.warn('Failed to install an app to a real device.')
                return False
            self.start_simulator(_device_udid)
            if _device_udid is None:
                _device_udid = "booted"
            ret = self._install_for_simulator(_device_udid, file_path)
        
        if ret[0]:
            if os.path.exists(pkgcachedir):
                shutil.rmtree(pkgcachedir)
        else:
            log.debug('install error: %s' % str(ret[1]))
        
        self.install_error = ret[1]
        return ret[0]
        
    def _uninstall_for_simulator(self, udid, bundle_id):
        try:
            cmd = "xcrun simctl uninstall %s %s" % (udid, bundle_id)
            subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            return (True, "")
        except subprocess.CalledProcessError as e:
            return (False, e.output)
    
    def uninstall(self, _bundle_id, _device_udid=None):
        '''通过udid指定设备卸载指定bundle_id的APP
        
        :param _bundle_id: APP的bundle_id，例如：com.tencent.qq.dailybuild.test
        :type _bundle_id: str
        :param _device_udid: 设备的udid(当udid为None时，如果有真机连接，则卸载第一台连接上的真机内的APP，如果无真机连接，则卸载默认模拟器上的APP)
        :type _device_udid: str
        :returns: bool
        '''
        self.uninstall_error = ""
        simulator_flag = False
        if _device_udid:
            for device in self.get_devices():
                if _device_udid == device["udid"]:
                    simulator_flag = device["simulator"]
                    break
        else:
            devices = self.get_real_devices()
            if len(devices) > 0:
                _device_udid = devices[0]["udid"]
            else:
                devices = self.get_simulators()
                if len(devices) > 0:
                    _device_udid = devices[0]["udid"]
                    simulator_flag = True            

        if _device_udid is None:
            return False
        if simulator_flag:
            self.start_simulator(_device_udid)
            ret = self._uninstall_for_simulator(_device_udid, _bundle_id)
        else:
            ip = InstallationProxy(_device_udid)
            ret = ip.uninstall(_bundle_id)
        
        self.uninstall_error = ret[1]
        return ret[0] 
    
    def _shutdown_simulator(self, udid):
        cmd = [self.fbsimctl, udid, 'shutdown']
        return True if subprocess.call(cmd, close_fds=True) == 0 else False
    
    def reboot(self, udid):
        if self.is_simulator(udid):
            self._shutdown_simulator(udid)
            self.start_simulator(udid)
        else:
            mobiledevice.reboot(udid)

    def get_crash_log(self, udid, procname):
        '''获取指定进程的最新的crash日志
        
        :param udid: 设备的udid
        :type udid: str  
        :param procname: app的进程名，可通过xcode查看
        :type procname: str 
        :return: string or None - crash内容
        '''
        log = None
        if self.is_simulator(udid):
            root_path = os.path.join(os.path.expanduser('~'), 'Library/Logs/DiagnosticReports')
            for crash_log in os.listdir(root_path):
                if crash_log.startswith(procname) and crash_log.endswith('crash'):
                    crash_log_path = os.path.join(root_path, crash_log)
                    with open(crash_log_path, "rb") as fd:
                        log = fd.read().decode("utf-8")
                    if udid in log:
                        os.remove(crash_log_path)
                        return log
                    else:
                        log = None
        else:
            logfile = mobiledevice.get_crash_log(procname, udid)
            if logfile and os.path.isfile(logfile):
                with open(logfile, "rb") as fd:
                    log = fd.read().decode("utf-8")
        return log
    
    def _convert_timestamp(self, format_time):
        parsed_time = time.strptime(format_time, "%b %d %H:%M:%S %Y")
        return time.mktime(parsed_time)
    def _get_simulator_app_data_path(self, udid, bundle_id):
        try:  #先尝试simctl命令获取sandbox路径,如果失败再尝试分析系统安装日志获取路径
            cmd = "xcrun simctl get_app_container %s %s data" % (udid, bundle_id)
            app_path = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, close_fds=True)
            if PY3:
                app_path = app_path.decode()            
            return app_path[:-1]
        except subprocess.CalledProcessError:
            pass
        install_log_path = os.path.join(os.path.expanduser('~'), 'Library/Logs/CoreSimulator/%s/MobileInstallation' % udid)
        apps_path = os.path.join(os.path.expanduser('~'), 'Library/Developer/CoreSimulator/Devices/%s/data/Containers/Data/Application' % udid)
        app_path = None
        timestamp = 0
        for logfile in os.listdir(install_log_path):
            if logfile.startswith('mobile_installation.log'):
                with open(os.path.join(install_log_path, logfile), "rb") as fd:
                    for line in fd:
                        if 'Made container live for %s at %s' % (bundle_id, apps_path) in line :
                            line_timestamp = self._convert_timestamp(line[4:24])
                            if line_timestamp > timestamp:
                                app_path = line
                                timestamp = line_timestamp
                        elif 'Data container for %s is now at %s' % (bundle_id, apps_path) in line:
                            line_timestamp = self._convert_timestamp(line[4:24])
                            if line_timestamp > timestamp:
                                app_path = line
                                timestamp = line_timestamp
        return app_path[app_path.find(apps_path):-1]
    
    def push_file(self, udid, bundle_id, localpath, remotepath):
        '''拷贝Mac本地文件到iOS设备sandbox的指定目录中
        
        :param udid: 设备的udid,如果不传入udid，则表示向手机的系统目录传入文件
        :type udid: str 
        :param bundle_id: app的bundle id
        :type bundle_id: str   
        :param localpath: Mac上的文件路径
        :type localpath: str
        :param remotepath: sandbox上的目录，例如：/Library/Caches/test/
        :type remotepath: str
        :returns: boolean
        '''
        if bundle_id:
            if self.is_simulator(udid):
                sandbox_root = self._get_simulator_app_data_path(udid, bundle_id)
                remotepath = remotepath[1:] if remotepath.startswith('/') else remotepath
                remote_file = os.path.join(sandbox_root, remotepath)
                shutil.copy(localpath, remote_file)
                return True
            else:
                return mobiledevice.push_file(bundle_id, localpath, remotepath, udid)
        else:
            if self.is_simulator(udid):
                cmd = 'xcrun simctl addmedia %s %s' % (udid, localpath)
                process = subprocess.Popen(cmd, shell=True, stderr=subprocess.STDOUT)
                
                process.communicate()
                return process.poll() == 0
            else:
                raise Exception("This operation is not supported by the device")
 
    def pull_file(self, udid, bundle_id, remotepath, localpath='/tmp', is_dir=False, is_delete = True):
        '''拷贝手机中sandbox指定目录的文件到Mac本地
        
        :param udid: 设备的udid
        :type udid: str 
        :param bundle_id: app的bundle id
        :type bundle_id: str   
        :param remotepath: sandbox上的目录或者文件，例如：/Library/Caches/test/
        :type remotepath: str        
        :param localpath: 本地的目录
        :type localpath: str
        :param is_dir: remotepath是否为目录，默认为单个文件
        :type is_dir: bool
        :param is_delete: 是否删除
        :type is_delete: bool
        :returns: list or None
        '''
        if self.is_simulator(udid):
            local_files = []
            sandbox_root = self._get_simulator_app_data_path(udid, bundle_id)
            remotepath = remotepath[1:] if remotepath.startswith('/') else remotepath
            remote_file = os.path.join(sandbox_root, remotepath)
            if is_dir:
                for root, _, files in os.walk(remote_file):
                    for f in files:
                        if udid:
                            (short_name, extension) = os.path.splitext(f)
                            new_f = '%s-%s%s' % (short_name, udid, extension)
                        filename = os.path.join(root, f)
                        local_file = os.path.join(localpath, new_f)
                        shutil.copy(filename, local_file)
                        local_files.append(local_file)
                        if is_delete:
                            os.remove(filename)
            else:
                if udid:
                    (short_name, extension) = os.path.splitext(os.path.basename(remotepath))
                    new_f = '%s-%s%s' % (short_name, udid, extension)
                local_file = os.path.join(localpath, new_f)
                shutil.copy(remote_file, local_file)
                local_files.append(local_file)
                if is_delete:
                    os.remove(remote_file)
            return local_files
        else:
            return mobiledevice.pull_file(bundle_id, remotepath, localpath, udid, is_dir, is_delete)
 
    def remove_files(self, udid, bundle_id, file_path):
        '''删除手机上指定app中的文件或者目录
        
        :param udid: 设备的udid
        :type udid: str 
        :param bundle_id: app的bundle id
        :type bundle_id: str 
        :param file_path: 待删除的文件或者目录，例如: /Documents/test.log
        :type file_path: str  
        '''
        if self.is_simulator(udid):
            sandbox_root = self._get_simulator_app_data_path(udid, bundle_id)
            file_path = file_path[1:] if file_path.startswith('/') else file_path
            file_path = os.path.join(sandbox_root, file_path)
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.exists(file_path):
                shutil.rmtree(file_path)
        else:
            mobiledevice.remove_files(bundle_id, file_path, udid)
            
    def list_apps_with_fbsimctl(self, udid, app_type):
        try:
            apps_info =[]
            cmd = "%s --json %s list_apps" % (self.fbsimctl, udid)
            result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            if PY3:
                result = result.decode()             
            result = result.split('\n')
            for line in result:
                if 'list_apps' in line:
                    line = json.loads(line, encoding='utf-8')
                    if line['event_type'] == 'discrete':
                        apps_info = line['subject']
                        break
            apps = []
            for app_info in apps_info:
                if app_type == 'all':
                    apps.append({app_info['bundle']['bundle_id']:app_info['bundle']['name']})
                elif app_info['install_type'] == app_type:
                    apps.append({app_info['bundle']['bundle_id']:app_info['bundle']['name']})
            return apps
        except subprocess.CalledProcessError as e:
            raise Exception('list_apps for simulator error:%s' % e.output)
    
    def list_apps(self, udid, app_type): 
        '''获取设备上的app列表
        
        :param udid: 设备的udid
        :type udid: str 
        :param app_type: app的类型(user/system/all)
        :type app_type: str 
        :returns: list
        '''
        if self.is_simulator(udid):
            return self.list_apps_with_fbsimctl(udid, app_type)
        else:
            return InstallationProxy(udid).list_apps(app_type)
    
    def get_syslog(self, watchtime, logFile, processName, udid):
        '''获取设备上服务日志

        :param watchtime: 观察时间
        :type watchtime: int
        :param logFile: 日志文件名
        :type logFile: str
        :param processName: 服务名
        :type processName: str
        :param udid: 设备的udid
        :type udid: str
        '''
        if self.is_simulator(udid):
            root_path = os.path.join(os.path.expanduser('~'), 'Library/Logs/CoreSimulator/')
            syslog_path = os.path.join(os.path.join(root_path, udid),'system.log')
            with open(syslog_path,"rb") as fd:
                lines = fd.readlines()
            pattern = re.compile(r'\d{2}:\d{2}:\d{2}')
            time_end = pattern.search(lines[-1]).group()
            timestamp = int(time_end[0:2])*3600 + int(time_end[3:5])*60 + int(time_end[6:8])
            a = datetime.datetime.utcfromtimestamp(timestamp) 
            b = datetime.timedelta(seconds=watchtime)  
            start = (str(a-b))[-8:]
            time_start = int(start[6:8])+60*int(start[3:5])+3600*int(start[0:2])
            log = []
            for i in range(len(lines)):
                log.append(lines[len(lines)-i-1])
                if pattern.search(lines[len(lines)-i-1]):
                    tm = pattern.search(lines[len(lines)-i-1]).group()
                    time_now = int(tm[6:8])+60*int(tm[3:5])+3600*int(tm[0:2]) 
                    if (time_now < time_start):
                        break
                    
            with open(logFile, 'a') as f:
                for i in log:
                    f.write(i.replace("\x00", ""))       
        else:
            mobiledevice.get_syslog(watchtime, logFile, processName, udid)
    
    def update_sandbox_client(self, udid, bundle_id):
        '''获取SandboxClient对象，防止一直创建对象导致StartServiceError
        
        :param udid: 设备的udid
        :type udid: str
        :param bundle_id: 应用的bundle_id
        :type bundle_id: str
        '''
        if not self.udid or not self.bundle_id:
            self.udid = udid
            self.bundle_id = bundle_id
            self.sc = SandboxClient(udid, bundle_id)
        elif self.udid != udid or self.bundle_id != bundle_id:
            self.close_sandbox_client()
            self.sc = SandboxClient(udid, bundle_id)
        else:
            try:
                #调用sandboxClient接口方法，以确认该对象是否还可用
                self.sc.read_directory('/')
            except:
                self.sc = SandboxClient(udid, bundle_id)
    
    def close_sandbox_client(self):
        '''对象销毁
        '''
        self.bundle_id = None
        self.udid = None
        self.sc.close()
    
    def get_sandbox_path_files(self, udid, bundle_id, file_path):
        '''返回真机或者模拟器的沙盒路径
        
        :param udid: 设备的udid
        :type udid: str
        :param bundle_id: 应用的bundle_id
        :type bundle_id: str
        :param file_path: 沙盒目录
        :type file_path: str
        '''
        file_path = file_path.encode('utf-8')
        sandbox_tree = []
        tmp_dict = {}
        if self.is_simulator(udid):
            sandbox_root = self._get_simulator_app_data_path(udid, bundle_id)
            file_path = sandbox_root if file_path == '/' else file_path
            for l in os.listdir(file_path):
                tmp_dict['path'] = os.path.join(file_path, l)
                tmp_dict['is_dir'] = os.path.isdir(tmp_dict['path'])
                sandbox_tree.append(tmp_dict)
                tmp_dict = {}
        else:
            self.update_sandbox_client(udid, bundle_id)
            for l in self.sc.read_directory(file_path):
                if l not in ('.', '..'):
                    tmp_dict['path'] = os.path.join(file_path, l)
                    info = self.sc.get_file_info(tmp_dict['path'])
                    tmp_dict['is_dir'] = (info != None and info['st_ifmt'] == 'S_IFDIR')
                    sandbox_tree.append(tmp_dict)
                    tmp_dict = {}
        return sandbox_tree
     
    def is_sandbox_path_dir(self, udid, bundle_id, file_path):
        '''判断一个sandbox路径是否是一个目录
        
        :param udid: 设备的udid
        :type udid: str
        :param bundle_id: 应用的bundle_id
        :type bundle_id: str
        :param file_path: 沙盒目录
        :type file_path: str
        '''
        file_path = file_path.encode('utf-8')
        if self.is_simulator(udid):
            sandbox_root = self._get_simulator_app_data_path(udid, bundle_id)
            file_path = sandbox_root if file_path == '/' else file_path
            return os.path.isdir(file_path)
        else:
            self.update_sandbox_client(udid, bundle_id)
            info = self.sc.get_file_info(file_path)
            return (info != None and info['st_ifmt'] == 'S_IFDIR')
      
    def get_sandbox_file_content(self, udid, bundle_id, file_path):
        '''获取sandbox中文本文件的内容
        
        :param udid: 设备的udid
        :type udid: str
        :param bundle_id: 应用的bundle_id
        :type bundle_id: str
        :param file_path: 沙盒目录
        :type file_path: str
        '''
        file_path = file_path.encode('utf-8')
        if self.is_simulator(udid):
            if os.path.exists(file_path):
                with open(file_path, "rb") as fd:
                    return base64.b64encode(fd.read())
            else:
                raise Exception('file(%s) does not exist' % file_path)
        else:
            self.update_sandbox_client(udid, bundle_id)
            content = self.sc.get_file_contents(file_path)
            if content:
                return base64.b64encode(content) 
            
    def _get_device_by_fbsimctl(self):
        '''获取设备列表
        '''
        devices = []
        cmd = "%s --json list" % self.fbsimctl
        try:
            res = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            if PY3:
                res = res.decode()
            for dev in res.split('\n'):
                if dev == '' :
                    continue
                dev = json.loads(dev)['subject']
                if 'name' not in dev:
                    continue
                name = dev['name']
                if 'Apple Watch' in name:
                    continue
                if 'Apple TV' in name:
                    continue
                arch = dev['arch']
                if arch == 'arm64' :
                    dev[u'simulator'] = False
                else :
                    dev[u'simulator'] = True 
                ios = dev['os']
                dev[u'ios'] = ios.split(' ')[1].strip()
                devices.append(dev)
        except subprocess.CalledProcessError:
            pass
        return devices
