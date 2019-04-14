import serial
import threading
import time
import queue
import asyncio
import socket
import select
import os


class MockPort(object):

	def __init__(self, *args, **kwargs):
		self.in_str = b"generic response \n>"
		self.out_str = b""

	@property
	def out_waiting(self):
		pos = self.out_str.find(b'\n')
		if pos >= 0:
			print("Line written to serial: '{}'".format(repr(self.out_str[:pos])))
		self.out_str = self.out_str[pos + 1:]
		self.in_str += b"generic response \n>"
		return len(self.out_str)

	@property
	def in_waiting(self):
		count = len(self.in_str)
		return count

	def read(self, count):
		resp = self.in_str[:count]
		self.in_str = self.in_str[count:]
		return resp

	def write(self, s):
		self.out_str += s

	def __enter__(self):
		return self

	def __exit__(self, *args):
		pass


class ScopedSocketTimeout(object):

	__slots__ = ('_sock', '_old_timeout', '_new_timeout')

	def __init__(self, sock, new_timeout):
		self._sock = sock
		self._old_timeout = None
		self._new_timeout = new_timeout

	def __enter__(self):
		self._old_timeout = self._sock.gettimeout()
		self._sock.settimeout(self._new_timeout)
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self._sock.settimeout(self._old_timeout)


class SerialComm(object):
	
	__slots__ = (
		'port',
		'receive_queue',
		'send_queue',
		'callback_queue',
		'receive_buffer'
	)

	prompt = b">"
	mycroft_port   = 10003
	bluetooth_port = 10004

	def __init__(self):
		# self.port = MockPort(
		self.port = serial.Serial(
			port='/dev/ttyUSB0',
			baudrate=38400,
			dsrdtr=False,
			write_timeout=0,
			timeout=0
		)
		self.receive_queue  = queue.Queue()
		self.send_queue	    = queue.Queue()
		self.callback_queue = queue.Queue()
		self.receive_buffer = b""

	def __enter__(self):
		self.port.__enter__()
		return self
	
	def __exit__(self, *args):
		self.port.__exit__(*args)

	def enqueue_command(self, command, callback):
		self.send_queue.put(command)
		self.callback_queue.put(callback)

	async def send_commands(self):
		while True:
			while self.send_queue.empty() or self.port.out_waiting > 0:
				await asyncio.sleep(0)
			command = self.send_queue.get(block=False)
			self.port.write(command)
			await asyncio.sleep(0)

	async def receive_responses(self):
		prompt = SerialComm.prompt
		prompt_len = len(prompt)
		while True:
			while self.callback_queue.empty() or self.port.in_waiting == 0:
				await asyncio.sleep(0)
			self.receive_buffer += self.port.read(self.port.in_waiting)
			if len(self.receive_buffer) < prompt_len:
				pos = self.receive_buffer.find(prompt)
			else:
				recvd = len(self.receive_buffer)
				tail = self.receive_buffer[recvd - prompt_len:]
				tail_pos = tail.find(prompt)
				pos = -1 if tail_pos < 0 else ((recvd - prompt_len) + tail_pos)
			if pos >= 0:
				msg = self.receive_buffer[:pos]
				self.receive_buffer = self.receive_buffer[pos + prompt_len:]
				cb = self.callback_queue.get(block=False)
				gen = cb(msg)
				await gen
			await asyncio.sleep(0)

	async def read_socket(self, sock, port):
		with sock:
			sock.bind(("localhost", port))
			sock.listen(1)
			while not select.select([sock], [], [], 0)[0]:
				# yield until a connection is established
				await asyncio.sleep(0)
			conn, info = sock.accept()
			with conn:
				reader, writer = await asyncio.open_connection(sock=conn)
				def callback(resp):
					writer.write(resp)
					#writer.write(b'\0')
					return writer.drain()
				while True:
					cmd = await reader.readuntil(b'\n')
					print(cmd)
					self.enqueue_command(cmd, callback)
					await asyncio.sleep(0)


if __name__ == '__main__':
	with SerialComm() as serial_comm:
		asyncio.ensure_future(serial_comm.read_socket(
			socket.socket(socket.AF_INET, socket.SOCK_STREAM),
			SerialComm.mycroft_port
		))
		asyncio.ensure_future(serial_comm.read_socket(
			socket.socket(socket.AF_INET, socket.SOCK_STREAM),
			SerialComm.bluetooth_port
		))
		asyncio.ensure_future(serial_comm.send_commands())
		asyncio.ensure_future(serial_comm.receive_responses())
		loop = asyncio.get_event_loop()
		loop.run_forever()


