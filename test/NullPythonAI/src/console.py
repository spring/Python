# -*- coding: utf-8 -*-

import socket
import select
import code
import sys
import traceback

class StdoutWrap(object):
	def __init__(self, socket):
		self.socket=socket

	def write(self, data):
		self.socket.send(data)

class Console(object):
	def __init__(self, ai):
		self.ai=ai
		self.server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		self.read_set = []
		self.except_set = []
		self.write_set = []
		self.clients = []
		self.buf=""
		try:
			self.server.bind(("localhost",50000)) #listen on port 50000
			self.out("Openend simple Python Console on port localhost:50000")
			self.server.listen(5) #max 5 connections
			self.read_set.append(self.server)
			self.except_set.append(self.server)
			self.write_set.append(self.server)
			self.console=code.InteractiveInterpreter()
		except:
			self.out("Error binding Python Console to localhost:50000")

	def release(self):
		print "Closing Socket"
		self.server.close()
	def out(self,data):
		self.buf += data + "\n"
		sys.__stdout__.write(data + "\n")
	def dump(self,obj):
		for attr in dir(obj):
			print "obj.%s = %s" % (attr, getattr(obj, attr))
	def update(self, data):
		readready,writeready,exceptready = select.select(self.read_set, self.write_set, self.except_set, 0.0)
		for sock in readready:
			if self.server == sock:
				client, address = sock.accept()
				self.out('Connection from %s on port %d' % address)
				self.out('Welcome to the spring python-interface console!')
				self.StdoutWrap=StdoutWrap(client)
				sys.stdout=self.StdoutWrap
				sys.stderr=self.StdoutWrap
				self.clients.append(client)
				self.read_set.append(client)
				self.write_set.append(client)
				self.except_set.append(client)
			else:
				data = sock.recv(1024)
				if data:
					#self.console.runcode(data[:-2]) #remove \r\n
					try:
						exec(data[:-2])
					except:
						traceback.print_exc()
				else:
					self.out('Closed connection from ', sock.getpeername())
					self.clients.remove(sock)
					sock.close()
					self.read_set.remove(sock)
					self.except_set.remove(sock)
					self.write_set.remove(sock)
		for sock in exceptready:
			print "exception"
			self.read_set.remove(sock)
			self.except_set.remove(sock)
			self.write_set.remove(sock)
		for sock in writeready:
			if len(self.buf) > 0:
				written = sock.send(self.buf)
				self.buf = self.buf[written:]
				self.write_set.append(sock)
