#! /usr/bin/env python3
"""Sends a message to unlock the vault"""

import socket

client = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
client.connect('/tmp/bitwarden.sock')
client.send(b'OPEN')
client.close()
