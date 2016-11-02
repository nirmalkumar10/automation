#!/usr/bin/env python
"""
Pull build artifact from jenkins server

Usage:
        pull_build.py jenkins_job_name build_number|latest local_folder [artifact_name(s)]

Example:
        ./pull_build.py "Release-1.5" latest /tmp '*.deb'
        ./pull_build.py vco-build-test 1614  /tmp

Requires: jenkinsapi

Config:

[assembla]
# https://www.assembla.com/user/edit/manage_clients
API_KEY=<assembla api key>
API_SECRET=<assembla secret key>

[jenkins]
JENKINS_URL=https://build-01.eng.velocloud.net
# https://build-01.eng.velocloud.net/user/<user>/configure
JENKINS_USER=<user name>
JENKINS_SECRET=<api token>

"""

import sys
import os
from ConfigParser import ConfigParser
from jenkinsapi.jenkins import Jenkins
from jenkinsapi.utils.requester import Requester
import fnmatch

ASSEMBLA_API_KEY = None
ASSEMBLA_API_SECRET = None

JENKINS_URL = None
JENKINS_USER = None
JENKINS_SECRET = None

class VCRequester(Requester):
    def get_request_dict(self, params=None, data=None, files=None, headers=None):
                headers = headers or {}
                headers['X-Api-Key'] = ASSEMBLA_API_KEY
                headers['X-Api-Secret'] = ASSEMBLA_API_SECRET
                return super(VCRequester, self).get_request_dict(params, data, files, headers)

def usage():
        print "Usage: %s jenkins_job_name build_number|latest folder [artifact_name(s)]" % (sys.argv[0],)
        sys.exit(1)

def read_config():
        global ASSEMBLA_API_KEY, ASSEMBLA_API_SECRET, JENKINS_URL, JENKINS_USER, JENKINS_SECRET
        config = ConfigParser()
        config.read(os.path.expanduser('~/.assembla'))

        ASSEMBLA_API_KEY = config.get('assembla', 'API_KEY')
        ASSEMBLA_API_SECRET = config.get('assembla', 'API_SECRET')
        JENKINS_URL = config.get('jenkins', 'JENKINS_URL')
        JENKINS_USER = config.get('jenkins', 'JENKINS_USER')
        JENKINS_SECRET = config.get('jenkins', 'JENKINS_SECRET')

def get_jenkins_instance():
        # disable InsecureRequestWarning warning
        import warnings
        import requests.packages.urllib3 as urllib3
        warnings.simplefilter('ignore', urllib3.exceptions.InsecureRequestWarning)

        requester = VCRequester(username=JENKINS_USER, password=JENKINS_SECRET, baseurl=JENKINS_URL, ssl_verify=False)
        server = Jenkins(baseurl=JENKINS_URL, requester=requester)
        return server

def match_artifact(patterns, artifact_name):
        for p in patterns:
                if fnmatch.fnmatch(artifact_name, p):
                        return True
        return False
   
def download_image(arg_job_name,arg_build_id,arg_outdir,arg_artifact_patterns):
    job_name = arg_job_name 
    build_id = arg_build_id 
    outdir  = arg_outdir
    artifact_patterns = arg_artifact_patterns
    read_config()

    jenkins = get_jenkins_instance()
    job = jenkins.get_job(job_name)
    if build_id.lower() == 'latest':
         build = job.get_last_stable_build()
    else:
         build = job.get_build(int(build_id))

    name = build.name[len(job_name)+1:] if build.name.startswith(job_name) else build.name
    print "Found build '%s'. Build status: %s " % (name, build.get_status())

    artifacts = list(build.get_artifacts())
    if len(artifacts)==0:
       print "This build has no artifacts"
       sys.exit(1)
    print artifact_patterns

    build_folder = os.path.join(outdir, str(name))
    if not os.path.exists(build_folder):
        os.makedirs(build_folder)
    for artifact in artifacts:
        sys.stdout.write("Found artifact '%s'... " % (artifact.filename,))
        if not artifact_patterns or match_artifact(artifact_patterns, artifact.filename):
           sys.stdout.write("Downloading..." )
           sys.stdout.flush()
           artifact.save_to_dir(build_folder)
           print "Done."
        else:
            print "Skipping."
    return name 

if __name__ == "__main__":
        if len(sys.argv) < 4: usage()

        job_name = sys.argv[1]
        build_id = sys.argv[2]
        outdir = sys.argv[3]
        artifact_patterns = sys.argv[4:]
        download_image(job_name,build_id,outdir,artifact_patterns)
        
