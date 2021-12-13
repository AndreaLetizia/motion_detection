from flask import Flask
from flask import request
from flask import Response
from pywebpush import webpush, WebPushException
from common import Common
import json
import random

app = Flask(__name__)

@app.route('/motion_detected',methods = ['POST'])
def motionDetected():            
    try:
        status = request.get_data().decode()         
        cam = getSenderCam(request)
        #sendPush("Motion detected: " + cam['name'], status)
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
        privatKey = Common.getVapidKeys()['privateKey']
        subs = Common.getSubscriptions()
        response = None        
        data = json.dumps({"notification": {"title": title, "body": body}})
        if subs:      
            for s in subs:
                s.pop("id", None)
                response = webpush(
                    subscription_info=s,
                    vapid_private_key=privatKey,
                    data=data,                    
                    vapid_claims={"sub": "mailto:andrea.letizia@gmail.com"}
                )                
        return response.ok
    except WebPushException as ex:
        Common.logError("PUSH NOTIFICATION ERROR: ", ex)
        if ex.response and ex.response.json():
            extra = ex.response.json()
            print("Remote service replied with a {}:{}, {}",
                  extra.code,
                  extra.errno,
                  extra.message
                  )
        return False
    except Exception as e:     
        Common.logError("PUSH NOTIFICATION ERROR: ", e)
        return False

@app.route('/test',methods = ['GET'])
def test():
    sendPush("Titolo nota", "Questa è una notifica")    
    return Response("Ok", status=200)
    #subs = Common.getSubscriptions()
    #return Response(json.dumps(subs), status=200)
    
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
