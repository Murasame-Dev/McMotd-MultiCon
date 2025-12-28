import networktools_cpp
import json

test = networktools_cpp.tcping("2001:da8:d800:642::248", 443, 3000)

print(json.dumps(test, indent=4, ensure_ascii=False))

status = test["status"]
print (status)