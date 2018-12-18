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
'''pymobiledevice extended tools
'''

from __future__ import absolute_import, print_function

from cmd import Cmd
import os
import re
from subprocess import check_call, STDOUT, CalledProcessError
import tempfile
import time
import six

from pymobiledevice.afc import AFCClient, AFCShell
from pymobiledevice.diagnostics_relay import DIAGClient
from pymobiledevice.lockdown import LockdownClient
from pymobiledevice.screenshotr import screenshotr
from pymobiledevice.usbmux.usbmux import USBMux
from pymobiledevice.syslog import Syslog


TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

def list_devices():
    '''获取当前电脑上连接的所有iOS设备
    
    :returns: list - 包含所有iOS设备的UDID的数组
    '''
    mux = USBMux()
    if not mux.devices:
        mux.process(1)
    for _ in range(5): 
        mux.process(0.1)
    return [d.serial for d in mux.devices]


def get_device_info(udid = None, keyname = None):
    '''获取iOS设备的相关属性信息
    
    :param udid: iOS设备的udid
    :type udid: str
    :param keyname: iOS设备的特定信息字段的名称
    :type keyname: str
    :returns: str - iOS设备的信息
    ''' 
    lockdown = LockdownClient(udid)
    lockdown.startService("com.apple.afc")
    if keyname:
        return lockdown.allValues.get(keyname)
    else:
        return lockdown.allValues

    
def get_screenshot(udid = None, filepath = "/tmp/screenshot.png"):  
    '''获取iOS设备的屏幕快照
    
    :param udid: iOS设备的udid
    :type udid: str
    :param filepath: 屏幕快照的存储路径
    :type filepath: str
    :returns: boolean - 截图是否成功
    '''   
    result = False
    tiff_file = tempfile.NamedTemporaryFile(suffix='.tiff')
    tiff_file_path = tiff_file.name
    lockdown = LockdownClient(udid)
    screenshot = screenshotr(lockdown)
    data = screenshot.take_screenshot()
    with open(tiff_file_path, "wb") as fd:
        fd.write(data)
    screenshot.stop_session()
    try:
        args = ["/usr/bin/sips", "-s format png", tiff_file_path, "--out", filepath]
        check_call(" ".join(args), shell=True, stderr=STDOUT)
        result = True
    except CalledProcessError:
        pass
    finally:
        tiff_file.close()
    return result


def get_crash_log(procname, device_udid = None, log_path='/tmp'):
    afc_crash = AFCCrashLog(device_udid)
    return afc_crash.get_crash_log(procname, log_path, True)


def pull_file(bundle_id, remotepath, localpath='/tmp', device_udid = None, is_dir=False, is_delete = True):
    '''拷贝手机中sandbox指定目录的文件到Mac本地
    
    :param bundle_id: app的bundle id
    :type bundle_id: str   
    :param remotepath: sandbox上的目录或者文件，例如：/Library/Caches/test/
    :type remotepath: str        
    :param localpath: 本地的目录
    :type localpath: str
    :param device_udid: 设备的udid
    :type device_udid: str
    :param is_dir: remotepath是否为目录，默认为单个文件
    :type is_dir: bool
    :param is_delete: 是否删除
    :type is_delete: bool
    :returns: list or None
    '''
    afc_client = None
    try:
        files = None
        afc_client = SandboxClient(device_udid, bundle_id)
        files = afc_client.copy_to_local(remotepath, localpath, is_dir, is_delete)
    finally:
        if afc_client is not None:
            afc_client.close()
    return files


def push_file(bundle_id, localpath, remotepath, device_udid = None):
    '''拷贝Mac本地文件到手机中sandbox的指定目录地
    
    :param bundle_id: app的bundle id
    :type bundle_id: str   
    :param localpath: Mac上的文件路径
    :type localpath: str
    :param remotepath: sandbox上的目录或者文件，例如：/Library/Caches/test/
    :type remotepath: str        
    :param device_udid: 设备的udid
    :type device_udid: str
    :returns: boolean
    '''
    afc_client = None
    result = False
    try:
        afc_client = SandboxClient(device_udid, bundle_id)
        result = afc_client.copy_to_remote(localpath, remotepath)
        result = True
    finally:
        if afc_client is not None:
            afc_client.close()
    return result


def remove_files(bundle_id, file_path, device_udid = None):
    '''删除手机上指定app中的文件或者目录
    
    :param bundle_id: app的bundle id
    :type bundle_id: str 
    :param file_path: 待删除的文件或者目录，例如: /Documents/test.log
    :type file_path: str  
    :param device_udid: 设备的udid
    :type device_udid: str
    '''
    afc_client = None
    try:
        afc_client = SandboxClient(device_udid, bundle_id)
        afc_client.remove(file_path)
    finally:
        if afc_client is not None:
            afc_client.close()

    
def reboot(device_udid = None):
    '''重启手机
    
    :param device_udid: 设备的udid
    :type device_udid: str
    '''
    lockdown = LockdownClient(udid=device_udid)
    DIAGClient(lockdown).restart()
    time.sleep(10)
    for _ in range(20):
        if device_udid in list_devices():
            print('reboot successfully')
            break
    else:
        print('reboot error: real device disconect')


def get_syslog(watchtime, logFile, procName = None, device_udid = None):
    ''' 获取手机服务日志
    
    :param watchtime: 观察时间
    :type watchtime: 观察时间
    :param logFile: 日志名称
    :type device_udid: str
    :param procName: 进程名称
    :type procName: str
    :param device_udid: 设备的udid
    :type device_udid: str
    '''
    lockdown = LockdownClient(udid=device_udid)
    syslog = Syslog(lockdown)
    syslog.watch(watchtime, logFile, procName)
              

class InstallationProxy(object):
    
    def __init__(self, udid=None):
        self.udid = udid
        self.lockdown = LockdownClient(udid)
        self.service = self.lockdown.startService("com.apple.mobile.installation_proxy")
    
    def wait_completion(self, handler=None, *args):
        while True:
            z =  self.service.recvPlist()
            if not z:
                break
            completion = z.get("PercentComplete")
            if completion:
                if handler:
                    handler(completion,*args)    
#                 print "%s: %s%% Complete" % (z.get("Status"), completion)
            else:
                if z.get("Status") == "Complete" or ("Status" not in z and "CFBundleIdentifier" in z):
                    return (True, "")
                else:
                    return (False, z.get("ErrorDescription"))
    
    def send_cmd_for_bid(self, bundle_id, cmd="Archive", options=None, handler=None, *args):
        cmd = {"Command": cmd, "ApplicationIdentifier": bundle_id }
        if options:
            cmd.update(options) 
        self.service.sendPlist(cmd)
        return self.wait_completion(handler, *args)      
        
    def install(self, ipa_path, options=None, handler=None, *args):
        '''安装应用程序
        
        :param ipa_path: 安装包的路径
        :type ipa_path: str
        :return: boolean - 安装是否成功
        '''
        print("上传安装包...")
        afc_client = AFCClient(self.lockdown)
        tmp_ipa = "t%d.ipa" % time.time()
        with open(ipa_path, "rb") as f:
            ipa_content = f.read()
            afc_client.set_file_contents("/" + tmp_ipa, ipa_content)
            print("上传完毕")
        print("开始安装")
        cmd = {"Command":"Install", "PackagePath": tmp_ipa}
        if options:
            cmd.update(options)
        self.lockdown = LockdownClient(self.udid)
        self.service = self.lockdown.startService("com.apple.mobile.installation_proxy")
        self.service.sendPlist(cmd)
        ret = self.wait_completion(handler, args)
        return ret

    
    def uninstall(self, bundle_id, options=None, handler=None, *args):
        '''卸载应用程序
    
        :param bundle_id: 应用程序的bundle id
        :type bundle_id: str
        :return: boolean - 卸载是否成功
        '''     
        return self.send_cmd_for_bid(bundle_id, "Uninstall", options, handler, args)
    
    def apps_info(self):
        self.service.sendPlist({"Command": "Lookup"})
        return self.service.recvPlist()
    
    def list_apps(self, app_type='all'):
        options = {}
        if app_type == 'system':
            options["ApplicationType"]="System"
        elif app_type == 'user':
            options["ApplicationType"]="User"
        options["ReturnAttributes"] = ["CFBundleIdentifier",
#                                        "CFBundleDisplayName",
#                                        "CFBundleVersion",
                                        "CFBundleName",]
        self.service.sendPlist({"Command": "Browse", "ClientOptions":options})
        apps = []
        while True:
            z = self.service.recvPlist()
            if z.get("Status") == "BrowsingApplications":
                apps.extend(z["CurrentList"])
            elif z.get("Status") == "Complete":
                break
            else:
                raise Exception(z.get("ErrorDescription"))
        apps = [{app["CFBundleIdentifier"]:app["CFBundleName"]} for app in apps]
        return apps
    
    def __del__(self):
        if hasattr(self, "service"):
            self.service.close()
        
        
class AFCShell2(AFCShell):
    
    def __init__(self, afcclient, completekey='tab', stdin=None, stdout=None):
        Cmd.__init__(self, completekey=completekey, stdin=stdin, stdout=stdout)
        self.afc = afcclient
 
        self.curdir = '/'
        self.prompt = 'AFC$ ' + self.curdir + ' '
        self.complete_cat = self._complete
        self.complete_ls = self._complete
    
    def dir_walk(self,dirname):
        res = self.afc.dir_walk(dirname)
        file_iter = six.next(res)[2]
        return file_iter
    
    def set_file_contents(self,filename,data):
        return self.afc.set_file_contents(filename,data)

    def get_file_contents(self,filename):
        return self.afc.get_file_contents(filename)
    
    def do_rm(self, p):
        f =  self.afc.get_file_info(self.curdir + "/" + p)
        if f is None:
            return  
        elif 'st_ifmt' in f and f['st_ifmt'] == 'S_IFDIR':
            self.afc.remove_directory(self.curdir + "/" + p)
        else:
            self.afc.file_remove(self.curdir + "/" + p)    


class AFCCrashLog(AFCClient):
    def __init__(self, udid=None, lockdown=None):
        self.lockdown = lockdown if lockdown else LockdownClient(udid)
        self.service = None
        retry = 5
        while retry > 0:
            try:
                self.service = self.lockdown.startService("com.apple.crashreportcopymobile")
                break
            except:
                import traceback
                traceback.print_exc()
                retry -= 1
                time.sleep(5)
        if self.service is None:
            raise RuntimeError('Connect to crashreportcopymobile failed')
        self.afc_shell = AFCShell2(afcclient=self)
        super(AFCCrashLog, self).__init__(self.lockdown, service=self.service)
    
    def _filter_crash_log(self, logs, log_path, procname):
        latest_log = None
        latest_timestamp = 0
        for log in logs:
            result = re.match('%s/%s.+(\d{4}-\d{2}-\d{2}-\d{6}).*\.(ips|synced)' % (log_path, procname), log)
            if result:
                time_src = result.group(1)
                timestamp = int(time.mktime(time.strptime(time_src, "%Y-%m-%d-%H%M%S")))
                if timestamp > latest_timestamp:
                    latest_log = log
                    latest_timestamp = timestamp
        
        # 过滤掉Xcode的bug引起的假crash
        now = int(time.time()) 
        if now - latest_timestamp > 300: #判断crash文件的时间戳距离当前时间超过5分钟，则认为当前没有发生crash
            latest_log = None
        return latest_log
    
    def get_crash_log(self, procname, dest, is_delete = False):
        local_crashes =[]
        remote_crash_path = '/'
        for filename in self.afc_shell.dir_walk(remote_crash_path):
            if procname in filename:
                remote_crash_file = os.path.join(remote_crash_path, filename)
                data = self.afc_shell.get_file_contents(remote_crash_file)
                local_crash_file = os.path.join(dest, filename)
                local_crashes.append(local_crash_file)
                with open(local_crash_file, 'wb') as fp:
                    fp.write(data)
                if is_delete: 
                    self.afc_shell.do_rm(remote_crash_file)
        return self._filter_crash_log(local_crashes, dest, procname)
    
    def close(self):
        if self.service:
            self.service.close()


class SandboxClient(AFCClient):
    '''
    访问app的sandbox的类
    '''

    def __init__(self, udid=None, bid='com.tencent.sng.test.gn', sandbox="VendContainer", lockdown=None):
        self.lockdown = lockdown if lockdown else LockdownClient(udid)
        self.bid = bid
        self.service = None
        self.udid = udid
        retry = 5
        while retry > 0:
            try:
                self.service = self.lockdown.startService("com.apple.mobile.house_arrest")
                break
            except:
                import traceback
                traceback.print_exc()
                retry -= 1
                time.sleep(2)
                if retry <= 0:
                    raise
        if self.service is None:
            raise RuntimeError('Connect to house_arrest failed')

        self.service.sendPlist({"Command": sandbox, "Identifier": bid})
        status = self.service.recvPlist()
        if 'Error' in status and status['Error'] == "ApplicationLookupFailed":
            raise RuntimeWarning('ApplicationLookupFailed')
        if 'Status' in status and status['Status'] != 'Complete':
            raise RuntimeWarning('House arrest service launch failed')
        super(SandboxClient, self).__init__(self.lockdown, service=self.service)

        self.afc_shell = AFCShell2(self)
    
    def copy_to_local(self, remotepath, localpath='/tmp', is_dir=False, is_delete = False):
        '''拷贝手机中sandbox指定目录的文件到Mac本地
        :param remotepath: sandbox上的目录或者文件，例如：/Library/Caches/test/
        :type remotepath: str        
        :param localpath: 本地的目录
        :type localpath: str
        :param is_dir: remotepath是否为目录，默认为单个文件
        :type is_dir: bool
        :param is_delete: 是否删除，默认为单个文件
        :type is_delete: bool
        :return: list   拷贝后的本地文件列表
        '''
        local_files = []
        if is_dir:
            remotefiles = self.afc_shell.dir_walk(remotepath)
        else:
            filepath, filename = os.path.split(remotepath)
            remotefiles = [filename]
            remotepath = filepath
        
        for f in remotefiles:
            src = os.path.join(remotepath,f)
            content = self.afc_shell.get_file_contents(src)
            if self.udid:
                (short_name, extension) = os.path.splitext(f)
                new_f = '%s-%s%s' % (short_name, self.udid, extension)
            if content is None:
                continue
            dst = os.path.join(localpath,new_f)
            local_files.append(dst)
            with open(dst, 'wb') as fd:
                fd.write(content)
            if is_delete:
                self.afc_shell.do_rm(src)
        return local_files

    def copy_to_remote(self, localfile, remotepath):
        '''拷贝Mac本地文件到手机中sandbox的指定目录
        :param localfile: Mac本地文件路径（仅限文件拷贝）
        :type localfile: str
        :param remotepath: sandbox上的目录，例如：/Library/Caches/
        :type remotepath: str
        :return: bool
        ''' 
        result = False
        with open(localfile, 'rb') as fd:
            data = fd.read()
            remotefile = os.path.join(remotepath,os.path.basename(localfile))
            status = self.afc_shell.set_file_contents(remotefile,data)
            if status == 0:
                result = True
        return result
    
    def remove(self, files):
        '''删除sandbox中的文件或者目录
        '''
        self.afc_shell.do_rm(files)
    
    def close(self):
        '''必须显示调用该函数，否则会出现端口泄漏
        '''
        if self.service:
            self.service.close()