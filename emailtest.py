'''
Quick little script to test sending email from python

Author Siggi Bjarnason Copyright 2022

Following packages need to be installed as administrator
pip install requests
pip install jason

'''
# Import libraries
import smtplib
import sys
import os
import smtplib

# End imports

def CleanExit(strCause):
  print (strCause)
  sys.exit(9)

def LogEntry(strmsg):
  print(strmsg)

def main():
  strPort = 465
  bUseTLS = False
  if os.getenv("EMAILUSER") != "" and os.getenv("EMAILUSER") is not None:
    strUser = os.getenv("EMAILUSER")
  else:
    CleanExit("No email user name provided")

  if os.getenv("EMAILPWD") != "" and os.getenv("EMAILPWD") is not None:
    strPWD = os.getenv("EMAILPWD")
  else:
    CleanExit("No email user password provided")

  if os.getenv("EMAILSERVER") != "" and os.getenv("EMAILSERVER") is not None:
    strServer = os.getenv("EMAILSERVER")
  else:
    CleanExit("No email server provided")

  if os.getenv("EMAILPORT") != "" and os.getenv("EMAILPORT") is not None:
    strPort = os.getenv("EMAILPORT")
  else:
    LogEntry("No server port provided, using the default of {}".format(strPort))

  strSender = "Private Person <from@example.com>"
  strRCTP = "A Test User <to@example.com>"

  strMsg = "Subject: Howdy Partner\nTo: {}\nFrom: {}\nThis is a test e-mail message. just more testing".format(strRCTP,strSender)

  try:
    objSMTP = smtplib.SMTP(strServer,strPort)
    objSMTP.set_debuglevel(1)
    if bUseTLS:
      objSMTP.starttls()
    objResponse = objSMTP.login(strUser,strPWD)
    print ("Response from login: {}".format(objResponse))
    objResponse = objSMTP.sendmail(strSender, strRCTP, strMsg)
    print("Response from sendmail: {}".format(objResponse))
    print ("Successfully sent email via {} port {} to {}".format(strServer,strPort,strRCTP))
  except smtplib.SMTPException:
    print ("Error: unable to send email")

if __name__ == '__main__':
    main()
