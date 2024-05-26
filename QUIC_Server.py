import asyncio
import random
import socket

# Constants
SERVER_ADDRESS = ('localhost', 1234)  # Server address and port
BUFFER_SIZE = 1024  # Buffer size for receiving data

class QUICServerProtocol:
    def __init__(self, server):
        self.server = server

    def connection_made(self, transport):
        print("Client connected")
        self.transport = transport

    def connection_lost(self, exc):
        self.server.connection_lost()
        print("Client disconnected")

    def datagram_received(self, data, addr):
        # Simulate packet loss
        if random.random() < 0.1:  # Simulating 10% packet loss
            return

        # Handle incoming datagram
        self.server.packets_received += 1
        self.server.total_packet_rate += len(data)

        # Process the data (simulate file transfer)
        if data.endswith(b'EOF'):
            self.server.files_received += 1
            print("File received")
        else:
            self.server.total_data_rate += len(data)

class QUICServer:
    def __init__(self):
        self.transport = None
        self.files_received = 0
        self.packets_received = 0
        self.total_data_rate = 0
        self.total_packet_rate = 0

    async def serve(self):
        loop = asyncio.get_event_loop()
        # Create a socket and set SO_REUSEADDR option
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(SERVER_ADDRESS)  # Bind the socket to the address

        # Create a datagram endpoint using the socket
        self.transport, _ = await loop.create_datagram_endpoint(
            lambda: QUICServerProtocol(self),
            sock=sock
        )
        print("Server started")

        # Keep the server running indefinitely
        while True:
            await asyncio.sleep(1)  # Adjust as needed

    def connection_lost(self):
        # Perform cleanup tasks here
        pass

async def main():
    server = QUICServer()
    await server.serve()
    print("Server closed")

if __name__ == "__main__":
    asyncio.run(main())