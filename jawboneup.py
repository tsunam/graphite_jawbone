#!/usr/bin/python
# Import data from jawbone's website, and feed the data into graphite
import requests
import json
import time
import re
import socket
import struct
import pickle
import sys
class jawboneauth:
    def __init__(self, username, password, service='nudge'):
        self.authurl = "https://jawbone.com/user/signin/login"
        self.username = username
        self.password = password
        self.service = service
    def authentication(self):
        data = {'email': self.username, 'pwd': self.password, 'service': self.service}
        request = requests.get(self.authurl, params=data)
        jtoken = json.loads(request.text)
        result = jtoken['token']
        return result

class jawboneclient:
    def __init__(self, token):
        self.nudge_header = {'x-nudge-token': token}
        self.api_url_base = 'https://jawbone.com/nudge/api/users/@me/'
        self.prefix = "self.jawbone."
    def moves(self):
        request = requests.get(self.api_url_base + "moves", headers = self.nudge_header )
        jload = json.loads(request.text)
        prefix = self.prefix + "moves"
        return jload, prefix 
    def goals(self):
        request = requests.get(self.api_url_base + "goals", headers = self.nudge_header )
        jload = json.loads(request.text)
        prefix = self.prefix + "goals"
        return jload, prefix
    def sleeps(self):
        request = requests.get(self.api_url_base + "sleeps", headers = self.nudge_header )
        jload = json.loads(request.text)
        prefix = self.prefix + "sleeps"
        return jload, prefix
    def trends(self):
        request = requests.get(self.api_url_base + "trends", headers = self.nudge_header )
        jload = json.loads(request.text)
        prefix = self.prefix + "trends"
        return jload , prefix

def keyparse(data, prefix="servers", pickled=([]), epoch=int(time.time())):
        epoch2 = ""
        if isinstance(data, dict):
                for key, value in data.items():
                        if isinstance(value, dict):
                                #use asleep_time as the basis of all values when gathering sleep data
                                if "asleep_time" in value.keys():
                                    epoch=value["asleep_time"]
                                #don't include the date field as a directory since it will be new each day
                                if not key.startswith(time.strftime('%Y')) or key.startswith(str(int(time.strftime('%Y'))-1)):
                                    prefix2=prefix + "." + key
                                else:
                                    prefix2=prefix
                                for key in value.keys():
                                    if key.startswith(time.strftime('%Y')) or key.startswith(str(int(time.strftime('%Y'))-1)):
                                        epoch2=int(time.mktime(time.strptime(key, '%Y%m%d%H')))
                                        keyparse(value[key], prefix2, epoch=epoch2)
                                keyparse(value, prefix2, epoch=epoch)
                        if isinstance(value, list):
                                prefix2=prefix + "." + key
                                for item in value:
                                    keyparse(item, prefix2)
                        else:
                                prefix2=prefix + "." + key
                                if isinstance(value, (int, long, float, complex)):
                                        if isinstance(value, bool):
                                                continue
                                        else:
                                                pickled.append(( prefix2, (epoch, value)))
        return pickled

def json_parse(data):
    for section in data:
        nprefix = prefix + "." + section
        grapdata = keyparse(data[section], prefix=nprefix)
    return grapdata

def send_data(data, server, port):
    payload = pickle.dumps(data)
    header = struct.pack("!L", len(payload))
    message = header + payload
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((server, port))
    try:
        s.sendall(message)
    except socket.error, (value,message):
        print "could not send message:", message
        sys.exit(1)
    s.close()

server = "graphite.localhost"
port = 2004
jauth = jawboneauth('username', 'password')
japi = jauth.authentication()
jcli = jawboneclient(japi)
moves, prefix = jcli.moves()
grapdata = json_parse(moves)
send_data(grapdata, server, port)
sleeps, prefix = jcli.sleeps()
grapdata = json_parse(sleeps)
send_data(grapdata, server, port)
trends, prefix = jcli.trends()
grapdata = json_parse(trends)
send_data(grapdata, server, port)
