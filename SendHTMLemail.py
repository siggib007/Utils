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
from email.mime.application import MIMEApplication

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
  # placeholder for a function that closes everything down 
  # and cleans things up before exiting from a error condition
  
  print (strCause)
  sys.exit(9)

def LogEntry(strmsg):
  # placeholder for your event logging function.
  print(strmsg)

def SendHTMLEmail(strSubject, strBody, strTo, strFrom,lstHeaders=[],strAttachment="",strAttachName=""):
# Function that sends an email
  
  global strPort
  global bUseTLS
  global bUseStartTLS

# Fetch the email server username from environment variable
  if os.getenv("EMAILUSER") != "" and os.getenv("EMAILUSER") is not None:
    strUser = os.getenv("EMAILUSER")
  else:
    return "FATAL ERROR: No email user name provided"

# Fetch the email server password from environment variable, 
# please store securely in secrets manager like doppler
  if os.getenv("EMAILPWD") != "" and os.getenv("EMAILPWD") is not None:
    strPWD = os.getenv("EMAILPWD")
  else:
    return "FATAL ERROR: No email user password provided"

# Fetch the email server FQDN from environment variable
  if os.getenv("EMAILSERVER") != "" and os.getenv("EMAILSERVER") is not None:
    strServer = os.getenv("EMAILSERVER")
  else:
    return "FATAL ERROR: No email server provided"

# Fetch the email server SMTP port number from environment variable
  if os.getenv("EMAILPORT") != "" and os.getenv("EMAILPORT") is not None:
    strPort = os.getenv("EMAILPORT")
  else:
    LogEntry("No server port provided, using the default of {}".format(strPort))

# Fetch environment variable to indicate if SMTP connection supports SSL/TLS or not. Boolean
  if os.getenv("USESSL") != "" and os.getenv("USESSL") is not None:
    if os.getenv("USESSL").lower() == "true":
      bUseTLS = True
    else:
      bUseTLS = False
  else:
    LogEntry("No SSL directive provided, using the default of {}".format(bUseTLS))

# Fetch environment variable to indicate if SMTP connection supports STARTTLS or not. Boolean
# Only applicable if bUseTLS is false
  if os.getenv("USESTARTTLS") != "" and os.getenv("USESTARTTLS") is not None:
    if os.getenv("USESTARTTLS").lower() == "true":
      bUseStartTLS = True
    else:
      bUseStartTLS = False
  else:
    LogEntry("No SSL directive provided, using the default of {}".format(bUseStartTLS))

# Compose the email message
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

  #Create the attachment
  if strAttachment != "":
    if strAttachName == "":
      return "Error: Attachment provided but no attachment name"
    else:
      lstFileParts = strAttachName.split(".")
      objAttachment = MIMEApplication(strAttachment,_subtype=lstFileParts[1],name=strAttachName)
      objAttachment.add_header("content_disposition","attachment")
      objMsg.attach(objAttachment)

# Send the email message
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

def csv2array(strFilename,strFieldDelim):
  objFile = open(strFilename,"r")
  strLines = objFile.readlines()
  objFile.close()
  lstReturn = []
  for strLine in strLines:
    strLine = strLine.strip()
    if strFieldDelim in strLine:
      lstLineParts = strLine.split(strFieldDelim)
      lstReturn.append(lstLineParts)
  return lstReturn

def array2html(lstTable):
  i = 1
  strReturn = ""
  strReturn += "<html\n<head>\n<style>\n"
  strReturn += "table, th, td {\n"
  strReturn += "  border: 1px solid black;\n"
  strReturn += "  border-collapse: collapse;\n"
  strReturn += "}\n"
  strReturn += "</style>\n</head>\n<body>\n"
  for lstLineParts in lstTable:
    if i == 1:
      strReturn += "<table>\n<tr>\n"
      for strLineFields in lstLineParts:
        strReturn += "<th>" + strLineFields.strip() + "</th>"
      strReturn += "\n</tr>\n"
      i += 1
    else:
      strReturn += "<tr>\n"
      for strLineFields in lstLineParts:
        strReturn += "<td>" + strLineFields.strip() + "</td>"
      strReturn += "\n</tr>\n"
      i += 1
  strReturn += "</table>\n</body>\n</html>\n"
  return strReturn

      


def main():
# Define statics
  strFilename = "URLResp"
  strFileExt = "csv"
  strFieldDelim = ";"

#Generate test data
  lstTable = csv2array(strFilename+"."+strFileExt,strFieldDelim)
  strHTMLTable = array2html(lstTable)

# Prep to call the SendHTMLEmail function
  lstHeaders = []
  lstHeaders.append("X-Testing: This is my test header")
  lstHeaders.append("X-Test2: Second test header")
  lstHeaders.append("X-Test3: third test header")
  lstHeaders.append("X-Test4: fourt test header")
  strAttachName = "MyData.html"
  strSubject = "Complex HTML test with picture, table and attachment"
  strTO = "Siggi Supergeek <siggi@bjarnason.us>"
  strFrom = "Supergeek Admin <admin@supergeek.us>"
  strBody = "<h1>Welcome!!!!</h1>\n"
  strBody += "This is a <i>supergeek test</i> where we are testing for custom headers<br>\n"
  strBody += "I hope it works out great<br>\n"
  strBody += "<p>Here is a cute picture for you</p>\n"
  strBody += "<img src='https://img.xcitefun.net/users/2015/01/371695,xcitefun-cute-animals-pictures-41.jpg' width=100% >"
  strBody += "<p>Let's add a table for fun!</p>\n" + strHTMLTable


# Call the function with all the proper parameters
  strReturn = SendHTMLEmail(strSubject, strBody, strTO, strFrom, lstHeaders,strHTMLTable,strAttachName)

# Evaluate the response from the function
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
