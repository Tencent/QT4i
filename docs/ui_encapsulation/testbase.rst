.. include:: ../links/link.ref

.. _encap_testbase:

封装测试基类
======

======
测试基类概述
======

QTAF中实现的测试基类《|qtaf-testcase|_》提供了很多功能接口，如环境准备和清理、断言、日志相关等功能,详细见测试基类的相关说明。QT4i中的测试基类iTestBase重载了QTAF提供的测试基类，复用其功能，并扩展iOS需要的特定功能，如截图，获取crash日志等。

======
测试基类封装
======

目前qt4i的测试基类 :class:`qt4i.itestbase.iTestBase` 已经实现了iOS需要的常用功能。你可以在demolib/demotestbase.py中封装你的测试基类DemoTestBase，并且该类继承于iTestBase,即可使用iTestBase中已有功能，同时可重载各个接口扩展针对你测试项目的自定义的功能。例如可如下使用::
      
   from qt4i.itestcase import iTestCase
   from qt4i.device    import Device
   from testbase.conf import settings
   

   class DemoTestcase(iTestCase):
       '''Demo测试用例基类
       '''
   
       def pre_test(self):
           '''初始化测试用例
           '''
           super(iTestCase， self).pre_test()
           self.log_info("%s.pre_test "%self.__class__.__name__)
   
       def post_test(self):
           '''清理下测试用例
           '''
           super(iTestCase， self).post_test()
           self.clean_login()
           self.log_info("%s.post_test "%self.__class__.__name__)
           
       def clean_login(self):
           '''清理App的登录状态
           '''
           for device in Device.Devices:
               device.remove_file(settings.APP_BUNDLE_ID， "/Documents/contents/DemoAccountManager")   #被测App登录态文件的存储路径
 
即可实现测试用例的环境准备或环境清理功能。除了以上封装的基本功能，你可能还需使用或重载其他接口，如:

* ::根据进程名(可通过xcode查看)，获取App的crash日志::

   def get_crash_log(self, procname):  
   
* 每个步骤前自定义一些操作，例如每个步骤前都打印出时间戳，看出每个步骤耗时等，可以重载下面接口::

   def start_step(self, step):

等等，更多参考QTAF和QT4i接口文档。

.. warning:: 重载基类各个接口时，必须显式调用基类的函数，以免基类的逻辑无法被执行到。

======
测试基类使用
======

在用例中将该类作为测试用例的基类::
      
      class HelloTest(DemoTestBase):
      