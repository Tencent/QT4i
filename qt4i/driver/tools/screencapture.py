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

from __future__ import absolute_import, print_function

import Queue
import threading
import time
import struct
import subprocess
import re
import os
import traceback

import signal
import argparse
import atexit
import sys
from six.moves.socketserver import BaseRequestHandler
from six.moves.socketserver import TCPServer
from six.moves.socketserver import ThreadingMixIn
from six.moves.urllib.request import urlopen


from qt4i.driver.tools import logger as logging
from qt4i.driver.util import Process


DEFAULT_IP = '0.0.0.0'
DEFAULT_PORT = 12306
DEFAULT_AGENT_PORT = 8100
DEFAULT_PID_FILE = '/tmp/screencapure.pid'

logger = logging.get_logger()


class ArgumentParser(argparse.ArgumentParser):
    '''Argument parser, automatically display help while error
    '''

    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)


CMD_HELP = {
    "start": "start screencapure service daemon",
    "stop": "stop screencapure service daemon",
    "restart": "stop screencapure service daemon and start it again",
    "debug": "try to start screencapure service as a normal process for debug",
}

# 参数解析器
main_parser = ArgumentParser(description='QT4i screencapure program',
                             formatter_class=argparse.RawDescriptionHelpFormatter)

main_parser.add_argument('--pidfile', '-p', metavar='PIDFILE', dest='pidfile', default=DEFAULT_PID_FILE,
                         help='the path of pid file, %s is used by default' % DEFAULT_PID_FILE)

main_parser.add_argument('--udid', '-u', metavar='UDID', dest='udid', default=None,
                         help='udid of device')

main_parser.add_argument('--listen_port', '-l', metavar='LISTENPORT', dest='listen_port', default=DEFAULT_PORT,
                         help='listening port of driver server, port %s is used by default' % DEFAULT_PORT)

main_parser.add_argument('--mjpeg_port', '-m', metavar='MJPEGPORT', dest='mjpeg_port', default=DEFAULT_AGENT_PORT,
                         help='listening port of xctest agent, port %s is used by default' % DEFAULT_AGENT_PORT)

subparser_dict = {}
subparsers = main_parser.add_subparsers(title='List of Commands', metavar='COMMAND')
for command in CMD_HELP:
    subparser_dict[command] = subparsers.add_parser(command, help=CMD_HELP[command])
    subparser_dict[command].set_defaults(func=command)

subparser_dict['stop'].add_argument('--force', '-f', action='store_true', default=False,
                                    help='force stop driver server')


class Daemon(object):
    """
    A generic daemon class.
    Usage: subclass the Daemon class and override the run() method
    """

    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile

    def daemonize(self):
        """
        do the UNIX double-fork magic, see Stevens' "Advanced
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        # Do first fork
        self.fork()

        # Decouple from parent environment
        self.dettach_env()
        # Do second fork
        self.fork()

        # Flush standart file descriptors
        sys.stdout.flush()
        sys.stderr.flush()

        #
        self.attach_stream('stdin', mode='r')
        self.create_pidfile()

    def attach_stream(self, name, mode):
        """
        Replaces the stream with new one
        """
        stream = open(getattr(self, name), mode)
        os.dup2(stream.fileno(), getattr(sys, name).fileno())

    def dettach_env(self):
        os.chdir("/")
        os.setsid()
        os.umask(0)

    def fork(self):
        """
        Spawn the child process
        """
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as e:
            sys.stderr.write("Fork failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

    def create_pidfile(self):
        atexit.register(self.delpid)
        pid = str(os.getpid())
        open(self.pidfile, 'w+').write("%s\n" % pid)

    def delpid(self):
        """
        Removes the pidfile on process exit
        """
        os.remove(self.pidfile)

    def start(self, is_daemon=True):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        pid = self.get_pid()

        if pid:
            if Process().get_process_by_pid(pid, 'screencapture.py'):
                message = "pidfile %s already exist. Daemon already running?\n"
                logger.warning(message % self.pidfile)
                return
            else:
                os.remove(self.pidfile)

        # Start the daemon
        if is_daemon:
            self.daemonize()
        self.run()

    def get_pid(self):
        """
        Returns the PID from pidfile
        """
        try:
            pf = open(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except (IOError, TypeError):
            pid = None
        return pid

    def stop(self, silent=False):
        """
        Stop the daemon
        """
        # Get the pid from the pidfile
        pid = self.get_pid()

        if not pid:
            if not silent:
                message = "pidfile %s does not exist. Daemon not running?\n"
                logger.error(message % self.pidfile)
            return

            # Try killing the daemon process
        try:
            while True:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
        except OSError as err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                logger.error(str(err))
                sys.exit(1)

    def restart(self):
        """
        Restart the daemon
        """
        self.stop(silent=True)
        self.start()

    def run(self):
        """
        You should override this method when you subclass Daemon. It will be called after the process has been
        daemonized by start() or restart().
        """
        raise NotImplementedError


class ThreadedTCPServer(ThreadingMixIn, TCPServer):
    allow_reuse_address = True
    request_queue_size = 16


class ScreenConsumer(BaseRequestHandler):

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


class ScreenCaptureService(Daemon):

    def __init__(self, pidfile, udid, listen_port, mjpeg_port):
        Daemon.__init__(self, pidfile)
        self._udid = udid
        self._listen_port = listen_port
        self._mjpeg_port = mjpeg_port

    def start(self, is_daemon=True):
        '''启动service
        '''
        pid = self.get_pid()
        if pid:
            process = Process().get_process_by_pid(pid, 'screencapture.py')
            if process:
                Process().kill_process_by_pid(pid)
                logger.warning('Kill old screencapure server process %d' % pid)
            else:
                os.remove(self.pidfile)

        # start damon
        if is_daemon:
            self.daemonize()
        self.run()

    def run(self):
        if self._udid:
            if self._mjpeg_port:
                screen_producer = ScreenProducer(self._udid, int(self._mjpeg_port))
                screen_producer.start()
                server = ThreadedTCPServer(('localhost', int(self._listen_port)), ScreenConsumer)
                server.screen_producer = screen_producer
                server.serve_forever()

    def stop(self, silent=False):
        '''停止service
        '''
        Daemon.stop(self, silent)


class MJpegClient(object):

    def __init__(self, url):
        self.stream = urlopen(url)
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
            body = l[i + 1:].strip()

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

    def __init__(self, udid, mjpeg_port):
        super(ScreenProducer, self).__init__()
        self._clients = set()
        self._udid = udid
        self.running = True
        self._mutex = threading.Lock()
        self.no_client = True
        self.mjpeg_conn_event = threading.Event()
        self.mjpeg_conn_event.clear()

        if re.match(r'^[a-f0-9]+$', udid):
            self._is_simulator = False
            self._url = "http://127.0.0.1:%s" % mjpeg_port
        else:
            self._is_simulator = True

    @property
    def is_sim(self):
        return self._is_simulator

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
            logger.exception(traceback.format_exc())
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
            logger.exception(traceback.format_exc())
            time.sleep(1)

    def run(self):
        while self.running:
            if self.is_sim:
                self._capture_screen_by_simctl()
            else:
                self._capture_screen_by_xctestagent()

    def stop(self):
        self.running = False


if __name__ == '__main__':
    args = main_parser.parse_args()
    sc = ScreenCaptureService(args.pidfile, args.udid, args.listen_port, args.mjpeg_port)

    if args.func == 'start':
        sc.start()

    elif args.func == 'stop':
        sc.stop()

    elif args.func == 'restart':
        sc.restart()

    elif args.func == 'debug':
        sc.start(False)

    else:
        main_parser.print_help()
        sys.exit(1)
