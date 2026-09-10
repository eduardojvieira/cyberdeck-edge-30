#!/usr/bin/env python3
"""Read-only Wayfire 0.9 IPC snapshot; no screen/input mutation."""
import glob
import json
import os
import socket
import stat
import struct


def receive(sock, size):
    data = bytearray()
    while len(data) < size:
        part = sock.recv(size - len(data))
        if not part:
            raise EOFError('Wayfire closed an incomplete response')
        data.extend(part)
    return data


def query(sock, method, data=None):
    request = json.dumps({'method': method, 'data': data or {}}).encode()
    sock.sendall(struct.pack('=I', len(request)) + request)
    size, = struct.unpack('=I', receive(sock, 4))
    if not 0 < size <= 1024 * 1024:
        raise ValueError('Invalid Wayfire response size')
    return json.loads(receive(sock, size))


if __name__ == '__main__':
    paths = glob.glob(f'/run/user/{os.getuid()}/wayfire-*.socket') + glob.glob('/tmp/wayfire-*.socket')
    paths = [p for p in paths if stat.S_ISSOCK(os.stat(p).st_mode) and os.stat(p).st_uid == os.getuid()]
    if len(paths) != 1:
        raise RuntimeError(f'Expected one owned Wayfire socket, found {len(paths)}')
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.settimeout(2)
        sock.connect(paths[0])
        for method in ('window-rules/list-outputs', 'window-rules/list-views'):
            print(json.dumps({'method': method, 'result': query(sock, method)}), flush=True)
        method = 'wayfire/get-config-option'
        option = {'option': 'autorotate-iio/lock_rotation'}
        print(json.dumps({'method': method, 'data': option, 'result': query(sock, method, option)}), flush=True)
