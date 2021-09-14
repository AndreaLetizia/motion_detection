from flask import Flask
from flask import request
from flask import Response
from pywebpush import webpush, WebPushException
from datetime import datetime
from common import Common
import json

app = Flask(__name__)

@app.route('/motion_detected',methods = ['POST'])
def motionDetected():    
    now = datetime.now()
    
    if request.headers.getlist("X-Forwarded-For"):
        camIP = request.headers.getlist("X-Forwarded-For")[0]        
    else:
        camIP = request.remote_addr    
            
    try:
        status = request.get_data().decode() #ON/OFF
        camlist = json.loads(Common.getCamlist())        
        camName = "<unknown location>";    
        for cam in camlist:
            if cam['localUrl'] == camIP:    
                camName = cam['name'] 
                break
        Common.logMotion(now, camName, camIP, status)
        return Response("OK", status=200)
    except Exception as e:                
        Common.logError("MOTION DETECTION ERROR: ", e)
        return Response("Error on motionDetected", status=200)    

def sendPush(title, body):
    try:        
        subs = Common.getSubscriptions()
        response = None
        if subs:      
            for s in subs:
                response = webpush(
                    subscription_info=json.loads(s),
                    data=json.dumps({"title": title, "body": body}),
                    vapid_private_key="770ESMW3cuQh8kPoTPflJZlAiLLse_EMPXqzcDYnv_M"
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
    return Response("OK", status=200)

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5001)
