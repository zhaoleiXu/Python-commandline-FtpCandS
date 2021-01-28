from threading import Thread
from socket import *
import os
from time import sleep

HOST = '0.0.0.0'
PORT = 7788
ADDR = (HOST,PORT)
FTPROOT = '/home/air/pythonproject/learningprojects/ftpserver/ftproot'

class FtpServer:
	"""docstring for FtpServer
	参数：套接字，根路径
	变量：套接字 connfd  不许改
	     根路径 ftproot 不许改
	     当前路径 currentpath  前后无'/',需要拼接
	     路径 path 返回服务器上的物理路径
	command def: 
	L  列出目录下文件
	T  前往上下级目录 .. 回上级，/ 回根，目录名进下级目录，其他均返回当前目录
	P  放置文件到服务器
	G  获取服务器上文件
	Q  退出服务器
	OK 确认指令
	##  发送结束符
	"""
	def __init__(self, connfd,ftproot):
		super(FtpServer, self).__init__()
		self._connfd = connfd
		self._ftproot = ftproot
		self.currentpath = ''

	@property
	def connfd(self):
		return self._connfd
	
	@property
	def ftproot(self):
		return self._ftproot
	
	@property
	def path(self):
		if not self.currentpath:
			return self.ftproot
		return self.ftproot + '/' + self.currentpath
	
	def do_list(self):
		"""
		列出当前目录下文件和目录
		"""
		files = os.listdir(self.path)
		if not files:
			self.connfd.send("file type none".encode())
			return
		else:
			self.connfd.send(b'OK')
			sleep(0.1)
		fstr = ''
		for file in files:
			#返回文件和目录
			if file[0] != '.':
				if os.path.isfile(self.path+ '/' +file):
					fstr += file + '(f)' + '\n'
				elif os.path.isdir(self.path +'/' + file):
					fstr += file +'(d)'+ '\n'
		self.connfd.send(fstr.encode())

	def do_get(self,filename):
		"""
		当前目录下发文件，不存在不发
		参数：   文件名
		"""
		try:
			fd = open(self.path + '/' + filename,'rb')
		except Exception as e:
			print(e)
			self.connfd.send('文件不存在'.encode())
			return
		else:
			self.connfd.send(b'OK')
			sleep(0.1)
		while True:
			data = fd.read(1024)
			if not data:
				sleep(0.1)
				self.connfd.send(b'##')
				break
			self.connfd.send(data)
	
	def do_put(self,filename):
		"""
		当前目录上传文件，已存在不许上传
		参数：  文件名
		"""
		if os.path.exists(self.path + '/' + filename):
			self.connfd.send('already exists.'.encode())
			return
		else:
			self.connfd.send(b'OK')
		#上传接收文件
		fd = open(self.path + '/' + filename,'wb')
		while True:
			data = self.connfd.recv(1024)
			if data == b'##':
				break
			fd.write(data)
		fd.close()

	def to_dir(self,path_str):
		"""
		前往ftp某层目录
		参数： path_str  目录路径，前后无需'/'
		可用参数值    '..'  回上层
		             '/'  回根目录
		             目录名称   一层或多层均可
		"""
		#只有这个功能是自己写的，其它都是别人的^_^
		#未输入目录，提示不予处理
		if not path_str:
			self.connfd.send(b'dir needed.')
			return
		#回上级目录
		elif path_str == '..':
			#当前目录可能多层，也可能1层
			if '/' in self.currentpath:
				tmppath = self.currentpath.split('/')
				# 结束为-1时，最后一个恰好去掉，返回上层
				self.currentpath = '/'.join(tmppath[:-1])
			else:
				#只有一层或者已经在根目录,不能再返了
				self.currentpath = ''
				self.connfd.send(b'root dir reached.')
				return
		#  '/'认为要返回根目录
		elif path_str == '/':
			self.currentpath = ''
			self.connfd.send(b'root dir reached.')
			return
		#  进一层或多层目录
		elif os.path.isdir(self.path +'/'+ path_str):
			if self.currentpath:
				self.currentpath += '/'+path_str
			else:
				self.currentpath = path_str
		else:
			msg = 'no such dir:"%s"'%path_str 
			self.connfd.send(msg.encode())
			return
		self.connfd.send(self.currentpath.encode())

def handle(connfd):
	"""循环接收处理客户端请求"""

	#data = connfd.recv(1024).decode()
	ftpsvr = FtpServer(connfd,FTPROOT)
	#提前准备退出提示，以免断开时获取不到
	clstr = str(ftpsvr.connfd.getpeername())+" exited."
	while True:
		data = connfd.recv(1024).decode()
		if not data or data == 'Q':
			print(clstr)
			return
		elif data[0] == 'L':
			ftpsvr.do_list()
		elif data[0] == 'G':
			filename = data[2:].strip()
			ftpsvr.do_get(filename)
		elif data[0] == 'P':
			filename = data[2:].strip()
			ftpsvr.do_put(filename)
		elif data[0] == 'T':
			#print(data)
			#dir 里允许空格，不再split ' '了，直接截掉前2字符
			fstr = data[2:].strip()
			#print(fstr)
			ftpsvr.to_dir(fstr)

		

def main():
	#创建tcp socket监听套接字
	sockftp = socket()
	sockftp.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
	sockftp.bind(ADDR)
	sockftp.listen(5)
	print("Listen the port %s"%PORT)
	while True:
		try:
			#收到请求
			connfd,addr = sockftp.accept()
		except KeyboardInterrupt:
			print("Exiting FtpServer....")
			return
		except Exception as e:
			print(e)
			continue
		#打印谁接入了
		print("Linking client:",addr)
		#创建线程处理请求，忽略子线程退出消息
		client = Thread(target=handle,args=(connfd,))
		client.setDaemon(True)
		client.start()

if __name__ == '__main__':
	main()