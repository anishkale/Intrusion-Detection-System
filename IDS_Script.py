 #!/usr/bin/python3

#required libraries
import sys
import picamera        
from twilio.rest import Client
from gpiozero import MotionSensor
import ssl
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import paho.mqtt.client as mqtt
# for motion sensor
import RPi.GPIO as GPIO
import time
from datetime import datetime


#called while client tries to establish connection with the server 
def on_connect(mqttc, obj, flags, rc):
    if rc==0:
        print ("Subscriber Connection status code: "+str(rc)+" | Connection status: successful")
        mqttc.subscribe("$aws/things/rasoberry-pi/shadow/update/accepted", qos=0)
    elif rc==1:
        print ("Subscriber Connection status code: "+str(rc)+" | Connection status: Connection refused")

#called when a topic is successfully subscribed to
def on_subscribe(mqttc, obj, mid, granted_qos):
    print("Subscribed: "+str(mid)+" "+str(granted_qos)+"data"+str(obj))

#called when a message is received by a topic
def on_message(mqttc, obj, msg):
    print("Received message from topic: "+msg.topic+" | QoS: "+str(msg.qos)+" | Data Received: "+str(msg.payload))

#creating a client with client-id=mqtt-test
mqttc = mqtt.Client(client_id="cgao")
pir = MotionSensor(22)
mqttc.on_connect = on_connect
mqttc.on_subscribe = on_subscribe
mqttc.on_message = on_message
camera = picamera.PiCamera()
#Configure network encryption and authentication options. Enables SSL/TLS support.
#adding client-side certificates and enabling tlsv1.2 support as required by aws-iot service
mqttc.tls_set(ca_certs="/home/pi/Motion/rootCA.pem.crt",
	            certfile="/home/pi/Motion/8536d9f271-certificate.pem.crt",
	            keyfile="/home/pi/Motion/8536d9f271-private.pem.key",
              tls_version=ssl.PROTOCOL_TLSv1_2, 
              ciphers=None)

#connecting to aws-account-specific-iot-endpoint
mqttc.connect("a1u4dndeq7rcvc.iot.us-east-2.amazonaws.com", port=8883) #AWS IoT service hostname and portno

#automatically handles reconnecting
#start a new thread handling communication with AWS IoT
mqttc.loop_start()

sensor = 12
account_sid = "AC9e7896f1396cdcbfa0116b99bdc4a07c"
auth_token = "07a40eeae284a6c5816c4509879e82c7"
myPhone = "4079248682"
client = Client(account_sid, auth_token)
GPIO.setwarnings(False)
#GPIO.setmode(GPIO.BOARD)
GPIO.setup(sensor,GPIO.IN)
m = 0
i = 0
rc=0
state = 0
sum = 0
fromaddr = "anishkale34@gmail.com"
toaddr = "anishkale24@gmail.com"
 
msg = MIMEMultipart()
 
msg['From'] = fromaddr
msg['To'] = toaddr
msg['Subject'] = "Test"
 
body = "Intrusion"
 
msg.attach(MIMEText(body, 'plain'))
 
filename = "image.jpg"
attachment = open("/home/pi/Motion/image.jpg", "rb")
 
part = MIMEBase('application', 'octet-stream')
part.set_payload((attachment).read())
encoders.encode_base64(part)
part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
 
msg.attach(part)
 
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login(fromaddr, "websitep")
text = msg.as_string()

try:
    while rc == 0:
        if pir.motion_detected:
            if state == 0:
                i = 1
                state = 1
                sum = sum + 1
                print(i)     # i = 1: Motion detected; i = 0: No Motion
            if m == 0:
                client.messages.create(to=myPhone,from_="3213166893",body="Intrusion detected")
                camera.capture('image.jpg')
                server.sendmail(fromaddr, toaddr, text)
                server.quit()
                m = m + 1
        if not pir.motion_detected:
            state = 0
            i = 0
        data={}
        data['motion']=i
        data['time']=datetime.now().strftime('%Y/%m/%d %H:%M:%s')
        data['count']=sum
        playload = '{"state":{"reported":'+json.dumps(data)+'}}'
        print(playload)

        #the topic to publish to
        #the names of these topics start with $aws/things/thingName/shadow.
        msg_info = mqttc.publish("$aws/things/rasoberry-pi/shadow/update", playload, qos=1)
        time.sleep(0.5)  

except KeyboardInterrupt:
    pass

GPIO.cleanup()
