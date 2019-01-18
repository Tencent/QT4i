.. include:: ../links/link.ref

内嵌webview的自动化
=============

针对内嵌webview的iOS App， QT4i提供了两种UI自动化测试方案:基于原生控件树和基于H5页面DOM树的测试方案。

============
基于原生控件树的测试方案
============

基于原生控件树的测试方案也即把webview当做原生控件，按照QT4i的UI元素定义和封装，即可完成UI自动化测试，具体
可参考UI元素封装 :ref:`ui_encaps`。

===============
基于H5页面DOM树的测试方案
===============

基于原生控件树的测试方案在某些测试场景中可能存在一些不足，例如：控件ID缺失不方便定位控件，H5页面映射到原生控
件树导致一些控件元素丢失等等。因此，我们提出了基于H5页面DOM树的测试方案，该方案基于H5页面的DOM树进行UI控件
的查找定位，不依赖原生控件树，可以有效地解决原生控件树的问题。该测试方案的具体使用步骤如下：

- 通过操作原生控件，进入H5页面
- 实例化IOSWebView
- 封装WebPage
- 通过WebPage进行Web控件的查找和操作

-------------
IOSWebView的定义
-------------

:class:`qt4i.web.IOSWebView` 是QT4i实现的WebView类，提供iOS端的web控件的接口实现，包含获取webview坐标，
web控件的点击、滑动、长按、文本输入以及js注入等功能。用户需要通过原生控件的方式定义IOSWebView::

   from qt4i.icontrols import Window
   
   class BrowserWindow(Window):
       '''
       浏览器窗口基类
       '''
   
   
       def __init__(self, app):
           self._app = app
           Window.__init__(self, self._app)
           scroll_win = Window(self._app, "webroot")
           locators = {
               'webview' : {'type':IOSWebView, 'root':scroll_win, 'locator':'webview', 'url':'index', 'title':'demo'},
           }
           self.updateLocator(locators)

其中title和url是可选参数，默认都不提供的话，从WebInspector的缓存中获取第一个H5页面。

- title: 对应H5页面的 **document.title** 的内容
- url: 对应H5页面的 **location.href** 的内容, 支持正则表达式

----------
WebPage的封装
----------

一个WebPage对应一个H5页面，通常由一个 **ui_map** 字典组成，其中包含了对当前H5页面中的若干
web控件(WebElement)的定义，每个web控件的定义包含控件名、控件类型、locator、ui_map等属性。

.. list-table:: web控件的属性详解
   :widths: 15 5 30
   :header-rows: 1
   :align: center

   * - 属性名
     - 必选项
     - 描述
   * - 控件名
     - Y
     - 包含对web控件的文本描述，对应于字典中的key
   * - type
     - N
     - 控件类型，默认值为WebElement，如果需要定义成数组，需要使用ui_list(xxx)
   * - locator
     - Y
     - Web控件定位符，使用XPath描述
   * - ui_map
     - N
     - 定义当前Web控件的子控件的属性字典，可以嵌套，内容可以包含以上所有属性，包括"ui_map"
     
.. note:: web控件的XPath可以通过苹果官方的工具 `Safari Technology Preview <https://developer.apple.com/safari/technology-preview/>`_ 查看

下面的代码片段展示了一个WebPage的封装::

   from qt4w import XPath
   from qt4w.webcontrols import WebElement, WebPage, ui_list
   
   class LifePrivilegePage(WebPage):
       '''生活特权页面
       '''
       ui_map = {
           '限时福利列表': {
               'type': ui_list(WebElement),
               'locator': XPath('//div[@class="mod-list list-walfare"]/ul/li'),
               'ui_map':{
                   '名称': XPath('//div[@class="info"]/h3'),
                   '描述': XPath('//div[@class="info"]/p[1]'),
                   '我要抢': XPath('//p[@class="surplus-time"]/button')
               }  
           }
       }
       

.. note:: web控件的XPath可以通过苹果官方的工具 `Safari Technology Preview <https://developer.apple.com/safari/technology-preview/>`_ 查看


-----------
web控件的查找和操作
-----------

在介绍完成webview定义和WebPage封装之后，接下来就给大家讲解如何使用WebPage进行Web控件的查找和操作。
 
#. 首先进入App的H5页面
#. 初始化webview
#. 使用步骤2中的webview初始化WebPage
#. 使用control('控件名')的方式查找web控件
#. 基于WebElement提供的接口获取web控件的属性和对web控件进行点击等操作

下面的代码片段展示了Web控件的查找和操作的具体步骤::

    device = Device()
    app = DemoApp()
    app.enter_h5_page()                               #  进入H5页面
    webview = BrowserWindow(app).Controls['webview']  #  初始化webview
    page = LifePrivilegePage(webview)                 #  初始化WebPage
    for elem in page.control('限时福利列表'):           #  查找'限时福利列表'
        name = elem.control('名称').inner_text
        description = elem.control('描述').inner_text
   
WebPage和WebElement类提供了诸多Web相关接口(例如 :inner_text)可参考《|qt4w|_》的文档。
