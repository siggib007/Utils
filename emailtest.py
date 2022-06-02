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

def main():
  if os.getenv("APIKEY") != "" and os.getenv("APIKEY") is not None:
    strAPIKey = os.getenv("APIKEY")
  else:
    CleanExit("No API key provided")


  sender = 'from@fromdomain.com'
  receivers = ['to@todomain.com']

  message = """From: From Person <from@fromdomain.com>
  To: To Person <to@todomain.com>
  Subject: SMTP e-mail test

  This is a test e-mail message.
  """

  try:
    smtpObj = smtplib.SMTP('localhost')
    smtpObj.sendmail(sender, receivers, message)
    print ("Successfully sent email")
  except smtplib.SMTPException:
    print ("Error: unable to send email")

if __name__ == '__main__':
    main()
