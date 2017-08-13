#!/usr/bin/env python
"""
Multicast to HTTP relay server.

Copyright 2016 Lasse Karstensen

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import sys
import struct
import socket
import argparse
import BaseHTTPServer
import SocketServer
from time import time
from urlparse import urlparse
from logging import basicConfig, DEBUG, INFO, debug, info
from SimpleHTTPServer import SimpleHTTPRequestHandler

import daemon

READ_BUFFER_SIZE = 4096


def is_class_d(addr):
    """
    >>> is_class_d("239.0.0.254")
    True
    >>> is_class_d("index.html")
    False
    >>> is_class_d("10.0.0.2")
    False
    """
    assert type(addr) == str
    try:
        socket.inet_pton(socket.AF_INET, addr)
        net = int(addr[:3])  # Dirty
    except (ValueError, socket.error) as e:
        return False

    if net < 224 or net > 239:
        return False
    return True


class RelayHandler(SimpleHTTPRequestHandler):
    sys_version = "v0.1"
    server_version = "mcast2http"

    def synth_error(self, returncode, message):
        msg = "%s %s" % (returncode, message)
        self.send_response(returncode)
        self.send_header("Content-type", "text/plain")
        self.send_header("Content-Length", len(msg))
        self.send_header("Connection", "close")
        self.send_header("Cache-Control", "private, no-cache, must-revalidate")
        self.end_headers()
        self.wfile.write(msg)

    def parse_request_path(self, path):
        p = urlparse(path)
        patharg = p.path.split("/")
        if len(patharg) == 2:  # Short format, use default port.
            addr = (patharg[1], 1234)
        elif len(patharg) == 3:  # /group/port
            try:
                addr = (patharg[1], int(patharg[2]))
            except ValueError:
                return False
        else:
            return False

        if not is_class_d(addr[0]):
            return False

        return addr

    def do_HEAD(self):
        addr = self.parse_request_path(self.path)
        if addr is False:
            return self.synth_error(400, "Bad request")

        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Connection", "close")
        self.end_headers()

    def do_GET(self):
        # Try out some delay-related socket options on client connection.
        self.connection.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
        self.connection.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0x10)

        info("%s requested %s" % (self.client_address[0], self.path))

        if self.path in ["/", "/favicon.ico"]:
            return self.synth_error(403, "Forbidden")

        addr = self.parse_request_path(self.path)
        if not addr:
            return self.synth_error(400, "Bad request")

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                             socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(addr)

        sock.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF,
                        socket.inet_aton(self.server.config.mcastip))
        mreq = struct.pack('4sl', socket.inet_aton(addr[0]), socket.INADDR_ANY)
        sock.setsockopt(socket.SOL_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        sock.settimeout(self.server.config.timeout / 1.0e3)

        initial_read = True
        bytecount = 0L
        t0 = time()

        while True:
            try:
                chunk = sock.recv(READ_BUFFER_SIZE)
            except socket.timeout as e:
                info("%s read timeout after %.2fs: %s" %
                     (self.path, time() - t0, e.message))

                if initial_read:
                    return self.synth_error(404,
                                            "No data received after %.2f seconds\n" %
                                            sock.gettimeout())
                break

            if initial_read:
                self.send_response(200)
                self.send_header("Content-type", "application/octet-stream")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Connection", "close")
                self.end_headers()
                info("%s:%s ttfb %.3fms" % (addr[0], addr[1],
                                            (time() - t0)*1.0e3))

            try:
                self.wfile.write(chunk)
                bytecount += len(chunk)
                if initial_read:
                    self.wfile.flush()
                    initial_read = False
            except socket.error as e:
                if e.errno == 104:  # Connection reset by peer.
                    pass
                else:
                    info("%s %s: %s" % (self.client_address[0], self.path,
                                        str(e)))
                break

        info("%s finished %s:%s after %i bytes" %
             (self.client_address[0], addr[0], addr[1], bytecount))
        del sock


class ThreadedHTTPServer(SocketServer.ThreadingMixIn,
                         BaseHTTPServer.HTTPServer):
    """Handle requests in a separate thread."""
    def handle_error(self, request, client_address):
        if self.config.debug:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="mcast2http - multicast to HTTP relay.",
        epilog="Relays multicasted data to HTTP clients.")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Be verbose.")
    parser.add_argument("--fork", action="store_true", default=False,
                        help="Daemonize process.")
    parser.add_argument("--pidfile", default="/var/tmp/mcast2http.pid",
                        help="File to write process identifier to when daemonized.")
    parser.add_argument("--mcastip", type=str,
                        help="""Source IPv4 address to join multicast groups from.
                        NOTE! If unset, a short TCP connection to google.com
                        will determine the local address.""")
    parser.add_argument("--timeout", default=2000, type=int,
                        help="""Time out requests after this long.
                             (Default: 2000 [milliseconds])""")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debugging output.")
    parser.add_argument("listen", type=str,
                        help="""HTTP server listen address.
                        (Examples: "0.0.0.0", "::")""")
    parser.add_argument("port", type=int,
                        help="HTTP server listen port.  (Example: 8080)")

    if len(sys.argv) == 1:
        parser.print_help()
        exit()
    args = parser.parse_args()

    if args.verbose:
        basicConfig(level=DEBUG)
    else:
        basicConfig(level=INFO)

    # I'm not very happy about this, but it seems like the only semi-
    # portable way to find what public IP address is going to be used.
    if args.mcastip is None:
        debug("Connecting to google.com to find our public address...")
        s = socket.create_connection(("ipv4.google.com", 80))
        assert s.family == socket.AF_INET
        args.mcastip = s.getsockname()[0]
        s.close()

    debug("Will join groups from ip4:%s" % args.mcastip)

    SocketServer.TCPServer.allow_reuse_address = True
    if ":" in args.listen:  # Dirty
        SocketServer.TCPServer.address_family = socket.AF_INET6

    httpd = ThreadedHTTPServer((args.listen, args.port), RelayHandler)
    httpd.config = args

    if args.fork:
        daemon.daemonize(args.pidfile)

    info("Listening on port [%s]:%s" % (args.listen, args.port))

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        info("Ctrl-c caught, normal exit")
