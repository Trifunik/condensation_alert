import time
import dht12
import microcoapy.microcoapy
import network
import network_info
import machine

I2C = machine.I2C
Pin = machine.Pin

# --- init pins  ---
led = Pin(10, Pin.OUT)

# --- init variales  ---
current_time = 0
divisor = 24
data_list = []
last_temp = 0.0
last_hum = 0.0

wlan = network.WLAN(network.STA_IF)
client = microcoapy.Coap()

_MY_SSID = network_info.MY_SSID
_MY_PASS = network_info.MY_PASS
_SERVER_IP = network_info.SERVER_IP
_SERVER_PORT = 5683  # default CoAP port
COAP_TIME = '/time'
COAP_DIVISOR = '/divisor'
COAP_DATA = '/data'

i2c = I2C(scl=Pin(26), sda=Pin(0))
sensor = dht12.DHT12(i2c)

# --- define functions ---
# --- Wifi functions
def do_connect():
	global wlan
	wlan.active(True)
	if not wlan.isconnected():
		print('connecting to network...')
		wlan.connect(_MY_SSID, _MY_PASS)
		while not wlan.isconnected():
			pass
		print('connected')

def do_disconnect():
	global wlan
	wlan.disconnect()
	wlan.active(True)
	

# --- CoAP functions --- 
#  -- Time --
def getTime(client):
	bytesTransferred = client.get(_SERVER_IP, _SERVER_PORT, COAP_TIME, b'\x20')
	client.poll(4000)

def receivedGetCallback(packet, sender):
	print('Message received:', packet, ', from: ', sender)
	print(packet.payload)
	global current_time
	global divisor
	
	if packet.token == b'\x10':
		divisor = int(packet.payload)
	elif packet.token == b'\x20':
		current_time = int(packet.payload)

#  -- Divisor --s
def getDivisor(client):
	bytesTransferred = client.get(_SERVER_IP, _SERVER_PORT, COAP_DIVISOR, b'\x10')
	client.poll(4000)

# -- send data --
def putData(client, data):
	print("data: ", data)
	# About to post message...
	bytesTransferred = client.put(_SERVER_IP, _SERVER_PORT, COAP_DATA, data, None, microcoapy.COAP_CONTENT_FORMAT.COAP_TEXT_PLAIN)
	print("[PUT] Sent bytes: ", bytesTransferred)
	# wait for respose to our request for 2 seconds
	client.poll(4000)

def receivedMessageCallback(packet, sender):
		print('Message received:', packet, ', from: ', sender)

def convertAndSendData(client):
	global divisor
	global data_list

	idx = 0
	while idx < divisor:
		putData(client, str(int(data_list[idx][0]))+","+str(int(data_list[idx][1]))+","+str(int(data_list[idx][2])))
		idx+=1

	del data_list[:]
		
def doMeasure(timeStamp):
	global data_list
	global sensor
	global last_hum
	global last_temp

	try:
		sensor.measure()
		last_hum = sensor.humidity()
		last_temp = sensor.temperature()
	except:
		print("MEASURE ERROR", timeStamp)
	finally:
		data_list.append([timeStamp, last_temp, last_hum])
		return

# Programm started
for x in range(5):
	led.value(0)
	time.sleep(0.3)
	led.value(1)
	time.sleep(0.3)

# protection against leaking current
led = Pin(10, Pin.IN, Pin.PULL_HOLD)
	
while True:
	do_connect()
	# Starting CoAP...
	client.start()
	# get current time
	client.resposeCallback = receivedGetCallback
	getTime(client)

	# get divisor
	getDivisor(client)

	# stop CoAP
	client.stop()

	do_disconnect()

	# --- Measuremet
	time_diff = int(86400/ divisor)

	idx = 0
	while idx < divisor:
		doMeasure(current_time+time_diff*idx)
		machine.lightsleep(time_diff * 1000)
		idx+=1

	do_connect()
	# Starting CoAP...
	client.start()

	client.resposeCallback = receivedMessageCallback
	convertAndSendData(client)

	# stop CoAP
	client.stop()
	do_disconnect()
