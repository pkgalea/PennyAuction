import pyshark
capture = pyshark.LiveCapture(interface='eth0')
capture.sniff(timeout=10)
capture