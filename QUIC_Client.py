import asyncio
import random
import time
from aiostream import stream

# Constants
SERVER_ADDRESS = ('localhost', 1234)  # Server address and port
num_flows = 3  # Number of concurrent flows

class QUICClientProtocol(asyncio.DatagramProtocol):
    def __init__(self, client):
        self.transport = None
        self.client = client

    def connection_made(self, transport):
        print("Connected to server")
        self.transport = transport
        self.client.transport = transport  # Store transport in client

    def connection_lost(self, exc):
        print("Connection lost")

    def datagram_received(self, data, addr):
        if data == b'EOF':
            print("File transfer completed")
            self.transport.close()

class QUICClient:
    def __init__(self):
        self.transport = None
        self.stats = []  # List to store statistics for each flow

    async def connect(self):
        loop = asyncio.get_running_loop()
        # Create a datagram endpoint
        self.transport, _ = await loop.create_datagram_endpoint(
            lambda: QUICClientProtocol(self),
            remote_addr=SERVER_ADDRESS
        )
        print("Connection established")

    def send_file(self, filename, num_flows=1):
        # Generate random packet sizes for each flow
        flow_packet_sizes = [random.randint(1000, 2000) for _ in range(num_flows)]
        print(f"Flow packet sizes: {flow_packet_sizes}")

        async def file_stream(flow_id):
            chunk_size = flow_packet_sizes[flow_id]
            bytes_sent = 0
            packets_sent = 0
            start_time = time.time()

            with open(filename, 'rb') as file:
                file.seek(flow_id * chunk_size)  # Seek to start position for the flow
                while chunk := file.read(chunk_size):
                    yield chunk
                    bytes_sent += len(chunk)
                    packets_sent += 1
                    await asyncio.sleep(0.01)  # Simulate some delay

            yield b'EOF'
            end_time = time.time()

            duration = end_time - start_time
            # Store statistics for the flow
            self.stats.append({
                'flow_id': flow_id,
                'bytes_sent': bytes_sent,
                'packets_sent': packets_sent,
                'duration': duration,
                'avg_data_rate': bytes_sent / duration,
                'avg_packet_rate': packets_sent / duration
            })

        # Create a stream for each flow
        return [stream.iterate(file_stream(i)) for i in range(num_flows)]

async def main():
    client = QUICClient()
    await client.connect()
    
    # Send file using multiple flows
    file_streams = client.send_file('example.txt', num_flows=num_flows)
    
    async def send_stream(file_stream):
        async with file_stream.stream() as streamer:
            async for chunk in streamer:
                client.transport.sendto(chunk)
                print(f"Sent chunk: {len(chunk)} bytes")

    await asyncio.gather(*(send_stream(fs) for fs in file_streams))
    
    # Print statistics after file transfer
    total_bytes_sent = 0
    total_packets_sent = 0
    total_duration = max(stat['duration'] for stat in client.stats)
    
    for stat in client.stats:
        print(f"Flow {stat['flow_id']} statistics:")
        print(f"  Total bytes sent: {stat['bytes_sent']} bytes")
        print(f"  Total packets sent: {stat['packets_sent']} packets")
        print(f"  Average data rate: {stat['avg_data_rate']:.2f} bytes/second")
        print(f"  Average packet rate: {stat['avg_packet_rate']:.2f} packets/second")

        total_bytes_sent += stat['bytes_sent']
        total_packets_sent += stat['packets_sent']

    print(f"Total statistics:")
    print(f"  Total bytes sent: {total_bytes_sent} bytes")
    print(f"  Total packets sent: {total_packets_sent} packets")
    print(f"  Overall average data rate: {total_bytes_sent / total_duration:.2f} bytes/second")
    print(f"  Overall average packet rate: {total_packets_sent / total_duration:.2f} packets/second")
    print(f"  Total duration: {total_duration:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main())