'''
Quick little script to send slack messages from python

Author Siggi Bjarnason Copyright 2022

Following packages need to be installed as administrator
pip install requests
pip install jason
'''
# Import libraries
import os
import sys
import subprocess
try:
  import requests
except ImportError:
  subprocess.check_call([sys.executable, "-m", "pip", "install", 'requests'])
finally:
  import requests
try:
  import json
except ImportError:
  subprocess.check_call([sys.executable, "-m", "pip", "install", 'json'])
finally:
  import json
# End imports


def getInput(strPrompt):
  if sys.version_info[0] > 2:
    return input(strPrompt)
  else:
    print("Please upgrade to python 3 or greater")
    sys.exit()
# end getInput


def SendNotification(strMsg):
  global strNotifyURL

  iTimeOut = 20  # Connection timeout in seconds
  iMaxMSGlen = 199  # Truncate the slack message to this length

  strNotifyURL = strNotifyURL
  dictHeader = {}
  dictHeader["Content-Type"] = "application/json"
  dictHeader["Accept"] = "application/json"
  dictHeader["Cache-Control"] = "no-cache"
  dictHeader["Connection"] = "keep-alive"
  dictHeader["Authorization"] = "Bearer " + strNotifyToken

  dictPayload = {}
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
    if isinstance(WebRequest, requests.models.Response) == False:
      return "FAIL. Response is unknown type"
    else:
      dictResponse = json.loads(WebRequest.text)
      if isinstance(dictResponse, dict):
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


def initvars():
  global strNotifyChannel
  global strNotifyToken
  global strNotifyURL
  global strNotifyEnable

  if os.getenv("NOTIFYENABLE") != "" and os.getenv("NOTIFYENABLE") is not None:
    strNotifyEnable = os.getenv("NOTIFYENABLE")
  else:
    strNotifyEnable = None
    print("No Notify enable provided")

  if os.getenv("NOTIFYURL") != "" and os.getenv("NOTIFYURL") is not None:
    strNotifyURL = os.getenv("NOTIFYURL")
  else:
    strNotifyURL = None
    print("No Notify URL provided")

  if os.getenv("NOTIFYCHANNEL") != "" and os.getenv("NOTIFYCHANNEL") is not None:
    strNotifyChannel = os.getenv("NOTIFYCHANNEL")
  else:
    strNotifyChannel = None
    print("No Notify Channel provided")

  if os.getenv("NOTIFYTOKEN") != "" and os.getenv("NOTIFYTOKEN") is not None:
    strNotifyToken = os.getenv("NOTIFYTOKEN")
  else:
    strNotifyToken = None
    print("No token provided")

  if strNotifyToken is None or strNotifyChannel is None or strNotifyURL is None:
    return False
  else:
    if strNotifyEnable == "false":
      return False
    else:
      return True


def main():
  bNotifyEnable = initvars()
  if not bNotifyEnable:
    print("notifications not enable, can't do anything")
    sys.exit(5)

  if len(sys.argv) > 1:
    strMsg = sys.argv[1]
  else:
    strMsg = ""

  if strMsg == "":
    strMsg = getInput("Please provide a message to send: ")

  if strMsg == "":
    print("No message provided, nothing to do")
    sys.exit(2)

  if bNotifyEnable:
    print(SendNotification(strMsg))
  else:
    print("unable to send notifications, not enabled")


if __name__ == '__main__':
  main()
