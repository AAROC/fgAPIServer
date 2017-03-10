#!/usr/bin/env python
# Copyright (c) 2015:
# Istituto Nazionale di Fisica Nucleare (INFN), Italy
# Consorzio COMETA (COMETA), Italy
#
# See http://www.infn.it and and http://www.consorzio-cometa.it for details on
# the copyright holders.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from flask import Flask
from flask import request
from flask import Response
from functools import wraps
from OpenSSL import SSL
from fgapiserverconfig import FGApiServerConfig
import os
import sys
import json
import logging.config

"""
  FutureGateway APIServer front-end
"""

__author__ = "Riccardo Bruno"
__copyright__ = "2015"
__license__ = "Apache"
__version__ = "v0.0.2-30-g37540b8-37540b8-37"
__maintainer__ = "Riccardo Bruno"
__email__ = "riccardo.bruno@ct.infn.it"

# setup path
fgapirundir = os.path.dirname(os.path.abspath(__file__)) + '/'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# fgapiserver configuration file
fgapiserver_config_file = fgapirundir + 'fgapiserver.conf'

# Load configuration
fg_config = FGApiServerConfig(fgapiserver_config_file)

# fgapiserver settings
fgapiver = fg_config.get_config_value('fgapiver')
fgapiserver_name = fg_config.get_config_value('fgapiserver_name')
fgapisrv_host = fg_config.get_config_value('fgapisrv_host')
fgapisrv_port = int(fg_config.get_config_value('fgapisrv_port'))
fgapisrv_debug = (fg_config.get_config_value(
    'fgapisrv_debug').lower() == 'true')
fgapisrv_iosandbox = fg_config.get_config_value('fgapisrv_iosandbox')
fgapisrv_geappid = int(fg_config.get_config_value('fgapisrv_geappid'))
fgjson_indent = int(fg_config.get_config_value('fgjson_indent'))
fgapisrv_key = fg_config.get_config_value('fgapisrv_key')
fgapisrv_crt = fg_config.get_config_value('fgapisrv_crt')
fgapisrv_logcfg = fg_config.get_config_value('fgapisrv_logcfg')
fgapisrv_dbver = fg_config.get_config_value('fgapisrv_dbver')
fgapisrv_secret = fg_config.get_config_value('fgapisrv_secret')
fgapisrv_notoken = (fg_config.get_config_value(
    'fgapisrv_notoken').lower() == 'true')
fgapisrv_notokenusr = fg_config.get_config_value('fgapisrv_notokenusr')
fgapisrv_lnkptvflag = fg_config.get_config_value('fgapisrv_lnkptvflag')
fgapisrv_ptvendpoint = fg_config.get_config_value('fgapisrv_ptvendpoint')
fgapisrv_ptvuser = fg_config.get_config_value('fgapisrv_ptvuser')
fgapisrv_ptvpass = fg_config.get_config_value('fgapisrv_ptvpass')
fgapisrv_ptvdefusr = fg_config.get_config_value('fgapisrv_ptvdefusr')
fgapisrv_ptvmapfile = fg_config.get_config_value('fgapisrv_ptvmapfile')

# fgapiserver database settings
fgapisrv_db_host = fg_config.get_config_value('fgapisrv_db_host')
fgapisrv_db_port = int(fg_config.get_config_value('fgapisrv_db_port'))
fgapisrv_db_user = fg_config.get_config_value('fgapisrv_db_user')
fgapisrv_db_pass = fg_config.get_config_value('fgapisrv_db_pass')
fgapisrv_db_name = fg_config.get_config_value('fgapisrv_db_name')

# Logging
logging.config.fileConfig(fgapisrv_logcfg)
logger = logging.getLogger(__name__)
logger.debug(fg_config.show_conf())

# setup Flask app
app = Flask(__name__)


##
#  Authentication
##

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    print "Ckecking for: %s - %s" % (username, password)
    return username == fgapisrv_ptvuser and fgapisrv_ptvpass == password


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

##
# PTV handlers
##


#
# /get-token; PTV endpoint to retrieve a new valid token
# Portals normally return a json in the format:
#    {
#        "error": null,
#        "groups": null,
#        "subject": "<the-subject>",
#        "token": "<the-new-token>"
#    }
# This PTV handler totally ignores basic authentication credentials
# (username/password) contained in the request form but needs the
# subject field initially returned by the checktoken/ call
#
@app.route('/get-token', methods=['GET', 'POST'])
@app.route('/%s/get-token' % fgapiver, methods=['GET', 'POST'])
@requires_auth
def get_token():
    response = {}
    subject = request.values.get('subject')
    if request.method == 'GET':
        message = "Unhandled method: '%s'" % request.method
        response["error"] = message
        ctk_status = 400
    elif request.method == 'POST':
        response = {
            "error": None,
            "groups": None,
            "subject": subject,
            "token": "eyJraWQiOiJyc2ExIiwiYWxnIjoiUlMyNTYifQ.eyJzdWIiOiIzYTJkN"
                     "BmNS0zYmRjLTQwMjAtODJjYi0xMDI4OTQzYzc3N2QiLCJpc3MiOiJodH"
                     "wczpcL1wvaWFtLXRlc3QuaW5kaWdvLWRhdGFjbG91ZC5ldVwvIiwiZXh"
                     "IjoxNDc2MjY3NjA2LCJpYXQiOjE0NzYyNjQwMDYsImp0aSI6IjRjN2Y5"
                     "TczLWJmYzItNDEzYy1hNzhjLWUxZmJlMGU2NjAwYSJ9.BfDlr6Far_oe"
                     "7z-SuLPbXgfKx3VuHJ0iuL-Dyd6G5_7_rNPrvZr5Da_HJUfonOLr8uOo"
                     "UhMUIP_Xiw4ZuWVIIhNPDSdu4lhWy5kkcoQ3rI9myNT2WxLA3IP2ZEwP"
                     "InefF0LzAlMj4-iQQw-kAavKgvA00sO8cww9Hzx6Thfw"
        }
        ctk_status = 200
    else:
        message = "Unhandled method: '%s'" % request.method
        response["error"] = message
        ctk_status = 400
    # include _links part
    response["_links"] = [{"rel": "self", "href": "/get-token"}, ]
    js = json.dumps(response, indent=fgjson_indent)
    resp = Response(js, status=ctk_status, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    return resp


#
# /checktoken; PTV normally uses a portal endpoint to verify incoming Tokens
# Portals normally return a json in the format:
#    { "token_status": "<valid|invalid>",
#    ["portal_user": "<portal_username>"
#     "portal_group": "<portal user group name>" ] }
# Optional fields portal_user and portal_groups are used to map the portal
# user/group with a FutureGateway user/group
# This PTV handler totally ignores basic authentication credentials
# (username/password) contained in the request form
#
@app.route('/get-token-info', methods=['GET', 'POST'])
@app.route('/%s/get-token-info' % fgapiver, methods=['GET', 'POST'])
@app.route('/checktoken', methods=['GET', 'POST'])
@app.route('/%s/checktoken' % fgapiver, methods=['GET', 'POST'])
@requires_auth
def checktoken():
    response = {}
    token = request.values.get('token')
    if request.method == 'GET':
        message = "Unhandled method: '%s'" % request.method
        response["error"] = message
        ctk_status = 400
    elif request.method == 'POST':
        # response = {
        #    "token_status": "valid",
        #    # you may specify:
        #    #  portal_user - A portal user that can be mapped by
        #    #                fgapiserver_ptvmap.json map file
        #    #  portal_group - A portal group that can be mapped by
        #    #                 fgapiserver_ptvmap.json map file
        #    # "portal_user": fgapisrv_ptvdefusr
        #    "portal_group": "admin"
        # }
        response = {
            "error": None,
            "groups": [
                "Users",
                "Developers"
            ],
            # "subject": "a9f37548-4024-4330-88bf-4f43067e6bdb"
            "subject": "98e3009e-e39b-11e6-bcba-5eef910c8578"
        }
        ctk_status = 200
    else:
        message = "Unhandled method: '%s'" % request.method
        response["error"] = message
        ctk_status = 400
    # include _links part
    response["_links"] = [{"rel": "self", "href": "/checktoken"}, ]
    js = json.dumps(response, indent=fgjson_indent)
    resp = Response(js, status=ctk_status, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    return resp


##
# Orchestrator test handler
##


def create_inprogress():
    return {
        "uuid": "756ed6b2-ed63-4992-a8f8-8d5d8045ae02",
        "creationTime": "2016-08-01T12:47+0000",
        "status": "CREATE_IN_PROGRESS",
        "outputs": {},
        "task": "NONE",
        "links": [
            {
                "rel": "self",
                "href": ("http://90.147.170.152:8080/orchestrator/deployments/"
                         "756ed6b2-ed63-4992-a8f8-8d5d8045ae02")
            },
            {
                "rel": "resources",
                "href": ("http://90.147.170.152:8080/orchestrator/deployments/"
                         "756ed6b2-ed63-4992-a8f8-8d5d8045ae02/resources")
            },
            {
                "rel": "template",
                "href": ("http://90.147.170.152:8080/orchestrator/deployments/"
                         "756ed6b2-ed63-4992-a8f8-8d5d8045ae02/template")
            }
        ]
    }
    return response


def create_failed():
    return {
        "uuid": "756ed6b2-ed63-4992-a8f8-8d5d8045ae02",
        "creationTime": "2016-08-01T12:47+0000",
        "updateTime": "2016-08-01T12:47+0000",
        "status": "CREATE_FAILED",
        "statusReason": ("Error 400: Error Creating Inf.: "
                         "Some deploys did not proceed "
                         "successfully: All machines could not be "
                         "launched: \nAttempt 1: Error launching the VMs of "
                         "type ambertools_server to cloud ID one of type "
                         "OpenNebula. Cloud Provider "
                         "Error: No ONE network found for network: "
                         "public_net\n"
                         "Attempt 2: Error launching the VMs of type "
                         "ambertools_server to cloud ID one of type "
                         "OpenNebula. "
                         "Cloud Provider Error: No ONE network found for "
                         "network:  public_net\nAttempt 3: Error "
                         "launching the "
                         "VMs of type ambertools_server to cloud ID one of "
                         " type OpenNebula.  Cloud Provider Error: No ONE "
                         "network found for network: public_net\n\n"),
        "outputs": {},
        "task": "NONE",
        "cloudProviderName": "provider-UPV-GRyCAP",
        "links": [
            {
                "rel": "self",
                "href": ("http://90.147.170.152:8080/orchestrator/deployments/"
                         "756ed6b2-ed63-4992-a8f8-8d5d8045ae02")
            },
            {
                "rel": "resources",
                "href": ("http://90.147.170.152:8080/orchestrator/deployments/"
                         "756ed6b2-ed63-4992-a8f8-8d5d8045ae02/resources")
            },
            {
                "rel": "template",
                "href": ("http://90.147.170.152:8080/orchestrator/deployments/"
                         "756ed6b2-ed63-4992-a8f8-8d5d8045ae02/template")
            }
        ]
    }


def create_complete():
    return {
        "uuid": "1bff4c04-e8b7-43be-8846-a39df1664433",
        "creationTime": "2016-04-12T19:34+0000",
        "updateTime": "2016-04-12T19:38+0000",
        "status": "CREATE_COMPLETE",
        "outputs": {
            "node_creds": "{password=7Uxz4RJR, user=jobtest}",
            "node_ip": "localhost"
        },
        "task": "NONE",
        "links": [
            {
                "rel": "self",
                "href": ("http://90.147.170.152/orchestrator/deployments/"
                         "1bff4c04-e8b7-43be-8846-a39df1664433")
            },
            {
                "rel": "resources",
                "href": ("http://90.147.170.152/orchestrator/deployments/"
                         "1bff4c04-e8b7-43be-8846-a39df1664433/resources")
            },
            {
                "rel": "template",
                "href": ("http://90.147.170.152/orchestrator/deployments/"
                         "1bff4c04-e8b7-43be-8846-a39df1664433/template")
            }
        ]
    }


def check_input():
    return {
        "parameters": {
            "number_cpus": 1,
            "memory_size": "1 GB"
        },
        "template": (
            "tosca_definitions_version: tosca_simple_yaml_1_0\n\n"
            "imports:\n - indigo_custom_types: "
            "https://raw.githubusercontent.com/indigo-dc/tosca-types"
            "/master/custom_types.yaml\n\ndescription: TOSCA template "
            "for deploying an instance of AmberTools v15\n"
            "\ntopology_template:\n"
            " inputs:\n number_cpus:\n type: integer\n "
            "description: number of cpus required for the instance\n "
            "default: 1\n memory_size:\n type: string\n description: "
            "ram memory required for the instance\n default: 1 GB\n\n "
            "node_templates:\n\n ambertools:\n type: tosca.nodes.indigo."
            "Ambertools\n requirements:\n - host: ambertools_server\n\n "
            "ambertools_server:\n type: tosca.nodes.indigo.Compute\n "
            "capabilities:\n endpoint:\n properties:\n network_name: "
            "PUBLIC\n ports:\n ssh_port:\n protocol: tcp\n source: 22\n "
            "host:\n properties:\n num_cpus: { get_input: number_cpus }\n "
            "mem_size: { get_input: memory_size }\n os:\n properties:\n "
            "type: linux\n distribution: ubuntu\n version: 14.04\n "
            "image: indigodatacloudapps/ambertools\n\n outputs:\n "
            "instance_ip:\n value: { get_attribute: [ ambertools_server, "
            "public_address, 0 ] }\n instance_creds:\n value: { "
            "get_attribute: [ ambertools_server, endpoint, credential,"
            " 0 ] }")
    }


@app.route('/orchestrator/deployments/<uuid>', methods=['GET', 'DELETE'])
def orchestrator_deployments_get(uuid):
    response = {}
    dep_status = 404
    token = request.headers.get('Authorization')
    if request.method == 'GET':
        print "endpoint: /orchestrator/deployments/%s (GET)" % uuid
        print "token: %s" % token
        dep_status = 200
        # response = create_inprogress()
        response = create_complete()
        # response = create_failed()
    elif request.method == 'DELETE':
        print "endpoint: /orchestrator/deployments/%s (DELETE)" % uuid
        dep_status = 404
        response = {"error": "Method not yet implemented"}
    print "response: '%s'" % response
    js = json.dumps(response, indent=fgjson_indent)
    resp = Response(js, status=dep_status, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    return resp


@app.route('/orchestrator/deployments', methods=['POST'])
def orchestrator_deployments():
    response = {}
    dep_status = 404
    token = request.headers.get('Authorization')
    if request.method == 'GET':
        dep_status = 404
        response = {"error": "Method not supported"}
    elif request.method == 'POST':
        print "endpoint: /orchestrator/deployments (POST)"
        print "token: %s" % token
        dep_status = 201
        response = create_inprogress()
    js = json.dumps(response, indent=fgjson_indent)
    resp = Response(js, status=dep_status, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    return resp


# Common header section


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers',
                         'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods',
                         'GET,PUT,POST,DELETE,PATCH')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Server', fgapiserver_name)
    return response


#
# The app starts here
#

# Now execute accordingly to the app configuration (stand-alone/wsgi)
if __name__ == "__main__":
    if len(fgapisrv_crt) > 0 and len(fgapisrv_key) > 0:
        context = SSL.Context(SSL.SSLv23_METHOD)
        context.use_privatekey_file(fgapisrv_key)
        context.use_certificate_file(fgapisrv_crt)
        app.run(host=fgapisrv_host, port=fgapisrv_port,
                ssl_context=context, debug=fgapisrv_debug)
    else:
        app.run(host=fgapisrv_host, port=fgapisrv_port+1, debug=fgapisrv_debug)
