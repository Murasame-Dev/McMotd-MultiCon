import network_utils_externel_cpp
import json

print(json.dumps(network_utils_externel_cpp.ping("www.baidu.com", 4), indent=4))
print(json.dumps(network_utils_externel_cpp.pingv6("::1", 4), indent=4))
print(json.dumps(network_utils_externel_cpp.tracert("www.baidu.com", 30), indent=4))
