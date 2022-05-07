

import socket
class DNSServer:
    def __init__(self, ip='127.0.0.1', port=5533):
        self.index = 0
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.ip, self.port))
        self.file_name = "10servers"
        self.servers = []
        with open(self.file_name) as file_object:
            for line in file_object:
                self.servers.append(line.strip('\n'))
    
    def start(self):
        while True:
            message, address = self.receive()
            self.reply(address)

    def receive(self):
        return self.socket.recvfrom(2333)

    def reply(self, address):
        self.index += 1
        self.index %= len(self.servers)
        self.socket.sendto((self.servers[self.index]).encode(), address)

if __name__ == '__main__':
    dns = DNSServer()
    dns.start()