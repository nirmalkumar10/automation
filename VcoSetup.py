import qa_env
import pull
import os
import sys
import Util
import json
import fnmatch
import paramiko
import commn
import time
from paramiko import SSHClient
from scp import SCPClient
#name = "modem-pool"
#Vco = "52.52.71.56"
#GwName = "modem-gateway"
#gatewayIp = "52.9.182.185"
#model = "edge500"
#gatewayLocation = "Mt-View"
#EnterpriseName = "modem-enterprise"
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

global VCO_SCRIPTS_PATH
VCO_SCRIPTS_PATH = qa_env._VCO_SCRIPTS_ROOT + str(qa_env._VCO_VERSION)

class init_setup():
      def __init__(self):
          with open("test_config.json") as json_file:
                self.test_config = Dotable(json.load(json_file))
          self.edgeId =  None
          self.edgeindex = "1"
      def create_gatewayPool(self):
          cmd =VCO_SCRIPTS_PATH + "/gatewayPoolLib.js "+  \
          " -a createGateWayPoolExe "+  \
          " -v " + self.test_config["edge"]["vco"] +   \
          " -gatewayPoolName "+ self.test_config["edge"]["gwPoolName"]
          print cmd
          result=Util.execute_Command(cmd)
          id = None
          
          parseresult = Util.loadArgument(result,'result',None)
          if(parseresult  != "PASS"):
             return False
          print parseresult 
          self.GwPoolId= Util.loadArgument(result,'id',None)
          print "Gateway Pool create with GwPoolId "+ str(self.GwPoolId)
          return True

      def create_gateway(self):
          cmd =VCO_SCRIPTS_PATH + "/gatewayLib.js "+  \
          " -a createGateWayExe "+  \
          " -v " + self.test_config["edge"]["vco"] +   \
          " -gatewayPoolId "+ str(self.GwPoolId)+   \
          " -gatewayName  "+ self.test_config["edge"]["GwName"]  + \
          " -gatewayIP " + self.test_config["edge"]["gatewayIp"] + \
          " -gatewayLocation " + self.test_config["edge"]["gatewayLocation"]
          print cmd
          result=Util.execute_Command(cmd)
          
          self.GwActivationKey = Util.loadArgument(result,'activationKey',None)
          self.id = Util.loadArgument(result,'id',None)
          self.gwid = Util.loadArgument(result,'fwid',None)
          self.GwPoolId = Util.loadArgument(result,'GatewaypoolId',None)
          if(self.GwActivationKey == None or self.id ==None or self.GwPoolId ==None):
              return False
          else:
            print "Gateway created with Activation Key " + self.GwActivationKey
          return True

      def create_Profile(self,new_enterprise=None):
          if new_enterprise != None:
             enterpriseName = new_enterprise
             cmd = VCO_SCRIPTS_PATH + "/ProfileCreationV3.js "+    \
             " -v " + self.test_config["edge"]["vco"] +   \
             " -p " + self.test_config["edge"]["vco"] +   \
             " -s " + self.test_config["edge"]["vco"] +   \
             " -t " + str(enterpriseName) +  \
             " -gatewayPoolId " + str(self.GwPoolId)
             print cmd
          else:
            pass
          result=Util.execute_Command(cmd)
          self.configProfileId = Util.loadArgument(result,'configProfileId',None)
          self.enterpriseId = Util.loadArgument(result,'enterpriseId',None) 
          print "New Profile "+ enterpriseName +" created with configProfileId " + str(self.configProfileId) + " enterpriseId " + str(self.enterpriseId)

      def create_edge_at_vco(self):
           self.enterpriseId = self.get_enterpriseId()  
           self.configProfileId = self.get_ProfileId()
           WanLinksData = dict()
           WanLinksData[" "] = dict()
           print json.dumps(WanLinksData) 
           cmd = VCO_SCRIPTS_PATH +"/EdgeCreation.js -t "+ self.test_config["edge"]["enterprise"] + " -e "+str(self.edgeindex) + " -n "+str(self.enterpriseId) + " -c "+str(self.configProfileId) + " -v "+self.test_config["edge"]["vco"] + " -m " + self.test_config["edge"]["model"] +" -w " + """'""" + json.dumps(WanLinksData) + """'"""
           print cmd
           result=Util.execute_Command(cmd)
           print result
           self.edgeId = Util.loadArgument(result,'id',None)
           self.EdgeActivationKey = Util.loadArgument(result,'activationKey',None)
           print "Edge created with Edge ID:" + str(self.edgeId ) +"Key:" +self.EdgeActivationKey
      
      def delete_edge_at_vco(self):
           username = self.test_config["edge"]["enterprise"]+'@'+self.test_config["edge"]["enterprise"]+'.com'
           password = "autoPass123"
           self.edgeId = self.get_edges()
           self.enterpriseId = self.get_enterpriseId()
           cmd  = VCO_SCRIPTS_PATH+"/EdgeDeletion.js -n "+str(self.enterpriseId)+" -e "+str(self.edgeId)+" -v "+ self.test_config["edge"]["vco"] + ' -u '+username+ ' -p '+password
           print cmd
           result=Util.execute_Command(cmd)
           print "Edge deleted with Edge ID: "+ str(self.edgeId)
           self.result = Util.loadArgument(result,'result',None)

      def get_enterpriseId(self):
          cmd =VCO_SCRIPTS_PATH + "/EnterpriseLib.js "+  \
                " -a getEnterpriseExe "+  \
                " -v " + self.test_config["edge"]["vco"] +   \
                " -enterpriseName " + self.test_config["edge"]["enterprise"]

          result=Util.execute_Command(cmd)
          self.enterpriseId = Util.loadArgument(result,'id',None)
          print str(self.enterpriseId) 
          if self.enterpriseId == None:
              return None
          return self.enterpriseId

      def get_ProfileId(self):
          cmd =VCO_SCRIPTS_PATH + "/EnterpriseProfileLib.js "   +\
                " -a getEnterpriseConfigurationExe "                               +\
                " -v " +   self.test_config["edge"]["vco"]    +\
                " -enterpriseId " + str(self.enterpriseId)                 +\
                " -enterpriseConfigName " + "\""+ "Quick Start VPN" +"\""
          result=Util.execute_Command(cmd)
          self.configProfileId = Util.loadArgument(result,'id',None)
          print str(self.configProfileId)
          if(self.configProfileId == None):
              return False
          return self.configProfileId
     
      def get_edges(self):
          self.edgeId = None
          cmd =VCO_SCRIPTS_PATH + "/EnterpriseLib.js "+  \
                " -a getEnterpriseEdgeListExe "+  \
                " -v " + self.test_config["edge"]["vco"] +   \
                " -enterpriseName " + self.test_config["edge"]["enterprise"]
          result=Util.execute_Command(cmd)
          for edge in result:
               self.edgeId= Util.loadArgument(edge,'id',None)
               print "Edge Id : " + str(self.edgeId)           
          return self.edgeId

      def get_gatewayPool(self):
            print "Getting gateway Pool information"
            cmd =VCO_SCRIPTS_PATH + "/gatewayPoolLib.js "+  \
                " -a getGatewayPoolExe "+  \
                " -v " + self.test_config["edge"]["vco"] +   \
                " -gatewayPoolName "+ self.test_config["edge"]["gwPoolName"] 
            print cmd
            result=Util.execute_Command(cmd)
            self.id = None
            self.result = Util.loadArgument(result,'result',None)
            print self.result
            self.id = Util.loadArgument(result,'id',None)
            if(self.result!= "PASS"):
                return False
            else:
                return True 

      def get_gateway(self):
            cmd =VCO_SCRIPTS_PATH + "/gatewayLib.js "+  \
                " -a getGatewayExe "+  \
                " -v " + self.test_config["edge"]["vco"] +   \
                " -gatewayIP " + self.test_config["edge"]["gatewayIP"]
            print cmd
            result=Util.execute_Command(cmd)
            self.result = Util.loadArgument(result,'result',None)
            self.gw_id = Util.loadArgument(result,'id',None)
            #print "VCO delete gw %s" % self.result
            if(self.result!= "PASS"):
                return False
            else:
                return True

      def delete_gateway(self):
          cmd =VCO_SCRIPTS_PATH + "/gatewayLib.js "+  \
                " -a deleteGatewayExe "+  \
                " -v " + self.test_config["edge"]["vco"] +   \
                " -gatewayIP " + self.test_config["edge"]["gatewayIp"]
          result=Util.execute_Command(cmd)
          self.result = Util.loadArgument(result,'result',None)
          print "VCO delete gw %s" % self.result
          if(self.result!= "PASS"):
              return False
          return True
     
      def delete_gatewayPool(self):
          cmd =VCO_SCRIPTS_PATH + "/gatewayPoolLib.js "+  \
                " -a deleteGatewayPoolExe "+  \
                " -v " + self.test_config["edge"]["vco"] +   \
                " -gatewayPoolName "+ self.test_config["edge"]["gwPoolName"]
          print cmd
          result=Util.execute_Command(cmd)

          self.id = None

          self.result = Util.loadArgument(result,'result',None)
          print self.result
          if(self.result!= "PASS"):
              return False
          else:
              print "VCO delete gwPool %s" % self.result
          return True 

      def delete_Profile(self):
          self.get_enterpriseId()
          self.get_ProfileId()
          if self.get_edges() !=  None:
             self.delete_edge_at_vco()
          print "Sleeping for 120 seconds since edge got deactivated"

          try:
              cmd = "vc_procmon restart"
              ssh_handle = commn.connect(host=self.test_config["edge"]["hostname"],login='root',password=self.test_config["edge"]["password"],port=22,handle_type="SSH")
              print "process restart:" +cmd
              ssh_op = commn.exec_cmd(ssh_handle,cmd)
          except:
              print "Edge restarted  from VCO"

          time.sleep(120) 
          ## Delete the profile and operator
          cmd = VCO_SCRIPTS_PATH + "/ProfileDeletion.js "+    \
          " -v " + self.test_config["edge"]["vco"] +    \
          " -t " + self.test_config["edge"]["enterprise"]

          result=Util.execute_Command(cmd)
          self.result = Util.loadArgument(result,'result',None)
          if(self.result!= "PASS"):
             return False
          print "VCO delete profile %s" % self.result
          return True
      
      def download_images(self):
          job_name  = self.test_config["edge"]["release"]
          build_id = self.test_config["edge"]["build"]
          outdir = "/tmp"
          artifact_patterns = ['*.deb' , '*'+ self.test_config["edge"]["model"]+'*'+'.zip']
          self.current_build =  pull.download_image(job_name,build_id,outdir,artifact_patterns)
 
      def send_image_to_edge(self):
         ssh = SSHClient()
         ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
         #ssh.load_system_host_keys(os.path.expanduser("~/.ssh/known_hosts"))
         ssh.connect(self.test_config["edge"]["hostname"],username=self.test_config["edge"]["login"],password=self.test_config["edge"]["password"])

         # SCPCLient takes a paramiko transport as its only argument
         scp = SCPClient(ssh.get_transport())
         for file in os.listdir('/tmp/'+self.current_build):
             if fnmatch.fnmatch(file, "edge-imageupdate-"+self.test_config["edge"]["model"]+"*"+".zip"):
                scp.put("/tmp/"+self.current_build+"/"+file, '~/')
                print "filematch:"+file
                self.edge_image_file = file
         scp.close()
         ssh.close()
     
      def send_rpc_to_edge(self):
         ssh = SSHClient()
         ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
         #ssh.load_system_host_keys(os.path.expanduser("~/.ssh/known_hosts"))
         ssh.connect(self.test_config["edge"]["hostname"],username=self.test_config["edge"]["login"],password=self.test_config["edge"]["password"])
         cmd1  = "mkdir /root/qa/"
         stdin, stdout, stderr = ssh.exec_command(cmd1)
         # SCPCLient takes a paramiko transport as its only argument
         scp = SCPClient(ssh.get_transport())
         scp.put("/tmp/check_rpc_server.py", '/root/qa/')
         scp.put("/tmp/tinyrpc.tar.gz",'/root/qa/tinyrpc.tar.gz')
         scp.put("/tmp/pyutil.tar.gz",'/root/qa/pyutil.tar.gz')

         cmd  = "tar -xf /root/qa/tinyrpc.tar.gz -C /root/qa/"
         stdin, stdout, stderr = ssh.exec_command(cmd)
         print stdout.readlines()
 
         cmd  = "tar -xf /root/qa/pyutil.tar.gz -C /root/qa/"     
         stdin, stdout, stderr = ssh.exec_command(cmd)    
         print stdout.readlines()

         scp.close()
         ssh.close()     
   
      def send_image_to_gateway(self):
         ssh = SSHClient()
         ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
         ssh.connect("52.9.182.185", username="ubuntu", password="None", key_filename="dev-uswest.pem")
         scp = SCPClient(ssh.get_transport())

         for file in os.listdir('/tmp/'+self.current_build):
             if fnmatch.fnmatch(file, "gatewayd*"+".deb"):
                scp.put("/tmp/"+self.current_build+"/"+file, '~/')
                print "filematch:"+file
                self.gw_image_file = file

         scp.close()
         ssh.close()
      
      def install_edge_image(self):
         cmd = "/root/swupdater "+self.edge_image_file
         ssh_handle = commn.connect(host=self.test_config["edge"]["hostname"],login='root',password=self.test_config["edge"]["password"],port=22,handle_type="SSH")
         print "Installing Image:" +cmd
         ssh_op = commn.exec_cmd(ssh_handle,cmd)
         print "Sleep for 180 secs before connecting again"
         time.sleep(180)

      def activate_edge(self):
         cmd = "ls \/opt\/vc\/.edge.info"
         ssh = SSHClient()
         ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
         ssh.connect(self.test_config["edge"]["hostname"],username=self.test_config["edge"]["login"],password=self.test_config["edge"]["password"])
         stdin, stdout, stderr = ssh.exec_command(cmd)
         if not "No such file" in stdout.readlines():
            cmd = 'rm -f \/opt\/vc\/.edge.info'
            stdin, stdout, stderr = ssh.exec_command(cmd)
            cmd = '/opt/vc/bin/vc_procmon restart'
            stdin, stdout, stderr = ssh.exec_command(cmd)
            time.sleep(40)

         '''ssh_handle = commn.connect(host=self.test_config["edge"]["hostname"],login='root',password=self.test_config["edge"]["password"],port=22,handle_type="SSH")
         output = commn.exec_cmd(ssh_handle, cmd, prompt='# ')
         if not 'No such file' in output:
           cmd = 'rm -f \/opt\/vc\/.edge.info'
           output = commn.exec_cmd(ssh_handle, cmd, prompt='# ')
           cmd = '/opt/vc/bin/vc_procmon restart'
           output = commn.exec_cmd(ssh_handle, cmd, prompt)
           time.sleep(40)'''
             
         cmd = '\/opt\/vc\/bin\/activate.py '+ self.EdgeActivationKey + ' -s ' +self.test_config["edge"]["vco"]+ ' -i'
         stdin, stdout, stderr = ssh.exec_command(cmd)
         print stdout.readlines()
         #output = commn.exec_cmd(ssh_handle, cmd, prompt='# ')
  
      def install_gw_image(self):
         cmd ="sudo dpkg -i "+self.gw_image_file+ " -f"
         print cmd
         ssh = SSHClient()
         ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
         ssh.connect("52.9.182.185", username="ubuntu", password="None", key_filename="dev-uswest.pem")
         stdin, stdout, stderr = ssh.exec_command(cmd)
         time.sleep(30)
         ssh.close()    
           
      def activate_gateway(self):
         cmd ="sudo /opt/vc/bin/activate.py -f "+self.GwActivationKey + ' -s ' +self.test_config["edge"]["vco"]+ ' -i'
         print cmd
         ssh = SSHClient()
         ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
         ssh.connect("52.9.182.185", username="ubuntu", password="None", key_filename="dev-uswest.pem")
         stdin, stdout, stderr = ssh.exec_command(cmd)
         print stdout.readlines() 
 
if __name__ == "__main__":
     vco = init_setup()
     print "In main" 
     #vco.create_gatewayPool()
     #vco.create_gateway()
     #vco.create_Profile(EnterpriseName)
     #vco.get_enterpriseId()  
     #vco.get_ProfileId()
     #vco.get_edges()
     #vco.delete_edge_at_vco()
     #vco.create_edge_at_vco()
     #vco.activate_edge() 
     #ret = vco.get_gatewayPool() 
     #print ret
     #vco.delete_Profile()
     #vco.delete_gateway()
     #vco.delete_gatewayPool()
     vco.send_rpc_to_edge()

