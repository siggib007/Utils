'''
Quick little script to test sending email from python

Author Siggi Bjarnason Copyright 2022

Following packages need to be installed as administrator
pip install requests
pip install jason

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
bUseTLS = False
iDebugLevel = 0


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


def SendHTMLEmail(strSubject, strBody, strTo, strFrom):

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

  #objMsg = email.message.EmailMessage(email.policy.SMTP)
  objMsg = MIMEMultipart('alternative')
  objMsg["To"] = strTo
  objMsg["From"] = strFrom
  objMsg["Subject"] = strSubject
  objMsg['Date'] = email.utils.formatdate(localtime=True)
  objMsg['Message-ID'] = email.utils.make_msgid()
  #objMsg.add_header('Content-Type', 'text/html')
  #objMsg.set_content(strHTML, subtype="html")
  #objMsg.set_content(strTxtBody, subtype="plain")
  #strMsg = "Subject: Howdy Partner\nTo: {}\nFrom: {}\nThis is a test e-mail message. just more testing".format(strRCTP,strSender)
  oPart1 = MIMEText(remove_tags(strBody), "plain")
  opart2 = MIMEText(strBody, "html")
  objMsg.attach(oPart1)
  objMsg.attach(opart2)

  try:
    objSMTP = smtplib.SMTP(strServer,strPort)
    objSMTP.set_debuglevel(iDebugLevel)
    if bUseTLS:
      objSMTP.starttls()
    objResponse = objSMTP.login(strUser,strPWD)
    print ("Response from login: {}".format(objResponse))
    objResponse = objSMTP.send_message(objMsg)
    objSMTP.quit()
    print("Response from sendmail: {}".format(objResponse))
    print ("Successfully sent email via {} port {} to {}".format(strServer,strPort,strTo))
  except smtplib.SMTPException:
    print ("Error: unable to send email")

def main():
  SendHTMLEmail("strSubject", "strBody", "strTo", "strFrom")

if __name__ == '__main__':
    main()