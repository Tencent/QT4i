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
'''pymobiledevice的扩展工具集
'''
# 16/05/27  jerry  创建


import os
import tempfile
import time
from subprocess import check_call, STDOUT, CalledProcessError

from pymobiledevice.afc import AFCClient, AFCShell
from pymobiledevice.lockdown import LockdownClient
from pymobiledevice.screenshotr import screenshotr
from pymobiledevice.usbmux.usbmux import USBMux

def idevice_id():
    '''获取当前电脑上连接的所有iOS设备
    
    :return: list - 包含所有iOS设备的UDID的数组
    '''
    mux = USBMux()
    if not mux.devices:
        mux.process(1)
    return [d.serial for d in mux.devices]


def ideviceinfo(udid = None, keyname = None):
    '''获取iOS设备的相关属性信息
    
    :param udid: iOS设备的udid
    :type udid: str
    :param keyname: iOS设备的特定信息字段的名称
    :type keyname: str
    :return: str - iOS设备的信息
    ''' 
    lockdown = LockdownClient(udid)
    lockdown.startService("com.apple.afc")
    if keyname:
        return lockdown.allValues.get(keyname)
    else:
        return lockdown.allValues

    
def idevicescreenshot(udid = None, filepath = "/tmp/screenshot.png"):  
    '''获取iOS设备的屏幕快照
    
    :param udid: iOS设备的udid
    :type udid: str
    :param filepath: 屏幕快照的存储路径
    :type filepath: str
    :return: boolean - 截图是否成功
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
    except CalledProcessError, e:
        print e.output
    finally:
        tiff_file.close()
    return result


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
                    print "calling handler"
                    handler(completion,*args)    
#                 print "%s: %s%% Complete" % (z.get("Status"), completion)
            else:
                if z.get("Status") == "Complete":
                    print "安装成功"
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
        print "上传安装包..."
        afc_client = AFCClient()
        tmp_ipa = "t%d.ipa" % time.time()
        with open(ipa_path, "rb") as f:
            ipa_content = f.read()
            afc_client.set_file_contents("/" + tmp_ipa, ipa_content)
            print "上传完毕"
        print "开始安装"
        cmd = {"Command":"Install", "PackagePath": tmp_ipa}
        if options:
            cmd.update(options)
        self.service.sendPlist(cmd)
        return self.wait_completion(handler, args)
    
    def uninstall(self, bundle_id, options=None, handler=None, *args):
        '''卸载应用程序
    
        :param bundle_id: 应用程序的bundle id
        :type bundle_id: str
        :return: boolean - 卸载是否成功
        '''     
        return  self.send_cmd_for_bid(bundle_id, "Uninstall", options, handler, args)
    
    def apps_info(self):
        self.service.sendPlist({"Command": "Lookup"})
        return self.service.recvPlist()
    
    def __del__(self):
        self.close()
    

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
                time.sleep(10)
        if self.service is None:
            raise RuntimeError('Connect to crashreportcopymobile failed')
        self.afc_shell = AFCShell(client=self)
        super(AFCCrashLog, self).__init__(self.lockdown, service=self.service)
    
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
        return local_crashes


class SandboxClient(AFCClient):
    '''
    访问app的sandbox的类
    '''

    def __init__(self, udid=None, bid='com.tencent.sng.test.gn', sandbox="VendContainer", lockdown=None):
        self.lockdown = lockdown if lockdown else LockdownClient(udid)
        self.bid = bid
        self.service = None
        retry = 5
        while retry > 0:
            try:
                self.service = self.lockdown.startService("com.apple.mobile.house_arrest")
                break
            except:
                import traceback
                traceback.print_exc()
                retry -= 1
                time.sleep(5)
        if self.service is None:
            raise RuntimeError('Connect to house_arrest failed')

        self.service.sendPlist({"Command": sandbox, "Identifier": bid})
        self.afc_shell = AFCShell(client=self)
        status = self.service.recvPlist()
        if status.has_key('Error') and status['Error'] == "ApplicationLookupFailed":
            raise RuntimeWarning('ApplicationLookupFailed')
        if status.has_key('Status') and status['Status'] != 'Complete':
            raise RuntimeWarning('House arrest service launch failed')
        
        super(SandboxClient, self).__init__(self.lockdown, service=self.service)
    
    def copy_to_local(self, remotepath, localpath='/tmp', is_dir=False, is_delete = False):
        '''拷贝手机中sandbox指定目录的文件到Mac本地
        :param remotepath: sandbox上的目录或者文件，例如：/Library/Caches/QQINI/
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
            if content is None:
                continue
            dst = os.path.join(localpath,f)
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


if __name__ == '__main__':
    print idevice_id()
    print ideviceinfo(keyname="DeviceClass")
    print ideviceinfo(keyname="DeviceName")
    print ideviceinfo(keyname="ProductVersion")
    print idevicescreenshot()
