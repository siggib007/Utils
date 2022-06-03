'''
Quick little script to test sending email from python

Author Siggi Bjarnason Copyright 2022

Following packages need to be installed as administrator
pip install bs4

'''
# Import libraries
import sys
import requests
import os
import string
import time
import urllib.parse as urlparse
import subprocess as proc
import platform
import json
# End imports

def SendNotification (strMsg):
  if not bNotifyEnabled:
    return "notifications not enabled"
  dictNotify = {}
  dictNotify["token"] = strNotifyToken
  dictNotify["channel"] = strNotifyChannel
  dictNotify["text"]=strMsg[:199]
  strNotifyParams = urlparse.urlencode(dictNotify)
  strURL = strNotifyURL + "?" + strNotifyParams
  bStatus = False
  WebRequest = None
  try:
    WebRequest = requests.get(strURL,timeout=iTimeOut)
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
          LogEntry ("Successfully sent slack notification\n{} ".format(strMsg))
        else:
          LogEntry ("Slack notification response: {}".format(dictResponse))
      else:
        LogEntry ("response is not a dictionary, here is what came back: {}".format(dictResponse))
      if not bStatus or WebRequest.status_code != 200:
        LogEntry ("Problme: Status Code:[] API Response OK={}")
        LogEntry (WebRequest.text)
      else:
        pass
        # LogEntry ("WebRequest status: {}, bStatus: {}".format(WebRequest.status_code,bStatus))
  else:
    LogEntry("WebRequest not defined")