=======
弹窗的自动处理
=======

QT4i提供了弹窗的自动处理机制，当被测App在用例执行中出现Alert弹窗时，可以通过在被测App的测试基类中
定义弹窗的处理规则来实现自动处理。

**弹窗处理规则说明:** 

1. 优先遍历用户定义的预期规则 ``rules_of_alert_auto_handle`` 处理（其中 ``message_text`` 表示Alert标题栏文字， ``button_text`` 表示Alert的按钮字段，两者均支持正则匹配）；
2. 如果1中定义的规则不满足，则按照flag_alert_auto_handled设置的规则处理；
3. 当 ``rules_of_alert_auto_handle`` 设置为True，但是又希望某个弹窗由用例中来处理，则可通过在 ``rules_of_alert_auto_handle`` 中添加只包含message_text的规则实现。


使用示例如下::
 
    class DemoApp(App):
        '''被测App基类
        '''
    
        def __init__(self, device, app_name=settings.APP_BUNDLE_ID, trace_template=None, trace_output=None):
            App.__init__(self, device, app_name, trace_template, trace_output)
            self.set_environment()
            self.start()

        def set_environment(self):
            '''配置自动处理Alert弹框规则
            '''
            self.rules_of_alert_auto_handle = [

                # 测试账号
                {
                    'message_text' : '测试号码',  # 支持正则表达式
                    'button_text'  : '^确定$'  # 支持正则表达式
                },

                # 退出登录
                {
                    'message_text': '退出登录', #屏蔽退出登录的自动处理
                },
            ]
            self.flag_alert_auto_handled = False


.. note:: 如果弹窗被处理了，但是预期的控件出现找不到的场景，可适当延长该控件的查找时间即可。