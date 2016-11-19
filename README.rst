# Multicast to HTTP relay server.

Reads from a HTTP specificed multicast group:port and relay the received
data out over the HTTP socket.

Run with:

   $ ./mcast2http.py 0.0.0.0 8080

Supply your eth0/em0 address to --ip for multicast joins to work. Start
with "--help" to list other non-mandatory arguments.

Client-side example:

    $ curl http://example.com:8080/239.255.0.10/1234

will send any data received from the group 239.255.0.10 on port 1234 to
curl (which will print to stdout, ruining your terminal :-)).
Content-Type is application/octet-stream.

Typical usage is for viewing dvb/mpeg2ts streams. Usually an .m3u
playlist file fed to VLC/Kodi make more suitable clients.

There is no authorization or authentication.

Back of envelope performance evaluation indicate that this will serve
100-500Mbit/s on recent hardware. I don't believe it to handle multiple
cores especially well, but it is good enough for me right now.

## Contact

Author: Lasse Karstensen <lasse.karstensen@gmail.com>, November 2014.
