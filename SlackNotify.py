'''
Quick little script to send slack messages from python

Author Siggi Bjarnason Copyright 2022

Following packages need to be installed as administrator
pip install requests
pip install jason
'''
# Import libraries
import requests
import os
import json
import sys
# End imports


def SendNotification(strMsg, strNotifyChannel, strNotifyToken):
  iTimeOut = 20     #Connection timeout in seconds
  iMaxMSGlen = 199  #Truncate the slack message to this length

  strNotifyURL = "https://slack.com/api/chat.postMessage"
  dictHeader = {}
  dictHeader["Content-Type"] = "application/json"
  dictHeader["Accept"] = "application/json"
  dictHeader["Cache-Control"] = "no-cache"
  dictHeader["Connection"] = "keep-alive"
  dictHeader["Authorization"] = "Bearer " + strNotifyToken

  dictPayload={}
  dictPayload["channel"] = strNotifyChannel
  dictPayload["text"] = strMsg[:iMaxMSGlen]

  bStatus = False
  WebRequest = None
  try:
    WebRequest = requests.post(
        strNotifyURL, timeout=iTimeOut, json=dictPayload, headers=dictHeader)
  except Exception as err:
    return "FAIL. Issue with sending notifications. {}".format(err)
  if WebRequest is not None:
    if isinstance(WebRequest,requests.models.Response)==False:
      return "FAIL. Response is unknown type"
    else:
      dictResponse = json.loads(WebRequest.text)
      if isinstance(dictResponse,dict):
        if "ok" in dictResponse:
          bStatus = dictResponse["ok"]
          if bStatus:
            return "OK. Successfully sent the following slack notification:\n{} ".format(strMsg[:iMaxMSGlen])
          else:
            return "FAIL. Failed to send slack message:{} ".format(dictResponse["error"])
        else:
          return "FAIL. Slack unexpected response from slack: {}".format(WebRequest.text)
      else:
        return "FAIL. Failed to load response into a dictionary, here is what came back: {}".format(WebRequest.text)
  else:
    return "FAIL. WebRequest not defined, implies that the call was not attempted for some reason"

def main():
  if os.getenv("NOTIFYCHANNEL") != "" and os.getenv("NOTIFYCHANNEL") is not None:
    strNotifyChannel = os.getenv("NOTIFYCHANNEL")
  else:
    strNotifyChannel = None

  if os.getenv("NOTIFYTOKEN") != "" and os.getenv("NOTIFYTOKEN") is not None:
    strNotifyToken = os.getenv("NOTIFYTOKEN")
  else:
    strNotifyToken = None

  if strNotifyToken is None or strNotifyChannel is None:
    print("unable to send notifications, missing either the token or the channel")
    sys.exit(9)

  print(SendNotification("More testing",strNotifyChannel,strNotifyToken))

if __name__ == '__main__':
    main()
