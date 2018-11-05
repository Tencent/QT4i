// QT4i-Instruments端-JavaScript-API

(function($) {
    UIAElementsCache = function() {
        this.caches = {};
        this.id = 0;
        this.append(UIATarget.localTarget().frontMostApp());
    };
    UIAElementsCache.prototype = {
        release_all : function() {
            this.caches = {};
        },
        release_invalid : function() {
            //for (var id in this.caches) {
            //    if (!this.caches[id].isValid()) {
            //        delete this.caches[id];
            //    };
            //};
        },
        release : function(id) {
            //var element = this.caches[id];
            //if (!element.isValid()) {
            //    delete this.caches[id];
            //};
        },
        append : function(element) {
            if (element == null || element.toString() == "[object UIAElementNil]") {
                return undefined;
            }
            var id = (this.id += 1);
            this.caches[id] = element;
            return id;
        },
        append_elements : function(elements) {
            var ids = new Array();
            for (var i = 0; i < elements.length; i++) {
                ids.push(this.append(elements[i]));
            };
            return ids;
        },
        set : function(id, element) {
            if (this.caches[id]) {
                this.caches[id] = element;
                return true;
            };
            return false;
        },
        get : function(id) {
            this.set(1, UIATarget.localTarget().frontMostApp());
            if ( typeof id == 'number') {
                var element = this.caches[id];
                if (element) {
                    //if (element.isValid()) {
                        return element;
                    //} else {
                    //    this.release(id);
                    //};
                };
            };
            if ( typeof id == 'string' && new RegExp(/^\/classname *\= *(\'|\")\w+(\'|\").*$/i).test(id)) {
                var element = $.QPath(id).findElement(0);
                if (element) {
                    return element;
                };
                throw new Error("element not found: " + id);
            };
            throw new Error("element id is invalid: " + id);
        }
    };
})($);

// -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

(function($) {

    var uia_elements_cache = new UIAElementsCache();

    var switch_locator = function(strategy, locator) {
        switch(strategy.toLocaleLowerCase()) {
            case 'qpath':
                return $.QPath(locator);
        };
    };

    var last_alert_msg = null;
    var flag_alert_auto_handled = Environment.flag_alert_auto_handled ? Environment.flag_alert_auto_handled : false;
    var rules_of_alert_auto_handle = Environment.rules_of_alert_auto_handle ? Environment.rules_of_alert_auto_handle : new Array();

    UIATarget.onAlert = function(alert) {
        alert.logElementTreeExt();
        $.log("enter onAlert flag_alert_auto_handled: "+$.str.objectToString(flag_alert_auto_handled))
        var texts = alert.getAllTexts();
        last_alert_msg = texts;
        var buttons = [];
        buttons = alert.getElementsByClassName('^UIAButton$');
        if (buttons.length == 0) {
            buttons = alert.getElementsByClassName('^UIACollectionCell$');
        };
        if (buttons.length == 0) {
            buttons = alert.getElementsByClassName('^UIATableCell$');
        };
        for (var rule_i = 0; rule_i < rules_of_alert_auto_handle.length; rule_i++) {
            var rule = rules_of_alert_auto_handle[rule_i];
            for (var text_i = 0; text_i < texts.length; text_i++) {
                var text = texts[text_i];
                if (rule.message_text == text || new RegExp(rule.message_text).test(text)) {
                    if (rule.button_text) {
                        for (var button_i = 0; button_i < buttons.length; button_i++) {
                            var button = buttons[button_i];
                            var button_texts = button.getAllTexts();
                            for (var button_text_i = 0; button_text_i < button_texts.length; button_text_i++) {
                                var button_text = button_texts[button_text_i];
                                if (rule.button_text == button_text || new RegExp(rule.button_text).test(button_text)) {
                                    button.tap();
                                    //for(var delay_i=0; delay_i<30; delay_i++){
                                    //    UIATarget.localTarget().delay(0.1);
                                    //    if (alert.isValid()==false){
                                    //        return true;
                                    //    };
                                    //};
                                    $.log("onAlert double matched: "+$.str.objectToString(flag_alert_auto_handled))
                                    return true;
                                };
                            };
                        };
                    };
                    $.log("onAlert single matched: "+$.str.objectToString(flag_alert_auto_handled))
                    return true;
                };
            };
        };
        $.log("onAlert no matched: "+$.str.objectToString(flag_alert_auto_handled))
        return flag_alert_auto_handled;
    };

    // -*- -*- -*- -*- -*- -*-

    api = {

        'DoNotReturn' : encodeURIComponent("<<<[[[DoNotReturn]]]>>>"),

        // -*- -*- -*- -*- -*- -*-

        'uia.release' : function(cmd_id) {
            /**
             * 终止并退出Driver
             * Returns
             *  'released'      - 终止完毕
             */
            return bootstrap.release();
        },

        'uia.set_cmd_fetch_delegate_timeout' : function(cmd_id, seconds) {
            /**
             * 设置cmd_fetch_delegate的超时值
             * Paramaters:
             *  seconds         - 秒
             */
            var seconds = parseInt(seconds);
            if (seconds > 0) {
                Environment.cmd_fetch_delegate_timeout = seconds;
            };
        },

        'uia.get_cmd_fetch_delegate_timeout' : function(cmd_id) {
            /**
             * 获取cmd_fetch_delegate的超时值
             * Returns
             *  seconds         - 秒
             */
            return Environment.cmd_fetch_delegate_timeout;
        },

        'uia.uia_elements_cache.release_all' : function(cmd_id) {
            /**
             * 清空所有的elements的缓存（异常时会自动清理，element无效时会自动清理）
             */
            uia_elements_cache.release_all();
        },

        'uia.uia_elements_cache.release_invalid' : function(cmd_id) {
            /**
             * 清空无效的element的缓存（异常时会自动清理，element无效时会自动清理）
             */
            uia_elements_cache.release_invalid();
        },

        'uia.uia_elements_cache.release_element' : function(cmd_id, id) {
            /**
             * 清理指定element的缓存
             * Paramaters:
             *  id              - element的id
             */
            uia_elements_cache.release(id);
        },

        'uia.front_most_app' : function(cmd_id) {
            return uia_elements_cache.append(UIATarget.localTarget().frontMostApp());
        },

        // -*- -*- -*- -*- -*- -*-

        'uia.element.function' : function(cmd_id, id, func, args) {
            /**
             * 调用指定element的原生函数（UIAElement）
             * Paramaters:
             *  id              - element的id
             *  func            - 函数名
             *  args            - 函数的有序参数集合
             * Returns:
             *  return value    - 被调用函数的返回值（基础类型）
             */
            var element = uia_elements_cache.get(id);
            var args = args ? args : [];
            if (element[func]) {
                return element[func].apply(element, args);
            };
            throw new Error('uia.element.function "func: ' + func + '" is invalid.');
        },

        'uia.element.is_valid' : function(cmd_id, id) {
            try {
                uia_elements_cache.get(id);
                return true;
            } catch(e) {
                return false;
            };
        },

        'uia.element.find' : function(cmd_id, locator, timeout, interval, strategy, parent_id) {
            /**
             * 查找单个element对象，返回查找到的element对象的缓存id。不指定parent_id则从UIAApplication下开始搜索。
             * 第一个对象永远是UIAApplication - 这是为了兼容Python层Window封装不写Path。
             * Paramaters:
             *  locator         - 定位element的字符串，例如: "/classname='UIAWindow'"
             *  parent_id       - 父element的id，如不指定则从UIAApplication下查找
             *  timeout         - 查找element的超时值（单位: 秒）
             *  strategy        - locator的类型，例如: "qpath"
             * Returns          - json: {'element': id, 'path': <encode str>, 'valid_path_part': <encode str>, 'invalid_path_part': <encode str>, 'find_count': <int>, "find_time": int}
             */
            var strategy   = strategy ? strategy : 'qpath';
            var locator    = switch_locator(strategy, locator);
            var parent     = parent_id ? uia_elements_cache.get(parent_id) : null;
            var timeout    = timeout ? (timeout * 1000 - 80) : 0;
            var interval   = interval ? (interval * 1000) : 10;
            var result     = locator.findElement(timeout, interval, parent);
            var element    = result['element'];
            var element_id = element ? uia_elements_cache.append(element) : null;
            result['element'] = element_id;
            $.log("TORPC: " + $.str.objectToString({'id':cmd_id, 'result':result}));
            return api.DoNotReturn;
        },

        'uia.element.find_elements' : function(cmd_id, locator, timeout, interval, strategy, parent_id) {
            /**
             * 查找多个element对象，返回查找到的element对象的缓存的id集合。不指定parent_id则从UIAApplication下开始搜索。
             * Paramaters:
             *  locator         - 定位element的字符串，例如: "/classname='UIAWindow'"
             *  parent_id       - 父element的id，如不指定则从UIAApplication下查找
             *  timeout         - 查找element的超时值（单位: 秒）
             *  strategy        - locator的类型，例如: "qpath"
             * Returns          - json: {'elements': [{'element':id, 'attributes':<encode str>}], 'path': <encode str>, 'valid_path_part': <encode str>, 'invalid_path_part': <encode str>, 'find_count': <int>, "find_time": int}
             */
            var strategy      = strategy ? strategy : 'qpath';
            var locator       = switch_locator(strategy, locator);
            var parent        = parent_id ? uia_elements_cache.get(parent_id) : null;
            var timeout       = timeout ? (timeout * 1000 - 100) : 0;
            var interval      = interval ? (interval * 1000) : 10;
            var result        = locator.findElements(timeout, interval, parent);
            var elements      = result['elements'];
            var elements_dict = new Array();
            for (var i=0; i<elements.length; i++){
                var element_id   = uia_elements_cache.append(elements[i]);
                var element_dict = encodeURIComponent($.str.objectToString(elements[i].getElementDict()));
                elements_dict.push({'element': element_id, 'attributes': element_dict});
            };
            result['elements'] = elements_dict;
            $.log("TORPC: " + $.str.objectToString({'id':cmd_id, 'result':result}));
            return api.DoNotReturn;
        },

        'uia.element.first_with_name' : function(cmd_id, id, name) {
           /**
            * 通过name文本获取第一个匹配的子element
            * Paramaters:
            *  id              - element的id
            *  name            - 预期子element的name
            * Returns:
            *  id              - 子控件的id
            */
            var root = uia_elements_cache.get(id);
            var elem = root.elements().firstWithName(name);
            return uia_elements_cache.append(elem);
        },

        'uia.element.with_name' : function(cmd_id, id, name) {
           /**
            * 通过name文本获取匹配的子elements
            * Paramaters:
            *  id              - element的id
            *  name            - 预期子element的name
            * Returns:
            *  id              - 子控件的id集合
            */
            var root = uia_elements_cache.get(id);
            var elems = root.elements().withName(name);
            return uia_elements_cache.append_elements(elems);
        },

        'uia.element.first_with_predicate' : function(cmd_id, id, predicate) {
           /**
            * 通过predicate文本获取第一个匹配的子element
            * Paramaters:
            *  id              - element的id
            *  predicate       - 预期子element的predicate （例如：“name beginswith 'xxx'”）
            * Returns:
            *  id              - 子控件的id
            */
            var root = uia_elements_cache.get(id);
            var elem = root.elements().firstWithPredicate(predicate);
            return uia_elements_cache.append(elem);
        },

        'uia.element.with_predicate' : function(cmd_id, id, predicate) {
           /**
            * 通过predicate文本获取匹配的子elements
            * Paramaters:
            *  id              - element的id
            *  predicate       - 预期子element的predicate （例如：“name beginswith ‘xxx'”）
            * Returns:
            *  id              - 子控件的id集合
            */
            var root = uia_elements_cache.get(id);
            var elems = root.elements().withPredicate(predicate);
            return uia_elements_cache.append_elements(elems);
        },

        'uia.element.first_with_value_for_key' : function(cmd_id, id, key, value) {
           /**
            * 通过匹配指定key的value，获取第一个匹配的子element
            * Paramaters:
            *  id              - element的id
            *  key             - key （例如：label、name、value）
            *  value           - 对应key的value值
            * Returns:
            *  id              - 子控件的id
            */
            var root = uia_elements_cache.get(id);
            var elem = root.elements().firstWithValueForKey(value, key);
            return uia_elements_cache.append(elem);
        },

        'uia.element.with_value_for_key' : function(cmd_id, id, key, value) {
           /**
            * 通过匹配指定key的value，获取匹配的子elements
            * Paramaters:
            *  id              - element的id
            *  key             - key （例如：label、name、value）
            *  value           - 对应key的value值
            * Returns:
            *  id              - 子控件的id集合
            */
            var root = uia_elements_cache.get(id);
            var elems = root.elements().withValueForKey(value, key);
            return uia_elements_cache.append_elements(elems);
        },

        'uia.element.get_parent' : function(cmd_id, id) {
            /**
             * 获取指定element的父element的id
             * Paramaters:
             *  id              - element的id
             * Returns:
             *  id              - 父element的id
             */
            var parent = uia_elements_cache.get(id).parent();
            return parent ? uia_elements_cache.append(parent) : undefined;
        },

        'uia.element.get_children' : function(cmd_id, id) {
            /**
             * 获取指定element的子elements集合
             * Paramaters:
             *  id              - element的id
             * Returns:
             *  [id, ...]       - 子elements的id集合
             */
            var elements = uia_elements_cache.get(id).elements();
            return elements.length > 0 ? uia_elements_cache.append_elements(elements) : [];
        },

        'uia.element.get_attr' : function(cmd_id, id, name) {
            /**
             * 获取指定element的属性
             * Paramaters:
             *  id              - element的id
             *  name            - 属性名，例如: name、lable、value
             * Returns:
             *  attr value      - 返回基础类型的数据
             */
            var name = name.toLowerCase();
            if (new RegExp(/^isEnabled$|^enabled$|^isValid$|^valid$|^isVisible$|^visible$|^hasKeyboardFocus$|^focus$/i).test(name)) {
                switch (name) {
                    case "isenabled":
                        name = "isEnabled";
                        break;
                    case "enabled":
                        name = "isEnabled";
                        break;
                    case "isvalid":
                        name = "isValid";
                        break;
                    case "valid":
                        name = "isValid";
                        break;
                    case "isvisible":
                        name = "isVisible";
                        break;
                    case "visible":
                        name = "isVisible";
                        break;
                    case "haskeyboardfocus":
                        name = "hasKeyboardFocus";
                        break;
                    case "focus":
                        name = "hasKeyboardFocus";
                        break;
                };
            };
            return api['uia.element.function'](cmd_id, id, name);
        },

        'uia.element.get_rect' : function(cmd_id, id) {
            /**
             * 获取指定element的坐标和长宽
             * Paramaters:
             *  id              - element id
             * Returns:
             *  JSON            - 坐标和长宽
             */
            return uia_elements_cache.get(id).rect();
        },

        'uia.element.capture' : function(cmd_id, id, path) {
            /**
             * 截图（截取指定element的图片，并将图片输出至指定的路径）
             * Paramaters:
             *  path            - 将图片存储至该路径（png格式），例如：/Users/tester/Desktop/test.png
             *                    不传路径 或 路径仅含文件名，则截图后存储至默认路径（默认路径内存储的图片每次重启都会被清空）。
             */
            var rect = uia_elements_cache.get(id).rect();
            return api['uia.target.capture_rect'](cmd_id, rect, path);
        },

        'uia.element.tap' : function(cmd_id, id, x, y) {
            /**
             * 点击指定的element
             * Paramaters:
             *  id              - element id
             *  x               - x坐标（相对于当前element），可不传入该参数
             *  y               - y坐标（相对于当前element），可不传入该参数
             */
            var element = uia_elements_cache.get(id);
            var rect = element.rect();
            var size = rect['size'];
            var x = size['width'] * x;
            var y = size['height'] * y;
            //element.scrollToVisible();
            element.tap(x, y);
        },

        'uia.element.double_tap' : function(cmd_id, id, x, y) {
            /**
             * 双击指定的element
             * Paramaters:
             *  id              - element id
             *  x               - x坐标（相对于当前element），可不传入该参数
             *  y               - y坐标（相对于当前element），可不传入该参数
             */
            if (x && y) {
                for (var i = 0; i < 2; i++) {
                    api['uia.element.tap'](cmd_id, id, x, y);
                };
            } else {
                var element = uia_elements_cache.get(id);
                //element.scrollToVisible();
                element.doubleTap();
            };
        },

        'uia.element.tap_with_options' : function(cmd_id, id, options) {
            /**
             * 自定义点击
             * Paramaters:
             *  id              - element id
             *  options = {
             *     tapCount     : 1,                    // 轻触次数
             *     touchCount   : 1,                    // 触摸点
             *     duration     : 1,                    // 持续时间
             *     tapOffset    : { x: 1.0, y: 0.1 }    // 轻触偏移百分比
             *  }
             */
            var element = uia_elements_cache.get(id);
            //element.scrollToVisible();
            element.tapWithOptions(options);
        },

        'uia.element.click' : function(cmd_id, id, x, y) {
            /**
             * 点击指定的element(适配QTA)
             * Paramaters:
             *  id              - element id
             *  x               - x坐标（相对于当前element），可不传入该参数
             *  y               - y坐标（相对于当前element），可不传入该参数
             */
            api['uia.element.tap'](cmd_id, id, x, y);
        },

        'uia.element.double_click' : function(cmd_id, id, x, y) {
            /**
             * 双击指定的element
             * Paramaters:
             *  id              - element id
             *  x               - x坐标（相对于当前element），可不传入该参数
             *  y               - y坐标（相对于当前element），可不传入该参数
             */
            api['uia.element.double_tap'](cmd_id, id, x, y);
        },

        'uia.element.drag_inside_with_options' : function(cmd_id, id, options) {
            /**
             * 拖拽
             * Paramaters:
             *  id              - element id
             *  options = {
             *     touchCount   : 1,                    // 触摸点
             *     duration     : 0.5,                  // 时间
             *     startOffset  : { x: 0.0, y: 0.1},    // 偏移百分比
             *     endOffset    : { x: 1.0, y: 0.1 },   // 偏移百分比
             *     repeat       : 1                     // 重复该操作
             *     interval     : 0                     // 重复该操作的间隙时间（秒）
             *  }
             */
            var repeat = options.repeat ? options.repeat : 1;
            var interval = options.interval ? options.interval : 0;
            for (var i = 0; i < repeat; i++) {
                uia_elements_cache.get(id).dragInsideWithOptions(options);
                if (repeat > 1 && interval > 0) {
                    UIATarget.localTarget().delay(interval);
                };
            };
        },

        'uia.element.drag_inside_right_to_left' : function(cmd_id, id) {
            /**
             * 单指在控件的中央从右向左拖拽（回避控件边缘，拖拽过程使用1秒）
             */
            var _options = {
                touchCount : 1,
                duration : 1.5,
                startOffset : {
                    x : 0.5,
                    y : 0.5
                },
                endOffset : {
                    x : 0.1,
                    y : 0.5
                }
            };
            uia_elements_cache.get(id).dragInsideWithOptions(_options);
        },

        'uia.element.drag_inside_left_to_right' : function(cmd_id, id) {
            /**
             * 单指在控件的中央从左向右拖拽（回避控件边缘，拖拽过程使用1秒）
             */
            var _options = {
                touchCount : 1,
                duration : 1.5,
                startOffset : {
                    x : 0.5,
                    y : 0.5
                },
                endOffset : {
                    x : 0.9,
                    y : 0.5
                }
            };
            uia_elements_cache.get(id).dragInsideWithOptions(_options);
        },

        'uia.element.drag_inside_up_to_down' : function(cmd_id, id) {
            /**
             * 单指在控件的中央从上向下拖拽（回避控件边缘，拖拽过程使用1秒）
             */
            var _options = {
                touchCount : 1,
                duration : 1.5,
                startOffset : {
                    x : 0.5,
                    y : 0.5
                },
                endOffset : {
                    x : 0.5,
                    y : 0.9
                }
            };
            uia_elements_cache.get(id).dragInsideWithOptions(_options);
        },

        'uia.element.drag_inside_down_to_up' : function(cmd_id, id) {
            /**
             * 单指在控件的中央从下向上拖拽（回避控件边缘，拖拽过程使用1秒）
             */
            var _options = {
                touchCount : 1,
                duration : 1.5,
                startOffset : {
                    x : 0.5,
                    y : 0.5
                },
                endOffset : {
                    x : 0.5,
                    y : 0.1
                }
            };
            uia_elements_cache.get(id).dragInsideWithOptions(_options);
        },

        'uia.element.flick_inside_with_options' : function(cmd_id, id, options) {
            /**
             * 弹去/拂去
             * Paramaters:
             *  id              - element id
             *  options = {
             *     touchCount   : 1,                    // 触摸点
             *     startOffset  : { x: 0.5, y: 0.9 },   // 偏移百分比
             *     endOffset    : { x: 1.0, y: 0.9 }    // 偏移百分比
             *     repeat       : 1                     // 重复该操作
             *     interval     : 0                     // 重复该操作的间隙时间（秒）
             *  }
             */
            var repeat = options.repeat ? options.repeat : 1;
            var interval = options.interval ? options.interval : 0;
            for (var i = 0; i < repeat; i++) {
                uia_elements_cache.get(id).flickInsideWithOptions(options);
                if (repeat > 1 && interval > 0) {
                    UIATarget.localTarget().delay(interval);
                };
            };
        },

        'uia.element.flick_inside_right_to_left' : function(cmd_id, id) {
            /**
             * 单指在控件中央从右向左弹去/拂去（回避控件边缘）
             */
            var _options = {
                touchCount : 1,
                startOffset : {
                    x : 0.5,
                    y : 0.5
                },
                endOffset : {
                    x : 0.1,
                    y : 0.5
                }
            };
            uia_elements_cache.get(id).flickInsideWithOptions(_options);
        },

        'uia.element.flick_inside_left_to_right' : function(cmd_id, id) {
            /**
             * 单指在控件中央从左向右弹去/拂去（回避控件边缘）
             */
            var _options = {
                touchCount : 1,
                startOffset : {
                    x : 0.5,
                    y : 0.5
                },
                endOffset : {
                    x : 0.9,
                    y : 0.5
                }
            };
            uia_elements_cache.get(id).flickInsideWithOptions(_options);
        },

        'uia.element.flick_inside_up_to_down' : function(cmd_id, id) {
            /**
             * 单指在控件中央从上向下弹去/拂去（回避控件边缘）
             */
            var _options = {
                touchCount : 1,
                startOffset : {
                    x : 0.5,
                    y : 0.5
                },
                endOffset : {
                    x : 0.5,
                    y : 0.9
                }
            };
            uia_elements_cache.get(id).flickInsideWithOptions(_options);
        },

        'uia.element.flick_inside_down_to_up' : function(cmd_id, id) {
            /**
             * 单指在控件中央从下向上弹去/拂去（回避控件边缘）
             */
            var _options = {
                touchCount : 1,
                startOffset : {
                    x : 0.5,
                    y : 0.5
                },
                endOffset : {
                    x : 0.5,
                    y : 0.1
                }
            };
            uia_elements_cache.get(id).flickInsideWithOptions(_options);
        },

        'uia.element.rotate_with_options' : function(cmd_id, id, options) {
            /**
             * 旋转
             * Paramaters:
             *  id              - element id
             *  options = {
             *     centerOffset : {x:0.0, y:0.0},   // 中心点
             *     duration     : 1.5,              // 持续时间
             *     radius       : 100,              // 半径
             *     rotation     : 100,              // 旋转弧度的长度，默认为圆周率PI
             *     touchCount   : 2                 // 触摸点（最大5个点，这里默认2个）
             *  }
             */
            uia_elements_cache.get(id).rotateWithOptions(options);
        },

        'uia.element.scroll_to_visible' : function(cmd_id, id) {
            /**
             * 自动滚动到该element为可见
             * Paramaters:
             *  id              - element id
             */
            uia_elements_cache.get(id).scrollToVisible();
            // --- --- --- retry无效
            //var element = uia_elements_cache.get(id);
            //var retry = retry ? retry : 5;
            //var target = UIATarget.localTarget();
            //var error = null;
            //for (var i = 0; i < retry; i++) {
            //    try {
            //        element.scrollToVisible();
            //        return;
            //    } catch(e) {
            //        target.delay(1);
            //        error = e;
            //    };
            //};
            //throw error;
            // --- --- ---
        },

        'uia.element.touch_and_hold' : function(cmd_id, id, duration) {
            /**
             * 持续按住
             * Paramaters:
             *  id              - element id
             *  duration        - 按住多长时间（秒）
             */
            uia_elements_cache.get(id).touchAndHold(duration);
        },

        'uia.element.two_finger_tap' : function(cmd_id, id) {
            /**
             * 二指轻触
             * Paramaters:
             *  id              - element id
             */
            uia_elements_cache.get(id).twoFingerTap();
        },

        'uia.element.wait_for_invalid' : function(cmd_id, id, timeout) {
            /**
             * 等待当前element直到无效
             * Paramaters:
             *  id              - element id
             *  timeout         - 超时值（秒）
             */
            var element = uia_elements_cache.get(id);
            var timeout = timeout ? timeout : 5;
            var target = UIATarget.localTarget();
            target.pushTimeout(timeout);
            var result = element.waitForInvalid();
            target.popTimeout();
            return result;
        },

        'uia.element.set_value' : function(cmd_id, id, value) {
            /**
             * 设置指定element的value
             * Paramaters:
             *  id              - element id
             *  value           - 值
             */
            uia_elements_cache.get(id).setValue(value);
        },

        'uia.element.drag_to_value' : function(cmd_id, id, value) {
            /**
             * 设置指定slider的value
             * Paramaters:
             *  id              - element id
             *  value           - 值
             */
            uia_elements_cache.get(id).dragToValue(value);
        },        

        'uia.element.sent_keys' : function(cmd_id, id, keys) {
            /**
             * 在指定element中键盘输入
             * Paramaters:
             *  id              - element id
             *  keys            - 键入的字符串
             */
            var elem = uia_elements_cache.get(id);
            elem.tap();
            elem.typeString(keys);
        },

        'uia.element.get_element_dict' : function(cmd_id, id) {
            /**
             * 获取指定element的属性信息
             * Returns
             *  JSON String     - 属性
             */
            var dict = uia_elements_cache.get(id).getElementDict();
            var result = encodeURIComponent($.str.objectToString(dict, true));
            $.log("TORPC: " + $.str.objectToString({
                'id' : cmd_id,
                'result' : result
            }));
            return api.DoNotReturn;
        },

        'uia.element.log_element_dict' : function(cmd_id, id) {
            /**
             * 打印并获取指定element的属性信息
             * Returns
             *  JSON String     - 属性
             */
            var dict = uia_elements_cache.get(id).logElementDict();
            var result = encodeURIComponent($.str.objectToString(dict, true));
            $.log("TORPC: " + $.str.objectToString({
                'id' : cmd_id,
                'result' : result
            }));
            return api.DoNotReturn;
        },

        'uia.element.get_element_tree' : function(cmd_id, id) {
            /**
             * 获取指定element的所有子孙element树
             * Paramaters:
             *  id              - element的id
             * Returns:
             *  JSON            - 子孙节点树
             */
            var dict = uia_elements_cache.get(id).getElementTree();
            var result = encodeURIComponent($.str.objectToString(dict, true));
            $.log("TORPC: " + $.str.objectToString({
                'id' : cmd_id,
                'result' : result
            }));
            return api.DoNotReturn;
        },

        'uia.element.log_element_tree_ext' : function(cmd_id, id) {
            /**
             * 从指定element开始获取UI树
             * Returns
             *  JSON String     - UI树
             */
            var dict = uia_elements_cache.get(id).logElementTreeExt();
            var result = encodeURIComponent($.str.objectToString(dict, true));
            $.log("TORPC: " + $.str.objectToString({
                'id' : cmd_id,
                'result' : result
            }));
            return api.DoNotReturn;
        },

        // -*- -*- -*- -*- -*- -*-

        'uia.application.function' : function(cmd_id, func, args) {
            /**
             * 调用UIAApplication的原生函数
             * Paramaters:
             *  func            - 函数名
             *  args            - 函数的有序参数集
             * Returns:
             *  return value    - 被调用函数的返回值（基础类型）
             */
            var app = UIATarget.localTarget().frontMostApp();
            var args = args ? args : [];
            if (app[func]) {
                return app[func].apply(app, args);
            };
            throw new Error('uia.application.function "func: ' + func + '" is invalid.');
        },

        //'uia.application.get_attr' : function(cmd_id, name) {
        //    /**
        //     * 获取UIAApplication的属性
        //     * Paramaters:
        //     *  name            - 属性名，例如: name、lable、value
        //     * Returns:
        //     *  attr value      - 返回基础类型的数据
        //     */
        //    return api['uia.application.function'](cmd_id, name);
        //},

        'uia.application.get_main_window' : function(cmd_id) {
            /**
             * 获取App的主窗口
             * Returns
             *  id              - element的id
             */
            return uia_elements_cache.append(UIATarget.localTarget().frontMostApp().mainWindow());
        },

        'uia.application.get_interface_orientation' : function(cmd_id) {
            /**
             * 获取接口方向
             * Returns
             *  number          - 表示方向
             */
            return UIATarget.localTarget().frontMostApp().interfaceOrientation();
        },

        'uia.application.get_app_bundle_id' : function(cmd_id) {
            /**
             * 获取App的bundleID
             * Returns
             *  string          - bundleID
             */
            return UIATarget.localTarget().frontMostApp().bundleID();
        },

        'uia.application.get_app_version' : function(cmd_id) {
            /**
             * 获取App的version
             * Returns
             *  string          - version
             */
            return UIATarget.localTarget().frontMostApp().version();
        },

        // -*- -*- -*- -*- -*- -*-

        'uia.target.function' : function(cmd_id, func, args) {
            /**
             * 调用UIATarget的原生函数（注：device命名空间对应UIATarget对象）
             * Paramaters:
             *  func            - 函数名
             *  args            - 函数的有序参数集
             * Returns:
             *  return value    - 被调用函数的返回值（基础类型）
             */
            var target = UIATarget.localTarget();
            var args = args ? args : [];
            if (target[func]) {
                return target[func].apply(target, args);
            };
            throw new Error('uia.target.function "func: ' + func + '" is invalid.');
        },

        //'uia.target.get_attr' : function(cmd_id, name) {
        //    /**
        //     * 获取UIATarget的属性
        //     * Paramaters:
        //     *  name            - 属性名，例如: name、lable、value
        //     * Returns:
        //     *  attr value      - 返回基础类型的数据
        //     */
        //    return api['uia.target.function'](cmd_id, name);
        //},

        'uia.target.get_rect' : function(cmd_id) {
            /**
             * 获取设备屏幕大小
             * Returns:
             *  宽高
             */
            return UIATarget.localTarget().rect();
        },

        'uia.target.get_model' : function(cmd_id) {
            /**
             * 获取设备模型
             * Returns:
             *  string
             */
            return UIATarget.localTarget().model();
        },

        'uia.target.get_name' : function(cmd_id) {
            /**
             * 获取设备名
             * Returns:
             *  string
             */
            return UIATarget.localTarget().name();
        },

        'uia.target.get_system_name' : function(cmd_id) {
            /**
             * 获取系统名
             * Returns:
             *  string
             */
            return UIATarget.localTarget().systemName();
        },

        'uia.target.get_system_version' : function(cmd_id) {
            /**
             * 获取系统版本
             * Returns:
             *  string
             */
            return UIATarget.localTarget().systemVersion();
        },

        'uia.target.capture_rect' : function(cmd_id, rect, path) {
            /**
             * 截图（指定区域截图，并将图片输出至指定的路径）
             * Paramaters:
             *  rect            - 指定区域
             *                    {
             *                      origin : { x: xposition, y: yposition },
             *                      size   : { width: widthvalue, height: heightvalue}
             *                    }
             *  path            - 将图片存储至该路径（png格式），例如：/Users/tester/Desktop/test.png
             *                    不传路径 或 路径仅含文件名，则截图后存储至默认路径（默认路径内存储的图片每次重启都会被清空）。
             */
            var name = String(new Date().getTime());
            if (path) {
                var nodes = path.split('/');
                if (nodes[nodes.length - 1].length > 0) {
                    name = nodes[nodes.length - 1].replace(/\.\w{3,4} *$/, '');
                    nodes[nodes.length - 1] = name;
                };
                path = nodes.join('/');
            };
            if (!new RegExp('^/').test(path)) {
                path = [Environment.screen_shot_path, name].join('/');
            };
            UIATarget.localTarget().captureRectWithName(rect, name);
            name += '.png';
            path += '.png';
            $.log('ScreenshotCaptured: {"name": "' + name + '", "path": "' + path + '"}');
            return path;
        },

        'uia.target.capture_screen' : function(cmd_id, path) {
            /**
             * 截屏(将输出图片至指定的路径)
             * Paramaters:
             *  path            - 将图片存储至该路径（png格式），例如：/Users/tester/Desktop/test.png
             *                  - 不传路径 或 路径仅含文件名，则截图后存储至默认路径（默认路径内存储的图片每次重启都会被清空）。
             */
            var name = String(new Date().getTime());
            if (path) {
                var nodes = path.split('/');
                if (nodes[nodes.length - 1].length > 0) {
                    name = nodes[nodes.length - 1].replace(/\.\w{3,4} *$/, '');
                    nodes[nodes.length - 1] = name;
                };
                path = nodes.join('/');
            };
            if (!new RegExp('^/').test(path)) {
                path = [Environment.screen_shot_path, name].join('/');
            };
            UIATarget.localTarget().captureScreenWithName(name);
            name += '.png';
            path += '.png';
            $.log('ScreenshotCaptured: {"name": "' + name + '", "path": "' + path + '"}');
            return path;
        },

        'uia.target.get_element_tree_and_capture_screen' : function(cmd_id, path) {
            /**
             * 获取UI树并截屏（输出的JSON字符串数据需要URL解码）
             * Paramaters:
             *  path            - 将图片存储至该路径（png格式），例如：/Users/tester/Desktop/test.png
             *                  - 不传路径 或 路径仅含文件名，则截图后存储至默认路径（默认路径内存储的图片每次重启都会被清空）。
             * Returns:
             *  Dict            - { element_tree: {}, capture_screen: file_path }
             */
            $.log("TORPC: " + $.str.objectToString({
                'id' : cmd_id,
                'result' : encodeURIComponent($.str.objectToString({
                    element_tree : UIATarget.localTarget().getElementTree(),
                    capture_screen : api['uia.target.capture_screen'](cmd_id, path)
                }, true))
            }));
            return api.DoNotReturn;

        },

        'uia.target.set_rules_of_alert_auto_handle' : function(cmd_id, rules) {
            /**
             * 设置自动处理Alert规则
             * Paramaters:
             *  rules = [ {"message_text": "message_text", "button_text": "button_text"}, ... ]
             *          message_text - (支持正则表达式)在Alert内所有Element的文本中的某文本（单一Element的label、name、value，等于三段文本。其中一项匹配即可。）
             *          button_text  - (支持正则表达式)在Alert内的匹配文本的按钮（UIAButton的label、name、value，等于三段文本。其中一项匹配即可。）
             */
            rules_of_alert_auto_handle = rules;
        },

        'uia.target.get_rules_of_alert_auto_handle' : function(cmd_id) {
            /**
             * 查询已设置的自动处理Alert规则
             * Returns:
             *  list - [ {"message_text": "message_text", "button_text": "button_text"}, ... ]
             */
            return encodeURIComponent($.str.objectToString(rules_of_alert_auto_handle, true));
        },

        'uia.target.add_rule_of_alert_auto_handle' : function(cmd_id, message_text, button_text) {
            /**
             * 自动处理Alert规则增加一项
             * Paramaters:
             *  message_text - (支持正则表达式)在Alert内所有Element的文本中的某文本（单一Element的label、name、value，等于三段文本。其中一项匹配即可。）
             *  button_text  - (支持正则表达式)在Alert内的匹配文本的按钮（UIAButton的label、name、value，等于三段文本。其中一项匹配即可。）
             */
            rules_of_alert_auto_handle.push({
                message_text : message_text,
                button_text : button_text
            });
        },

        'uia.target.clean_rules_of_alert_auto_handle' : function(cmd_id) {
            /**
             * 清除所有自动处理Alert的规则
             */
            rules_of_alert_auto_handle = new Array();
        },

        'uia.target.turn_on_auto_close_alert' : function(cmd_id) {
            /**
             * 打开自动关闭alert框(如果rules_of_alert_auto_handle无匹配，则交由系统自动关闭)
             */
            flag_alert_auto_handled = false;
            // 我方未处理，UIA默认自动处理
        },

        'uia.target.turn_off_auto_close_alert' : function(cmd_id) {
            /**
             * 关闭自动关闭alert框
             */
            flag_alert_auto_handled = true;
            // 我方已处理，UIA不再自动处理
        },

        'uia.target.get_last_alert_msg' : function(cmd_id) {
            /**
             * 获取最近一次alert框的提示内容
             * Returns
             *  msg             - 文本内容
             */
            return last_alert_msg;
        },

        'uia.target.delay' : function(cmd_id, seconds) {
            /**
             * 等待
             * Paramaters:
             *  seconds   - 秒
             */
            UIATarget.localTarget().delay(seconds);
        },

        'uia.target.get_element_tree' : function(cmd_id) {
            /**
             * 从顶层开始获取UI树（输出的JSON字符串数据需要URL解码）
             * Returns
             *  JSON String     - UI树
             */
            var dict = UIATarget.localTarget().getElementTree();
            var result = encodeURIComponent($.str.objectToString(dict, true));
            $.log("TORPC: " + $.str.objectToString({
                'id' : cmd_id,
                'result' : result
            }));
            return api.DoNotReturn;
        },

        'uia.target.log_element_tree_ext' : function(cmd_id) {
            /**
             * 从顶层开始获取UI树（输出的JSON字符串数据需要URL解码）
             * Returns
             *  JSON String     - UI树
             */
            var dict = UIATarget.localTarget().logElementTreeExt();
            var result = encodeURIComponent($.str.objectToString(dict, true));
            $.log("TORPC: " + $.str.objectToString({
                'id' : cmd_id,
                'result' : result
            }));
            return api.DoNotReturn;
        },

        'uia.target.click_volume_down' : function(cmd_id) {
            /**
             * 按下一次减少音量按键
             */
            UIATarget.localTarget().clickVolumeDown();
        },

        'uia.target.click_volume_up' : function(cmd_id) {
            /**
             * 按下一次增加音量按键
             */
            UIATarget.localTarget().clickVolumeUp();
        },

        'uia.target.hold_volume_down' : function(cmd_id, seconds) {
            /**
             * 持续按住减少音量按键
             * * Paramaters:
             *  seconds         - 秒
             */
            var seconds = seconds ? seconds : 1;
            UIATarget.localTarget().holdVolumeDown(seconds);
        },

        'uia.target.hold_volume_up' : function(cmd_id, seconds) {
            /**
             * 持续按住增加音量按键
             * * Paramaters:
             *  seconds         - 秒
             */
            var seconds = seconds ? seconds : 1;
            UIATarget.localTarget().holdVolumeUp(seconds);
        },

        'uia.target.deactivate_app_ror_duration' : function(cmd_id, seconds) {
            /**
             * 将App置于后台一定时间
             * Paramaters:
             *  seconds         - 秒
             * Returns
             *  Boolean
             */
            var seconds = seconds ? seconds : 3;
            return UIATarget.localTarget().deactivateAppForDuration(seconds);
        },

        'uia.target.get_device_orientation' : function(cmd_id) {
            /**
             * 获取设备的方向
             * Returns
             *  Number
             *      UIA_DEVICE_ORIENTATION_UNKNOWN
             *      UIA_DEVICE_ORIENTATION_PORTRAIT
             *      UIA_DEVICE_ORIENTATION_PORTRAIT_UPSIDEDOWN
             *      UIA_DEVICE_ORIENTATION_LANDSCAPELEFT
             *      UIA_DEVICE_ORIENTATION_LANDSCAPERIGHT
             *      UIA_DEVICE_ORIENTATION_FACEUP
             *      UIA_DEVICE_ORIENTATION_FACEDOWN
             */
            return UIATarget.localTarget().deviceOrientation();
        },

        'uia.target.tap' : function(cmd_id, point) {
            /**
             * 双击
             * Paramaters:
             *  point           - { x: 0.5, y: 0.5 }
             */
            var _rect = UIATarget.localTarget().rect();
            var _point = point ? point : {};
            _point.x = _point.x ? _rect.size.width * _point.x : _rect.size.width * 0.5;
            _point.y = _point.y ? _rect.size.height * _point.y : _rect.size.height * 0.5;
            UIATarget.localTarget().tap(_point);
        },

        'uia.target.double_tap' : function(cmd_id, point) {
            /**
             * 双击
             * Paramaters:
             *  point           - { x: 100, y: 100 }
             */
            var _rect = UIATarget.localTarget().rect();
            var _point = point ? point : {};
            _point.x = _point.x ? _point.x : _rect.size.width * 0.5;
            _point.y = _point.y ? _point.y : _rect.size.height * 0.5;
            UIATarget.localTarget().doubleTap(_point);
        },

        'uia.target.tap_with_options' : function(cmd_id, point, options) {
            /**
             * 双击
             * Paramaters:
             *  point           - { x: 100, y: 100 }
             *  options         - {
             *                      tapCount    : 1, 几次，默认1次
             *                      touchCount  : 1, 几点，默认1个点（例如两个手指则为2）
             *                      duration    : 0  按住的时间，默认是0
             *                    }
             */
            UIATarget.localTarget().tapWithOptions(point, options);
        },

        'uia.target.touch_and_hold' : function(cmd_id, point, duration) {
            /**
             * 双击
             * Paramaters:
             *  point           - { x: 100, y: 100 }
             *  duration        - 按住多少秒
             */
            UIATarget.localTarget().touchAndHold(point, duration);
        },

        'uia.target.drag_from_to_for_duration' : function(cmd_id, from_point, to_point, duration, repeat, interval) {
            /**
             * 拖拽
             * Paramaters:
             *  from_point      - { x: 0.5, y: 0.9 } // 偏移百分比
             *  to_point        - { x: 0.5, y: 0.1 } // 偏移百分比
             *  duration        - 持续时间（秒）
             *  repeat          - 重复该操作
             *  interval        - 重复该操作的间隙时间（秒）
             */
            var rect = UIATarget.localTarget().rect();
            var from_point = {
                x : Math.floor(rect.size.width * from_point.x),
                y : Math.floor(rect.size.height * from_point.y)
            };
            var to_point = {
                x : Math.floor(rect.size.width * to_point.x),
                y : Math.floor(rect.size.height * to_point.y)
            };
            var duration = duration ? duration : 0.5;
            var repeat = repeat ? repeat : 1;
            var interval = interval ? interval : 0;
            for (var i = 0; i < repeat; i++) {
                UIATarget.localTarget().dragFromToForDuration(from_point, to_point, duration);
                if (repeat > 1 && interval > 0) {
                    UIATarget.localTarget().delay(interval);
                };
            };
        },

        'uia.target.drag_right_to_left' : function(cmd_id) {
            /**
             * 屏幕中央从右向左拖拽（回避屏幕边缘）
             */
            var _from_point = {
                x : 0.5,
                y : 0.5
            };
            var _to_point = {
                x : 0.1,
                y : 0.5
            };
            api['uia.target.drag_from_to_for_duration'](cmd_id, _from_point, _to_point);
        },

        'uia.target.drag_left_to_right' : function(cmd_id) {
            /**
             * 屏幕中央从左向右拖拽（回避屏幕边缘）
             */
            var _from_point = {
                x : 0.5,
                y : 0.5
            };
            var _to_point = {
                x : 0.9,
                y : 0.5
            };
            api['uia.target.drag_from_to_for_duration'](cmd_id, _from_point, _to_point);
        },

        'uia.target.drag_up_to_down' : function(cmd_id) {
            /**
             * 屏幕中央从上向下拖拽（回避屏幕边缘）
             */

            var _from_point = {
                x : 0.5,
                y : 0.5
            };
            var _to_point = {
                x : 0.5,
                y : 0.9
            };
            api['uia.target.drag_from_to_for_duration'](cmd_id, _from_point, _to_point);
        },

        'uia.target.drag_down_to_up' : function(cmd_id) {
            /**
             * 屏幕中央从下向上拖拽（回避屏幕边缘）
             */
            var _from_point = {
                x : 0.5,
                y : 0.5
            };
            var _to_point = {
                x : 0.5,
                y : 0.1
            };
            api['uia.target.drag_from_to_for_duration'](cmd_id, _from_point, _to_point);
        },

        'uia.target.flick_from_to' : function(cmd_id, from_point, to_point, repeat, interval) {
            /**
             * 弹去/拂去
             * Paramaters:
             *  from_point      - { x: 0.5, y: 0.9 } // 偏移百分比
             *  to_point        - { x: 0.5, y: 0.1 } // 偏移百分比
             *  repeat          - 重复该操作
             *  interval        - 重复该操作的间隙时间（秒）
             */

            var rect = UIATarget.localTarget().rect();
            var from_point = {
                x : Math.floor(rect.size.width * from_point.x),
                y : Math.floor(rect.size.height * from_point.y)
            };
            var to_point = {
                x : Math.floor(rect.size.width * to_point.x),
                y : Math.floor(rect.size.height * to_point.y)
            };
            var repeat = repeat ? repeat : 1;
            var interval = interval ? interval : 0;
            for (var i = 0; i < repeat; i++) {
                UIATarget.localTarget().flickFromTo(from_point, to_point);
                if (repeat > 1 && interval > 0) {
                    UIATarget.localTarget().delay(interval);
                };
            };
        },

        'uia.target.flick_right_to_left' : function(cmd_id) {
            /**
             * 屏幕中央从右向左弹去/拂去
             */
            var _from_point = {
                x : 0.5,
                y : 0.5
            };
            var _to_point = {
                x : 0.1,
                y : 0.5
            };
            api['uia.target.flick_from_to'](cmd_id, _from_point, _to_point);
        },

        'uia.target.flick_left_to_right' : function(cmd_id) {
            /**
             * 屏幕中央从左向右弹去/拂去
             */
            var _from_point = {
                x : 0.5,
                y : 0.5
            };
            var _to_point = {
                x : 0.9,
                y : 0.5
            };
            api['uia.target.flick_from_to'](cmd_id, _from_point, _to_point);
        },

        'uia.target.flick_up_to_down' : function(cmd_id) {
            /**
             * 屏幕中央从上向下弹去/拂去
             */
            var _from_point = {
                x : 0.5,
                y : 0.5
            };
            var _to_point = {
                x : 0.5,
                y : 0.9
            };
            api['uia.target.flick_from_to'](cmd_id, _from_point, _to_point);
        },

        'uia.target.flick_down_to_up' : function(cmd_id) {
            /**
             * 屏幕中央从下向上弹去/拂去
             */
            var _from_point = {
                x : 0.5,
                y : 0.5
            };
            var _to_point = {
                x : 0.5,
                y : 0.1
            };
            api['uia.target.flick_from_to'](cmd_id, _from_point, _to_point);
        },

        'uia.target.lock_for_duration' : function(cmd_id, duration) {
            /**
             * 持续锁定一段时间
             * Paramaters:
             *  duration        - 持续多久（秒）
             */
            UIATarget.localTarget().lockForDuration(duration);
        },

        'uia.target.pinch_close_from_to_for_duration' : function(cmd_id, from_point, to_point, duration) {
            /**
             * 捏合
             * Paramaters:
             *  from_point      - { x: 100, y: 100 }
             *  to_point        - { x: 200, y: 200 }
             *  duration        - 从起点至终点消耗的时间（控制快慢）
             */
            UIATarget.localTarget().pinchCloseFromToForDuration(from_point, to_point, duration);
        },

        'uia.target.pinch_open_from_to_for_duration' : function(cmd_id, from_point, to_point, duration) {
            /**
             * 展开
             * Paramaters:
             *  from_point      - { x: 100, y: 100 }
             *  to_point        - { x: 200, y: 200 }
             *  duration        - 从起点至终点消耗的时间（控制快慢）
             */
            UIATarget.localTarget().pinchOpenFromToForDuration(from_point, to_point, duration);
        },

        'uia.target.rotate_with_options' : function(cmd_id, location, options) {
            /**
             * 旋转
             * Paramaters:
             *  location        - { x: 100, y: 100 } 中心点
             *  options         - {
             *                      duration    : 1,    持续的时间（秒）
             *                      radius      : 50,   半径
             *                      rotation    : 100,  圆周，默认是圆周率PI
             *                      touchCount  : 2     触摸点数量 2 - 5
             *                    }
             */
            UIATarget.localTarget().rotateWithOptions(location, options);
        },

        'uia.target.set_device_orientation' : function(cmd_id, orientation) {
            /**
             * 设置设备的方向
             * Paramaters:
             *  orientation     - 代表方向的数值
             *                      UIA_DEVICE_ORIENTATION_UNKNOWN
             *                      UIA_DEVICE_ORIENTATION_PORTRAIT
             *                      UIA_DEVICE_ORIENTATION_PORTRAIT_UPSIDEDOWN
             *                      UIA_DEVICE_ORIENTATION_LANDSCAPELEFT
             *                      UIA_DEVICE_ORIENTATION_LANDSCAPERIGHT
             *                      UIA_DEVICE_ORIENTATION_FACEUP
             *                      UIA_DEVICE_ORIENTATION_FACEDOWN
             */
            UIATarget.localTarget().setDeviceOrientation(orientation);
        },

        'uia.target.set_location' : function(cmd_id, coordinates) {
            /**
             * 设置设备的GPS坐标
             * Paramaters:
             *  coordinates     - {
             *                      latitude    : 100, // 以度为单位的纬度。正值表示纬度赤道以北。负值表示纬度赤道以南。
             *                      longitude   : 100  // 以度为单位的经度。测量是相对于零子午线，用正值向东延伸的经络及经络的负值西侧延伸。
             *                    }
             */
            UIATarget.localTarget().setLocation(orientation);
        },

        'uia.target.set_location_with_options' : function(cmd_id, coordinates, options) {
            /**
             * 设置设备的GPS坐标
             * Paramaters:
             *  coordinates     - {
             *                      latitude    : 100, // 以度为单位的纬度。正值表示纬度赤道以北。负值表示纬度赤道以南。
             *                      longitude   : 100  // 以度为单位的经度。测量是相对于零子午线，用正值向东延伸的经络及经络的负值西侧延伸。
             *                    }
             *  options         - {
             *                      altitude            : 50, // 海拔高度，以米为单位，相对于海平面。正值表示海拔高度。负值表示低于海平面的高度。
             *                      horizontalAccuracy  : 10, // 水平半径，不确位置时的范围内，以米为单位。负的值是无效的。
             *                      verticalAccuracy    : 10, // 垂直半径，不确位置时的范围内，以米为单位。负的值是无效的。
             *                      course              : 1,  // 设备是移动的，不确定移动方向
             *                      speed               : 1   // 移动速度（米/秒）
             *                    }
             */
            UIATarget.localTarget().setLocationWithOptions(orientation, options);
        },

        'uia.target.shake' : function(cmd_id) {
            /**
             * 摇晃设备
             */
            UIATarget.localTarget().shake();
        },

        'uia.target.unlock' : function(cmd_id) {
            /**
             * 解锁设备
             */
            UIATarget.localTarget().unlock();
        },

        'uia.target.lock' : function(cmd_id) {
            /**
             * 锁定设备
             */
            UIATarget.localTarget().lock();
        },

        'uia.keyboard.sent_keys' : function(cmd_id, keys) {
            /**
             * 键盘输入
             */
            UIATarget.localTarget().frontMostApp().keyboard().typeString(keys);
        },
    };

})($);
