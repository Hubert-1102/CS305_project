import socket


# import proxy1_framework


class DNSServer:
    def __init__(self, ip='127.0.0.1', port=5523):
        self.index = 0
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.ip, self.port))
        self.file_name = "servers/2servers"
        self.servers = []

    def start(self):
        # 向netsim.py 发送请求以获得对应文件名，只请求一次
        self.socket.sendto('file'.encode(), ('127.0.0.1', 5555))
        file_receive, address2 = self.socket.recvfrom(2333)
        self.file_name = file_receive.decode()
        with open(self.file_name) as file_object:
            for line in file_object:
                self.servers.append(line.strip('\n'))
        while True:
            message, address = self.receive()
            if message.decode() == 'esc':
                # 收到退出信号
                exit(0)
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
