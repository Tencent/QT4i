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
'''WebDriver命令
'''

class Command(object):
    """
    Defines constants for the standard WebDriver commands.

    While these constants have no meaning in and of themselves, they are
    used to marshal commands through a service that implements WebDriver's
    remote wire protocol:

        https://github.com/SeleniumHQ/selenium/wiki/JsonWireProtocol

    """

    # Keep in sync with org.openqa.selenium.remote.DriverCommand

    HEALTH = "health"
    DEACTIVATE_APP = "deactivateApp"
    STATUS = "status"
    SESSION = "Session"
    GET_ALL_SESSIONS = "getAllSessions"
    DELETE_SESSION = "deleteSession"
    CLOSE = "close"
    START = "start"
    QUIT = "quit"
    GET = "get"
    FIND_ELEMENT = "findElement"
    FIND_ELEMENTS = "findElements"
    FIND_CHILD_ELEMENT = "findChildElement"
    FIND_CHILD_ELEMENTS = "findChildElements"
    CLEAR_ELEMENT = "clearElement"
    CLICK_ELEMENT = "clickElement"
    SEND_KEYS_TO_ELEMENT = "sendKeysToElement"
    SEND_KEYS_TO_ACTIVE_ELEMENT = "sendKeysToActiveElement"
    SUBMIT_ELEMENT = "submitElement"
    GET_WINDOW_SIZE = "getWindowSize"
    GET_WINDOW_POSITION = "getWindowPosition"
    SET_WINDOW_SIZE = "setWindowSize"
    SET_WINDOW_POSITION = "setWindowPosition"
    SWITCH_TO_WINDOW = "switchToWindow"
    SWITCH_TO_FRAME = "switchToFrame"
    SWITCH_TO_PARENT_FRAME = "switchToParentFrame"
    GET_ACTIVE_ELEMENT = "getActiveElement"
    GET_CURRENT_URL = "getCurrentUrl"
    GET_PAGE_SOURCE = "getPageSource"
    GET_TITLE = "getTitle"
    EXECUTE_SCRIPT = "executeScript"
    GET_ELEMENT_TREE = "getElementTree"
    GET_ELEMENT_TEXT = "getElementText"
    GET_ELEMENT_VALUE = "getElementValue"
    GET_ELEMENT_TAG_NAME = "getElementTagName"
    SET_ELEMENT_SELECTED = "setElementSelected"
    IS_ELEMENT_SELECTED = "isElementSelected"
    IS_ELEMENT_ENABLED = "isElementEnabled"
    IS_ELEMENT_DISPLAYED = "isElementDisplayed"
    GET_ELEMENT_LOCATION = "getElementLocation"
    GET_ELEMENT_LOCATION_ONCE_SCROLLED_INTO_VIEW = "getElementLocationOnceScrolledIntoView"
    GET_ELEMENT_SIZE = "getElementSize"
    GET_ELEMENT_RECT = "getElementRect"
    GET_ELEMENT_ATTRIBUTE = "getElementAttribute"
    ELEMENT_EQUALS = "elementEquals"
    SCREENSHOT = "screenshot"
    ELEMENT_SCREENSHOT = "elementScreenshot"
    IMPLICIT_WAIT = "implicitlyWait"
    EXECUTE_ASYNC_SCRIPT = "executeAsyncScript"
    SET_SCRIPT_TIMEOUT = "setScriptTimeout"
    SET_TIMEOUTS = "setTimeouts"
    MAXIMIZE_WINDOW = "windowMaximize"

    #Alerts
    DISMISS_ALERT = "dismissAlert"
    ACCEPT_ALERT = "acceptAlert"
    SET_ALERT_VALUE = "setAlertValue"
    GET_ALERT_TEXT = "getAlertText"
    SET_ALERT_CREDENTIALS = "setAlertCredentials"

    # Advanced user interactions
    CLICK = "mouseClick"
    DOUBLE_CLICK = "mouseDoubleClick"
    MOUSE_DOWN = "mouseButtonDown"
    MOUSE_UP = "mouseButtonUp"
    MOVE_TO = "mouseMoveTo"

    # Screen Orientation
    SET_SCREEN_ORIENTATION = "setScreenOrientation"
    GET_SCREEN_ORIENTATION = "getScreenOrientation"

    # Touch Actions
    SINGLE_TAP = "touchSingleTap"
    TOUCH_DOWN = "touchDown"
    TOUCH_UP = "touchUp"
    TOUCH_MOVE = "touchMove"
    TOUCH_SCROLL = "touchScroll"
    DOUBLE_TAP = "touchDoubleTap"
    LONG_PRESS = "touchLongPress"
    FLICK = "touchFlick"
    FORCE_TOUCH = 'forceTouch'

    #HTML 5
    EXECUTE_SQL = "executeSql"

    GET_LOCATION = "getLocation"
    SET_LOCATION = "setLocation"

    GET_APP_CACHE = "getAppCache"
    GET_APP_CACHE_STATUS = "getAppCacheStatus"
    CLEAR_APP_CACHE = "clearAppCache"

    GET_LOCAL_STORAGE_ITEM = "getLocalStorageItem"
    REMOVE_LOCAL_STORAGE_ITEM = "removeLocalStorageItem"
    GET_LOCAL_STORAGE_KEYS = "getLocalStorageKeys"
    SET_LOCAL_STORAGE_ITEM = "setLocalStorageItem"
    CLEAR_LOCAL_STORAGE = "clearLocalStorage"
    GET_LOCAL_STORAGE_SIZE = "getLocalStorageSize"

    GET_SESSION_STORAGE_ITEM = "getSessionStorageItem"
    REMOVE_SESSION_STORAGE_ITEM = "removeSessionStorageItem"
    GET_SESSION_STORAGE_KEYS = "getSessionStorageKeys"
    SET_SESSION_STORAGE_ITEM = "setSessionStorageItem"
    CLEAR_SESSION_STORAGE = "clearSessionStorage"
    GET_SESSION_STORAGE_SIZE = "getSessionStorageSize"

    # Mobile
    GET_NETWORK_CONNECTION = "getNetworkConnection"
    SET_NETWORK_CONNECTION = "setNetworkConnection"
    CURRENT_CONTEXT_HANDLE = "getCurrentContextHandle"
    CONTEXT_HANDLES = "getContextHandles"
    SWITCH_TO_CONTEXT = "switchToContext"
    
    #QT4i
    QTA_DEVICE_CLICK = "qtaDeviceClick"
    QTA_DEVICE_DOUBLE_CLICK = "qtaDeviceDoubleClick"  
    QTA_DEVICE_LONG_CLICK = "qtaDeviceLongClick"
    QTA_DEVICE_DRAG = "qtaDeviceDrag"
    QTA_DEVICE_PINCH = "qtaDevicePinch"
    QTA_DEVICE_ROTATE = "qtaDeviceRotate"
    QTA_DEVICE_SENDKEYS = "qtaDeviceSendKeys"
    QTA_FIND_ELEMENTS =  "qtaFindElements"
    QTA_ELEMENT_CLICK = "qtaElementClick"
    QTA_ELEMENT_DOUBLE_CLICK = "qtaElementDoubleClick"
    QTA_ELEMENT_LONG_CLICK = "qtaElementLongClick"
    QTA_ELEMENT_DRAG = "qtaElementDrag"
    QTA_ELEMENT_SENDKEYS = "qtaElementSendKeys"
    QTA_GET_PARENT_ELEMENT = "qtaGetParent"
    QTA_GET_CHILDREN_ELEMENTS = "qtaGetChildren"
    QTA_SCROLL_TO_VISIBLE = "qtaScrollToVisible"
    QTA_DRAG_TO_VALUE = "qtaDragToValue"
    QTA_GET_ELEMENT_ATTRS = "qtaGetElementAttrs"
    QTA_ALERT_RULES_UPDATE = "qtaAlertRulesUpdate"
    QTA_ELEMENT_SETVALUE = "qtaElementSetValue"
    QTA_ELEMENT_TREE = "qtaElementTree"
    QTA_STOP_AGENT = "qtaStopAgent"
    QTA_GET_FOREGROUND_APP_NAME = "qtaGetForegroundAppName"
    QTA_GET_FOREGROUND_APP_PID = "qtaGetForegroundAppPid"
    QTA_GET_ELEMENT_WIN_INFO = "qtaGetElementWinInfo"
    QTA_ALERT_DISMISS = "qtaAlertDismiss"
    QTA_DEVICE_LOCK = "qtaDeviceLock"
    QTA_DEVICE_UNLOCK = "qtaDeviceUnlock"
    QTA_SANDBOX_LIST = "qtaSandboxList"
    QTA_SANDBOX_REMOVE = "qtaSandboxRemove"
    QTA_ALBUM_UPLOAD = "qtaAlbumUpload"
    QTA_STUB_CALL = "qtaStubCall"
    QTA_DEVICE_VOLUME = "qtaDeviceVolume"
    QTA_DEVICE_SIRI = "qtaDeviceSiri"
    QTA_DEVICE_SCREEN_DIRECTION = "qtaDeviceScreenDirection"
    QTA_DEVICE_DETAIL_INFO = "qtaDeviceDetailInfo"
    QTA_WHEEL_SELECT = "qtaWheelSelect"