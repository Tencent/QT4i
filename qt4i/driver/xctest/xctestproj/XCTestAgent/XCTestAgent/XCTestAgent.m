/**
 * Tencent is pleased to support the open source community by making QTA available.
 * Copyright (C) 2016THL A29 Limited, a Tencent company. All rights reserved.
 * Licensed under the BSD 3-Clause License (the "License"); you may not use this
 * file except in compliance with the License. You may obtain a copy of the License at
 *
 * https://opensource.org/licenses/BSD-3-Clause
 *
 * Unless required by applicable law or agreed to in writing, software distributed
 * under the License is distributed on an "AS IS" basis, WITHOUT WARRANTIES OR CONDITIONS
 * OF ANY KIND, either express or implied. See the License for the specific language
 * governing permissions and limitations under the License.
 */

#import <XCTest/XCTest.h>

#import <WebDriverAgentLib/FBDebugLogDelegateDecorator.h>
#import <WebDriverAgentLib/FBConfiguration.h>
#import <WebDriverAgentLib/FBFailureProofTestCase.h>
#import <WebDriverAgentLib/FBWebServer.h>
#import <WebDriverAgentLib/XCTestCase.h>

@interface XCTestAgent : FBFailureProofTestCase <FBWebServerDelegate>

@end

@implementation XCTestAgent

+ (void)setUp
{
    [FBDebugLogDelegateDecorator decorateXCTestLogger];
    [FBConfiguration disableRemoteQueryEvaluation];
    [super setUp];
}

/**
 Never ending test used to start WebDriverAgent
 */
- (void)testRunner
{
    FBWebServer *webServer = [[FBWebServer alloc] init];
    webServer.delegate = self;
    [webServer startServing];
}

#pragma mark - FBWebServerDelegate

- (void)webServerDidRequestShutdown:(FBWebServer *)webServer
{
    [webServer stopServing];
}

@end
