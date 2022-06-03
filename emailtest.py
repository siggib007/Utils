'''
Quick little script to send email from python

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
import ssl

# End imports
strPort = 465
bUseTLS = False
bUseStartTLS = False
iDebugLevel = 0
iTimeout = 15

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
  global strPort
  global bUseTLS
  global bUseStartTLS

  if os.getenv("EMAILUSER") != "" and os.getenv("EMAILUSER") is not None:
    strUser = os.getenv("EMAILUSER")
  else:
    return "FATAL ERROR: No email user name provided"

  if os.getenv("EMAILPWD") != "" and os.getenv("EMAILPWD") is not None:
    strPWD = os.getenv("EMAILPWD")
  else:
    return "FATAL ERROR: No email user password provided"

  if os.getenv("EMAILSERVER") != "" and os.getenv("EMAILSERVER") is not None:
    strServer = os.getenv("EMAILSERVER")
  else:
    return "FATAL ERROR: No email server provided"

  if os.getenv("EMAILPORT") != "" and os.getenv("EMAILPORT") is not None:
    strPort = os.getenv("EMAILPORT")
  else:
    LogEntry("No server port provided, using the default of {}".format(strPort))

  if os.getenv("USESSL") != "" and os.getenv("USESSL") is not None:
    if os.getenv("USESSL").lower() == "true":
      bUseTLS = True
    else:
      bUseTLS = False
  else:
    LogEntry("No SSL directive provided, using the default of {}".format(bUseTLS))

  if os.getenv("USESTARTTLS") != "" and os.getenv("USESTARTTLS") is not None:
    if os.getenv("USESTARTTLS").lower() == "true":
      bUseStartTLS = True
    else:
      bUseStartTLS = False
  else:
    LogEntry("No SSL directive provided, using the default of {}".format(bUseStartTLS))

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
      if bUseStartTLS:
        objSMTP.starttls()
    objSMTP.set_debuglevel(iDebugLevel)
    objResponse = objSMTP.login(strUser,strPWD)
    LogEntry ("Response from login: {}".format(objResponse))
    objSMTP.send_message(objMsg)
    objSMTP.quit()
    LogEntry ("Successfully sent email via {} port {} to {}".format(strServer,strPort,strTo))
    return "SUCCESS"
  except ssl.SSLError as err:
    return "SSL Error: {}".format(err)
  except smtplib.SMTPException as err:
    return "Error: unable to send email. {}".format(err)

def main():
  lstHeaders = []
  lstHeaders.append("X-Testing: This is my test header")
  lstHeaders.append("X-Test2: Second test header")
  lstHeaders.append("X-Test3: third test header")
  lstHeaders.append("X-Test4: fourt test header")
  strReturn = SendHTMLEmail("Custom header test", "<h1>Welcome!!!!</h1>\nThis is a <i>supergeek test</i> where we are testing for custom headers",
                "Siggi Supergeek <siggi@bjarnason.us>", "Supergeek Admin <admin@supergeek.us>",lstHeaders)
  if strReturn == "SUCCESS":
    LogEntry("Email sent successfully")
  elif strReturn[:5] == "Error":
    LogEntry("unable to send email. {}".format(strReturn))
  elif strReturn[:11] == "FATAL ERROR":
    LogEntry("Failed to send email. {}".format(strReturn))
  else:
    LogEntry("other non-sucess: {}".format(strReturn))

if __name__ == '__main__':
    main()
