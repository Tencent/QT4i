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

import base64
import os
import time
import uuid
import re
import json
import subprocess
from six.moves.urllib.request import urlopen
from six.moves.urllib.request import Request

from qt4i.driver.rpc import rpc_method
from qt4i.driver.rpc import RPCEndpoint
from qt4i.driver.xctest.agent import XCUITestAgentManager
from qt4i.driver.xctest.agent import EnumDevice
from qt4i.driver.xctest.webdriverclient.command import Command
from qt4i.driver.xctest.webdriverclient.by import By
from qt4i.driver.tools.dt import DT
from qt4i.driver.tools import mobiledevice
from qt4i.driver.tools.logger import get_logger_path_by_name, clean_expired_log, str_to_time
from qt4i.driver.tools import logger
from qt4i.driver.xctest.webdriverclient.exceptions import NoSuchElementException
from qt4i.driver.xctest.webdriverclient.exceptions import XCTestAgentTimeoutException
from qt4i.driver.util.uimap import UIA_XCT_MAPS
from qt4i.driver.xctest.webdriverclient.errorhandler import ErrorCode
from qt4i.driver.util.modalmap import DeviceProperty
from testbase.conf import settings
from tuia.qpathparser import QPathParser
from pymobiledevice import lockdown


DEFAULT_IP = '127.0.0.1'
DEFAULT_PORT = 8100
TMP_LOAD_FILE = '/tmp/tmpFile'

TMP_DIR_PATH = settings.get('QT4I_TMP_DIR_PATH', '/tmp')

def convert_to_qpath(element):
    '''转换成qpath
    '''
    if 'type' in element:
        element['classname'] = element['type']
        element.pop('type')
    if 'isEnabled' in element:
        element['enabled'] = (element['isEnabled'] == '1')
        element.pop('isEnabled')
    if 'isVisible' in element:
        element['visible'] = (element['isVisible'] == '1')
        element.pop('isVisible')
    if 'rect' in element:
        element['rect']= {
            'origin': {'x': element['rect']['x'], 'y': element['rect']['y']},
            'size'  : {'width': element['rect']['width'], 'height': element['rect']['height']},
        }
    children = []
    for child in element.get('children', []):
        children.append(convert_to_qpath(child))
    element['children'] = children
    return element

class lazy(object): 
    def __init__(self, func): 
        self.func = func 
    
    def __get__(self, instance, cls): 
        val = self.func(instance) 
        setattr(instance, self.func.__name__, val) 
        return val

class Device(RPCEndpoint):
    '''XCUIDevice/XCUIApplication API
    '''
    rpc_name_prefix = "device."
    agent_manager = XCUITestAgentManager()

    def __init__(self, rpc_server, device_id):
        self.rpc_server = rpc_server
        self.udid = device_id
        RPCEndpoint.__init__(self)
    
    @rpc_method   
    def dismiss_alert(self, rule):     
        ''' 弹窗处理
        
        :param rule: 弹窗规则
        :type  rule: list
        ''' 
        env = {
                'rules_of_alert_auto_handle' : rule,
                'flag_alert_auto_handled'    : False
             }
        self.agent.execute(Command.QTA_ALERT_DISMISS, env)      
                  
    @rpc_method
    def stop_all_agents(self):
        '''
        该接口请不要再使用，准备遗弃，请使用host中对应接口
        '''
        XCUITestAgentManager.stop_all_agents()
    
    @lazy
    def agent(self):
        '''延迟初始化agent
        '''
        return self.agent_manager.get_agent(self.udid)

    @rpc_method
    def start_agent(self, agent_ip=DEFAULT_IP, agent_port=DEFAULT_PORT, keep_alive=False, retry=3, timeout=55):
        '''启动Agent，只支持设备主机使用，本地运行不使用该接口
        '''
        self._agent_port = agent_port
        self.agent_manager.start_agent(self.udid, agent_ip, agent_port, keep_alive, retry, timeout)

    @rpc_method
    def restart_agent(self):
        '''重启Agent，只支持设备主机使用，本地运行不使用该接口
        '''
        self.agent_manager.restart_agent(self.udid)

    @rpc_method
    def stop_agent(self):
        '''关闭Agent
        '''
        self.agent_manager.stop_agent(self.udid)
          
    @rpc_method
    def install(self, file_path):
        '''通过udid指定真机安装IPA或模拟器安装APP(注意：真机所用IPA不能在模拟器上安装和使用，IPA与APP相互不兼容)
        
        :param file_path: IPA或APP安装包的路径(注意：当前Mac机必须能访问到该路径)
        :type file_path: str
        :returns: boolean -- True if successfully installed, False if not
        '''
        try :
            dt = DT()
            dt.install(file_path, self.udid)
            return True
        
        except (AttributeError, lockdown.StartServiceError) :
            # 删除 ~/.pymobiledevice中的plist文件          
            dir_user = os.path.expanduser('~')
            dir_plist = os.path.join(dir_user,'.pymobiledevice')
            for root ,dirs ,files in os.walk(dir_plist):  #@UnusedVariable
                for name in files :
                    if name.startswith(self.udid):
                        os.remove(os.path.join(root, name))
                        
            try:
                if not self._isagent_working() :
                    raise RuntimeError('start agent error')
                dt.install(file_path, self.udid)
                return True
            
            except lockdown.NotTrustedError :
                rules = [
                    # 处理信任弹框
                    {
                        'message_text' : '要信任此电脑吗',
                        'button_text'  : '^信任$|^Allow$|^不信任$'
                    },
                ]       
                env = {
                      'rules_of_alert_auto_handle' : rules,
                      'flag_alert_auto_handled'    : True
                    }
                self.agent.execute(Command.QTA_ALERT_DISMISS, env)
                if dt.install(file_path, self.udid) :
                    return True
                raise 
            
        except :
            if dt.install_error == "" :
                import traceback
                dt.install_error = traceback.format_exc()
            raise RuntimeError("install error: %s" % dt.install_error.encode('utf8'))
        
    def _isagent_working(self):
        '''检查当前Agent是否在工作
        '''
        response = self.agent.execute(Command.HEALTH)
        return response['value'] == 'XCTestAgent is ready'

    @rpc_method
    def get_xcode_version(self):
        '''查询Xcode版本
        
        '''
        return DT().get_xcode_version()

    @rpc_method
    def get_ios_version(self):
        '''查询ios版本
        
        '''
        return DT().get_device_by_udid(self.udid)['ios']

    @rpc_method
    def uninstall(self, bundle_id):
        '''通过udid指定设备卸载指定bundle_id的APP
        
        :param bundle_id: APP的bundle_id，例如"tencent.com.sng.test.gn"
        :type bundle_id: str
        :returns: boolean -- if uninstall app successfully, False if not
        '''
        dt = DT()
        if dt.uninstall(bundle_id, self.udid):
            return True
        raise RuntimeError("uninstall error: %s" % dt.uninstall_error.encode('utf8'))
    
    @rpc_method
    def reboot(self):
        '''重启手机
        
        :param device_udid: 设备的udid
        :type device_udid: str
        '''
        return DT().reboot(self.udid)
    
    @rpc_method
    def start_app(self, bundle_id, app_params=None, env=None, trace_template=None, trace_output=None, retry=3, timeout=55):
        '''启动设备上的指定APP
        
        :param bundle_id: 要启动的APP的Bundle ID
        :type bundle_id: str
        :param app_params: APP 使用的参数
        :type app_params: dict
        :param trace_template: 专项测试使用trace_template的路径
        :type trace_template: str
        :param trace_output: 专项测试使用trace_output
        :type trace_output: str
        :param retry: 启动失败重试次数
        :type retry: int
        :param timeout: 单次启动超时 (秒)
        :type timeout: int
        :returns: boolean -- True if start successfully , or raise exception
        ''' 
        desired_caps = {}
        desired_caps['bundleId'] = bundle_id
        ios_version = DT().get_device_by_udid(self.udid)['ios']
        if DT.compare_version(ios_version, '12.0') >= 0:
            app_list = []
            for app in DT().list_apps(self.udid, 'all'):
                app_list.extend(app.keys())
            if bundle_id not in app_list:
                raise Exception("Failed to launch application, %s not exist" % bundle_id)
        if app_params:
            params_list = []
            for k in app_params:
                params_list.append("-%s %s" % (k, app_params[k]))
            desired_caps['arguments'] = params_list
        for _ in range(retry):
            try:
                self.agent.execute(Command.START, desired_caps)
                break
            except XCTestAgentTimeoutException:
                self.restart_agent()
        else:
            raise XCTestAgentTimeoutException('Failed to start app: %s' % bundle_id)       
        if env:
            self.agent.execute(Command.QTA_ALERT_RULES_UPDATE, env)
        return True
    
    @rpc_method
    def stop_app(self, bundle_id):
        '''停止指定app
        
        :returns: boolean -- True if start successfully, False if not
        '''
        return self.agent.execute(Command.QUIT)
    
    @rpc_method
    def get_rect(self):
        '''获取设备屏幕大小
        
        :returns: 坐标和高宽
        '''
        return {
            'origin': {'y': 0, 'x': 0},
            'size'  : self.agent.execute(Command.GET_WINDOW_SIZE)['value'],
        }
    
    @rpc_method
    def get_model(self):
        '''获取设备模型(iPhone/iPad)
        :returns: str
        '''
        if self.agent.has_session():
            return self.agent.capabilities['device']
        else:
            return self.agent.execute(Command.STATUS)['value']['os']['name']
    
    @rpc_method
    def get_name(self):
        '''获取设备名
        
        :returns: str
        '''
        raise NotImplementedError
    
    @rpc_method
    def get_system_version(self):
        '''获取系统版本(9.3.2)
        
        :returns: str
        '''
        return self.agent.execute(Command.STATUS)['value']['os']['version']
    
    @rpc_method
    def capture_screen(self):
        '''截屏
        
        :returns: str -- base64编码后截图数据
        '''
        try:
            base64_img = self.agent.capture_screen()
            if base64_img is None:
                base64_img = self.agent.execute(Command.SCREENSHOT)['value'].encode('ascii')
            else:
                base64_img = base64_img['value']
        except:
            filename = '/tmp/%s.png' % uuid.uuid1()
            if self.agent.type == EnumDevice.Simulator:
                version = DT().get_xcode_version()
                if version >= '8':
                    cmd = ['xcrun', 'simctl', 'io', self.udid,'screenshot',filename]
                    p = subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE, stderr=subprocess.PIPE,shell=False)
                    p.communicate()
                    retcode = p.poll()
                    if retcode != 0:
                        raise Exception("simulator screenshot error")
                else:
                    raise Exception("simulator screenshot error: Xcode version less than 8 does not support")
            elif not mobiledevice.get_screenshot(self.udid, filename):
                raise Exception("mobiledevice screenshot error")
            with open(filename, "rb") as fd:
                base64_img = base64.b64encode(fd.read())
            os.remove(filename)
        return base64_img

    @rpc_method
    def get_element_tree(self):
        '''从顶层开始获取UI树字典
        
        :returns: dict
        '''
        result = self.agent.execute(Command.GET_ELEMENT_TREE)['value']['tree']
        return convert_to_qpath(result)
    
    @rpc_method
    def get_element_tree_and_capture_screen(self, filepath=None):
        '''获取UI树并截屏(该接口仅限UISpy使用)
        
        :param filepath: 将图片存储至该路径（png格式）
        :type filepath: str
        :returns: dict : { element_tree: {}, capture_screen: file_path }
        '''
        result = {}
        result['element_tree'] = self.get_element_tree()
        result['capture_screen'] = self.capture_screen(filepath)
        return result

    @rpc_method
    def set_alert_auto_handling_rules(self, rules):
        '''设置自动处理Alert规则
        
                    当message_text匹配到Alert框内的任意文本，则点击button_text指定的按钮。
                    文本以段为单元，元素的label、name、value分为三段文本。规则匹配范围是Alert框内的所有元素的文本。
        :param rules: 规则集合
        :type rules: list - [ {"message_text": "message_text", "button_text": "button_text"}, ... ]
        '''
        self.agent.execute(Command.QTA_ALERT_RULES_UPDATE, rules)

    @rpc_method
    def get_alert_auto_handling_rules(self):
        '''获取已设置的自动处理Alert规则
        
        :returns: list - [ {"message_text": "message_text", "button_text": "button_text"}, ... ]
        '''
        raise NotImplementedError

    @rpc_method
    def add_alert_auto_handling_rule(self, message_text, button_text):
        '''自动处理Alert规则，添加一项规则
        
        :param message_text: Alert内文本片段，支持正则表达式（范围是所谓文本，每个元素的label/name/value为文本段）
        :type message_text: str
        :param button_text: Alert内按钮的文本，支持正则表达式（元素的label/name/value）
        :type button_text: str
        '''
        raise NotImplementedError

    @rpc_method
    def clear_alert_auto_handling_rules(self):
        '''自动处理Alert规则，清空所有规则
        '''
        raise NotImplementedError

    @rpc_method
    def disable_alert_auto_handling(self):
        '''关闭自动关闭alert框
        '''
        raise NotImplementedError
    
    @rpc_method
    def enable_alert_auto_handling(self):
        '''打开自动关闭alert框(优先级低于set_alert_auto_handling_rules所设置的策略)
        '''
        raise NotImplementedError
    
    @rpc_method
    def background_app(self, seconds=3):
        '''将App置于后台一定时间
        
        :param seconds: 秒
        :type seconds: int
        '''
        self.agent.execute(Command.DEACTIVATE_APP, {'duration':seconds})
    
    @rpc_method
    def click(self, x, y, options=None):
        '''单击（全局操作）
        
        :param x: 横向坐标（从左向右，屏幕百分比）
        :type x: float
        :param y: 纵向坐标（从上向下，屏幕百分比）
        :type y: float
        :param options: 屏幕操作扩展参数
        :type options: dict
        '''
        self.agent.execute(Command.QTA_DEVICE_CLICK, {'x':x, 'y':y, 'options':options})['value']
    
    @rpc_method
    def double_click(self, x, y):
        '''双击（全局操作）
        
        :param x: 横向坐标（从左向右，屏幕百分比）
        :type x: float
        :param y: 纵向坐标（从上向下，屏幕百分比）
        :type y: float
        '''
        self.agent.execute(Command.QTA_DEVICE_DOUBLE_CLICK, {'x':x, 'y':y})['value']
    
    @rpc_method
    def long_click(self, x, y, seconds=3):
        '''长按
        :param x: 横向坐标（从左向右，屏幕百分比）
        :type x: float
        :param y: 纵向坐标（从上向下，屏幕百分比）
        :type y: float
        :param seconds: 秒
        :type seconds: int
        '''
        self.agent.execute(Command.QTA_DEVICE_LONG_CLICK, {'x':x, 'y':y, 'duration':seconds})['value']
    
    @rpc_method
    def drag(self, x0, y0, x1, y1, duration=0.1, repeat=1, interval=1, velocity=1000):
        '''拖拽（全局操作）
        :param x0: 起始横向坐标（从左向右，屏幕百分比）
        :type x0: float
        :param y0: 起始纵向坐标（从上向下，屏幕百分比）
        :type y0: float
        :param x1: 终止横向坐标（从左向右，屏幕百分比）
        :type x1: float
        :param y1: 终止纵向坐标（从上向下，屏幕百分比）
        :type y1: float
        :param duration: 起始坐标按下的时间（秒）
        :type duration: float
        '''
        self.agent.execute(Command.QTA_DEVICE_DRAG, 
                {'x0':x0, 'y0':y0, 'x1':x1, 'y1':y1, 'duration':duration, 
                 'repeat':repeat, 'interval':interval, 'velocity':velocity})['value']
    
    @rpc_method
    def pinch(self, x0, y0, x1, y1, opposing=True, seconds=1):
        '''捏合/展开
        :param x0: 起始横向坐标（从左向右，屏幕百分比）
        :type x0: float
        :param y0: 起始纵向坐标（从上向下，屏幕百分比）
        :type y0: float
        :param x1: 终止横向坐标（从左向右，屏幕百分比）
        :type x1: float
        :param y1: 终止纵向坐标（从上向下，屏幕百分比）
        :type y1: float
        :param opposing: True为展开；False为捏合
        :type opposing: boolean
        :param seconds: 秒
        :type seconds: int
        '''
        raise NotImplementedError
    
    @rpc_method
    def rotate(self, x, y, options=None):
        '''旋转
        
        :param x: 横向坐标（从左向右，屏幕百分比）
        :type x: float
        :param y: 纵向坐标（从上向下，屏幕百分比）
        :type y: float
        :param options     : 自定义项
        :type options      : dict : {
                            :           duration    : 1,    持续的时间（秒）
                            :           radius      : 50,   半径
                            :           rotation    : 100,  圆周，默认是圆周率PI
                            :           touchCount  : 2     触摸点数量 2 - 5
                            :          }
        '''
        raise NotImplementedError
    
    @rpc_method
    def set_location(self, coordinates, options=None):
        '''设置设备的GPS坐标
        
        :param _coordinates : 经纬度
        :type _coordinates  : dict : {
                            :           latitude    : 100, // 以度为单位的纬度。正值表示纬度赤道以北。负值表示纬度赤道以南。
                            :           longitude   : 100  // 以度为单位的经度。测量是相对于零子午线，用正值向东延伸的经络及经络的负值西侧延伸。
                            :          }
        '''
        raise NotImplementedError
    
    @rpc_method
    def shake(self):
        '''摇晃设备
        '''
        raise NotImplementedError
    
    @rpc_method
    def volume(self, cmd):
        '''调高音量
        '''
        self.agent.execute(Command.QTA_DEVICE_VOLUME, {'value':cmd})
    
    @rpc_method
    def screen_direction(self, direct):
        '''调高音量
        '''
        self.agent.execute(Command.QTA_DEVICE_SCREEN_DIRECTION, {'value':direct})
        
    @rpc_method
    def siri(self, cmd):
        ''' siri交流
        '''
        self.agent.execute(Command.QTA_DEVICE_SIRI, {'value':cmd}) 
    
    @rpc_method
    def unlock(self):
        '''解锁设备
        '''
        self.agent.execute(Command.QTA_DEVICE_UNLOCK)
    
    @rpc_method
    def lock(self, seconds=0):
        '''锁定设备
        
        :param seconds: 秒, 0表示锁定设备；大于0表示锁定一段时间后解锁
        :type seconds: int
        '''
        self.agent.execute(Command.QTA_DEVICE_LOCK)
        
    @rpc_method
    def send_keys(self, keys):
        '''键盘输入
        
        :param keys: 键入的字符串
        :type keys: str
        '''
        self.agent.execute(Command.QTA_DEVICE_SENDKEYS, {'value':keys})['value']
    
    @rpc_method
    def get_driver_log(self, start_time=None):
        '''获取driver日志
        
        :parm start_time 用例执行的开始时间
        :type str
        '''
        driver_log_name = 'xctest_%s' % self.udid
        
        return self._read_to_log(driver_log_name, start_time)

    @rpc_method
    def get_crash_log(self, procname):
        '''通过设备的udid的获取指定进程的最新的crash日志
        
        :param proc_name: app的进程名，可通过xcode查看
        :type proc_name: str        
        :returns: str
        '''
        return DT().get_crash_log(self.udid, procname)
    
    @rpc_method
    def get_log(self, start_time=None):
        '''获取日志信息
        
        :parm start_time 用例执行的开始时间
        :type str
        '''
        
        log_name = 'driverserver_%s' % self.udid
        
        return self._read_to_log(log_name, start_time)
    
    def _read_to_log(self, log_name, start_time):
        '''获取日志内容
        
        :parm end_time 用例结束的时间
        :type time(默认为None，则表示切割的存放日志整个都有效)
        :param log_name 日志名称
        :type str
        :parm start_time 用例执行的开始时间
        :type str
        '''
        #兼容client端为旧版本，server端为新版本，只返回当前文件的日志（日志会过多或过少）
        if not start_time:
            with open(get_logger_path_by_name(log_name)) as fd:
                return fd.read()
        
        log = ''
        log_tmp = ''
        is_log_tmp = '' #当前文件的顶部没时间匹配的待确定是否属于日志内容
        pattern = r'^\[(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})'
        flag = False #标记该时间段的日志是否已经取完
        is_flag = False #标记取到的未匹配时间的行是否属于日志内容
        start_time = str_to_time(start_time)
        files = os.listdir(logger.TMP_DIR_PATH)
        
        for f in files:
            log_path = os.path.join(logger.TMP_DIR_PATH, f)
            if not flag and os.path.exists(log_path) and f.find(log_name) != -1:
                with open(log_path, "rb") as fd:
                    for line in fd:
                        line = line.decode("utf-8")
                        match = re.search(pattern, line)
                        if match:
                            cur_time = str_to_time(match.group(1))
                            if cur_time < start_time:
                                flag = True
                                is_log_tmp = ''
                                continue
                            elif cur_time == start_time and is_log_tmp:
                                is_log_tmp = ''
                                log_tmp += line
                            else:
                                is_flag = True
                                log_tmp += line
                        elif is_flag:
                            log_tmp += line
                        else:
                            is_log_tmp += line
                log_tmp = is_log_tmp + log_tmp
                log = log_tmp + log
                log_tmp = ''
        return log
    
    @rpc_method
    def cleanup_log(self):
        '''清理日志
        '''
        clean_expired_log("driverserver_%s" % self.udid)
        clean_expired_log('xctest_%s' % self.udid)
    
    @rpc_method
    def push_file(self, bundle_id, localpath, remotepath):
        '''拷贝Mac本地文件到iOS设备sandbox的指定目录
        
        :param bundle_id: app的bundle id
        :type bundle_id: str   
        :param localpath: Mac上的文件路径
        :type localpath: str
        :param remotepath: sandbox上的目录，例如：/Library/Caches/test/
        :type remotepath: str        
        :returns: boolean
        '''
        return DT().push_file(self.udid, bundle_id, localpath, remotepath)
    
    @rpc_method
    def download_file_and_push(self, bundle_id, file_url, remotepath):
        '''支持URL上传文件到IOS设备sandbox的指定目录
        
        :param bundle_id: app的bundle id
        :type bundle_id: str
        :parameter file_url 文件下载链接
        :type file_url: str
        :param remotepath: sandbox上的目录，例如：/Library/Caches/test/
        :type remotepath: str
        :returns: boolean
        '''
        filename = os.path.basename(file_url)
        if not os.path.exists(TMP_LOAD_FILE):
            os.mkdir(TMP_LOAD_FILE)
        localpath = os.path.join(TMP_LOAD_FILE, filename)
        flag = False
        
        try:
            r = urlopen(file_url)
            with open(localpath, "wb") as wd:
                while True:
                    s = r.read(1024*1024*10)
                    if not s:
                        break
                    wd.write(s)
            flag = self.push_file(bundle_id, localpath, remotepath)
        except Exception:
            logger.get_logger("xctest_%s" % self.udid).exception("download_file_and_push")
        finally:
            if os.path.exists(localpath):
                os.remove(localpath)
            return flag
    
    @rpc_method
    def get_sandbox_file_content(self, bundle_id, file_path):
        '''获取sandbox中文本文件的内容
        
        :param bundle_id: 应用的bundle_id
        :type bundle_id: str
        :param file_path: 沙盒目录
        :type file_path: str
        '''
        return DT().get_sandbox_file_content(self.udid, bundle_id, file_path)

    @rpc_method
    def pull_file(self, bundle_id, remotepath, localpath='/tmp', is_dir=False, is_delete = False):
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
        return DT().pull_file(self.udid, bundle_id, remotepath, localpath, is_dir, is_delete)
    
    @rpc_method
    def list_files(self, bundle_id, file_path):
        '''列出手机上指定app中的文件或者目录
        
        :param bundle_id: app的bundle id
        :type bundle_id: str 
        :param file_path: sandbox的目录，例如: /Documents/
        :type file_path: str  
        '''
        response = self.agent.execute(Command.QTA_SANDBOX_LIST, {'path':file_path})
        if not isinstance(response, dict) or response['status'] == ErrorCode.QT4I_STUB_NOT_EXIST:
            file_list = DT().get_sandbox_path_files(self.udid, bundle_id, file_path)
            if not DT().is_simulator(self.udid):
                DT().close_sandbox_client()
        else:
            file_list = response['value']
        return file_list
    
    @rpc_method
    def remove_files(self, bundle_id, file_path):
        '''删除手机上指定app中的文件或者目录
        
        :param bundle_id: app的bundle id
        :type bundle_id: str 
        :param file_path: 待删除的文件或者目录，例如: /Documents/test.log
        :type file_path: str  
        '''
        response = self.agent.execute(Command.QTA_SANDBOX_REMOVE, {'path':file_path})
        if not isinstance(response, dict) or response['status'] == ErrorCode.QT4I_STUB_NOT_EXIST:
            DT().remove_files(self.udid, bundle_id, file_path)
    
    @rpc_method
    def get_syslog(self, watchtime, processName=None):
        '''获取手机系统日志
        
        :parm watchtime : 观察时间
        :type watchtime : int
        :parm processName : 手机服务名称(默认为全部查看)
        :type processName : str
        :returns: str
        '''
        if not os.path.isdir(TMP_DIR_PATH):
            os.mkdir(TMP_DIR_PATH)
        logFile = os.path.join(TMP_DIR_PATH, "sys_%s.log" %self.udid)         
        DT().get_syslog(watchtime, logFile, processName, self.udid)
        log = ''
        with open(logFile, 'rb') as fd:
            for line in fd:
                log += line
        return log

    @rpc_method
    def get_foreground_app_name(self):
        return self.agent.execute(Command.QTA_GET_FOREGROUND_APP_NAME)['value']
    
    @rpc_method
    def get_foreground_app_pid(self):
        return self.agent.execute(Command.QTA_GET_FOREGROUND_APP_PID)['value']
    
    @rpc_method
    def get_screen_orientation(self):
        orientation = self.agent.execute(Command.GET_SCREEN_ORIENTATION)['value']
        orientation_number = 0
        if orientation == 'PORTRAIT':
            orientation_number = 1
        elif orientation == 'UIA_DEVICE_ORIENTATION_PORTRAIT_UPSIDEDOWN':  
            orientation_number = 2
        elif orientation == 'LANDSCAPE':
            orientation_number = 3    
        elif orientation == 'UIA_DEVICE_ORIENTATION_LANDSCAPERIGHT': 
            orientation_number = 4
        return  orientation_number 
    
    @rpc_method
    def get_app_list(self, app_type):
        return DT().list_apps(self.udid, app_type)
    
    @rpc_method
    def get_sandbox_path_files(self, bundle_id, file_path):
        '''返回真机或者模拟器的沙盒路径
        
        :param bundle_id: 应用的bundle_id
        :type bundle_id: str
        :param file_path: 沙盒目录
        :type file_path: str
        '''
        return DT().get_sandbox_path_files(self.udid, bundle_id, file_path)

    @rpc_method
    def is_sandbox_path_dir(self, bundle_id, file_path):
        '''判断一个sandbox路径是否是一个目录
        
        :param bundle_id: 应用的bundle_id
        :type bundle_id: str
        :param file_path: 沙盒目录
        :type file_path: str
        '''
        return DT().is_sandbox_path_dir(self.udid, bundle_id, file_path)
    
    @rpc_method
    def close_sandbox_client(self):
        '''销毁sandboxClient对象
        '''
        DT().close_sandbox_client()
        
    @rpc_method
    def upload_photo(self, photo_data, album_name, cleared=True):
        '''上传照片到系统相册
        
        :param photo_data: base64编码后的数据
        :type photo_data: str
        :param album_name: 系统相册名
        :type album_name : str
        :param cleared: 是否清空已有的同名相册
        :type cleared : boolean
        :returns: boolean
        '''
        params = {'image':photo_data, 'albumName':album_name, 'cleared':cleared}
        response = self.agent.execute(Command.QTA_ALBUM_UPLOAD, params)
        if not isinstance(response, dict) or response['status'] == ErrorCode.QT4I_STUB_NOT_EXIST:
            return False
        else:
            return response['value']
        
    @rpc_method
    def call_qt4i_stub(self, method, params, clazz=None):
        '''QT4i Stub通用接口
        
        :param method: 函数名
        :type method : str
        :param params: 函数参数
        :type params : list
        :returns: str
        '''
        if clazz:
            params = {'method':method, 'params':params, 'object':clazz}
        else:
            params = {'method':method, 'params':params}
        
        if method.startswith('createFile'):
            url = "%s/stub" % self.agent.stub_server_url
            request = Request(url, data=json.dumps(params))
            response = urlopen(request)
            result = response.read() 
            result = json.loads(result)
            return result['result']
        
        response = self.agent.execute(Command.QTA_STUB_CALL, params)
        if not isinstance(response, dict) or response['status'] == ErrorCode.QT4I_STUB_NOT_EXIST:
            raise Exception('QT4i Stub not exist')
        else:
            res = response['value']
            if res['result']:
                return res['data']
            else:
                raise Exception('method not implemented in QT4i Stub')
            
    @rpc_method
    def get_device_detail(self):
        '''获取设备详细信息
        '''
        is_simulator = DT().is_simulator(self.udid)
        device_type = self.agent.execute(Command.QTA_DEVICE_DETAIL_INFO)['value']
        return DeviceProperty.get_property(device_type, is_simulator)


class Application(RPCEndpoint):
    '''UIAApplication API
    '''
    rpc_name_prefix = "app."

    def __init__(self, rpc_server, device_id):
        self.rpc_server = rpc_server
        self.udid = device_id
        RPCEndpoint.__init__(self)
    
    @lazy
    def agent(self):
        '''延迟初始化agent
        '''
        agent_manager = XCUITestAgentManager()
        if agent_manager.has_agent(self.udid):
            return agent_manager.get_agent(self.udid)
        else:
            return None

    @rpc_method
    def get_app_bundle_id(self):
        '''获取当前App的BundleID
        
        :returns: str
        '''
        if self.agent and self.agent.has_session():
            return self.agent.capabilities['CFBundleIdentifier']
    
    @rpc_method
    def get_app_version(self):
        '''获取App的Version
        
        :returns: str
        '''
        raise NotImplementedError

    @rpc_method
    def has_crashed(self): 
        '''当前App是否发生crash
        
        :returns: boolean
        '''
        if self.agent:
            return self.agent.get_crash_flag()
        return False
    

class Element(RPCEndpoint):
    '''UIAElement API
    '''
    rpc_name_prefix = "element."

    def __init__(self, rpc_server, device_id):
        self.rpc_server = rpc_server
        self.udid = device_id
        RPCEndpoint.__init__(self)
    
    @lazy
    def agent(self):
        '''延迟初始化agent
        '''
        agent_manager = XCUITestAgentManager()
        if agent_manager.has_agent(self.udid):
            return agent_manager.get_agent(self.udid)
        else:
            return None
    
    @rpc_method
    def find_element(self, locator, timeout=3, interval=0.005, strategy=By.QPATH, parent_id=None):
        '''查找单个element对象，返回查找到的element对象的缓存id，不指定parent_id则从Application下开始搜索。
        
        :param locator: 定位element的字符串，例如: "/classname='UIAWindow'"
        :type locator: str
        :param timeout: 查找element的超时值（单位: 秒）
        :type timeout: float
        :param interval: 在查找element的超时范围内，循环的间隔（单位: 秒）
        :type interval: float
        :param strategy: locator的类型，例如: "qpath", "xpath", "id", "name"
        :type strategy: str
        :param parent_id: 父element的id，如不指定则从UIAApplication下查找
        :type parent_id: str
        :returns: dict : {'element': id, 'path': <encode str>, 'valid_path_part': <encode str>, 'invalid_path_part': <encode str>, 'find_count': <int>, "find_time": int}
        '''
        result = self.find_elements(locator, timeout, interval, strategy, parent_id)
        if result['elements']:
            result.update(result['elements'][0])
        else:
            result['element'] = None
        result.pop('elements')
        return result
    
    @rpc_method
    def find_elements(self, locator, timeout=3, interval=0.005, strategy=By.QPATH, parent_id=None):
        '''查找单个element对象，返回查找到的element对象的缓存id。不指定parent_id则从UIAApplication下开始搜索。
        
        :param locator: 定位element的字符串，例如: "/classname='UIAWindow'"
        :type locator: str
        :param timeout: 查找element的超时值（单位: 秒）
        :type timeout: float
        :param interval: 在查找element的超时范围内，循环的间隔（单位: 秒）
        :type interval: float
        :param strategy: locator的类型，例如: "qpath", "xpath", "id", "name"
        :type strategy: str
        :param parent_id: 父element的id，如不指定则从UIAApplication下查找
        :type parent_id: int
        :returns: dict : {'elements': [{'element':id, 'attributes':<encode str>}], 'path': <encode str>, 'valid_path_part': <encode str>, 'invalid_path_part': <encode str>, 'find_count': <int>, "find_time": int}
        '''
        if strategy == "qpath":
            #解析QPath
            qpath_array, qpath_lex = QPathParser().parse(locator)
            for node in qpath_array:
                if 'classname' in node:
                    if node['classname'][1] in UIA_XCT_MAPS.keys():
                        node['classname'][1] = UIA_XCT_MAPS[node['classname'][1]]
            locator_value = qpath_array
            valid_path = None
            invalid_path = None
        else:
            locator_value = locator
        start_time = time.time()
        elements = []
        count = 0
        parent_id = parent_id if parent_id else 1
        while True:
            before_step_time = time.time()
            count += 1
            response = self.agent.execute(Command.QTA_FIND_ELEMENTS,
                                {'using': strategy, 'value': locator_value, 'id':parent_id})
            elements = response['value']
            after_step_time = time.time()
            step_time = after_step_time - before_step_time
            if elements or after_step_time - start_time >= timeout:
                break
            if interval > 0:
                sleep_time = interval - step_time
                if sleep_time > 0:
                    time.sleep(sleep_time)
        if elements:
            elements = [{'element': int(e['ELEMENT'])} for e in elements]
            if strategy == "qpath":
                valid_path = locator
                invalid_path = ""
        else:
            if strategy == "qpath":
                valid_path_index = response['info']['index']
                locations = []
                if valid_path_index + 1 < len(qpath_lex):
                    valid_path_index = valid_path_index + 1
                for _ in qpath_lex[valid_path_index].values():
                    locations.extend(_)
                locations.sort()
                valid_index = locations[0] - 1 
                valid_path = locator[0:valid_index]
                invalid_path = locator[valid_index+1:]
        find_time = int((time.time() - start_time)*1000)
        result = {'elements':elements, 
                  'find_count':count,
                  'find_time':find_time}
        if strategy == "qpath":
            result['valid_path_part'] = valid_path
            result['invalid_path_part'] = invalid_path
        return result

    @rpc_method
    def find_element_with_predicate(self, element_id, predicate):
        '''通过predicate文本获取第一个匹配的子element
        
        :param element_id: element的id
        :type element_id: int
        :param predicate: 预期子element的predicate （例如：“name beginswith 'xxx'”）
        :type predicate: str
        :returns: int or None
        '''
        try:
            element = self.agent.execute(Command.FIND_CHILD_ELEMENT, {'id':element_id, 'using':By.PREDICATE_STRING, 'value':predicate})['value']
            if 'ELEMENT' in element:
                return int(element['ELEMENT'])
        except NoSuchElementException:
            return

    @rpc_method
    def find_elements_with_predicate(self, element_id, predicate):
        '''通过predicate文本获取所有匹配的子element
        
        :param element_id: element的id
        :type element_id: int
        :param predicate: 预期子element的predicate （例如：“name beginswith 'xxx'”）
        :type predicate: str
        :returns: list - [id1, id2, id3...]
        '''
        try:
            elements = self.agent.execute(Command.FIND_CHILD_ELEMENTS, {'id':element_id, 'using':By.PREDICATE_STRING, 'value':predicate})['value']
            if type(elements) == type([]):
                return [{'element': int(e['ELEMENT'])} for e in elements]
        except NoSuchElementException:
            return []

    @rpc_method
    def find_element_with_value_for_key(self, element_id, key, value):
        '''通过匹配指定key的value，获取第一个匹配的子element
        
        :param element_id: element的id
        :type element_id: int
        :param key: key （例如：label、name、value）
        :type key: str
        :param value: 对应key的value值
        :type value: str
        :returns: int or None
        '''
        try:
            element = self.agent.execute(Command.FIND_CHILD_ELEMENT, {'id':element_id, 'using':By.LINK_TEXT, 'value':'%s=%s' %(key, value)})['value']
            if 'ELEMENT' in element:
                return int(element['ELEMENT'])
        except NoSuchElementException:
            return

    @rpc_method
    def find_elements_with_value_for_key(self, element_id, key, value):
        '''通过匹配指定key的value，获取所有匹配的子element
        
        :param element_id: element的id
        :type element_id: int
        :param key: key （例如：label、name、value）
        :type key: str
        :param value: 对应key的value值
        :type value: str
        :returns: list - [id1, id2, id3...]
        '''
        try:
            elements = self.agent.execute(Command.FIND_CHILD_ELEMENTS, {'id':element_id, 'using':By.LINK_TEXT, 'value':'%s=%s' %(key, value)})['value']
            if type(elements) == type([]):
                return [{'element': int(e['ELEMENT'])} for e in elements]
        except NoSuchElementException:
            return []
    
    @rpc_method
    def get_element_tree(self, element_id, max_depth=0):
        '''获取指定element的所有子孙element树
        
        :param element_id: element的id
        :type element_id: int
        :param max_depth: 树的深度, 默认为0，获取所有子孙控件树
        :type max_depth: int
        :returns: dict
        '''
        if element_id == 1:
            result = self.agent.execute(Command.GET_ELEMENT_TREE)['value']['tree']
        else:
            result = self.agent.execute(Command.QTA_ELEMENT_TREE, 
                {'id': element_id, 'max_depth':max_depth})['value']['tree']
        return convert_to_qpath(result)
    
    @rpc_method
    def get_parent_element(self, element_id):
        '''获取指定element的父element的id
        
        :param element_id: element的id
        :type element_id: int
        :returns: int
        '''
        if element_id == 1:
            raise Exception("Current element is already root element.")
        element =  self.agent.execute(Command.QTA_GET_PARENT_ELEMENT, {'id': element_id})['value']
        if 'ELEMENT' in element:
            return int(element['ELEMENT'])
    
    @rpc_method
    def get_children_elements(self, element_id):
        '''获取指定element的子elements集合
        
        :param element_id: element的id
        :type element_id: int
        :returns: list : [int, ...]
        '''
        elements = self.agent.execute(Command.QTA_GET_CHILDREN_ELEMENTS, {'id': element_id})['value']
        if type(elements) == type([]):
            return [int(e['ELEMENT']) for e in elements]
        return []
    
    @rpc_method
    def get_rect(self, element_id):
        '''获取指定element的坐标和长宽
        
        :param element_id: element的id
        :type element_id: int
        :return: dict : 坐标和长宽
        '''
        if element_id == 1:
            format_rect = {
                'origin': {'x': 0, 'y': 0},
                'size'  : self.agent.execute(Command.GET_WINDOW_SIZE)['value'],
            }
        else:
            rect = self.agent.execute(Command.GET_ELEMENT_RECT, {'id': element_id})['value']
            format_rect = {
                'origin': {'x': rect['x'], 'y': rect['y']},
                'size'  : {'width': rect['width'], 'height': rect['height']},
            }
        return format_rect
    
    @rpc_method
    def capture(self, element_id, filepath=None):
        '''截图（截取指定element的图片，并将图片输出至指定的路径）
        
        :param element_id: element的id
        :type element_id: int
        :param filepath: 将图片存储至该路径（png格式），不传路径 或 路径仅含文件名，则截图后存储至默认路径。
        :type filepath: str
        :returns: str
        '''
        raise NotImplementedError
    
    @rpc_method
    def click(self, element_id, x=0.5, y=0.5, options=None):
        '''点击指定的element
        
        :param element_id: element的id
        :type element_id: int
        :param x: x坐标（相对于当前element），可不传入该参数
        :type x: float
        :param y: y坐标（相对于当前element），可不传入该参数
        :type y: float
        '''
        if x is None:
            x = 0.5
        if y is None:
            y = 0.5
        if element_id == 1:
            self.agent.execute(Command.QTA_DEVICE_CLICK, {'x':x, 'y':y, 'options':options})['value']
        else:     
            self.agent.execute(Command.QTA_ELEMENT_CLICK, 
                {'id':element_id, 'x':x, 'y':y, 'options':options})['value']
    
    @rpc_method
    def double_click(self, element_id, offset_x=0.5, offset_y=0.5):
        '''双击指定的element
        
        :param element_id: element的id
        :type element_id: int
        '''
        if element_id == 1:
            self.agent.execute(Command.QTA_DEVICE_DOUBLE_CLICK, {'x':0.5, 'y':0.5})['value']
        else:
            self.agent.execute(Command.QTA_ELEMENT_DOUBLE_CLICK, {'id':element_id, 'x':offset_x, 'y':offset_y})['value']
    
    @rpc_method
    def drag(self, element_id, x0, y0, x1, y1, duration=0.1):
        '''控件内部拖拽
        
        :param element_id: element的id
        :type element_id: int
        :param x0: 起始横向坐标（从左向右，屏幕百分比）
        :type x0: float
        :param y0: 起始纵向坐标（从上向下，屏幕百分比）
        :type y0: float
        :param x1: 终止横向坐标（从左向右，屏幕百分比）
        :type x1: float
        :param y1: 终止纵向坐标（从上向下，屏幕百分比）
        :type y1: float
        :param duration: 起始坐标按下的时间（秒）
        :type duration: float
        '''
        if element_id == 1:
            self.agent.execute(Command.QTA_DEVICE_DRAG, 
                {'x0':x0, 'y0':y0, 'x1':x1, 'y1':y1,'duration':duration})['value']
        else:
            self.agent.execute(Command.QTA_ELEMENT_DRAG, 
                {'id':element_id, 'x0':x0, 'y0':y0, 'x1':x1, 'y1':y1,'duration':duration})['value']
    
    @rpc_method
    def tap(self, element_id, options):
        '''拂去/拖拽等自定义操作
        
        :param element_id: element的id
        :type element_id: int
        :param options     : 自定义项
        :type options      : dict : {
                            :           touchCount   : 1,                    // 触摸点
                            :           duration     : 0.5,                  // 时间
                            :           startOffset  : { x: 0.0, y: 0.1},    // 偏移百分比
                            :           endOffset    : { x: 1.0, y: 0.1 },   // 偏移百分比
                            :           repeat       : 1                     // 重复该操作
                            :           interval     : 0                     // 重复该操作的间隙时间（秒）
                            :        }
        '''
        raise NotImplementedError
    
    @rpc_method
    def rotate(self, element_id, options):
        '''旋转
        
        :param element_id: element的id
        :type element_id: int
        :param _options     : 自定义项
        :type _options      : dict : {
                            :           centerOffset : {x:0.0, y:0.0},   // 中心点
                            :           duration     : 1.5,              // 持续时间
                            :           radius       : 100,              // 半径
                            :           rotation     : 100,              // 旋转弧度的长度，默认为圆周率PI
                            :           touchCount   : 2                 // 触摸点（最大5个点，这里默认2个）
                            :          }
        '''
        raise NotImplementedError
    
    @rpc_method
    def scroll_to_visible(self, element_id, rate=1.0):
        '''自动滚动到该element为可见
        
        :param element_id: element的id
        :type element_id: int
        '''
        self.agent.execute(Command.QTA_SCROLL_TO_VISIBLE, {'id':element_id, 'velocity':rate})
    
    @rpc_method
    def long_click(self, element_id, offset_x=0.5, offset_y=0.5, seconds=3):
        '''持续按住
        
        :param element_id: element的id
        :type element_id: int
        :param seconds: 秒
        :type seconds: int
        '''
        if element_id == 1:
            self.agent.execute(Command.QTA_DEVICE_LONG_CLICK, {'x':0.5, 'y':0.5, 'duration':seconds})['value']
        else:
            self.agent.execute(Command.QTA_ELEMENT_LONG_CLICK, {'id':element_id, 'x':offset_x, 'y':offset_y, 'duration':seconds})['value']
    
    @rpc_method
    def wait_for_invalid(self, element_id, seconds=5):
        '''等待当前element直到无效
        
        :param element_id: element的id
        :type element_id: int
        :param seconds: 秒
        :type seconds: int
        :returns: boolean
        '''
        raise NotImplementedError
    
    @rpc_method
    def set_value(self, element_id, value):
        '''设置指定element的value
        
        :param element_id: element的id
        :type element_id: int
        :param value: 值
        :type value: str
        '''
        self.agent.execute(Command.QTA_ELEMENT_SETVALUE, {'id':element_id, 'value':value})['value']
    
    @rpc_method
    def drag_to_value(self, element_id, value):
        '''slider滑到指定位置(0-1之间)
        
        :param element_id: element的id
        :type element_id: int
        :param value: 值
        :type value: str
        '''
        self.agent.execute(Command.QTA_DRAG_TO_VALUE, {'id':element_id, 'value':value})
        
    @rpc_method
    def send_keys(self, element_id, keys):
        '''在指定element中键盘输入
        
        :param element_id: element的id
        :type element_id: int
        :param keys: 键入的字符串
        :type keys: str
        '''
        if element_id == 1 :
            return self.agent.execute(Command.QTA_DEVICE_SENDKEYS, {'value':keys})['value']
        else:
            return self.agent.execute(Command.QTA_ELEMENT_SENDKEYS, {'id':element_id, 'value':keys})['value']
    
    @rpc_method
    def get_element_attrs(self, element_id):
        '''获取指定element的属性信息
        
        :param element_id: element的id
        :type element_id: int
        :returns: str: dict
        '''
        attrs = self.agent.execute(Command.QTA_GET_ELEMENT_ATTRS, {'id': element_id})['value']
        return self._convert_attrs(attrs)
    
    def _convert_attrs(self, attrs):
        '''转译属性名称及对应值
        '''
        if 'type' in attrs:
            attrs['classname'] = attrs['type']
            attrs.pop('type')
        if 'isEnabled' in attrs:
            attrs['enabled'] = (attrs['isEnabled'] == '1')
            attrs.pop('isEnabled')
        if 'isVisible' in attrs:
            attrs['visible'] = (attrs['isVisible'] == '1')
            attrs.pop('isVisible')
        children = []
        for child in attrs.get('children', []):
            children.append(self._convert_attrs(child))
        attrs['children'] = children
        return attrs
    
    @rpc_method
    def get_element_attr(self, element_id, attr_name):
        '''获取指定element的属性信息
        
        :param element_id: element的id
        :type element_id: int
        :param attr_name: 属性名
        :type attr_name: str
        :returns: str or boolean or None
        '''
        return self.agent.execute(Command.GET_ELEMENT_ATTRIBUTE, {'id': element_id, 'name': attr_name})['value']
    
    @rpc_method
    def get_element_win_info(self, element_id):
        '''获取指定element的窗口信息
        
        :param element_id: element的id
        :type element_id: int
        :returns: dict
        '''
        return self.agent.execute(Command.QTA_GET_ELEMENT_WIN_INFO, {'id': element_id})['value']
    
    @rpc_method
    def select_picker_wheel(self, element_id, value):
        '''设置PickerWheel的选项
        
        :param element_id: element的id
        :type element_id: int
        :param value: 选项
        :type value: str
        '''
        self.agent.execute(Command.QTA_WHEEL_SELECT, {'id':element_id, 'value':value})['value']

    @rpc_method
    def force_touch(self, element_id, pressure, duration):
        self.agent.execute(Command.FORCE_TOUCH, 
            {'id':element_id, 'pressure':pressure, 'duration':duration})['value']