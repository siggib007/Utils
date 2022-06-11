import akeyless
import os
import sys

configuration = akeyless.Configuration(host = "https://api.akeyless.io")
api_client = akeyless.ApiClient(configuration)
api = akeyless.V2Api(api_client)
if os.getenv("AKEYLESS_ID") != "" and os.getenv("AKEYLESS_ID") is not None:
  strAccessID = os.getenv("AKEYLESS_ID")
else:
  print ("FATAL ERROR: No access ID provided")
  sys.exit(9)

if os.getenv("AKEYLESS_KEY") != "" and os.getenv("AKEYLESS_KEY") is not None:
  strAccessKey = os.getenv("AKEYLESS_KEY")
else:
  print("FATAL ERROR: No access key provided")
  sys.exit(9)

body = akeyless.Auth(access_id=strAccessID, access_key=strAccessKey)
res = api.auth(body)

# if auth was successful, there should be a token
token = res.token

lstSecretNames = []
lstSecretNames.append("MySecret1")
lstSecretNames.append("MyFirstSecret")
lstSecretNames.append("/TSC/AnotherTest2")
lstSecretNames.append("/Test/MyPathTest")
body = akeyless.GetSecretValue(
    names=lstSecretNames, token=token)
res = api.get_secret_value(body)
print(res)
