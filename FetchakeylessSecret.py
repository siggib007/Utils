from logging import exception
import akeyless
import os
import sys


def FetchSecret(lstSecretNames):
  objConfig = akeyless.Configuration(host = "https://api.akeyless.io")
  objClient = akeyless.ApiClient(objConfig)
  objAPI = akeyless.V2Api(objClient)
  if os.getenv("AKEYLESS_ID") != "" and os.getenv("AKEYLESS_ID") is not None:
    strAccessID = os.getenv("AKEYLESS_ID")
  else:
    return "FATAL ERROR: No access ID provided"

  if os.getenv("AKEYLESS_KEY") != "" and os.getenv("AKEYLESS_KEY") is not None:
    strAccessKey = os.getenv("AKEYLESS_KEY")
  else:
    return "FATAL ERROR: No access key provided"

  objBody = akeyless.Auth(access_id=strAccessID, access_key=strAccessKey)
  objResponse = objAPI.auth(objBody)

  # if auth was successful, there should be a token
  objToken = objResponse.token
  objBody = akeyless.GetSecretValue(
      names=lstSecretNames, token=objToken)
  try:
    objResponse = objAPI.get_secret_value(objBody)
  except akeyless.exceptions.ApiException as err:
    return "Error occured during fetch: {}".format(err)

  return objResponse

lstSecretNames = []
lstSecretNames.append("MySecret1")
lstSecretNames.append("MySecret2")
lstSecretNames.append("MyFirstSecret")
lstSecretNames.append("/TSC/AnotherTest2")
lstSecretNames.append("/Test/MyPathTest")

dictSecrets = FetchSecret(lstSecretNames)
if isinstance(dictSecrets,dict):
  strSecret1 = dictSecrets["MySecret1"]
  strSecret2 = dictSecrets["MyFirstSecret"]
  strSecret3 = dictSecrets["/TSC/AnotherTest2"]
  strSecret4 = dictSecrets["/Test/MyPathTest"]
else:
  print(dictSecrets)
  sys.exit(9)

print ("Fetched values for the following secrets")
i = 1
for strKey in dictSecrets.keys():
  print ("{}:{}".format(i,strKey))
  i += 1

print("\nValues\n1:{}\n2:{}\n3:{}\n4:{}\n".format(strSecret1,strSecret2,strSecret3,strSecret4))
