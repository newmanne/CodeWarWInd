"""
Created on January 15, 2013

@author: Windward Studios, Inc. (www.windward.net).

No copyright claimed - do anything you want with this code.
"""

from __future__ import print_function

import threading, time
import socket as sock
from collections import deque
from debug import trap, bugprint, printrap

BUFFER_SIZE = 65536 * 4
PORT = 1707

class TcpClient(threading.Thread):
    """Threaded socket wrapper that sends and receives data from the server."""
    
    def __init__(self, host, callback):
        threading.Thread.__init__(self)
        
        socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM, sock.IPPROTO_TCP)
        bugprint(host, PORT)
        socket.connect( (host, PORT) )
        #socket.settimeout(.5)
        self.socket = socket
        
        self.receiver = Receiver( (host, PORT), socket, self )
        self.callback = callback
        self.running = True
    
    def run(self):
        bugprint("TcpClient running...")
        self.receiver.start()
        input = self.receiver.input
        while self.running:
            if len(input):
               self.callback.incomingMessage(input.popleft())
#           time.sleep(.25)
        self.socket.close()
    
    def sendMessage(self, message):
        # compute the length of the message (4 byte, little-endian)
        length = len(message)
        hexlen = "{:08x}".format(length)
        assert len(hexlen) == 8 # length should not be more than 4 bytes
        chrstr = [chr(int(hexlen[i:i+2], 16)) for i in range(0, 8, 2)]
        chrstr.reverse()
        retlen = ''.join(chrstr)
        try:
            #send the length
            self.socket.send(retlen) # fix this
            
            # send the message
            ret = self.socket.send(message)
            while ret < length:
                ret += self.socket.send(message[ret:])
            assert ret == length
        except sock.timeout: # fix this
            printrap("Socket operation (send) timed out")
            self.sendMessage(message)
        
    def connectionLost(self, err):
        self.callback.connectionLost(err)
    
    def close(self):
        self.receiver.running = False
        self.running = False
    
 
class Receiver(threading.Thread):
    '''Waits in a separate thread for data from the server.'''
    
    def __init__(self, address, socket, callback):
        threading.Thread.__init__(self)
        self.callback = callback
        self.socket = socket
        self.input = deque()
        self.running = True
    
    def run(self):
        bugprint("Receiver running...")
        socket = self.socket
        input = self.input
        
        while self.running:
            data = getData(socket, self)
            while data is None:
                data = getData(socket, self)
            end = data.rfind('>')
            assert end > 0
            data = data[:end+1] # strip ending nonsense C# bogus banana characters
            input.append(data)
        socket.close()
    
    def connectionLost(self, err):
        self.callback.connectionLost(err)
    

def getData(socket, callback):
    try:
        # compute the length of the message (4 byte, little-endian)
        recstr = socket.recv(4)
        while len(recstr) < 4:
            recstr += socket.recv(4 - len(recstr))
        assert len(recstr) == 4
        lenstr = ["{:02x}".format(ord(char)) for char in recstr]
        lenstr.reverse()
        length = int(''.join(lenstr), 16)
        
        # receive message into buffer
        data = socket.recv(length)
        received = len(data)
        buff = []
        while received < length:
            buff.append(data)
            data = socket.recv(length - received)
            received += len(data)
        else:
            assert received == length
            if buff:
                buff.append(data)
                data = ''.join(buff)
        return data
    except sock.timeout:
        trap("Socket operation (receive) timed out")
        return None
    except sock.error as err: # fix this
        if err.errno == 10054: # The connection has been reset.
            callback.connectionLost(err)
        else:
            printrap("WARNING - socket error on receive: " + str(err)) # fix this
            raise err
    
