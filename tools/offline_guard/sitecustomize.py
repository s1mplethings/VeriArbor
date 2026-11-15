"""Offline qualification subprocess guard: only loopback connections allowed."""
import socket

_connect = socket.socket.connect
_connect_ex = socket.socket.connect_ex


def _check(address):
    if isinstance(address, tuple) and address[0] not in ('127.0.0.1', '::1', 'localhost'):
        raise RuntimeError('CLOSURE_OFFLINE_ONLY: non-loopback network dispatch denied')


def connect(self, address):
    _check(address)
    return _connect(self, address)


def connect_ex(self, address):
    _check(address)
    return _connect_ex(self, address)


socket.socket.connect = connect
socket.socket.connect_ex = connect_ex
