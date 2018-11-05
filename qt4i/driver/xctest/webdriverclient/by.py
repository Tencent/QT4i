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
'''控件定位策略
'''

class By(object):
    """
    Set of supported locator strategies.
    """

    ID = "id"
    NAME = "name"
    QPATH = "qpath"
    XPATH = "xpath"
    TAG_NAME = "tag name"
    LINK_TEXT = "link text"
    CLASS_NAME = "class name"
    PREDICATE_STRING = "predicate string"
    PARTIAL_LINK_TEXT = "partial link text"

    @classmethod
    def is_valid(cls, by):
        for attr in dir(cls):
            if by == getattr(cls, attr):
                return True
        return False