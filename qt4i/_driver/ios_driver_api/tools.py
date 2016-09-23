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
'''driver-tools-api
'''
# 2014/10/25    cherry    创建
# 2015/12/29    jerry          替换DT工具集的实现方式（simctl+libimobiledevice）
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

import getpass
import os
import re
import subprocess
import time
from _base  import Register
from qt4i._driver.ios_driver_api.mobiledevice import AFCCrashLog
from qt4i._driver.ios_driver_api.mobiledevice import idevice_id
from qt4i._driver.ios_driver_api.mobiledevice import ideviceinfo
from qt4i._driver.ios_driver_api.mobiledevice import idevicescreenshot
from qt4i._driver.ios_driver_api.mobiledevice import InstallationProxy
from qt4i._driver.ios_driver_api.mobiledevice import SandboxClient
from pymobiledevice.diagnostics_relay import DIAGClient

from qt4i._driver._jsonp import Json
from qt4i._driver._files import FileManager
from qt4i._driver._task  import Task
from qt4i._driver._print import print_err
from testbase.util import Timeout
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
CurrentDirectoryPath = os.path.abspath(os.path.dirname(__file__))
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-



class DT(Register):
    '''DeviceTool-API - 用于查询设备信息，以及安装和卸载APP
    '''

    def register(self):
        self._register_functions('dt')

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):cls._instance = super(cls, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    
    def __init__(self, _server=None):
        Register.__init__(self, _server)
        self._server = _server
        self.xcode_version = DT.get_xcode_version()
    
    @staticmethod
    def get_xcode_version():
        version = "7.2"
        try:
            xcode_info = subprocess.check_output("xcodebuild -version", shell=True, stderr=subprocess.STDOUT)
            version = re.match(r'Xcode\s(\d+\.\d+)', xcode_info.split('\n')[0]).group(1)
        except subprocess.CalledProcessError, e:
            print_err(e.output)
        return version         
    
    def get_real_devices(self):
        '''查询当前Mac机上已连接的真机设备（仅含真机，不含模拟器）
        
        :return: list[dict] or None（意外情况）
        '''
        udids = idevice_id()
        devices = []
        for udid in udids:
            infos = ideviceinfo(udid)
            device = {}
            device["ios"] = infos["ProductVersion"]
            device["name"] = infos["DeviceName"]
            device["simulator"] = False
            device["udid"] = udid
            devices.append(device)
        
        return devices  
    
    def _get_simulators_below_xcode_7(self):
        devices = []
        try:
            cmd = "xcrun simctl list devices"
            result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
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
        except subprocess.CalledProcessError, e:
            print_err(e.output)
        return devices
    
    def _get_simulators_above_xcode_7(self):
        devices = []
        try:
            cmd = "xcrun simctl list -j devices"   
            result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            json_devices = Json().loads(result)["devices"]
            for k in json_devices:
                if k.startswith("iOS"):
                    ios_version = re.match(r'iOS\s(\d+\.\d+)', k).group(1)
                    for dev in json_devices[k]:
                        dev["ios"] = ios_version
                        dev["simulator"] = True
                        devices.append(dev)
        except subprocess.CalledProcessError, e:
            print_err(e.output)
        return devices          
    
    def get_simulators(self):
        '''查询已安装的模拟器(如果没必要查询真机，仅查模拟器的性能更佳)
        :return: list[dict] or None（意外情况）
        '''
        if self.xcode_version < "7.0":
            return self._get_simulators_below_xcode_7()         
        else:
            return self._get_simulators_above_xcode_7()         
    
    def get_devices(self):
        '''查询当前Mac机上的所有可用设备(含真机与模拟器，并产生缓存)
        :return: list[dict]
        '''
        _devices = []
        _real_devices = self.get_real_devices()
        _simulators = self.get_simulators()
        if len(_real_devices) > 0 : _devices += _real_devices
        if len(_simulators) > 0     : _devices += _simulators
        return _devices
    
    def get_device_by_name(self, _name):
        '''通过设备名查询当前Mac机上的可用设备(含真机与模拟器)
        :param _name: 设备名(支持正则表达式)，例如：iPhone 5s (8.1 Simulator)
        :type _name: str
        :return: dict or None
        '''
        _devices = self.get_devices()
        for _item in _devices:
            if _name == _item["name"] or re.match(_name, _item["name"]):
                return _item
    
    def get_device_by_udid(self, _device_udid):
        '''通过设备的udid查询当前Mac机上的设备(含真机与模拟器)
        :param _device_udid: 设备的udid
        :type _device_udid: str
        :return: dict or None
        '''
        _devices = self.get_devices()
        for _item in _devices:
            if _device_udid == _item["udid"]:
                return _item
    
    def check_device_udid_is_valid(self, _device_udid):
        '''检测udid是否有效（含真机与模拟器）
        :param _device_udid: 真机或模拟器的udid
        :type _device_udid: str
        :return: bool
        '''
        device = self.get_device_by_udid(_device_udid)
        return bool(device)
    
    def get_simulator_by_name(self, _name):
        '''通过模拟器名查询模拟器(如果没必要查询真机，仅查模拟器的性能极佳)
        :param _name: 模拟器名(支持正则表达式)，例如：iPhone 5s (8.1 Simulator)
        :type _name: str
        :return: dict or None
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
        :return: dict or None
        '''
        _simulators = self.get_simulators()
        if _simulators:
            for _item in _simulators:
                if _device_udid == _item["udid"]:
                    return _item
    
    def get_default_simulator(self):
        '''查询默认的模拟器(由于模拟器只能有一个实例，所以有默认模拟器。真机不存在默认真机的情况)
        :return: dict or None（意外情况）
        '''
        raise Exception("get_default_simulator unsupported")
    
    def set_default_simulator(self, _device_udid):
        '''设置默认模拟器
        :param _device_udid: 模拟器的udid
        :type _device_udid: str
        :return: bool
        '''
        raise Exception("set_default_simulator unsupported")
    
    def app_info(self, _file_path):
        '''获取APP安装包的信息(IPA或APP均可)
        :param _file_path: IPA或APP安装包的路径(注意：当前Mac机必须能访问到该路径)
        :type _file_path: str
        :return: dict or None
        '''
        raise Exception("app_info unsupported")
    
    def start_simulator(self, udid=None):
        simulator = "Simulator"
        if self.xcode_version < "7.0":
            simulator = "iOS Simulator"
        if udid:
            cmd = "open -a \"%s\" --args -CurrentDeviceUDID %s" % (simulator, udid)
        else:
            cmd = "open -a \"%s\"" % simulator
        ret = subprocess.call(cmd, shell=True)
        if ret != 0:
            return False
        
        #检查模拟器是否启动成功
        def check_started():
            for s in self.get_simulators():
                if s["state"] == "Booted" and (s["udid"] == udid or udid is None):
                    return True
            return False
        return Timeout().check(check_started, True)

    def _install_for_simulator(self, udid, app_path):
        try:
            cmd = "xcrun simctl install %s %s" % (udid, app_path)
            subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            return (True, "")
        except subprocess.CalledProcessError, e:
            print_err(e.output)
        return (False, e.output)
    
    def install(self, _file_path, _device_udid=None):
        '''通过udid指定真机安装IPA或模拟器安装APP(注意：真机所用IPA不能在模拟器上安装和使用，IPA与APP相互不兼容)
        :param _file_path: IPA或APP安装包的路径(注意：当前Mac机必须能访问到该路径)
        :type _file_path: str
        :param _device_udid: 设备的udid(当udid为None时，IPA包则安装到第一台连接上的真机上，APP包则安装到默认模拟器上)
        :type _device_udid: str
        :return: bool
        '''
        self.install_error = ""
        if _file_path.endswith("ipa"):
            ip = InstallationProxy(_device_udid)
            ret = ip.install(_file_path)
        else:
            self.start_simulator(_device_udid)
            if _device_udid is None:
                _device_udid = "booted"
            ret = self._install_for_simulator(_device_udid, _file_path)
        
        self.install_error = ret[1]
        return ret[0]
        
    def _uninstall_for_simulator(self, udid, bundle_id):
        try:
            cmd = "xcrun simctl uninstall %s %s" % (udid, bundle_id)
            subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            return (True, "")
        except subprocess.CalledProcessError, e:
            print_err(e.output)
        return (False, e.output)
    
    def uninstall(self, _bundle_id, _device_udid=None):
        '''通过udid指定设备卸载指定bundle_id的APP
        :param _bundle_id: APP的bundle_id，例如：com.tencent.qq.dailybuild.test
        :type _bundle_id: str
        :param _device_udid: 设备的udid(当udid为None时，如果有真机连接，则卸载第一台连接上的真机内的APP，如果无真机连接，则卸载默认模拟器上的APP)
        :type _device_udid: str
        :return: bool
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

            
# # -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-


class IMobileDevice(Register):
    '''
    基于mobiledevice的iOS设备管理接口封装（只适用于真机）
    '''
    
    def register(self):
        self._register_functions('imobiledevice')

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):cls._instance = super(cls, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    
    def __init__(self, _server=None):
        Register.__init__(self, _server)
        self._server = _server
    
    def get_device_type_by_udid(self, _device_udid):
        '''通过设备的udid查询当前iOS设备的类型
        
        :param _device_udid: 设备的udid
        :type _device_udid: str
        :return: string - 设备类型：iPad/iPhone/iPod/Unknown
        '''
        result = ideviceinfo(_device_udid, "DeviceClass")
        return result if result else 'Unknown'
    
    def get_screenshot_by_udid(self, filepath, _device_udid = None):
        '''通过设备的udid的获取屏幕快照
        
        :param _device_udid: 设备的udid
        :type _device_udid: str
        :param filepath: 屏幕快照的存储路径
        :type filepath: str
        :return: boolean
        '''
        return idevicescreenshot(_device_udid, filepath)
        
    
    def get_devices(self):
        '''获取真机的udid列表
        
        :return: list
        '''
        return idevice_id()
    
    def get_crash_log(self, procname, device_udid = None):
        '''通过设备的udid的获取指定进程的最新的crash日志
        
        :param proc_name: app的进程名，可通过xcode查看
        :type proc_name: str        
        :param device_udid: 设备的udid
        :type device_udid: str
        :return: string or None
        '''
        latest_log = None
        latest_timestamp = 0
        try:
            afc_crash = AFCCrashLog(device_udid)
            log_path = '/tmp/_attachments'
            crash_logs = afc_crash.get_crash_log(procname, log_path)
            for log in crash_logs:
                result = re.match('%s/.+_(\d{4}-\d{2}-\d{2}-\d{6})_.*\.ips' % log_path, log)
                if result:
                    time_src = result.group(1)
                    time_tmp = time.strptime(time_src, "%Y-%m-%d-%H%M%S")
                    timestamp = int(time.mktime(time_tmp))
                    if timestamp > latest_timestamp:
                        latest_log = log
                        latest_timestamp = timestamp
        
            # 过滤掉Xcode的bug引起的假crash
            now = int(time.time()) 
            if now - latest_timestamp > 300: #判断crash文件的时间戳距离当前时间超过5分钟，则认为当前没有发生crash
                latest_log = None
            if isinstance(latest_log, basestring) and os.path.isfile(latest_log):
                pass
            else:
                latest_log = None
        except Exception, e:
            print_err(e.message)
        finally:
            afc_crash.close()
        return latest_log
    
    def copy_to_local(self, bundle_id, remotepath, localpath='/tmp', device_udid = None, is_dir=False, is_delete = False):
        '''拷贝手机中sandbox指定目录的文件到Mac本地
        
        :param bundle_id: app的bundle id
        :type bundle_id: str   
        :param remotepath: sandbox上的目录或者文件，例如：/Library/info
        :type remotepath: str        
        :param localpath: 本地的目录
        :type localpath: str
        :param device_udid: 设备的udid
        :type device_udid: str
        :param is_dir: remotepath是否为目录，默认为单个文件
        :type is_dir: bool
        :param is_delete: 是否删除，默认为单个文件
        :type is_delete: bool
        :return: list or None
        '''
        try:
            files = None
            afc_client = SandboxClient(device_udid, bundle_id)
            files = afc_client.copy_to_local(remotepath, localpath, is_dir, is_delete)
        except Exception, e:
            print_err(e.message)
        finally:
            afc_client.close()
        return files

    def copy_to_remote(self, bundle_id, localpath, remotepath, device_udid = None):
        '''拷贝Mac本地文件到手机中sandbox的指定目录地
        
        :param bundle_id: app的bundle id
        :type bundle_id: str   
        :param localpath: Mac上的文件路径
        :type localpath: str
        :param remotepath: sandbox上的目录或者文件，例如：/Library/info
        :type remotepath: str        
        :param device_udid: 设备的udid
        :type device_udid: str
        :return: boolean
        '''
        result = False
        try:
            afc_client = SandboxClient(device_udid, bundle_id)
            result = afc_client.copy_to_remote(localpath, remotepath)
        except Exception, e:
            print_err(e.message)
        finally:
            afc_client.close()
        return result
    
    def reboot(self, device_udid = None):
        '''重启手机
        
        :param device_udid: 设备的udid
        :type device_udid: str
        '''
        DIAGClient(device_udid).restart()
        
    def remove(self, bundle_id, files, device_udid = None):
        '''删除手机上指定app中的文件或者目录
        
        :param bundle_id: app的bundle id
        :type bundle_id: str 
        :param bundle_id: 待删除的文件或者目录，例如: /Documents/test.log
        :type bundle_id: str  
        :param device_udid: 设备的udid
        :type device_udid: str
        '''
        try:
            afc_client = SandboxClient(device_udid, bundle_id)
            afc_client.remove(files)
        except Exception, e:
            print_err(e.message)
        finally:
            afc_client.close()
        
    
if __name__ == '__main__':
    print DT().get_devices()

