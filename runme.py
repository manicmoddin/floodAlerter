import json
import requests
import logging
from datetime import datetime
import time
import os

import paho.mqtt.client as mqtt

latitude  = os.environ['latitude']
longitude = os.environ['longitude']
distance  = os.environ['distance']

useMQTT    = os.environ['useMQTT']
mqttBroker = os.environ['mqttBroker']
mqttUser   = os.environ['mqttUser']
mqttPass   = os.environ['mqttPass']
mqttBase   = os.environ['mqttBase']

if latitude == "0":
    print("You will need to configure the latitude value")
    quit()

if longitude == "0":
    print("You will need to configure the longitude value")
    quit()

if distance == "0":
    print("You will need to configure the distance value")
    quit()

#logging.basicConfig(filename="FloodMonitor.log", format='%(asctime)s [%(levelname)s] %(message)s', level=logging.DEBUG)
logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.DEBUG)

logging.debug("latitude   : " + str(latitude))
logging.debug("longitude  : " + str(longitude))
logging.debug("distance   : " + str(distance))
logging.debug("useMQTT    : " + str(useMQTT))
logging.debug("mqttBroker : " + str(mqttBroker))
logging.debug("mqttUser   : " + str(mqttUser))
logging.debug("mqttPass   : " + str(mqttPass))
logging.debug("mqttBase   : " + str(mqttBase))

#####################
# Get Flood details #
#####################

def getFloodDetails(urlAppend):
    baseUrl = "https://environment.data.gov.uk/flood-monitoring/id/floods?"

    url = baseUrl + urlAppend
    logging.debug("Called getRiverLevel")

    try:
        response = requests.get(url)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'))
        else:
            return None
    except:
        logging.warning("Unable to fetch results")

##############
# MQTT Stuff #
##############

mqtt.Client.connected_flag=False                                    #create flag in class
client = mqtt.Client()         

def on_subscribe(client, userdata, mid, granted_qos):
    logging.debug(granted_qos)

def on_connect(client, userdata, flags, rc):
    if rc==0:
        client.connected_flag=True #set flag
        logging.debug("MQTT: Connected OK Returned code=" + str(rc))
        #client.subscribe(topic)
    else:
        print("MQTT: Bad connection Returned code= " + str(rc))


def on_message(client, userdata, message):
    #global displayFlag, displayFlagSet
    print("message received " ,str(message.payload.decode("utf-8")))
    print("message topic=",message.topic)
    print("message qos=",message.qos)
    print("message retain flag=",message.retain)

    if (message.topic == "house/alert/msg"):
        print ("Alert: " + message.payload.decode("utf-8"))

    
def connectMQTT (broker, mqttuser, mqttpass, baseTopic):
    global client

    mqttBroker = broker

          
    if mqttuser !='' or mqttpass != '':
        client.username_pw_set(username=mqttUser,password=mqttPass)
    client.on_connect=on_connect                                        #bind call back function
    client.on_message=on_message                                        #attach function to callback
    client.on_subscribe=on_subscribe

    client.loop_start()

    print("Connecting to broker ",mqttBroker)
    client.connect(mqttBroker)                                          #connect to broker
    while not client.connected_flag:                                    #wait in loop
        print("In wait loop")
        time.sleep(1)
    print("Connected")

    print("Subscribing to topic " + baseTopic + "/#")
    result = client.subscribe(baseTopic + "/#", 0)
    print(result)
    

print("Checking to see if need to connect to MQTT")
if useMQTT == "TRUE":
    connectMQTT(mqttBroker, mqttUser, mqttPass, mqttBase)
    print(client.connected_flag)

running = True
lastMessageTime = ''
checkedResult = 'firstRun'

while running:
    currentDetails = getFloodDetails("min-severity=3")
    #currentDetails = getFloodDetails("lat=" + str(latitude) + "&long=" + str(longitude) + "&dist=" + str(distance))

    if currentDetails is not None:
        numResults = len(currentDetails['items'])

        if numResults > 0:
            logging.debug("Found some results")
            #Check to see if the message is new
            if currentDetails['items'][0]['timeMessageChanged'] != lastMessageTime:
                print("This fucker is new")
                message =  currentDetails['items'][0]['message']
                severity = currentDetails['items'][0]['severity']
                lastMessageTime = currentDetails['items'][0]['timeMessageChanged']
                client.publish(mqttBase+"/floodAlert/message", message)
                client.publish(mqttBase+"/floodAlert/severity", severity)
                client.publish(mqttBase+"/floodAlert/lastMessageTime", lastMessageTime)
            else:
                print("There is info, but you already know about it!")
        else:
            logging.debug("Not found anything to report")
    time.sleep(300)