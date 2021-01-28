from socket import *
import sys
from time import sleep

class FtpClient:
	"""
		command def: 
	L  列出目录下文件
	T  前往上下级目录 .. 回上级，目录名进下级目录，其他均返回当前目录
	P  放置文件到服务器
	G  获取服务器上文件
	Q  退出服务器
	OK 确认指令
	##  发送结束符
	"""
	def __init__(self,sockcl):
		self.sockclient = sockcl

	def do_list(self):
		"""罗列当前目录下文件和目录"""
		self.sockclient.send(b"L")
		data = self.sockclient.recv(10).decode()
		if data == 'OK':
			# while True:
			# 	data = self.sockclient.recv(1024)
			# 	if data == b"##":
			# 		break
			# 	print(data.decode())
			data = self.sockclient.recv(4096)
			print(data.decode())
		else:
			print(data)

	def do_quit(self):
		"""退出客户端"""
		self.sockclient.send(b'Q')
		self.sockclient.close()
		sys.exit("Thanks for use.")

	def do_get(self,filename):
		"""
		从服务器当前目录下载文件
		参数：   下载文件名
		"""
		self.sockclient.send(('G '+filename).encode())
		data = self.sockclient.recv(128).decode()
		if data == 'OK':
			fd = open(filename,'wb')
			while True:
				data = self.sockclient.recv(1024)
				if data == b'##':
					break
				fd.write(data)
			fd.close()
		else:
			print(data)
	
	def do_put(self,filename):
		"""
		上传文件到服务器当前访问目录
		参数    文件名"""
		try:
			fd = open(filename,'rb')
		except Exception as e:
			print(e)
			return
		filename = filename.split('/')[-1]
		self.sockclient.send(('P '+filename).encode())
		data = self.sockclient.recv(128).decode()
		if data == 'OK':
			while True:
				data = fd.read(1024)
				if not data:
					sleep(0.1)
					self.sockclient.send(b'##')
					break
				self.sockclient.send(data)
			fd.close()
		else:
			print(data)

	def do_cd(self,cmd):
		"""
		前往某层目录
		参数  cmd 目录名（不限层数），
		也可是  / 回根目录 或 .. 回上层目录
		"""
		msg = 'T '+ cmd
		self.sockclient.send(msg.encode()) 
		data = self.sockclient.recv(1024).decode()
		print(data)

def request(sockcl):
	"""循环处理发送客户端请求"""
	ftp = FtpClient(sockcl)
	while True:
		print("cmmd: cd,list,get file,put file,quit.")
		cmd = input("command>>")
		if cmd.strip() == 'list':
			ftp.do_list()
		elif cmd.strip() == 'quit':
			ftp.do_quit()
		elif cmd[:3] == 'get':
			filename = cmd[3:].strip()
			ftp.do_get(filename)
		elif cmd[:3] == 'put':
			filename = cmd[3:].strip()
			ftp.do_put(filename)
		elif cmd[:2] == 'cd':
			#目录中允许空格，不再split 空格
			cmd = cmd[2:].strip()
			ftp.do_cd(cmd)




def main():
	"""主函数，设置服务器地址，发起请求"""
	ADDR = ('127.0.0.1',7788)
	sockcl = socket()
	try:
		sockcl.connect(ADDR)
	except Exception as e:
		print("Linking ftpserver failed..",e)
		return
	else:
		request(sockcl)


if __name__ == '__main__':
	main()