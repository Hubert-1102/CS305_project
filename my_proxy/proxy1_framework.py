import ctypes
import inspect
import socket
import logging
import math
import os
import sys
import threading
import time
from sys import argv
from urllib import request
from flask import Flask, Response, Request
import requests
import dns_server

ip = '127.0.0.1'
port = 5566
dns_ip = '127.0.0.1'
app = Flask(__name__)
rates = []
request_url = 'http://127.0.0.1'


@app.route('/')
def get_page():
    url = url_port
    print(url)
    return Response(requests.get('http://localhost:8080'))


@app.route('/<part>')
def forward(part):
    # if part != 'favicon.ico':
    return Response(requests.get('%s/%s' % (url_port, part)))


@app.route('/vod/<string:part>')
def video(part):
    if part == 'big_buck_bunny.f4m':
        f4m = Response(requests.get('%s/vod/big_buck_bunny.f4m' % url_port))
        no_list = Response(requests.get('%s/vod/big_buck_bunny_nolist.f4m' % url_port))
        lines = f4m.data.splitlines()
        x = len(lines)
        for i in range(1, x):
            line = lines[i].decode()
            if line.startswith('\t\t bitrate='):
                ratesx = line.split('"')
                rates.append(int(ratesx[1]))
        return no_list
    else:
        global count
        begin = time.time()
        begin_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        chars1 = part.split('Seg')  # chars[0] represent rate
        chars2 = chars1[1].split('-Frag')  # chars2[0] represent segment number
        # chars[1] represent frag number
        global throughput
        if count == 1:
            global flag
            flag = True
            content = Response(requests.get('%s/vod/100Seg1-Frag1' % url_port))
            size = sys.getsizeof(content.data)
            end = time.time()
            if end-begin==0:
                throughput=10000
            else:
                throughput = size * 8000 / ((end * 1000 - begin * 1000) * 1024)
            logging1(begin_time, end - begin, throughput, throughput, 10, int(request_port), 'Seg1-Frag1')
            # print(throughput)
        else:
            my_rate = 10
            for i in range(1, len(rates) - 1):
                if 1.5 * rates[i - 1] <= throughput < 1.5 * rates[i]:
                    my_rate = rates[i - 1]
                    break
            if throughput >= 1.5 * rates[len(rates) - 1]:
                my_rate = rates[len(rates) - 1]
            print(my_rate)
            print(throughput)
            content = Response(
                requests.get('%s/vod/%d%s%s%s%s' % (url_port, my_rate, 'Seg', chars2[0], '-Frag', chars2[1])))

            t = calculate_throughput(sys.getsizeof(content.data), begin, time.time(), alpha)
            logging1(begin_time, time.time() - begin, t, throughput, my_rate, int(request_port),
                     'Seg%s-Frag%s' % (chars2[0], chars2[1]))
        count += 1
        return content


def logging1(begin, spend, throughput, avgtput, bitrate, port, chunkname):
    # begin_time=time.strftime('%Y-%m-%d %H:%M:%S',begin)
    log_file.write('%s\t%.4f\t%.2f\t%.2f\t%s\t%s\t%s\n' % (begin, spend, throughput, avgtput, bitrate, port, chunkname))


def modify_request(message):
    """
    Here you should change the requested bit rate according to your computation of throughput.
    And if the request is for big_buck_bunny.f4m, you should instead request big_buck_bunny_nolist.f4m 
    for client and leave big_buck_bunny.f4m for the use in proxy.
    """


socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
socket.bind((ip, port))


class DNSServer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        dns_server.DNSServer(ip='127.0.0.1', port=int(dns_port)).start()


class DNSRequest(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while True:
            global request_port, url_port
            if exit_flag:
                socket.sendto('esc'.encode(), (dns_ip, int(dns_port)))
                sys.exit(0)
            time.sleep(4)
            socket.sendto(''.encode(), (dns_ip, int(dns_port)))
            # print(socket.recv(2333))
            request_port = (socket.recv(2333)).decode()
            url_port = request_url + ':' + request_port


def calculate_throughput(size, begin, end, alpha):
    """
    Calculate throughput here.
    """
    global throughput
    if end-begin==0:
        t=10000
    else:
        t = size * 8 / ((end - begin) * 1024)
    throughput = alpha * t + (1 - alpha) * throughput
    return t


def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""

    tid = ctypes.c_long(tid)

    if not inspect.isclass(exctype):
        exctype = type(exctype)

    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))

    if res == 0:

        raise ValueError("invalid thread id")

    elif res != 1:

        # """if it returns a number greater than one, you're in trouble,

        # and you should call it again with exc=NULL to revert the effect"""

        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)

        raise SystemError("PyThreadState_SetAsyncExc failed")


def stop_thread(thread):
    _async_raise(thread.ident, SystemExit)


class clock(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global count
        while True:
            last = count
            time.sleep(4)
            now = count
            if (now == last and flag):
                global exit_flag
                # exit(0)
                exit_flag=True
                stop_thread(thread_main)
                # if (len(argv) == 5):
                #     stop_thread(dns_request)
                #     stop_thread(dns)
                exit(0)


class main_thread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        app.run(port=listen_port)


USAGE = '用法错误，请按如下格式输入:\n./proxy <log> <alpha> <listen-port> <dns-port> [<default-port>]'

if len(argv) < 5:
    print(USAGE)
    exit(1)
# global request_port, alpha,  url_port,dns_port
global log_file
exit_flag=False
request_port=8080
flag = False
throughput = None
count = 1
url_port = 'http://localhost:8080'
# global file_log,alpha,listen_port,dns_port,port_request
if len(argv) == 6:
    name, open_file, alpha, listen_port, dns_port, request_port = argv
    log_file = open(open_file, 'a')
    alpha = float(alpha)
    url_port = 'http://localhost:8080'
    Time = clock()
    thread_main = main_thread()
    Time.start()
    thread_main.start()

if len(argv) == 5:
    name, open_file, alpha, listen_port, dns_port = argv
    log_file = open(open_file, 'a')
    alpha = float(alpha)
    url_port = 'http://localhost:8080'
    dns = DNSServer()
    Time = clock()
    thread_main = main_thread()
    dns_request = DNSRequest()
    Time.start()
    dns.start()
    thread_main.start()
    dns_request.start()
# def stop_thread(thread):
#     _async_raise(thread.ident, SystemExit)
# logging.basicConfig(level=logging.WARNING)

# app.run(port=21102)
