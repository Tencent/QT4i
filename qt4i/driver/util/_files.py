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
'''此模块用于归纳基础通用子模块
'''

import os, re, stat, shutil
from past.builtins import xrange


class FileManager(object):
    '''文件相关操作类
    '''
    
    def __init__(self, path):
        self.path = os.path.abspath(path)
    
    def exists(self):
        return os.path.exists(self.path)
    
    def repair_path(self, path=None):
        path = os.path.abspath(path or self.path)
        if not os.path.exists(path): os.makedirs(path)
        return os.path.exists(path)
    
    def __sort_by_ctime__(self, items):
        length = len(items)
        for i in xrange(length - 1, 0, -1):
            flag = 0
            for j in xrange(0, i):
                ctime1 = os.path.getctime(items[j])
                ctime2 = os.path.getctime(items[j + 1])
                if ctime1 > ctime2:
                    items[j], items[j + 1] = items[j + 1], items[j]
                    flag += 1
            if flag == 0 : break;
        return items
    
    def get_children(self, path=None, recursion=False, sort_by_ctime=False, name_filter=['.DS_Store']):
        items, path = [], os.path.abspath(path or self.path)
        if recursion:
            for dirpath, dirnames, filenames in os.walk(path) : items += [os.path.join(dirpath, name) for name in dirnames + filenames if name not in name_filter and not re.match('|'.join(name_filter), name, re.IGNORECASE)]
        else  : items = [os.path.join(path, item) for item in os.listdir(path) if item not in name_filter and not re.match('|'.join(name_filter), item, re.IGNORECASE)]
        if sort_by_ctime : items = self.__sort_by_ctime__(items)
        return items
    
    def force_delete(self, path=None):
        path = os.path.abspath(path or self.path)
        if path is None or os.path.exists(path) == False : return
        if os.path.isfile(path):
            os.chmod(path, stat.S_IWRITE)
            os.remove(path)
            return
        try    : shutil.rmtree(path)
        except :
            del_dir_paths = []
            for dirpath, dirnames, filenames in os.walk(path): #  #@UnusedVariable
                try    : shutil.rmtree(dirpath)
                except :
                    del_dir_paths.append(dirpath)
                    for filename in filenames:
                        del_file_path = os.path.join(dirpath, filename)
                        os.chmod(del_file_path, stat.S_IWRITE)
                        os.remove(del_file_path)
            del_dir_paths.sort(reverse=True)
            for del_dir_path in del_dir_paths:
                os.chmod(del_dir_path, stat.S_IWRITE)
                os.rmdir(del_dir_path)
    
    def force_copy_to(self, dst):
        # if os.path.exists(dst) and os.path.isdir(dst):
        #    dst = os.path.join(dst, os.path.basename(self.path))
        if os.path.exists(dst):
            self.force_delete(dst)
        self.repair_path(os.path.dirname(dst))
        if os.path.isfile(self.path):
            shutil.copy(self.path, dst)
        if os.path.isdir(self.path):
            shutil.copytree(self.path, dst)

def zip_decompress(zip_file, output_dir):
    '''解压zip文件到指定目录
    
    :param zip_file: 需解药的zip文件路径
    :param output_dir: 解压后保存的目录路径
    '''
    import zipfile
    if not zipfile.is_zipfile(zip_file):
        raise Exception('not support to decompress non-zipfile')
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, 0o777)
        
    f_zip = zipfile.ZipFile(zip_file, 'r')
    f_zip.extractall(output_dir)
    f_zip.close()