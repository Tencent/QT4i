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
'''UIAutomation和XCTest的控件映射表
'''
import six

from tuia.qpathparser import QPathParser


XCT_UIA_MAPS = {
    'Any': 'UIAElement',
    'Other': 'UIAElement',
    'Application':'UIAApplication',
    'Group': 'UIATableGroup',
    'Window': 'UIAWindow',
    'Sheet': 'UIAActionSheet',
    'Alert': 'UIAAlert',
    'Button': 'UIAButton',
    'Keyboard': 'UIAKeyboard',
    'Key': 'UIAKey',
    'NavigationBar': 'UIANavigationBar',
    'TabBar': 'UIATabBar',
    'Toolbar': 'UIAToolbar',
    'StatusBar': 'UIAStatusBar',
    'Table': 'UIATableView',
    'CollectionView': 'UIACollectionView',
    'Slider': 'UIASlider',
    'PageIndicator': 'UIAPageIndicator',
    'ProgressIndicator': 'UIAProgressIndicator',
    'Popover': 'UIAPopover',
    'ActivityIndicator': 'UIAActivityIndicator',
    'SegmentedControl': 'UIASegmentedControl',
    'Picker': 'UIAPicker',
    'PickerWheel': 'UIAPickerWheel',
    'Switch': 'UIASwitch',
    'Link': 'UIALink',
    'Image': 'UIAImage',
    'SearchField': 'UIASearchBar',
    'ScrollView': 'UIAScrollView',
    'StaticText': 'UIAStaticText',
    'TextField': 'UIATextField',
    'SecureTextField': 'UIASecureTextField',
    'TextView': 'UIATextView',
    'Menu': 'UIAEditingMenu',
    'MenuItem': 'UIAElement',
    'Map': 'UIAMapView',
    'WebView': 'UIAWebView',
    'Cell': 'UIATableCell',
}

UIA_XCT_MAPS = {
    'UIAElement':'Other',
    'UIAApplication':'Application',
    'UIATableGroup':'Group',
    'UIAWindow':'Window',
    'UIAActionSheet':'Sheet',
    'UIAAlert':'Alert',
    'UIAButton':'Button',
    'UIAKeyboard':'Keyboard',
    'UIAKey':'Key',
    'UIANavigationBar':'NavigationBar',
    'UIATabBar':'TabBar',
    'UIAToolbar': 'Toolbar',
    'UIAStatusBar':'StatusBar',
    'UIATableView':'Table',
    'UIACollectionView':'CollectionView',
    'UIASlider':'Slider',
    'UIAPageIndicator':'PageIndicator',
    'UIAProgressIndicator':'ProgressIndicator',
    'UIAPopover':'Popover',
    'UIAActivityIndicator':'ActivityIndicator',
    'UIASegmentedControl':'SegmentedControl',
    'UIAPicker':'Picker',
    'UIAPickerWheel':'PickerWheel',
    'UIASwitch':'Switch',
    'UIALink':'Link',
    'UIAImage':'Image',
    'UIASearchBar':'SearchField',
    'UIAScrollView':'ScrollView',
    'UIAStaticText':'StaticText',
    'UIATextField':'TextField',
    'UIASecureTextField':'SecureTextField',
    'UIATextView':'TextView',
    'UIAEditingMenu':'Menu',
    'UIAMapView':'Map',
    'UIAWebView':'WebView',
    'UIATableCell':'Cell',
}

def xctest2instruments(locator):
    qpath_array, _ = QPathParser().parse(locator)
    for node in qpath_array:
        if 'classname' in node:
            if node['classname'][1] in XCT_UIA_MAPS.keys():
                node['classname'][1] = XCT_UIA_MAPS[node['classname'][1]]
    new_locator = ''   
    for node in qpath_array:
        new_locator += '/'
        properties = []
        for p in node.keys():
            if isinstance(node[p][1], six.string_types):
                value = node[p][1]
                if six.PY2 and isinstance(node[p][1], unicode):
                    value = value.encode('utf-8')
                node_str = "{}{}\'{}\'".format(p, node[p][0], value)   
            else:
                node_str = "{}{}{}".format(p, node[p][0], node[p][1]) 
            properties.append(node_str)
        properties = ' & '.join(properties)
        new_locator += properties.decode('utf-8')
    return new_locator
