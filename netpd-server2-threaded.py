#!/usr/bin/python

#######################################################################
# THREADED NETPD SERVER
# 
# This is non-blocking version of the the netpd-server2. Each connected
# client uses it's own sender and receiver thread and messages are
# passed with python Queues between threads. 
#
# Although not recommend by many members of #python, this seems a
# reliable and well working approach.
#
# AUTHOR: Roman Haefeli, Copyright 2010
# LICENSE: GPL-2+
#
######################################################################


### MAIN SETTINGS ####################################################
# Which port should the server listen on?
PORT = 8004
# How many messages should be bufferd before disconnecting a non-
# responsive client?
BUFFERSIZE = 40000 
#######################################################################

import OSC, Queue, slip, socket, threading

# SENDER THREAD
class sender(threading.Thread):
	def __init__ (self, socket, queue):
		threading.Thread.__init__(self)
		self.socket = socket
		self.socket.settimeout(0.3)
		self.queue =  queue

	def run(self):
		no = self.socket.fileno()
		while 1:
			cmd, OSCmsg = self.queue.get()
			if cmd == 'msg':
				data = OSCmsg.SERIALpack()
				while True:
					try:
						self.socket.sendall(data)
						break
					except socket.timeout:
						thprint('queue size: %d' % self.queue.qsize())
						if self.queue.qsize() > BUFFERSIZE:
							cmd = 'stop'
							break
			if cmd == 'stop':
				break
		server.senders.remove(no)
		try:
			thprint('Client left: %s %d' % self.socket.getpeername())
			self.socket.shutdown(2)
		except:
			bla = 1
		goodbye(no)

# RECEIVER THREAD
class receiver(threading.Thread):
	def __init__ (self, socket, queue, sendqueue):
		threading.Thread.__init__(self)
		self.socket = socket
		self.queue = queue
		self.sendqueue = sendqueue
		self.peername = self.socket.getpeername()
		self.OSCcontainer = OSCpacket()

	def run(self):
		no = self.socket.fileno()
		thprint('Client joined: %s %d' % self.peername)
		rest = ''
		while 1:
			try:
				chunk = self.socket.recv(4096)
				if not chunk: break
				self.OSCcontainer.SERIALappend(chunk)
				for OSCmsg in self.OSCcontainer.SERIALunpack():
					self.queue.put((no, OSCmsg))
			except socket.timeout:
				pass
                thprint('Client left: %s %d' % self.peername)
		self.sendqueue.put(('stop', None))

# REQUEST HANDLER
class requesthandler(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.conn = socket.socket()
		self.conn.bind(('0.0.0.0', PORT))
		self.conn.listen(5)
		self.senders = clientmanager()
		self.recqueue = Queue.Queue(BUFFERSIZE)
		
	def run(self):
		thprint("Server listening on port %d" % PORT)
		while 1:
			self.conn.settimeout(3)
			try:
				sock, addr = self.conn.accept()
				no = sock.fileno()
				# make the sender queue 10% bigger than the disconnect limit
				sendqueue = Queue.Queue(int(BUFFERSIZE * 1.1))
				self.senders.add(no, sendqueue)
				recthread = receiver(sock, self.recqueue, sendqueue)
				sendthread = sender(sock, sendqueue)
				recthread.start()
				sendthread.start()
				welcome(no)
			except:
				if shutdown:
					break
		self.conn.close()

# CLIENT MANAGER
class clientmanager(dict):
	def __init__(self):
		self.lock = threading.Lock()

	def add(self, key, value):
		self.lock.acquire()
		self[key] = value
		self.lock.release()

	def remove(self, key):
		self.lock.acquire()
		del self[key]
		self.lock.release()

	def getall(self):
		copy = self.copy()
		return copy

	def get(self, key):
		if key in self:
			return self[key]
		else:
			return None

# create our own OSC container
class OSCpacket(OSC.OSCMessage):
	
	def __init__(self, address=""):
		OSC.OSCMessage.__init__(self, address)
		self.SERIAL = slip.slip()
	
	def unpack(self, raw):
		unpacked = OSC.decodeOSC(raw)
		packet = OSCpacket(unpacked[0])
		for i in range(len(unpacked[1])):
			if i > 0:
				packet.append(unpacked[i+1], unpacked[1][i])
		return packet

	def SERIALappend(self, chunk):
		self.SERIAL.append(chunk)

	def SERIALunpack(self):
		packetlist = []
		rawpacketlist = self.SERIAL.decode()
		for rawpacket in rawpacketlist:
			packetlist.append(OSCpacket().unpack(rawpacket))
		return packetlist

	def SERIALpack(self):
		return self.SERIAL.encode(self.pack())

	def pack(self):
		return self.getBinary()
			
# non-scrambled print
printlock = threading.Lock()
def thprint(msg):
	printlock.acquire()
	print msg
	printlock.release()

# SERVER METHODS
def welcome(no):
	pass

def goodbye(no):
	pass

def broadcast(msg):
	senderlist = server.senders.getall()
	for no in senderlist:
		senderlist[no].put(('msg', msg))

def sendsocketno(no):
	pass

def test(msg):
	pass

def sendtoclient(no, msg):
	pass

# MAIN
def main():
	global server
	global shutdown
	shutdown = False
	server = requesthandler()
	server.start()
	try:
		while 1:
			try:
				# Do the actual server work
				no, msg = server.recqueue.get(True, 1)
				print msg
				broadcast(msg)
			except Queue.Empty:
				pass
	except KeyboardInterrupt:
		senderlist = server.senders.getall()
		for no in senderlist:
			senderlist[no].put(('stop', []))
		shutdown = True
		thprint("\nStopping Server ...")
		exit()

if __name__ == '__main__':
	main()

