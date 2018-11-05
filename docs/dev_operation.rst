常见设备操作
======

在iOS自动化过程中，避免不了的是对设备的各种操作，如将当前App退到后台、滑动窗口、屏幕点击、音量调节等，现针对常见的设备操作进行解析，更多的功能请参考接口文档。

====
点击屏幕
====

如果你想直接基于屏幕进行点击操作，可以直接调用 :class:`qt4i.device.Device` 中定义的click()方法::

    device = Device()
    device.click()

默认点击屏幕正中间。

.. warning:: 通常情况下请优先使用QT4i各个控件类型提供的click接口去点击，只有在特殊情况下不方便使用该接口才改为点击屏幕固定坐标的方式。

====
模拟按键
====

iOS设备上有很多虚拟按键，如HOME键、音量键等，QT4A封装了常见的按键，在用例中实例化App类后可以获得app对象::

   device = Device()

然后可以模拟发送各类按键，如home键 ::
   
   device.deactivate_app_for_duration(seconds=-1)   #seconds为-1时，则模拟按Home键的效果; seconds传入整数值,可以将当前App置于后台一定时间
   
重启键::

   device.reboot() #重启

锁屏和解屏键::

   device.lock()   #锁屏
   device.unlock()  #解屏

音量调节(模拟器没有)::
    
   device._volume('up')  #调高音量

另外, :class:`qt4i.device.Device` 类封装的接口，还供siri交互，旋转屏幕等接口。
 
====
滑动屏幕
====

有时候你需要针对屏幕进行滑动，例如若App类开头有一些广告页面，需要滑动才会消失，那么可以调用::

    def drag(self, from_x=0.9, from_y=0.5, to_x=0.1, to_y=0.5, duration=0.5):
        '''回避屏幕边缘，全屏拖拽（默认在屏幕中央从右向左拖拽）
        
        :param from_x: 起点 x偏移百分比(从左至右为0.0至1.0)
        :type from_x: float
        :param from_y: 起点 y偏移百分比(从上至下为0.0至1.0)
        :type from_y: float
        :param to_x: 终点 x偏移百分比(从左至右为0.0至1.0)
        :type to_x: float
        :param to_y: 终点 y偏移百分比(从上至下为0.0至1.0)
        :type to_y: float
        :param duration: 持续时间（秒）
        :type duration: float
        '''
        
传入不同的坐标值,便可以实现上下左右，不同幅度的滑动。

====
屏幕截图
====

在执行用例过程中，有些场景需要截图下来帮助分析，可以调用接口::

    device = Device()
    device.screenshot(image_path='/User')
   
当然，QT4i在用例失败时也会截图保存App现场。如你还需其他截图，可自行调用。


   