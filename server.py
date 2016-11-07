import flask
from flask import Flask, render_template , request ,Response
from flask import send_file
import requests
import os
import subprocess
import json
import re
import time

app = Flask(__name__)

class Dotable(dict):
    __getattr__= dict.__getitem__
    def __init__(self, d):
        self.update(**dict((k, self.parse(v))
                           for k, v in d.iteritems()))
    @classmethod
    def parse(cls, v):
        if isinstance(v, dict):
            return cls(v)
        elif isinstance(v, list):
            return [cls.parse(i) for i in v]
        else:
            return v

@app.route('/')
def index():
  return render_template('json.html')

@app.route('/velocloudlogo.png')
def get_image():
    if request.args.get('type') == '1':
       filename = 'velocloudlogo.png'
    else:
       filename = 'velocloudlogo.png'
    return send_file(filename, mimetype='velocloudlogo.png')

@app.route('/my-link/')
def my_link():
  print 'Modem Test Started'
  #os.system("source ~/source-modem.sh")
  #os.system("python ModemAutomation.py")
  return 'Modem Test Started'

@app.route('/get_config/')
def get_config():
    home = os.path.expanduser('~')
    try:
       with open(home+"/Downloads/test_config.json") as json_file:
          test_config = Dotable(json.load(json_file))
          resp = json.dumps(test_config)
    except:
          resp = "File Not found"
    return(resp)
      
@app.route('/del_config/')
def del_config():
    reply = os.system("rm ~/Downloads/test*")
    return "File Deleted"

@app.route('/refresh/')
def refresh():
    print "refreshing interface"
    sendtext = " "
    home = os.path.expanduser('~')
    with open(home+"/Downloads/test_config.json") as json_file:
       test_config = Dotable(json.load(json_file))
    cmd = "ifconfig "+test_config["edge"]["lointf"]+ " down"
    p = os.system('echo %s|sudo -S %s' % (test_config["edge"]["hostpswd"], cmd))
    time.sleep(4)

    cmd = "ifconfig "+test_config["edge"]["lointf"]+ " up"
    p = os.system('echo %s|sudo -S %s' % (test_config["edge"]["hostpswd"], cmd))
    time.sleep(8)

    cmd = "ifconfig "+test_config["edge"]["lointf"] 
    proc = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    for reply in  out.splitlines():
       if "inet" in reply:
           match =re.search(r'\d+\.\d+\.\d+\.\d+',reply)
           if match:
               return 'Interface refreshed and IP:'+match.group()

@app.route('/ping/')
def ping():
    print "Pinging google.com"
    cmd = "ping -c 5 google.com"
    proc = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    print "program output:", out 
    return out

if __name__ == '__main__':
    os.system("rm ~/Downloads/test*")
    app.run(debug=True)

