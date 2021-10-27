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
        Common.logMotion(cam, status)
        sendPush("Motion detected: " + cam['name'], status)
        return Response("OK", status=200)
    except Exception as e:                
        Common.logError("MOTION DETECTION ERROR: ", e)
        return Response("Error on motionDetected", status=200)  

def getSenderCam(request):
    foundCam = None
    if request.headers.getlist("X-Forwarded-For"):
        camIP = request.headers.getlist("X-Forwarded-For")[0]        
    else:
        camIP = request.remote_addr 
        
    camlist = json.loads(Common.getCamlist())
    for cam in camlist:
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
                response = webpush(
                    subscription_info=json.loads(s),
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
    #sendPush("Titolo nota", "Questa è una notifica")
    l = Common.getCamlist()
    cams = json.dumps(random.sample(l, len(l)))
    return Response(cams, status=200)

@app.route('/test_alexa',methods = ['GET'])
def testAlexa():
    try:
        #subReq = request.get_data().decode()
        device = "Sala"
        text = "Questo è un testo di esempio"
        Common.alexaTalk(device, text)
        return Response("{'success': 'Alexa communication succeded'}", status=200)
    except Exception as e:
        Common.logError("ALEXA TALK ERROR: ", e)
        return Response("{'error': 'Alexa communication failed: " + str(e) + "'}", status=200)
        
@app.route('/halloween',methods = ['GET'])
def halloween():
    Common.halloween()
    return Response("Ok", status=200)
    
if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5001)
