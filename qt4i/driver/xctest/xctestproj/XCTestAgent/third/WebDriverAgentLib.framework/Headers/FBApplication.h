/**
 * Copyright (c) 2015-present, Facebook, Inc.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree. An additional grant
 * of patent rights can be found in the PATENTS file in the same directory.
 */

#import <WebDriverAgentLib/XCUIApplication.h>

NS_ASSUME_NONNULL_BEGIN

@interface FBApplication : XCUIApplication

/**
 Constructor used to get current active application
 */
+ (nullable instancetype)fb_activeApplication;

/**
 Constructor used to get the system application
 */
+ (instancetype)fb_systemApplication;

/**
 It allows to turn on/off waiting for application quiescence, while performing queries. Defaults to NO.
 */
@property (nonatomic, assign) BOOL fb_shouldWaitForQuiescence;

@end

NS_ASSUME_NONNULL_END
