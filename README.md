# IPv4 multicast to HTTP relay

Relay an IPv4 multicast group out on a HTTP connection. Multicast group
and port are specificed in the HTTP URL.

## Running

```
$ /usr/local/bin/mcast2http 0.0.0.0 8080
```

## Usage

    usage: mcast2http.py [-h] [-v] [--fork] [--pidfile PIDFILE]
		     [--mcastip MCASTIP] [--timeout TIMEOUT] [--debug]
		     listen port

    mcast2http - multicast to HTTP relay.

    positional arguments:
    listen             HTTP server listen address. (Examples: "0.0.0.0", "::")
    port               HTTP server listen port. (Example: 8080)

    optional arguments:
    -h, --help         show this help message and exit
    -v, --verbose      Be verbose.
    --fork             Daemonize process.
    --pidfile PIDFILE  File to write process identifier to when daemonized.
    --mcastip MCASTIP  Source IPv4 address to join multicast groups from. NOTE!
		     If unset, a short TCP connection to google.com will
		     determine the local address.
    --timeout TIMEOUT  Time out requests after this long. (Default: 2000
		     [milliseconds])
    --debug            Enable debugging output.

    Relay multicast data to HTTP clients.


## Client example

```
$ curl http://localhost:8080/239.255.0.10/1234
```

This will send any data received from the group `239.255.0.10` on port `1234` to
the HTTP client (in this case curl.)

Typical usage is for viewing DVB (MPEG2 TS) streams multicasted outside
of your control (MuMuDVB, other head-ends) on a network without multicast
routing.

A sample .m3u playlist file for VLC, XBMC/Kodi or similar players is included.

Back of envelope performance evaluation indicate that this will serve
100-500Mbit/s on recent hardware. Good enough for now.

## Known issues

* There is no authorization or authentication.
* Content-Type is always application/octet-stream, should be configurable.
* The finishing log statements are never run, since SocketServer throws a
socket.error with pipe closed when the client hangs up.


## Installation

For now a simple Makefile will install (and overwrite) the daemon.

    $ pip install daemon
    $ sudo make install

The daemon is usually run under systemd with the service file included. It
can also run standalone with --fork on non systemd systems.

## Contact

Issue tracking on the github issue tracker.

Author: Lasse Karstensen <lasse.karstensen@gmailNO_SPAM_PLEASE.com>, November 2014.
