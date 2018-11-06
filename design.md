# QT4i框架原理

QT4i是基于JSON-RPC和[QTAF](https://github.com/Tencent/QTAF)实现的C/S架构的iOS UI自动化测试框架，整体架构如下所示。

```
+------------------------------------------------------------+
|                                                            |
|                    QT4i API (client)                       |
|                                                            |
|                                                            |
+------------------------------+-----------------------------+
                               |
                               |   JSONRPC
+------------------------------+-----------------------------+
|                    QT4i Driver (server)                    |
|                                                            |
+-------------+ +------------+ +-------------+ +-----------+ |
||            | |            | |             | |           | |
|| instruments| |   XCTest   | | WebInspector| | DT Driver | |
||    Driver  | |   Driver   | |    Driver   | |           | |
||            | |            | |             | |           | |
+-------------+ +------------+ +-------------+ +-----------+ |
|                                                            |
+-----------------------------+------------------------------+
                              |
                              |
+-----------------------------+------------------------------+
|                      iOS Device(real/Simulator)            |
| +--------------------------------+   +-------------------+ |
| |                                |   |                   | |
| | QT4iStub(Optional)   APP       |   |    XCTestAgent    | |
| |                                |   |                   | |
| +--------------------------------+   +-------------------+ |
+------------------------------------------------------------+
```


自上而下依次是API层、驱动层和设备层。

### API层
**API层**是提供给用户编写脚本的接口，包含Device、App、Element等基础控件的定义和封装, 由于是JSONRPC的client，有效屏蔽底层的实现细节，可以灵活支持跨平台(MacOS/Windows)执行。

### 驱动层
**驱动层**是QT4i的核心层，向上提供API层接口的具体实现，按照功能区分为如下四个Driver。

 * XCTest Driver:基于XCTest框架的UI控件查找和操作的驱动层，其中底层XCTestAgent是基于[WebDriverAgent](https://github.com/facebook/WebDriverAgent)扩展实现。
 * WebInspector Driver:基于iOS WebInspector的调试协议的Webview控件驱动层，提供基于xpath的Webview页面的查找能力和JavaScript的注入能力。
 * DT Driver:基于[pymobiledevice-qta](https://github.com/qtacore/pymobiledevice)和xcode命令行工具的设备能力扩展层，提供安装卸载app、访问设备沙盒、查看iOS设备列表、App列表等设备相关的接口。
 * instrument Driver (Deprecated):基于instruments框架的UI控件查找和操作的驱动层，在Xcode9及以下版本支持。

### 设备层
**设备层**提供了XCTest Driver的底层代理（XCTestAgent）和App进程内的动态插桩的能力扩展（QT4iStub）。

