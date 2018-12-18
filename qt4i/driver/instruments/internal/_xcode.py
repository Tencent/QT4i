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
'''此模块用于归纳Xcode
'''
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
from __future__ import absolute_import, print_function

import os, re
from qt4i.driver.util import FileManager
from qt4i.driver.util import Task
from qt4i.driver.util import ThreadTask
CurrentDirectoryPath = os.path.abspath(os.path.dirname(__file__))
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

class Xcode(object):
    
    DeveloperPath = Task("xcode-select -p").execute()
    InstrumentsPath = Task("xcrun -f instruments").execute()
    InstrumentsTracetemplatePath = os.path.join(CurrentDirectoryPath, '_tracetemplate')
    InstrumentsTraceTemplatesPath = {'xcode5_default' : os.path.abspath('%s/../Applications/Instruments.app/Contents/PlugIns/AutomationInstrument.bundle/Contents/Resources/Automation.tracetemplate' % DeveloperPath),
                                     'xcode6_default' : os.path.abspath('%s/../Applications/Instruments.app/Contents/PlugIns/AutomationInstrument.xrplugin/Contents/Resources/Automation.tracetemplate' % DeveloperPath)}

    def __init__(self):
        self.instruments_command = None

    def __get_instruments_path__(self, simulator=False):
        return self.InstrumentsPath

    def __get_instruments_trace_templates_path__(self):
        _items = FileManager(self.InstrumentsTracetemplatePath).get_children()
        for _item in _items:
            _cur_name, _cur_ext = os.path.splitext(os.path.basename(_item))
            if re.match('^.tracetemplate$', _cur_ext, re.I):
                self.InstrumentsTraceTemplatesPath.update({_cur_name:_item})
        return self.InstrumentsTraceTemplatesPath
    
    def __get_instruments_trace_template__(self, _name_or_abspath=None):
        if _name_or_abspath and os.path.exists(_name_or_abspath):
            return _name_or_abspath
        _trace_templates_path = self.__get_instruments_trace_templates_path__()
        _trace_template = _trace_templates_path.get(_name_or_abspath)
        if _trace_template and os.path.exists(_trace_template):
            return _trace_template
        else:
            for _name in ['xcode6_default', 'xcode5_default']:
                _trace_template = _trace_templates_path.get(_name)
                if os.path.exists(_trace_template):
                    return _trace_template
        if None == _trace_template or False == os.path.exists(_trace_template):
            raise Exception('tracetemplate is invalid')
    
    def start_instruments(self, device_udid, device_simulator, bundle_id, uia_script, uia_results_path, trace_template=None, started_callback=None, stdout_line_callback=None, stderr_line_callback=None, return_code_callback=None, cwd=None, env=None, print_enable=False, **args):
        if not os.path.exists(self.InstrumentsPath):
            raise Exception('instruments is invalid.')
        if device_udid is None:
            raise Exception('device_udid is invalid.')
        if bundle_id is None:
            raise Exception('bundle_id is invalid.')
        if uia_script is None or os.path.exists(uia_script) == False:
            raise Exception('uia_script is invalid.')
        if uia_results_path is None or os.path.exists(uia_results_path) == False:
            raise Exception('uia_results_path is invalid.')
        instruments = self.__get_instruments_path__(device_simulator)
        trace_template = self.__get_instruments_trace_template__(trace_template)
        cwd = cwd or CurrentDirectoryPath
                 
        self.instruments_command = " ".join([
                            '%s' % instruments,
                            '-w "%s"' % device_udid,
                            '-t "%s"' % trace_template,
                            '' if args['trace_output'] is None else '-D "%s"' % args['trace_output'],
                            '"%s"' % bundle_id,
                            '-e UIASCRIPT "%s"' % uia_script,
                            '-e UIARESULTSPATH "%s"' % uia_results_path,
                            '-v',
                            args['params'] if 'params' in args else ''
                           ])
        return ThreadTask(self.instruments_command, started_callback, stdout_line_callback, stderr_line_callback, return_code_callback, cwd, env, print_enable)
