'''
Quick little script to test sending email from python

Author Siggi Bjarnason Copyright 2022

Following packages need to be installed as administrator
pip install requests
pip install jason
'''
# Import libraries
import sys
import requests
import os
import urllib.parse as urlparse
import json
# End imports

iTimeOut = 20
bNotifyEnabled = False

def CleanExit(strCause):
  print(strCause)
  sys.exit(9)

def LogEntry(strmsg):
  print(strmsg)

if os.getenv("NOTIFYURL") != "" and os.getenv("NOTIFYURL") is not None:
  strNotifyURL = os.getenv("NOTIFYURL")
else:
  strNotifyURL = None

if os.getenv("NOTIFYCHANNEL") != "" and os.getenv("NOTIFYCHANNEL") is not None:
  strNotifyChannel = os.getenv("NOTIFYCHANNEL")
else:
  strNotifyChannel = None

if os.getenv("NOTIFYTOKEN") != "" and os.getenv("NOTIFYTOKEN") is not None:
  strNotifyToken = os.getenv("NOTIFYTOKEN")
else:
  strNotifyToken = None

if strNotifyToken is None or strNotifyChannel is None or strNotifyURL is None:
  bNotifyEnabled = False
  LogEntry(
      "Missing configuration items for Slack notifications, turning slack notifications off")
else:
  bNotifyEnabled = True

def SendNotification (strMsg):
  if not bNotifyEnabled:
    return "notifications not enabled"
  dictHeader = {}
  dictHeader["Content-Type"] = "application/json"
  dictHeader["Accept"] = "application/json"
  dictHeader["Cache-Control"] = "no-cache"
  dictHeader["Connection"] = "keep-alive"
  dictHeader["Authorization"] = "Bearer " + strNotifyToken

  dictPayload={}
  dictPayload["channel"] = strNotifyChannel
  dictPayload["text"] = strMsg[:199]

  bStatus = False
  WebRequest = None
  try:
    WebRequest = requests.post(strNotifyURL, json=dictPayload, headers=dictHeader)
  except Exception as err:
    LogEntry ("Issue with sending notifications. {}".format(err))
  if WebRequest is not None:
    if isinstance(WebRequest,requests.models.Response)==False:
      LogEntry ("response is unknown type")
    else:
      dictResponse = json.loads(WebRequest.text)
      if isinstance(dictResponse,dict):
        if "ok" in dictResponse:
          bStatus = dictResponse["ok"]
          if bStatus:
            LogEntry("Successfully sent slack notification\n{} ".format(strMsg))
          else:
            LogEntry("Failed to send slack message:{} ".format(
                dictResponse["error"]))
        else:
          LogEntry ("Slack notification response: {}".format(dictResponse))
      else:
        LogEntry ("response is not a dictionary, here is what came back: {}".format(dictResponse))
  else:
    LogEntry("WebRequest not defined")

def main():
  SendNotification("this is a test")


if __name__ == '__main__':
    main()
