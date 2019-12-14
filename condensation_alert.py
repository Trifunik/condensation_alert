import dht12
import microcoapy
import network
import network_info
from machine import I2C, Pin

# --- init variales  ---
current_time = 0

wlan = network.WLAN(network.STA_IF)

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
    import network
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect(_MY_SSID, _MY_PASS)
        while not wlan.isconnected():
            pass
        print('connected')
    
# --- CoAP functions --- 
def receivedMessageCallback(packet, sender):
	print(packet.payload)
	global current_time 
	current_time = int(packet.payload)

def getTime(client):
    # About to post message...
    bytesTransferred = client.get(_SERVER_IP, _SERVER_PORT, COAP_TIME)
    print("[GET] Sent bytes: ", bytesTransferred)
    # wait for respose to our request for 2 seconds
    client.poll(2000)

do_connect()

client = microcoapy.Coap()
# setup callback for incoming respose to a request
client.resposeCallback = receivedMessageCallback

# Starting CoAP...
client.start()

# About to post message...
getTime(client)

# stop CoAP
client.stop()

#Debugging
print(current_time)
