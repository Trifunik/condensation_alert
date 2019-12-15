import time
import dht12
import microcoapy
import network
import network_info
from machine import I2C, Pin

# --- init variales  ---
current_time = 0
divisor = 0
data_list = []

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
	bytesTransferred = client.get(_SERVER_IP, _SERVER_PORT, COAP_TIME)
	client.poll(2000)

def receivedCurrentTimeCallback(packet, sender):
	print('Message received:', packet, ', from: ', sender)
	print(packet.payload)
	global current_time 
	current_time = int(packet.payload)

#  -- Divisor --
def getDivisor(client):
	bytesTransferred = client.get(_SERVER_IP, _SERVER_PORT, COAP_DIVISOR)
	client.poll(2000)

def receivedDivisorCallback(packet, sender):
	print(packet.payload)
	global divisor 
	divisor = int(packet.payload)

# -- send data --
def putData(client, data):
	print("data: ", data)
	# About to post message...
	bytesTransferred = client.put(_SERVER_IP, _SERVER_PORT, COAP_DATA, data, None, microcoapy.COAP_CONTENT_TYPE.COAP_TEXT_PLAIN)
	print("[PUT] Sent bytes: ", bytesTransferred)
	# wait for respose to our request for 2 seconds
	client.poll(2000)

def receivedMessageCallback(packet, sender):
		print('Message received:', packet, ', from: ', sender)

def convertAndSendData(client):
	global divisor
	global data_list

	idx = 0
	while idx < 8:
		putData(client, str(int(data_list[idx][0]))+","+str(int(data_list[idx][1]))+","+str(int(data_list[idx][2])))
		idx+=1

do_connect()
# Starting CoAP...
client.start()
# get current time
client.resposeCallback = receivedCurrentTimeCallback
getTime(client)

# get divisor
client.resposeCallback = receivedDivisorCallback
getDivisor(client)

# stop CoAP
client.stop()

do_disconnect()

# --- Measuremet
time_diff = int(86400/ divisor)

idx = 0
while idx < 10: # DEBUGGING
	sensor.measure()
	data_list.append([current_time+time_diff*idx, sensor.temperature(), sensor.humidity()])
	time.sleep(1)
	idx+=1

do_connect()
# Starting CoAP...
client.start()

client.resposeCallback = receivedMessageCallback
convertAndSendData(client)

# stop CoAP
client.stop()
do_disconnect()



