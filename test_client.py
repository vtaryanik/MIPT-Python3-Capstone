
"""
    Unittest for the class Client.

        python -m unittest test_client.py
"""

import unittest
from unittest.mock import patch
from collections import deque

# импорт модуля с решением
from client import Client, ClientError


class ServerSocketException(Exception):
    pass


class ServerSocket:
    """Mock socket module"""

    def __init__(self):
        self.response_buf = deque()
        self.rsp_map = {
            b'put test 0.5 1\n': b'ok\n\n',
            b'put test 2.0 2\n': b'ok\n\n',
            b'put test 0.4 2\n': b'ok\n\n',
            b'put load 301 3\n': b'ok\n\n',
            b'get key_not_exists\n': b'ok\n\n',
            b'get test\n': b'ok\n'
                           b'test 0.5 1\n'
                           b'test 0.4 2\n\n',
            b'get get_client_error\n': b'error\nwrong command\n\n',
            b'get *\n': b'ok\n'
                        b'test 0.5 1\n'
                        b'test 0.4 2\n'
                        b'load 301 3\n\n',
        }

    def sendall(self, data):
        return self.send(data)

    def send(self, data):
        if data in self.rsp_map:
            self.response_buf.append(self.rsp_map[data])
        else:
            raise ServerSocketException(f"request doesn't fit the protocol: {data}")

    def recv(self, bytes_count):
        try:
            rsp = self.response_buf.popleft()
        except IndexError:
            raise ServerSocketException("no data in the socket")

        return rsp

    @classmethod
    def create_connection(cls, *args, **kwargs):
        return cls()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __getattr__(self, feature):
        """ignore socket.connect, soket.bind, etc..."""
        pass


class TestClient(unittest.TestCase):
    @classmethod
    @patch("socket.create_connection", ServerSocket.create_connection)
    @patch("socket.socket", ServerSocket.create_connection)
    def setUpClass(cls):
        cls.client = Client("127.0.0.1", 10000, timeout=2)

    @patch("socket.create_connection", ServerSocket.create_connection)
    @patch("socket.socket", ServerSocket.create_connection)
    def test_client_put(self):
        metrics_for_put = [
            ("test", 0.5, 1),
            ("test", 2.0, 2),
            ("test", 0.4, 2),
            ("load", 301, 3),
        ]
        for metric, value, timestamp in metrics_for_put:
            try:
                self.client.put(metric, value, timestamp)
            except ServerSocketException as exp:
                message = exp.args[0]
                self.fail(f"Error invoking client.put("
                          f"'{metric}', {value}, timestamp={timestamp})\n{message}")

    @patch("socket.create_connection", ServerSocket.create_connection)
    @patch("socket.socket", ServerSocket.create_connection)
    def test_client_get_key(self):
        try:
            rsp = self.client.get("test")
        except ServerSocketException as exp:
            message = exp.args[0]
            self.fail(f"Error invoking client.get('test')\n{message}")

        metrics_fixture = {
            "test": [(1, .5), (2, .4)],
        }
        self.assertEqual(rsp, metrics_fixture)

    @patch("socket.create_connection", ServerSocket.create_connection)
    @patch("socket.socket", ServerSocket.create_connection)
    def test_client_get_all(self):
        try:
            rsp = self.client.get("*")
        except ServerSocketException as exp:
            message = exp.args[0]
            self.fail(f"Error invoking client.get('*')\n{message}")

        metrics_fixture = {
            "test": [(1, .5), (2, .4)],
            "load": [(3, 301.0)]
        }
        self.assertEqual(rsp, metrics_fixture)

    @patch("socket.create_connection", ServerSocket.create_connection)
    @patch("socket.socket", ServerSocket.create_connection)
    def test_client_get_not_exists(self):
        try:
            rsp = self.client.get("key_not_exists")
        except ServerSocketException as exp:
            message = exp.args[0]
            self.fail(f"Error invoking client.get('key_not_exists')\n{message}")

        self.assertEqual({}, rsp, "check rsp eq {}")

    @patch("socket.create_connection", ServerSocket.create_connection)
    @patch("socket.socket", ServerSocket.create_connection)
    def test_client_get_client_error(self):
        try:
            self.assertRaises(ClientError,
                              self.client.get, "get_client_error")
        except ServerSocketException as exp:
            message = exp.args[0]
            self.fail(f"Server's error message has been processed incorrectly: {message}")
