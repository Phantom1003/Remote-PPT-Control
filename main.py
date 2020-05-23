# -*- coding: utf-8 -*-

__author__ = 'sharpdeep'

import webbrowser
import socket,os
import socketserver
import http.server
from string import Template
import qrcode
import threading
from PPTControler import PPTControler

PORT = 8001
HOST = socket.gethostname()
IP_LIST = socket.gethostbyname_ex(HOST)[2]

class WifiPPTHandler(http.server.SimpleHTTPRequestHandler):
	def sendIndexPage(self):
		with open('template/index_template.html', 'r', encoding='utf-8') as ft:
			message = ft.read()
			self.send_response(200)
			self.send_header("Content-type", "text/html")
			self.end_headers()
			self.wfile.write(message.encode('utf-8'))

	def sendPlayPage(self):
		total_page = PPTControler().getActivePresentationSlideCount()
		with open('template/play_template.html', 'r', encoding='utf-8') as ft:
			message = (Template(ft.read()).substitute(current_page=1, total_page=total_page))
			self.send_response(200)
			self.send_header("Content-type", "text/html")
			self.end_headers()
			self.wfile.write(message.encode('utf-8'))

	def sendPenPage(self):
		total_page = PPTControler().getActivePresentationSlideCount()
		with open('template/pen.html', 'r', encoding='utf-8') as ft:
			message = ft.read()
			self.send_response(200)
			self.send_header("Content-type", "text/html")
			self.end_headers()
			self.wfile.write(message.encode('utf-8'))

	def sendImage(self):
		self.send_response(200)
		self.send_header('Content-type', 'image/png')
		self.end_headers()
		png_name = self.path.split('/')[-1]
		png_path = os.path.join('.', 'template', 'static', 'image', png_name)
		with open(png_path, 'rb') as f:
			self.wfile.write(f.read())

	def do_GET(self):
		if self.path == '/':
			self.sendIndexPage()
		elif self.path == '/play':
			PPTControler().fullScreen()
			try:
				self.sendPlayPage()
			except:
				self.sendIndexPage()
		elif self.path == '/nextpage':
			self.ajax(PPTControler().nextPage())
		elif self.path == '/prepage':
			self.ajax(PPTControler().prePage())
		elif self.path == '/click':
			self.ajax(PPTControler().click())
		elif '/static/image' in self.path:
			self.sendImage()
		elif self.path == '/pen':
			self.sendPenPage()
		elif '/move' in self.path:
			x_y = self.path.split('?')[-1]
			x = x_y.split('&')[0].split('=')[-1]
			y = x_y.split('&')[-1].split('=')[-1]
			self.ajax(PPTControler().moveMouse(x,y))
		elif self.path == '/touchstart':
			self.ajax(PPTControler().touchStart())
		elif self.path == '/touchend':
			self.ajax(PPTControler().touchEnd())
		elif self.path == '/favicon.ico':
			self.sendImage()

		else:
			print(self.path)

	def ajax(self,ret_str):
		self.send_response(200)
		self.send_header('Content-type','text/plain')
		self.end_headers()
		self.wfile.write(str(ret_str).encode('utf-8'))


class ResourceGenerate:
	def mkdir(self, path):
		if not os.path.exists(path):
			os.makedirs(path)

	def generatePages(self):
		self.connectPage()

	def connectPage(self):
		self.mkdir('./build')
		self.mkdir('./build/static')

		with open('build/home.html', 'w', encoding='utf-8') as f:
			res = ''
			for ip in self.ip_list:
				res += Template('''
					<li>http://$host:$port</li><br/>
					<center>
						<img src="static/$host.png" alt="$host">
					</center>
				''').substitute(host=ip, port=PORT)

				img = qrcode.make('http://{0}:{1}'.format(ip, PORT), version=1, box_size=8)
				img.save("./build/static/{0}.png".format(ip))

			with open('template/usage_template.html', 'r', encoding='utf-8') as ft:
				f.write(Template(ft.read()).substitute(IP_QR=res, HOST=HOST))

	def __init__(self, ip_list):
		self.ip_list = ip_list
		self.generatePages()


if __name__ == '__main__':
	ResourceGenerate(IP_LIST)
	webbrowser.open_new_tab(os.getcwd()+'/build/home.html')
	thread = []
	for IP in IP_LIST:
		print("Server start at {0}:{1}".format(IP,PORT))
		httpd = socketserver.TCPServer((IP,PORT), WifiPPTHandler)
		serverThread = threading.Thread(target=httpd.serve_forever)
		serverThread.daemon = True
		serverThread.start()
		thread += [serverThread]

	for t in thread:
		t.join()
