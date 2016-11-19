
install:
	install mcast2http.py /usr/local/bin/mcast2http
	install -m 0644 mcast2http.service /etc/systemd/system/

uninstall:
	rm /usr/local/bin/mcast2http
	rm /etc/systemd/system/mcast2http.service
