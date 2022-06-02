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

# End imports

def CleanExit(strCause):
  print (strCause)
  sys.exit(9)

def main():
  if os.getenv("APIKEY") != "" and os.getenv("APIKEY") is not None:
    strAPIKey = os.getenv("APIKEY")
  else:
    CleanExit("No API key provided")


if __name__ == '__main__':
    main()
