import unittest
from unittest.mock import patch, MagicMock
import socket
import threading

# Mocking QUICClient from QUIC_Client.py
class QUICClient:
    def _init_(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self.client_socket.connect((self.server_ip, self.server_port))

    def send_message(self, message):
        self.client_socket.sendall(message.encode())

    def receive_message(self):
        return self.client_socket.recv(1024).decode()

    def close_connection(self):
        self.client_socket.close()

# Mocking QUICServer from QUIC_Server.py
class QUICServer:
    def _init_(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.client_handlers = []

    def start_server(self):
        while True:
            client_socket, client_address = self.server_socket.accept()
            handler = threading.Thread(target=self.handle_client, args=(client_socket,))
            self.client_handlers.append(handler)
            handler.start()

    def handle_client(self, client_socket):
        while True:
            message = client_socket.recv(1024).decode()
            if not message:
                break
            client_socket.sendall(f"Echo: {message}".encode())
        client_socket.close()

    def stop_server(self):
        self.server_socket.close()
        for handler in self.client_handlers:
            handler.join()

class TestQUICClient(unittest.TestCase):

    @patch('socket.socket')
    def setUp(self, mock_socket):
        self.mock_socket_instance = mock_socket.return_value
        self.client = QUICClient('127.0.0.1', 8080)

    def test_connect_success(self):
        self.client.connect()
        self.mock_socket_instance.connect.assert_called_with(('127.0.0.1', 8080))

    def test_send_message_success(self):
        self.client.send_message('Hello, Server')
        self.mock_socket_instance.sendall.assert_called_with(b'Hello, Server')

    def test_receive_message_success(self):
        self.mock_socket_instance.recv.return_value = b'Hello, Client'
        response = self.client.receive_message()
        self.assertEqual(response, 'Hello, Client')

    def test_close_connection(self):
        self.client.close_connection()
        self.mock_socket_instance.close.assert_called_once()

class TestQUICServer(unittest.TestCase):

    @patch('socket.socket')
    def setUp(self, mock_socket):
        self.mock_socket_instance = mock_socket.return_value
        self.server = QUICServer('127.0.0.1', 8080)

    def test_start_server(self):
        with patch.object(self.server, 'handle_client', return_value=None):
            self.mock_socket_instance.accept.return_value = (MagicMock(), ('127.0.0.1', 50000))
            # Run the server in a separate thread to allow the test to run the accept loop once
            server_thread = threading.Thread(target=self.server.start_server)
            server_thread.start()
            self.mock_socket_instance.bind.assert_called_with(('127.0.0.1', 8080))
            self.mock_socket_instance.listen.assert_called_once_with(5)
            server_thread.join(timeout=1)  # Ensure the thread does not block forever

    def test_handle_client(self):
        mock_client_socket = MagicMock()
        mock_client_socket.recv.side_effect = [b'Hello, Server', b'']
        self.server.handle_client(mock_client_socket)
        mock_client_socket.sendall.assert_called_with(b'Echo: Hello, Server')

    def test_stop_server(self):
        self.server.stop_server()
        self.mock_socket_instance.close.assert_called_once()

if _name_ == '_main_':
    unittest.main()