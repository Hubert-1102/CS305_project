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
app = Flask(__name__)  # flask
rates = []
request_url = 'http://localhost'


@app.route('/')
def get_page():
    url = url_port
    print(url)
    return Response(requests.get('http://localhost:8080'))


@app.route('/<part>')
def forward(part):
    # 直接转发网页请求
    return Response(requests.get('%s/%s' % (url_port, part)))


@app.route('/vod/<string:part>')
# 转发视频请求以及f4m文件
def video(part):
    if part == 'big_buck_bunny.f4m':  # 解析f4m文件，获得视频支持的码率，添加到rates列表里，由小到大存放
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
        # 计算throughout 选择合适比特率
        begin = time.time()
        begin_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        chars1 = part.split('Seg')  # chars[0] represent rate
        chars2 = chars1[1].split('-Frag')  # chars2[0] represent segment number
        # chars[1] represent frag number
        global throughput
        if count == 1:  # 第一个视频片段，选择最低比特率
            global flag
            flag = True
            content = Response(requests.get('%s/vod/100Seg1-Frag1' % url_port))
            size = sys.getsizeof(content.data)
            end = time.time()
            if end - begin == 0:
                throughput = 10000
            else:
                throughput = size * 8 / ((end - begin) * 1024)
            logging1(begin_time, end - begin, throughput, throughput, 10, int(request_port), 'Seg1-Frag1')
            # print(throughput)
        else:
            # 根据throughout计算合适比特率
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
            # 计算throughout
            t = calculate_throughput(sys.getsizeof(content.response), begin, time.time(), alpha)
            # 生成日志文件
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
    # 打开位于另一个文件的dnsserver
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        dns_server.DNSServer(ip='127.0.0.1', port=int(dns_port)).start()


class DNSRequest(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    # 定时发送请求，得到不同端口号，保证均匀分配负载
    def run(self):
        while True:
            global request_port, url_port
            if exit_flag:
                # 用于正常退出dns服务器
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
    if end - begin == 0:
        t = 10000
    else:
        t = size * 8 / ((end - begin) * 1024)
    throughput = alpha * t + (1 - alpha) * throughput
    return t


def _async_raise(tid, exctype):
    # 用于在线程中关闭其他线程
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
    # 关闭其他线程
    _async_raise(thread.ident, SystemExit)


class clock(threading.Thread):
    # 用于计时的线程
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global count
        while True:
            last = count
            time.sleep(4)
            now = count
            if (now == last and flag):
                # 当视频片段不在请求，flag=true表示已经开始播放视频
                # 执行退出程序操作
                global exit_flag
                exit_flag = True
                stop_thread(thread_main)
                exit(0)


class main_thread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        # 运行flask，转发服务器请求，实现代理
        app.run(host='localhost', port=listen_port)


USAGE = '用法错误，请按如下格式输入:\n./proxy <log> <alpha> <listen-port> <dns-port> [<default-port>]'
# 若输入参数不符合要求，退出程序
if len(argv) < 5:
    print(USAGE)
    exit(1)

# global request_port, alpha,  url_port,dns_port
global log_file
exit_flag = False
request_port = 8080
flag = False
throughput = None
count = 1
url_port = 'http://localhost:8080'
# global file_log,alpha,listen_port,dns_port,port_request
# if len(argv) == 1:
#     alpha = 0.3
#     open_file = 'log_file.txt'
#     listen_port = 21103
#     dns_port = 5533
#     request_port = 8080
#     log_file = open(open_file, 'a')
#     Time = clock()
#     thread_main = main_thread()
#     Time.start()
#     thread_main.start()
if len(argv) == 6:
    # 给定请求端口，无需启动dns服务器
    name, open_file, alpha, listen_port, dns_port, request_port = argv
    log_file = open(open_file, 'a')
    alpha = float(alpha)
    url_port = 'http://localhost:%s' % request_port
    Time = clock()
    thread_main = main_thread()
    Time.start()
    thread_main.start()

if len(argv) == 5:
    # 未给定请求端口，启动dns服务器
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
