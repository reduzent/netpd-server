#!/usr/bin/python

"""THREADED NETPD SERVER
 
 This is non-blocking version of the the netpd-server2. Each connected
 client uses it's own sender and receiver thread and messages are
 passed with python Queues between threads. 

 Although not recommend by many members of #python, this seems a
 reliable and well working approach.

 AUTHOR: Roman Haefeli, Copyright 2010
 LICENSE: GPL-2+
"""

### MAIN SETTINGS ####################################################
# Which port should the server listen on?
PORT = 8003
# How many messages should be bufferd before disconnecting a non-
# responsive client?
BUFFERSIZE = 40000 
#######################################################################

import OSC, Queue, slip, socket, threading

class sender(threading.Thread):
	"""waits for messages from the queue and sends
	them over a socket.
	"""

	def __init__ (self, socket, queue):
		threading.Thread.__init__(self)
		self.socket = socket
		self.socket.settimeout(0.3)
		self.queue =  queue

	def run(self):
		"""start the sender thread
		"""
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
			self.socket.shutdown(2)
		except:
			pass
		goodbye(no)

class receiver(threading.Thread):
	"""waits for incoming messages from the socket and puts
	them into the receiver queue.
	"""

	def __init__ (self, socket, queue, sendqueue):
		threading.Thread.__init__(self)
		self.socket = socket
		self.queue = queue
		self.sendqueue = sendqueue
		self.peername = self.socket.getpeername()
		self.OSCcontainer = OSCpacket()

	def run(self):
		"""start the receiver thread.
		"""
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

class requesthandler(threading.Thread):
	"""waits for incoming connections and launches a receiver and
	a sender thread for each connecting client
	"""

	def __init__(self):
		threading.Thread.__init__(self)
		self.conn = socket.socket()
		self.conn.bind(('0.0.0.0', PORT))
		self.conn.listen(5)
		self.senders = clientmanager()
		self.recqueue = Queue.Queue(BUFFERSIZE)
		
	def run(self):
		"""start the requesthandler thread.
		"""
		thprint("Server listening on port %d" % PORT)
		while 1:
			self.conn.settimeout(3)
			try:
				sock, addr = self.conn.accept()
				no = sock.fileno()
				# make the sender queue 10% bigger than the disconnect limit
				sendqueue = Queue.Queue(int(BUFFERSIZE * 1.1))
				self.senders.add(no, (sendqueue, sock.getpeername()))
				recthread = receiver(sock, self.recqueue, sendqueue)
				sendthread = sender(sock, sendqueue)
				recthread.start()
				sendthread.start()
				welcome(no)
			except:
				if shutdown:
					break
		self.conn.close()

class clientmanager(dict):
	"""holds a list of all currently connected clients."""

	def __init__(self):
		self.lock = threading.Lock()

	def add(self, key, value):
		"""adds a new client to the list"""
		self.lock.acquire()
		self[key] = value
		self.lock.release()

	def remove(self, key):
		"""removes a client from the list"""
		self.lock.acquire()
		del self[key]
		self.lock.release()

	def getall(self):
		"""get a deep copy of the client list"""
		copy = self.copy()
		return copy

	def getqueue(self, key):
		"""get only the queue of the specified client"""
		if key in self:
			return self[key][0]
		else:
			return None

	def getaddr(self, key):
		"""get only the address, port of the specified client"""
		if key in self:
			return self[key][1]
		else:
			return None

	def get(self, key):
		"""get client data of specified client"""
		if key in self:
			return self[key]
		else:
			return None

class OSCpacket(OSC.OSCMessage):
	"""extended OSC packet container"""
	
	def __init__(self, address=""):
		OSC.OSCMessage.__init__(self, address)
		self.SERIAL = slip.slip()
	
	def unpack(self, raw):
		"""get a OSC packet from raw data"""
		unpacked = OSC.decodeOSC(raw)
		packet = OSCpacket(unpacked[0])
		for i in range(len(unpacked[1])):
			if i > 0:
				packet.append(unpacked[i+1], unpacked[1][i])
		return packet

	def SERIALappend(self, chunk):
		"""append SLIP encoded raw data to the OSC packet"""
		self.SERIAL.append(chunk)

	def SERIALunpack(self):
		"""get a list of one or more OSC packets from SLIP encoded
		raw data, that was previously appended using SERIALappend()"""
		packetlist = []
		rawpacketlist = self.SERIAL.decode()
		for rawpacket in rawpacketlist:
			packetlist.append(OSCpacket().unpack(rawpacket))
		return packetlist

	def SERIALpack(self):
		"""get SLIP encoded binary data of the OSC packet"""
		return self.SERIAL.encode(self.pack())

	def pack(self):
		"""get binary data of the OSC packet"""
		return self.getBinary()

	def getAddress(self):
		"""get the OSC address of the OSC packet"""
		return OSC.decodeOSC(self.getBinary())[0]
	
	def setAddress(self, address):
		"""overwrite current OSC address"""
		items = self.items()
		self.clear(address)
		self.extend(items)

	def decodeAddress(self):
		"""get a list of the OSC address fields"""
		return self.getAddress().split('/')[1:]

	def encodeAddress(self, addrlist):
		"""overwrite current OSC address by the address 
		composed of the given field list"""
		address = '/'+'/'.join(addrlist)
		self.setAddress(address)
			
printlock = threading.Lock()
def thprint(msg):
	"""A thread-safe print"""
	printlock.acquire()
	print msg
	printlock.release()

# Server methods
def welcome(no):
	"""is called whenever a new client connects"""
	number = len(server.senders)
	OSCmsg = OSCpacket('/s/server/num_of_clients')
	OSCmsg.append(number)
	broadcast(OSCmsg)

def goodbye(no):
	"""is called whenever a client disconnects"""
	welcome(no)

def broadcast(msg):
	"""broadcast a message to all connected clients"""
	senderlist = server.senders.getall()
	for no in senderlist:
		senderlist[no][0].put(('msg', msg))

def test(msg):
	"""does nothing. Is used by clients to keep connection alive."""
	pass

def sendtoclient(no, msg):
	"""send a message to specified client"""
	if no in server.senders:
		sender = server.senders.getqueue(no)
		sender.put(('msg', msg))


def main():
	"""start the netpd server"""
	global server
	global shutdown
	shutdown = False
	server = requesthandler()
	server.start()
	try:
		while 1:
			try:
				# Do the actual server work
				no, OSCmsg = server.recqueue.get(True, 1)
				addr = OSCmsg.decodeAddress()
				# proxy methods: b, <socketnumber>
				if  addr[0] == 'b':
					addr = [str(no)] + addr[1:]
					OSCmsg.encodeAddress(addr)
					broadcast(OSCmsg)
				elif addr[0].isdigit():
					receiver = int(addr[0])
					addr = [str(no)] + addr[1:]
					OSCmsg.encodeAddress(addr)
					sendtoclient(receiver, OSCmsg)
				# server methods: socket, ip
				elif addr[0] == 's':
					if addr[1] == 'server':
						if addr[2] == 'socket':
							OSCmsg.append(no)
							sendtoclient(no, OSCmsg)
						if addr[2] == 'ip':
							ipaddr = server.senders.getaddr(no)[0].split('.')
							OSCmsg.extend(ipaddr)
							sendtoclient(no, OSCmsg)
			except Queue.Empty:
				pass
	except KeyboardInterrupt:
		senderlist = server.senders.getall()
		for no in senderlist:
			senderlist[no][0].put(('stop', []))
		shutdown = True
		thprint("\nStopping Server ...")
		exit()

if __name__ == '__main__':
	main()

