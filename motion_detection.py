from flask import Flask
from flask import request
from flask import Response
from pywebpush import webpush, WebPushException
from common import Common
import json
import random
import requests
from urllib.request import urlopen
import time
import sys

app = Flask(__name__)

@app.route('/motion_detected',methods = ['POST'])
def motionDetected():            
    try:
        status = request.get_data().decode()         
        cam = getSenderCam(request)
        sendPush("Motion detected: " + cam['name'], status)
        #Common.sendMail('andrea.letizia@gmail.com', "Motion detected: " + cam['name'], status)
        Common.recordVideo(cam, 300)
        if Common.logMotion(cam, status):
            return Response("OK", status=200)
        else:
            raise Exception('Cannot write to db')
    except Exception as e:                
        Common.logError("MOTION DETECTION ERROR: ", e)
        return Response("Error on motionDetected", status=200)  

def getSenderCam(request):
    foundCam = None
    if request.headers.getlist("X-Forwarded-For"):
        camIP = request.headers.getlist("X-Forwarded-For")[0]        
    else:
        camIP = request.remote_addr 
        
    for cam in Common.getCamlist():
            if cam['localUrl'] == camIP:
                foundCam = cam
                break;                
    return foundCam
    
def sendPush(title, body):
    try:
        accessToken = Common.getOauth2AccessToken()        
        subs = Common.getSubscriptions()
        response = None        
        headers = {
            'Content-Type': 'application/json; UTF-8',
            'Authorization': 'Bearer ' + accessToken,
          }
        data = {
            "message": {
                "notification": 
                    {
                        "title": title, 
                        "body": body
                    },
                "webpush": 
                    {
                        "fcm_options": { "link": "/#/panoramica;notification=true" },
                        "headers": { "Urgency": "high" }
                    }
                }
            }
        if subs:
            for s in subs:
                subId = s.pop("id", None)
                data["message"]['token'] = s['device_token']
                response = requests.post("https://fcm.googleapis.com/v1/projects/domotica-64f83/messages:send", headers = headers, data=json.dumps(data))                
                Common.log(title + " sent to subscription " + str(subId))           
        return True 
    except Exception as e:     
        Common.logError("PUSH NOTIFICATION ERROR: ", e)
        return False 

@app.route('/test',methods = ['GET'])
def test():
    cam = Common.getCamlist()[0]    
    Common.recordVideo(cam, 30)
    return Response("OK", status=200)
    
@app.route('/volume4',methods = ['GET'])
def volume4():
    Common.alexaVolume('V4')
    return Response("Ok", status=200)
    
@app.route('/volume6',methods = ['GET'])
def volume6():
    Common.alexaVolume('V6')
    return Response("Ok", status=200)
    
@app.route('/volume10',methods = ['GET'])
def volume10():
    Common.alexaVolume('V10')
    return Response("Ok", status=200)
        
@app.route('/halloween',methods = ['GET'])
def halloween():
    Common.stopAlarm = False
    Common.halloween()
    return Response("Ok", status=200)
    
@app.route('/stop_alarm',methods = ['GET'])
def stopAlarm():
    Common.stopAlarm = True    
    return Response("Ok", status=200)
    
if __name__ == '__main__':    
    app.run(host='0.0.0.0',port=5001)
