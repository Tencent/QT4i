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
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
'''JSON扩展'''
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
import json
import six
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

class Json(object):
    
    def __encode__(self, obj, encoding):
        if isinstance(obj, dict):
            _dict = {}
            for _key, _value in obj.items():
                if isinstance(_value, (dict, list)): _dict.update({_key.encode(encoding):self.__encode__(_value, encoding)})
                elif isinstance(_value, six.string_types): _dict.update({_key.encode(encoding):_value.encode(encoding)})
                else: _dict.update({_key.encode(encoding):_value})
            return _dict
        if isinstance(obj, list):
            _list = []
            for _item in obj:
                if isinstance(_item, (dict, list)): _list.append(self.__encode__(_item, encoding))
                elif isinstance(_item, six.string_types): _list.append(_item.encode(encoding))
                else: _list.append(_item)
            return _list
     
    def loads(self, s, encoding='UTF-8'):
        return self.__encode__(json.loads(s), encoding)
 
    def dumps(self, obj, indent=4):
        return json.dumps(obj, indent=indent)
 
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
