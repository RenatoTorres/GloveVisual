import socket
import serial
import numpy as np
from threading import Thread, Event
import struct
import psutil

import time

#HOST = '169.254.46.226'  # Standard loopback interface address (localhost)
PORT = 65432             # Port to listen on (non-privileged ports are > 1023)


class GloveSckETH(Thread):
    def __init__(self, callback, threadkill):
        self.callback = callback
        self.threadkill = threadkill
        Thread.__init__(self)

    def recv_msg(self,s):
        # Read message length and unpack it into an integer
        raw_msglen = self.recvall(s,4)
        if not raw_msglen:
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]
        # Read the message data
        return self.recvall(s,msglen)

    def recvall(self, s, n):
        # Helper function to recv n bytes or return None if EOF is hit
        data = b''
        while len(data) < n:
            packet = s.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data

    def run(self):
        while not self.threadkill.is_set():
            F = np.random.rand(5)
            #print( F )
            self.callback(F)
            time.sleep(0.05)
        print('Bye!')

    def run_test(self):
        addrs = psutil.net_if_addrs()
        HOST = addrs['PI-ZEROW-OTG'][1].address
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))
            s.listen()
            conn, addr = s.accept()
            with conn:
                print('Connected: ', addr)
                while not self.threadkill.is_set():
                    data = self.recv_msg(conn)
                    if not data:
                        print('Disconnected: ', addr)
                        break

                    D = str(data, 'utf-8')
                    #print(D)
                    dS = D.split(',')
                    F = np.zeros(len(dS))
                    for d in dS:
                        v = d.split(':')
                        idx = int(v[0])
                        f = float(v[1])
                        if(idx < len(dS)):
                            F[ idx ] = f
                            #print( "Idx: {:>2} | V: {:>5}".format(idx, f) )
                            self.callback( F )
                conn.close()
                print('Bye!')


SER_PORT = 'COM4'
SER_SPEED = 115200
class GloveSckSerial(Thread):
    def __init__(self, callback, threadkill):
        Thread.__init__(self)
        self.callback = callback
        self.threadkill = threadkill

    def run_test(self):
        while not self.threadkill.is_set():
            F = np.random.rand(5)
            #print( F )
            self.callback(F)
            time.sleep(0.05)
        print('Bye!')

    def run(self):
        while not self.threadkill.is_set():
            s = serial.Serial(SER_PORT, SER_SPEED)
            print('Connected to ' + SER_PORT )
            while True:
                time.sleep(0.1)
                data = s.readline()
                D = str(data, 'utf-8')
                #print(D)
                dS = D.split(',')
                if( dS[0][0] != '0' or  dS[0][1] != ':'):
                    continue
                F = np.zeros(len(dS))
                for d in dS:
                    v = d.split(':')
                    idx = int(v[0])
                    f = float(v[1])
                    if(idx < len(dS)):
                        F[ idx ] = f
                        #print( "Idx: {:>2} | V: {:>5}".format(idx, f) )
                        self.callback(F)