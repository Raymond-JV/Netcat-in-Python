#!/usr/bin/env python

import argparse
import sys
import socket
import subprocess
import os
import threading
import time
import subprocess

args = ""
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server = ""
default_call = "/bin/sh"
run = True

def scan_args():
    global args
    parser = argparse.ArgumentParser(description="Netcat Copy Cat")
    parser.add_argument("client_ip", nargs="?", type=str)
    parser.add_argument("client_port", nargs="?", type=int)
    parser.add_argument("-l","--listen", dest="server_ip", action="store_const", const="localhost")
    parser.add_argument("-p", "--port", dest="server_port", type=int)
    parser.add_argument("-e", help="execute filename", dest="exec_file", nargs="?", type=str)
    parser.add_argument("-c", help="execute command", dest="exec_command",nargs="?", type=str)
    args = parser.parse_args()
    
def init_client(sock, ip, port):
    sock.connect((ip,port))

def init_server(sock, ip, port):
    sock.bind((ip,port))
    sock.listen(5)
    while True:
        global client
        global server
        server,addr = sock.accept()
        client,server = server,client
        #print "Incoming Connection\nIp: %s\nPort: %s" % (addr[0], addr[1])
        #print "Client: %s" % client 
        break
def init_socket(sock):
    global args
    if args.server_ip:
        init_server(sock, args.server_ip, args.server_port)
    else:
        init_client(sock, args.client_ip, args.client_port)
        
def check_fd(sock):
    if not os.isatty(0):
        write_data(sys.stdin.read())

def read_data(sock):
    buf = ""
    while True:
        data = sock.recv(1024)
        buf += data
        if len(data) < 1024:
            break
    return buf

def write_data(sock, data):
    for i in xrange(0, len(data), 1024):
        sock.send(data[i:i+1024])

def write_loop(sock):
    while True:
        buf = sys.stdin.readline()
        if len(buf):
            write_data(sock,buf)

def read_loop(sock):
    global run
    while True:
        buf = read_data(sock)
        if len(buf):
            sys.stdout.write(buf)
        else:
            run = False

def exec_loop(sock):
    global run
    global default_call
    while True:
        buf = read_data(sock)
        if len(buf):
            write_data(sock, subprocess.check_output(buf, shell=True, executable=default_call))
        else:
            run = False

def exec_command(sock):
    if args.exec_command:
        global default_call
        write_data(sock, subprocess.check_output([args.exec_command], shell=True, executable=default_call))
        sys.exit(0)

def exec_file():
    global args
    global default_call
    default_call = args.exec_file
    return default_call

def main():
    global client
    global run
    try:
        scan_args()
        init_socket(client)
        threads = []
        exec_found = exec_file()
        exec_command(client)
        if exec_found:
            threads.append(threading.Thread(target=exec_loop, args=(client,)))
        else:
            threads.append(threading.Thread(target=read_loop, args=(client,)))
            threads.append(threading.Thread(target=write_loop, args=(client,)))
        for t in threads:
            t.daemon = True
            t.start()
        while run:
            time.sleep(1)
    except SystemExit:
        pass
    except KeyboardInterrupt:
        pass
    finally:
        client.close()
main()
