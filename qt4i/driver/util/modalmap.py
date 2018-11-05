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
'''设备型号与设备信息映射
'''

class DeviceProperty(object):
    
    mapping_simulator_table = {   
        #iPhone SE
        'iPhone SE,N/A,N/A':'A1662, A1723, A1724',
        
        #iPhone 6
        'iPhone 6,N/A,N/A':'A1549, A1586, A1589',
        
        #iPhone 6 Plus
        'iPhone 6 Plus,N/A,N/A':'A1522, A1524, A1593',
        
        #iPhone 6s
        'iPhone 6s,N/A,N/A':'A1633, A1688, A1691, A1700',
        
        #iPhone 6s Plus
        'iPhone 6s Plus,N/A,N/A':'A1634, A1687, A1690, A1699',
        
        #iPhone 7
        'iPhone 7,N/A,N/A':'A1660, A1779, A1780, A1778',
        
        #iPhone 7 Plus
        'iPhone 7 Plus,N/A,N/A':'A1661, A1785, A1786, A1784',
        
        #iPhone 8
        'iPhone 8,N/A,N/A':'A1863, A1906, A1907, A1905',
        
         #iPhone 8 Plus
        'iPhone 8 Plus,N/A,N/A':'A1864, A1898, A1899, A1897',
        
        #iPhone X
        'iPhone X,N/A,N/A':'A1865, A1902, A1901',
        }
    
    mapping_real_table = {   
        #iPhone SE
        'iPhone SE,Gold,16GB':'MLXH2, MLXW2, MLY12, MLY52, MLY92, MLXM2',
        'iPhone SE,Gold,32GB' : 'MP8D2, MP8R2, MP8H2, MP8M2, MP7V2, MP842',
        'iPhone SE,Gold,64GB' : 'MLXK2, MLXY2, MLY32, MLY72, MLYC2, MLXP2',
        'iPhone SE,Gold,128GB': 'MP952, MP9J2, MP992, MP9E2, MP802, MP882',
        
        'iPhone SE,Rose Gold,16GB' : 'MLXJ2, MLXX2, MLY22, MLY62, MLYA2, MLXN2',
        'iPhone SE,Rose Gold,32GB' : 'MP8E2, MP8T2, MP8J2, MP8N2, MP7W2, MP852',
        'iPhone SE,Rose Gold,64GB' : 'MLXL2, MLY02, MLY42, MLY82, MLYD2, MLXQ2',
        'iPhone SE,Rose Gold,128GB': 'MP962, MP9K2, MP9A2, MP9F2, MP812, MP892',
        
        'iPhone SE,Silver,16GB' : 'MLLM2, MLLV2, MLLX2, MLM02, MLM32, MLLP2',
        'iPhone SE,Silver,32GB' : 'MP8C2, MP8Q2, MP8G2, MP8L2, MP7U2, MP832',
        'iPhone SE,Silver,64GB' : 'MLM52, MLMC2, MLME2, MLMG2, MLMJ2, MLM72',
        'iPhone SE,Silver,128GB': 'MP942, MP9H2, MP982, MP9D2, MP7Y2, MP872',
        
        'iPhone SE,Space Gray,16GB' : 'MLLL2, MLLU2, MLLW2, MLLY2, MLM22, MLLN2',
        'iPhone SE,Space Gray,32GB' : 'MP8A2, MP8P2, MP8F2, MP8K2, MP7T2, MP822',
        'iPhone SE,Space Gray,64GB' : 'MLM42, MLM62, MLMA2, MLMD2, MLMF2, MLMH2',
        'iPhone SE,Space Gray,128GB': 'MP932, MP9G2, MP972, MP9C2, MP7X2, MP862',
        
        #iPhone 6
        'iPhone 6,Gold,16GB' : 'MG3D2, MG492, MG4Q2, MG562, MG5Y2, MG6C2',
        'iPhone 6,Gold,64GB' : 'MG3L2, MG4J2, MG502, MG652, MG6J2, MG842',
        'iPhone 6,Gold,128GB': 'MG3G2, MG4E2, MG4V2, MG622',
        
        'iPhone 6,Silver,16GB' : 'MG3C2, MG4P2, MG482, MG5X2, MG552, MG6A2, MG7W2',
        'iPhone 6,Silver,64GB' : 'MG3K2, MG4H2, MG4X2, MG5C2, MG6H2, MG642, MG822',
        'iPhone 6,Silver,128GB': 'MG3F2, MG4C2',
        
        'iPhone 6,Space Gray,16GB': 'MG3A2, MG4N2, MG472, MG5W2, MG542, MG692',
        'iPhone 6,Space Gray,64GB': 'MG3H2, MG4F2, MG4W2, MG5A2, MG6G2, MG632',
        'iPhone 6,Space Gray,128GB': 'MG3E2, MG4A2, MG4R2, MG602',
        
        #iPhone 6 Plus
        'iPhone 6 Plus,Gold,16GB' : 'MGAA2, MGAN2, MGC12, MGCM2, MGCX2',
        'iPhone 6 Plus,Gold,64GB' : 'MGAK2, MGAW2, MGC72',
        'iPhone 6 Plus,Gold,128GB': 'MGAF2, MGAR2, MGC42, MGCQ2',
        
        'iPhone 6 Plus,Silver,16GB' : 'MGA92, MGC92, MGAM2, MGC02, MGCL2',
        'iPhone 6 Plus,Silver,64GB' : 'MGAJ2, MGAV2, MGC62',
        'iPhone 6 Plus,Silver,128GB': 'MGAE2, MGAQ2, MGC32',
        
        'iPhone 6 Plus,Space Gray,16GB': 'MGA82, MGAL2, MGAX2, MGCK2',
        'iPhone 6 Plus,Space Gray,64GB': 'MGAH2, MGAU2, MGC52, MGCR2',
        'iPhone 6 Plus,Space Gray,128GB': 'MGAC2, MGAP2, MGC22, MGCN2',
        
        #iPhone 6s
        'iPhone 6s,Gold,16GB' : 'MKQL2, MKQ72, MKR12, MKRE2, MKRW2, MKT92, ML7E2',
        'iPhone 6s,Gold,32GB' : 'MN0P2, MN172, MN1K2, MN1U2, MN1Y2',
        'iPhone 6s,Gold,64GB' : 'MKQC2, MKQQ2, MKR52, MKRJ2, MKT12, MKTE2, ML7J2',
        'iPhone 6s,Gold,128GB': 'MKQG2, MKQV2, MKR92, MKRP2, MKT52, MKTJ2, ML7N2',
        
        'iPhone 6s,Rose Gold,16GB' : 'MKQM2, MKQ82, MKRF2, MKRX2, MKR22, MKTA2, ML7F2',
        'iPhone 6s,Rose Gold,32GB' : 'MN0V2, MN192, MN1L2, MN1V2, MN202',
        'iPhone 6s,Rose Gold,64GB' : 'MKQD2, MKQR2, MKR62, MKRK2, MKT22, MKTF2, ML7K2',
        'iPhone 6s,Rose Gold,128GB': 'MKQH2, MKQW2, MKRA2, MKRQ2, MKT62, MKTK2, ML7P2',
        
        'iPhone 6s,Silver,16GB' : 'MKQ62, MKQK2, MKQY2, MKRD2, MKRT2, MKT82, ML7D2, NKQJ2',
        'iPhone 6s,Silver,32GB' : 'MN0N2, MN162, MN1G2, MN1Q2, MN1X2',
        'iPhone 6s,Silver,64GB' : 'MKQA2, MKQP2, MKR42, MKRH2, MKT02, MKTD2, ML7H2',
        'iPhone 6s,Silver,128GB': 'MKQF2, MKQU2, MKR82, MKRM2, MKT42, MKTH2, ML7M2',
        
        'iPhone 6s,Space Gray,16GB': 'MKQ52, MKQJ2, MKQX2, MKRC2, MKRR2, MKT72, ML7C2',
        'iPhone 6s,Space Gray,32GB': 'MN0M2, MN132, MN1E2, MN1M2, MN1W2',
        'iPhone 6s,Space Gray,64GB': 'MKQN2, MKQ92, MKR32, MKRG2, MKRY2, MKTC2, ML7G2',
        'iPhone 6s,Space Gray,128GB': 'MKQE2, MKQT2, MKR72, MKRL2, MKT32, MKTG2, ML7L2',
        
        #iPhone 6s Plus
        'iPhone 6s Plus,Gold,16GB' : 'MKTN2, MKU32, MKUN2, MKV62, MKVQ2, MKW72, ML6D2',
        'iPhone 6s Plus,Gold,64GB' : 'MKTT2, MKU82, MKUV2, MKVD2, MKVX2, MKWD2, ML6H2',
        'iPhone 6s Plus,Gold,128GB': 'MKTX2, MKUF2, MKV12, MKVH2, MKW22, MKWH2, ML6M2',
        
        'iPhone 6s Plus,Rose Gold,16GB' : 'MKU52, ML6E2, MKTP2, MKUP2, MKV72, MKVU2, MKW82',
        'iPhone 6s Plus,Rose Gold,64GB' : 'MKU92, ML6J2, MKTU2, MKUW2, MKVE2, MKVY2, MKWE2',
        'iPhone 6s Plus,Rose Gold,128GB': 'MKUG2, MKV22, ML6N2, MKVJ2, MKTY2',
        
        'iPhone 6s Plus,Silver,16GB' : 'MKTM2, MKU22, MKUJ2, MKV52, MKVP2, MKW62, ML6C2',
        'iPhone 6s Plus,Silver,64GB' : 'MKTR2, MKU72, MKUU2, MKV92, MKVW2, MKWC2, ML6G2',
        'iPhone 6s Plus,Silver,128GB': 'MKTW2, MKUE2, MKUY2, MKVG2, MKW12, MKWG2, ML6L2',
        
        'iPhone 6s Plus,Space Gray,16GB': 'MKU12, ML6A2, MKV32, MKTL2, MKUH2, MKVN2, MKW52',
        'iPhone 6s Plus,Space Gray,64GB': 'MKU62, ML6F2, MKTQ2, MKUQ2, MKV82, MKVV2, MKW92, ML642',
        'iPhone 6s Plus,Space Gray,128GB': 'MKUD2, ML6K2, MKTV2, MKUX2, MKVF2, MKW02, MKWF2',
        
        #iPhone 7
        'iPhone 7,black,32GB' : 'MN8G2, MNAC2, MNAY2, MNCE2, MNGQ2, MN9D2, MN9U2, MN8X2',
        'iPhone 7,black,128GB' : 'MN8L2, MNAJ2, MNC32, MNCK2, MNGX2, MN9H2, MN9Y2, MN922',
        'iPhone 7,black,256GB': 'MN8R2, MNAQ2, MNC82, MNCQ2, MN9N2, MNA62, MN972',
        
        'iPhone 7,Gold,32GB' : 'MN8J2, MNAE2, MNC12, MNCG2, MN9F2, MN9W2, MN902',
        'iPhone 7,Gold,128GB' : 'MN8N2, MNAL2, MNC52, MNCM2, MNH02, MN9K2, MNA32, MN942',
        'iPhone 7,Gold,256GB': 'MN8U2, MNAV2, MNCA2, MNCT2, MN9Q2, MNA82',
        
        'iPhone 7,Jet Black,128GB': 'MN8Q2, MNAP2, MNC72, MNCP2, MN9M2, MNA52, MN962',
        'iPhone 7,Jet Black,256GB': 'MN8W2, MNAX2, MNCD2, MNCV2, MN9T2, MNAA2, MN9C2',
        
        'iPhone 7,Red,128GB' : 'MPRV2, MPRT2, MPRH2, MPRL2, MPRN2, MPRQ2',
        'iPhone 7,Red,256GB' : 'MPRW2, MPRU2, MPRJ2, MPRM2, MPRP2, MPRR2',
        
        'iPhone 7,Rose Gold,32GB' : 'MN8K2, MNAF2, MNC22, MNCJ2, MN9G2, MN9X2, MN912',
        'iPhone 7,Rose Gold,128GB' : 'MN8P2, MNAM2, MNC62, MNH12, MNCN2, MN9L2, MNA42, MN952',
        'iPhone 7,Rose Gold,256GB': 'MN8V2, MNAW2, MNCC2, MNCU2, MN9R2, MNA92',
        
        'iPhone 7,Silver,32GB' : 'MN8H2, MNAD2, MNC02, MNCF2, MN9E2, MN9V2',
        'iPhone 7,Silver,128GB' : 'MN8M2, MNAK2, MNC42, MNCL2, MN9J2, MNA02',
        'iPhone 7,Silver,256GB': 'MN8T2, MNAU2, MNC92, MNCR2, MN9P2, MNA72',
        
        #iPhone 7 Plus
        'iPhone 7 Plus,black,32GB' : 'MNQH2, MNR12, MNR52, MNR92, MNRJ2, MNQR2, MNQW2, MNQM2',
        'iPhone 7 Plus,black,128GB' : 'MN482, MN5T2, MN642, MN6F2, MNFP2, MN522, MN5G2, MN4M2',
        'iPhone 7 Plus,black,256GB': 'MN4E2, MN5Y2, MN692, MN6L2, MNFV2, MN592, MN5M2, MN4W2',
        
        'iPhone 7 Plus,Gold,32GB' : 'MNQK2, MNR32, MNR72, MNRC2, MNRL2, MNQU2, MNQY2, MNQP2',
        'iPhone 7 Plus,Gold,128GB' : 'MN4A2, MN5V2, MN662, MN6H2, MNFR2, MN552, MN5J2, MN4Q2',
        'iPhone 7 Plus,Gold,256GB': 'MN4J2, MN612, MN6C2, MN6N2, MN5D2, MN5P2, MN4Y2',
        
        'iPhone 7 Plus,Jet Black,128GB': 'MN4D2, MN5X2, MN682, MN6K2, MN572, MN5L2, MN4V2',
        'iPhone 7 Plus,Jet Black,256GB': 'MN4L2, MN632, MN6E2, MN6Q2, MN5F2, MN5R2',
        
        'iPhone 7 Plus,Red,128GB' : 'MPR12, MPR02, MPQV2, MPQW2, MPQW2, MPQY2',
        'iPhone 7 Plus,Red,256GB' : 'MPRA2, MPR92, MPR52, MPR62, MPR72, MPR82',
        
        'iPhone 7 Plus,Rose Gold,32GB' : 'MNQL2, MNR42, MNR82, MNRD2, MNRM2, MNQV2, MNR02, MNQQ2',
        'iPhone 7 Plus,Rose Gold,128GB' : 'MN4C2, MN5W2, MN672, MN6J2, MNFT2, MN562, MN5K2, MN4U2',
        'iPhone 7 Plus,Rose Gold,256GB': 'MN4K2, MN622, MN6D2, MN6P2, MNFY2, MN5E2, MN5Q2',
        
        'iPhone 7 Plus,Silver,32GB' : 'MNQJ2, MNR22, MNR62, MNRA2, MNRK2, MNQT2, MNQX2, MNQN2',
        'iPhone 7 Plus,Silver,128GB' : 'MN492, MN5U2, MN652, MN6G2, MNFQ2, MN532, MN5H2, MN4P2',
        'iPhone 7 Plus,Silver,256GB': 'MN4F2, MN602, MN6A2, MN6M2, MN5C2, MN5N2, MN4X2, MN502',
        
        #iPhone8p
        'iPhone 8,Gold,64GB' : 'MQ6M2, MQ742, MQ772, MQ6J2, MQ6X2, MQ712',
        'iPhone 8,Gold,246GB': 'MQ7H2, MQ802, MQ832, MQ7E2, MQ7T2, MQ7W2',
        
        'iPhone 8,Silver,64GB' : 'MQ6L2, MQ732, MQ762, MQ6H2, MQ6W2, MQ702',
        'iPhone 8,Silver,256GB': 'MQ7G2, MQ7Y2, MQ822, MQ7D2, MQ7R2, MQ7V2',
        
        'iPhone 8,Space Gray,64GB': 'MQ6K2, MQ722, MQ752, MQ6G2, MQ6V2, MQ6Y2',
        'iPhone 8,Space Gray,256GB': 'MQ7F2, MQ7X2, MQ812, MQ7C2, MQ7Q2, MQ7U2',
        
        #iPhone8p
        'iPhone 8 Plus,Gold,64GB' : 'MQ8F2, MQ9F2, MQ982, MQ8N2, MQ8V2, MQ922',
        'iPhone 8 Plus,Gold,246GB': 'MQ8J2, MQ9C2, MQ9J2, MQ8R2, MQ8Y2, MQ952',
        
        'iPhone 8 Plus,Silver,64GB' : 'MQ8E2, MQ9E2, MQ972, MQ8M2, MQ8U2, MQ912',
        'iPhone 8 Plus,Silver,256GB': 'MQ8H2, MQ9A2, MQ9H2, MQ8Q2, MQ8X2, MQ942',
        
        'iPhone 8 Plus,Space Gray,64GB': 'MQ8D2, MQ9D2, MQ962, MQ8L2, MQ8T2, MQ902',
        'iPhone 8 Plus,Space Gray,256GB': 'MQ8G2, MQ9G2, MQ992, MQ8P2, MQ8W2, MQ932',
        
        #iPhoneX     
        'iPhone X,Silver,64GB' : 'MQCT2, MQCL2, MQAY2, MQA62, MQAK2, MQAR2, MQAD2',
        'iPhone X,Silver,256GB': 'MQCW2, MQCP2, MQC22, MQA92, MQAN2, MQAV2, MQAG2',
        
        'iPhone X,Space Gray,64GB': 'MQCR2, MQCK2, MQAX2, MQA52, MQAJ2, MQAQ2, MQAC2',
        'iPhone X,Space Gray,256GB': 'MQCV2, MQCN2, MQC12, MQA82, MQAM2, MQAU2, MQAF2',
        }

    @classmethod
    def get_property(cls, device_type, is_simulator):
        '''根据device_type,获取设备详细信息
        
        :param device_type : 设备型号
        :type device_type : str
        :param is_simulator : 模拟器
        :type is_simulator : bool
        
        :returns: attr - 设备属性字典
        '''
        attr = ''
        if is_simulator :
            dic = cls.mapping_simulator_table
        else :
            dic = cls.mapping_real_table
        for i in range(len(dic)):
            if attr != '' :
                break
            key = dic.keys()[i]
            value = dic[key]
            l = value.split(',')
            for i in l:
                if i.strip() == device_type:
                    attr = key
                    break
        if attr != '' :
            l = attr.split(',')
            attr = {
                    'model' : l[0],
                    'color' : l[1],
                    'storage' : l[2], 
                    }
        else :
            attr = {
                    'model' : 'Unknown',
                    'color' : 'N/A',
                    'storage' : 'N/A', 
                    }
        return attr