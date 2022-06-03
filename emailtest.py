'''
Quick little script to test sending email from python

Author Siggi Bjarnason Copyright 2022

Following packages need to be installed as administrator
pip install bs4

'''
# Import libraries
import sys
import os
import smtplib
import email.message
import email.policy
import email.utils
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from bs4 import BeautifulSoup

# End imports
strPort = 465
bUseTLS = True
iDebugLevel = 0
iTimeout = 5

def remove_tags(html):

    # parse html content
    soup = BeautifulSoup(html, "html.parser")

    for data in soup(['style', 'script']):
        # Remove tags
        data.decompose()

    # return data by retrieving the tag content
    return ' '.join(soup.stripped_strings)

def CleanExit(strCause):
  print (strCause)
  sys.exit(9)

def LogEntry(strmsg):
  print(strmsg)


def SendHTMLEmail(strSubject, strBody, strTo, strFrom,lstHeaders=[]):

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

  objMsg = MIMEMultipart('alternative')
  objMsg["To"] = strTo
  objMsg["From"] = strFrom
  objMsg["Subject"] = strSubject
  objMsg['Date'] = email.utils.formatdate(localtime=True)
  objMsg['Message-ID'] = email.utils.make_msgid()
  for strHead in lstHeaders:
    lstHeadParts = strHead.split(":")
    if len(lstHeadParts) == 2:
      strHeadName = lstHeadParts[0].strip()
      strHeadValue = lstHeadParts[1].strip()
      objMsg.add_header(strHeadName, strHeadValue)
  oPart1 = MIMEText(remove_tags(strBody), "plain")
  opart2 = MIMEText(strBody, "html")
  objMsg.attach(oPart1)
  objMsg.attach(opart2)

  try:
    if bUseTLS:
      objSMTP = smtplib.SMTP_SSL(strServer,strPort,timeout=iTimeout)
    else:
      objSMTP = smtplib.SMTP(strServer, strPort, timeout=iTimeout)
    objSMTP.set_debuglevel(iDebugLevel)
    objResponse = objSMTP.login(strUser,strPWD)
    print ("Response from login: {}".format(objResponse))
    objSMTP.send_message(objMsg)
    objSMTP.quit()
    print ("Successfully sent email via {} port {} to {}".format(strServer,strPort,strTo))
  except smtplib.SMTPException as err:
    print ("Error: unable to send email. {}".format(err))

def main():
  lstHeaders = []
  lstHeaders.append("X-Testing: This is my test header")
  lstHeaders.append("X-Test2: Second test header")
  lstHeaders.append("X-Test3: third test header")
  lstHeaders.append("X-Test4: fourt test header")
  SendHTMLEmail("Custom header test", "<h1>Welcome!!!!</h1>\nThis is a <i>supergeek test</i> where we are testing for custom headers",
                "Siggi Supergeek <siggi@bjarnason.us>", "Supergeek Admin <admin@supergeek.us>",lstHeaders)

if __name__ == '__main__':
    main()
