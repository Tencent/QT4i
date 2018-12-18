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
'''异常处理器
'''

from __future__ import absolute_import, print_function

import six

from qt4i.driver.xctest.webdriverclient.exceptions import ElementNotSelectableException
from qt4i.driver.xctest.webdriverclient.exceptions import ElementNotVisibleException
from qt4i.driver.xctest.webdriverclient.exceptions import InvalidElementStateException
from qt4i.driver.xctest.webdriverclient.exceptions import InvalidSelectorException
from qt4i.driver.xctest.webdriverclient.exceptions import InvalidQPathException
from qt4i.driver.xctest.webdriverclient.exceptions import ImeNotAvailableException
from qt4i.driver.xctest.webdriverclient.exceptions import ImeActivationFailedException
from qt4i.driver.xctest.webdriverclient.exceptions import NoSuchSessionException
from qt4i.driver.xctest.webdriverclient.exceptions import NoSuchElementException
from qt4i.driver.xctest.webdriverclient.exceptions import NoSuchFrameException
from qt4i.driver.xctest.webdriverclient.exceptions import NoSuchWindowException
from qt4i.driver.xctest.webdriverclient.exceptions import StaleElementReferenceException
from qt4i.driver.xctest.webdriverclient.exceptions import UnexpectedAlertPresentException
from qt4i.driver.xctest.webdriverclient.exceptions import NoAlertPresentException
from qt4i.driver.xctest.webdriverclient.exceptions import ErrorInResponseException
from qt4i.driver.xctest.webdriverclient.exceptions import TimeoutException
from qt4i.driver.xctest.webdriverclient.exceptions import WebDriverException
from qt4i.driver.xctest.webdriverclient.exceptions import MoveTargetOutOfBoundsException
from qt4i.driver.xctest.webdriverclient.exceptions import RotationNotAllowedException
from qt4i.driver.xctest.webdriverclient.exceptions import ApplicationDeadlockException
from qt4i.driver.xctest.webdriverclient.exceptions import ApplicationCrashedException
from qt4i.driver.xctest.webdriverclient.exceptions import XCTestAgentDeadException
from qt4i.driver.xctest.webdriverclient.exceptions import SendKeysFailedException




class ErrorCode(object):
    """
    Error codes defined in the WebDriver wire protocol.
    """
    # Keep in sync with org.openqa.selenium.remote.ErrorCodes and errorcodes.h
    SUCCESS = 0
    UNSUPPORTED = [1, 'unsupported']
    NO_SUCH_SESSION = [6, 'no such session']
    NO_SUCH_ELEMENT = [7, 'no such element']
    NO_SUCH_FRAME = [8, 'no such frame']
    UNKNOWN_COMMAND = [9, 'unknown command']
    STALE_ELEMENT_REFERENCE = [10, 'stale element reference']
    ELEMENT_NOT_VISIBLE = [11, 'element not visible']
    INVALID_ELEMENT_STATE = [12, 'invalid element state']
    UNKNOWN_ERROR = [13, 'unknown error']
    ELEMENT_IS_NOT_SELECTABLE = [15, 'element not selectable']
    JAVASCRIPT_ERROR = [17, 'javascript error']
    XPATH_LOOKUP_ERROR = [19, 'invalid selector']
    TIMEOUT = [21, 'timeout']
    NO_SUCH_WINDOW = [23, 'no such window']
    INVALID_COOKIE_DOMAIN = [24, 'invalid cookie domain']
    UNABLE_TO_SET_COOKIE = [25, 'unable to set cookie']
    UNEXPECTED_ALERT_OPEN = [26, 'unexpected alert open']
    NO_ALERT_OPEN = [27, 'no such alert']
    SCRIPT_TIMEOUT = [28, 'script timeout']
    INVALID_ELEMENT_COORDINATES = [29, 'invalid element coordinates']
    IME_NOT_AVAILABLE = [30, 'ime not available']
    IME_ENGINE_ACTIVATION_FAILED = [31, 'ime engine activation failed']
    INVALID_SELECTOR = [32, 'invalid selector']
    SESSION_NOT_CREATED = [33, 'session not created']
    MOVE_TARGET_OUT_OF_BOUNDS = [34, 'move target out of bounds']
    INVALID_XPATH_SELECTOR = [51, 'invalid selector']
    INVALID_XPATH_SELECTOR_RETURN_TYPER = [52, 'invalid selector']
    INVALID_QPATH = [60, 'invalid qpath']
    METHOD_NOT_ALLOWED = [405, 'unsupported operation']
    ROTATION_NOT_ALLOWED = [777, 'rotation not allowed']
    APPLICATION_DEADLOCK_DETECTED = [888, 'application deadlock detected']
    APPLICATION_CRASHED = [889, 'application crashed']
    XCTestAgent_NOT_BACKGROUND = [890, 'XCTestAgent Dead']
    SENDKEYS_FAILED = [891, 'sendkeys failed']
    QT4I_STUB_NOT_EXIST = 900


class ErrorHandler(object):
    """
    Handles errors returned by the WebDriver server.
    """
    ERROR_IN_RESPONSE_EXCEPTIONS = [
                            ErrorInResponseException, 
                            SendKeysFailedException,
                            XCTestAgentDeadException,
                            ApplicationCrashedException,
                            ]
    
    def check_response(self, response):
        """
        Checks that a JSON response from the WebDriver does not have an error.

        :Args:
         - response - The JSON response from the WebDriver server as a dictionary
           object.

        :Raises: If the response contains an error message.
        """
        status = response.get('status', None)
        if status is None or status == ErrorCode.SUCCESS \
            or status == ErrorCode.QT4I_STUB_NOT_EXIST:
            return

        value = None
        message = response.get("message", "")
        screen = response.get("screen", "")
        stacktrace = None
        
        exception_class = ErrorInResponseException
        if status in ErrorCode.NO_SUCH_SESSION \
                or status in ErrorCode.SESSION_NOT_CREATED:
            exception_class = NoSuchSessionException
        elif status in ErrorCode.NO_SUCH_ELEMENT:
            exception_class = NoSuchElementException
        elif status in ErrorCode.NO_SUCH_FRAME:
            exception_class = NoSuchFrameException
        elif status in ErrorCode.NO_SUCH_WINDOW:
            exception_class = NoSuchWindowException
        elif status in ErrorCode.STALE_ELEMENT_REFERENCE:
            exception_class = StaleElementReferenceException
        elif status in ErrorCode.ELEMENT_NOT_VISIBLE:
            exception_class = ElementNotVisibleException
        elif status in ErrorCode.INVALID_ELEMENT_STATE:
            exception_class = InvalidElementStateException
        elif status in ErrorCode.INVALID_SELECTOR \
                or status in ErrorCode.INVALID_XPATH_SELECTOR \
                or status in ErrorCode.INVALID_XPATH_SELECTOR_RETURN_TYPER:
            exception_class = InvalidSelectorException
        elif status in ErrorCode.INVALID_QPATH:
            exception_class = InvalidQPathException
        elif status in ErrorCode.ELEMENT_IS_NOT_SELECTABLE:
            exception_class = ElementNotSelectableException
        elif status in ErrorCode.INVALID_COOKIE_DOMAIN:
            exception_class = WebDriverException
        elif status in ErrorCode.UNABLE_TO_SET_COOKIE:
            exception_class = WebDriverException
        elif status in ErrorCode.TIMEOUT:
            exception_class = TimeoutException
        elif status in ErrorCode.SCRIPT_TIMEOUT:
            exception_class = TimeoutException
        elif status in ErrorCode.UNKNOWN_ERROR:
            exception_class = WebDriverException
        elif status in ErrorCode.UNEXPECTED_ALERT_OPEN:
            exception_class = UnexpectedAlertPresentException
        elif status in ErrorCode.NO_ALERT_OPEN:
            exception_class = NoAlertPresentException
        elif status in ErrorCode.IME_NOT_AVAILABLE:
            exception_class = ImeNotAvailableException
        elif status in ErrorCode.IME_ENGINE_ACTIVATION_FAILED:
            exception_class = ImeActivationFailedException
        elif status in ErrorCode.MOVE_TARGET_OUT_OF_BOUNDS:
            exception_class = MoveTargetOutOfBoundsException
        elif status in ErrorCode.ROTATION_NOT_ALLOWED:
            exception_class = RotationNotAllowedException
        elif status in ErrorCode.APPLICATION_DEADLOCK_DETECTED:
            exception_class = ApplicationDeadlockException
        elif status in ErrorCode.APPLICATION_CRASHED:
            exception_class = ApplicationCrashedException
        elif status in ErrorCode.XCTestAgent_NOT_BACKGROUND:
            exception_class = XCTestAgentDeadException
        elif status in ErrorCode.SENDKEYS_FAILED:
            exception_class = SendKeysFailedException
        else:
            exception_class = WebDriverException
        
        if isinstance(status, int):
            value_json = response.get('value', None)
            if value_json and isinstance(value_json, six.string_types):
                try:
                    import json
                    value = json.loads(value_json)
                except:
                    pass
                else:
                    status = value['error']
                    message = value['message']
                    raise exception_class(response, message)

        value = response['value']
        if isinstance(value, six.string_types):
            if exception_class in self.ERROR_IN_RESPONSE_EXCEPTIONS:
                raise exception_class(response, value)
            raise exception_class(value)
        message = ''
        if 'message' in value:
            message = value['message']

        screen = None
        if 'screen' in value:
            screen = value['screen']

        stacktrace = None
        if 'stackTrace' in value and value['stackTrace']:
            stacktrace = []
            try:
                for frame in value['stackTrace']:
                    line = self._value_or_default(frame, 'lineNumber', '')
                    file = self._value_or_default(frame, 'fileName', '<anonymous>')
                    if line:
                        file = "%s:%s" % (file, line)
                    meth = self._value_or_default(frame, 'methodName', '<anonymous>')
                    if 'className' in frame:
                        meth = "%s.%s" % (frame['className'], meth)
                    msg = "    at %s (%s)"
                    msg = msg % (meth, file)
                    stacktrace.append(msg)
            except TypeError:
                pass
        if exception_class in self.ERROR_IN_RESPONSE_EXCEPTIONS:
            raise exception_class(response, message)
        elif exception_class == UnexpectedAlertPresentException and 'alert' in value:
            raise exception_class(message, screen, stacktrace, value['alert'].get('text'))
        raise exception_class(message, screen, stacktrace)

    def _value_or_default(self, obj, key, default):
        return obj[key] if key in obj else default
