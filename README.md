# Multicast to HTTP relay server

Relay an IPv4 multicast group out on a HTTP connection. Multicast group
and port are specificed in the HTTP URL.

Running it:

    $ /usr/local/bin/mcast2http 0.0.0.0 8080

Start with "--help" (or no args) to list other accepted arguments.

Client-side example:

    $ curl http://localhost:8080/239.255.0.10/1234

will send any data received from the group 239.255.0.10 on port 1234 to
curl (which will print to stdout, ruining your terminal :-)).

Content-Type is application/octet-stream.

Typical usage is for viewing dvb/mpeg2ts streams. Usually an .m3u
playlist file fed to VLC/Kodi make more suitable clients.

There is no authorization or authentication.

Back of envelope performance evaluation indicate that this will serve
100-500Mbit/s on recent hardware. I don't believe it to handle multiple
cores especially well, but it is good enough for me right now.

## Known issues

* There is no authorization or authentication.
* Content-Type is always application/octet-stream, should be configurable.
* The finishing log statements are never run, since SocketServer throws a
socket.error with pipe closed when the client hangs up.


## Installation

For now a simple Makefile will install (and overwrite!) the juicy
parts. Beware!

    $ pip install daemon
    $ sudo make install

The daemon is usually run under systemd with the service file included. It
can also run standalone with --fork on non systemd systems.

## Contact

Issue tracking on the github issue tracker.

Author: Lasse Karstensen <lasse.karstensen@gmailNO_SPAM_PLEASE.com>, November 2014.
