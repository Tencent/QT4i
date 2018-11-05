# -*- coding:utf-8 -*-
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
'''远程控制的截屏服务
'''

import Queue
import threading
import time
import SocketServer
import struct
import subprocess
import urllib
import re
import traceback
import os
import sqlite3
from qt4i.driver.tools import logger


class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    allow_reuse_address = True
    request_queue_size = 16


class ScreenConsumer(SocketServer.BaseRequestHandler):
    
    def setup(self):
        self.screenqueue = Queue.Queue(24)
        self.screen_producer = self.server.screen_producer
        assert self.request.recv(10) == 'screenshot'
        self.screen_producer.add_client(self)
    
    def handle(self):
        while True:
            image_data = self.screenqueue.get()
            try:
                image_length = len(image_data)
                self.request.sendall(struct.pack("I", image_length) + image_data)
            except:
                break
        
    def finish(self):
        self.request.close()
        self.screen_producer.remove_client(self)


class ScreenCaptureService(object):
    
    
    def __init__(self, udid, listen_port):
        self.logger = logger.get_logger('driverserver_%s' % udid)
        self._udid = udid
        screen_producer = ScreenProducer(udid, self.logger)
        screen_producer.start()
        server = ThreadedTCPServer(('localhost', listen_port), ScreenConsumer)
        server.screen_producer = screen_producer
        server.serve_forever()


class MJpegClient(object):
    
    
    def __init__(self, url):
        self.stream = urllib.urlopen(url)
        self.boundary = None
        
    def parse_mjpeg_boundary(self):
        '''
        parse mjpeg stream boundary
        :param stream: mjpeg client stream
        :type stream: http.client.HTTPResponse
        :returns: str -- boundary
        '''
        
        if self.stream.getcode() != 200:
            raise Exception('Invalid response from server: %d' % self.stream.status)
        h = self.stream.info()
        content_type = h.get('Content-Type', None)
        match = re.search(r'boundary="?(.*)"?', content_type) 
        if match is None:
            raise Exception('Content-Type header does not provide boundary string')
        self.boundary = match.group(1)
    
    def read_mjpeg_frame(self):
        hdr = self._read_headers(self.boundary)
    
        clen = self._parse_content_length(hdr)
        if clen == 0:
            raise EOFError('End of stream reached')
    
        self._check_content_type(hdr, 'image/jpg')
        left = clen
        buf = ''
        while left > 0:
            tmp = self.stream.read(left)
            buf += tmp
            left -= len(tmp)
        return buf
    
    def close(self):
        self.stream.close()
        
    def _read_header_line(self):
        '''Read one header line within the stream.
        The headers come right after the boundary marker and usually contain
        headers like Content-Type and Content-Length which determine the type and
        length of the data portion.
        '''
        return self.stream.readline().strip()

    def _read_headers(self, boundary):
        '''Read and return stream headers.
        Each stream data packet starts with an empty line, followed by a boundary
        marker, followed by zero or more headers, followed by an empty line,
        followed by actual data. This function reads and parses the entire header
        section. It returns a dictionary with all the headers. Header names are
        converted to lower case. Each value in the dictionary is a list of header
        fields values.
        '''
        l = ''
        while True:
            l = self._read_header_line()
            if l != '':
                break
        if l != boundary:
            raise Exception('Boundary string expected, but not found')
    
        headers = {}
        while True:
            l = self._read_header_line()
            # An empty line indicates the end of the header section
            if l == '':
                break
    
            # Parse the header into lower case header name and header body
            i = l.find(':')
            if i == -1:
                raise Exception('Invalid header line: ' + l)
            name = l[:i].lower()
            body = l[i+1:].strip()
    
            lst = headers.get(name, list())
            lst.append(body)
            headers[name] = lst
    
        return headers

    def _parse_content_length(self, headers):
        # Parse and check Content-Length. The header must be present in
        # each chunk, otherwise we wouldn't know how much data to read.
        clen = headers.get('content-length', None)
        try:
            return int(clen[0])
        except (ValueError, TypeError):
            raise Exception('Invalid or missing Content-Length')
        
    def _check_content_type(self, headers, expected_type):
        ctype = headers.get('content-type', None)
        if ctype is None:
            raise Exception('Missing Content-Type header')
        ctype = ctype[0]
    
        i = ctype.find(';')
        if i != -1:
            ctype = ctype[:i]
        if ctype != expected_type:
            raise Exception('Wrong Content-Type: %s' % ctype)
        return True


class ScreenProducer(threading.Thread):
    
    
    def __init__(self, udid, logger):
        super(ScreenProducer, self).__init__()
        self.logger = logger
        self._clients = set()
        self._udid = udid
        self.running = True
        self._mutex = threading.Lock()
        self.no_client = True
        self.mjpeg_conn_event = threading.Event()
        self.mjpeg_conn_event.clear()  
              
        if re.match(r'^[a-f0-9]+$', udid):
            self._is_simulator = False
            mjpeg_port = self._get_mjpeg_port_from_db()
            self._url = "http://127.0.0.1:%s" % mjpeg_port
        else:
            self._is_simulator = True

    @property
    def is_sim(self):
        return self._is_simulator
    
    def _get_mjpeg_port_from_db(self):
        devhost_db = os.path.abspath(os.path.expanduser('~/drun5/devicehost/conf/devhost.db'))
        print devhost_db
        conn = sqlite3.connect(devhost_db)
        cmd = '''select agent_port from device where (udid = "%s")'''  %  self._udid
        rows = conn.execute(cmd).fetchall()
        if len(rows) > 0:
            port = rows[0][0]
            conn.close()
            return port+1000
        else:
            raise Exception('device:[%s] not exists in devhost.db')

    def add_client(self, client):
        with self._mutex:
            self._clients.add(client)
        self.no_client = False
        self.mjpeg_conn_event.set()
    
    def remove_client(self, client):
        with self._mutex:
            self._clients.discard(client)
            if len(self._clients) == 0:
                self.no_client = True
                self.mjpeg_conn_event.clear()
            
    def process_mjpeg_stream(self, mjpeg_client):
        mjpeg_client.parse_mjpeg_boundary()
        
        while True:
            jpeg_frame = mjpeg_client.read_mjpeg_frame()
            with self._mutex:
                if len(self._clients) == 0:
                    break
            for client in self._clients:
                if client.screenqueue.full():
                    continue
                client.screenqueue.put(jpeg_frame)
                
    def _capture_screen_by_xctestagent(self):
        try:
            if self.no_client:
                self.mjpeg_conn_event.wait()
            mjpeg_client = MJpegClient(self._url)
            self.process_mjpeg_stream(mjpeg_client)
        except EOFError:
            pass
        except Exception:
            self.logger.exception(traceback.format_exc()) 
        finally:
            mjpeg_client.close()          
        
    def _capture_screen_by_simctl(self):
        try:
            if self.no_client:
                self.mjpeg_conn_event.wait()
            cmd = 'xcrun simctl io %s screenshot --type=jpeg -' % self._udid
            jpeg_frame = subprocess.check_output(cmd, shell=True)
            with self._mutex:
                if len(self._clients) == 0:
                    return
            for client in self._clients:
                if client.screenqueue.full():
                    continue
                client.screenqueue.put(jpeg_frame)            
        except:
            self.logger.exception(traceback.format_exc())
            time.sleep(1)

    def run(self):
        while self.running:
            if self.is_sim:
                self._capture_screen_by_simctl()
            else:
                self._capture_screen_by_xctestagent()
        
    def stop(self):
        self.running = False