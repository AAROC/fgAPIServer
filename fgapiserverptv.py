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
import urllib2
import base64
import requests
import json
import logging
import logging.config
from fgapiserverdb import FGAPIServerDB
from fgapiserver_user import User

__author__ = "Riccardo Bruno"
__copyright__ = "2015"
__license__ = "Apache"
__version__ = "v0.0.2-30-g37540b8-37540b8-37"
__maintainer__ = "Riccardo Bruno"
__email__ = "riccardo.bruno@ct.infn.it"

"""
  fgapiserver_ptv - APIServer Portal Token Validator

  The portal validator class just verifies an incoming token within a
  portal linked to the APIServer
  In this case the portal must expose an API endpoint accessible via
  HTML basic authentication and
  listening for the following POST call:

    token: '<token to verify>'

  The output of the call must be the following json

  {
     "token_status": "<valid|invalid>"
   [,"portal_user" : "<portal username>"
    ,"portal_group": "<portal group>"]
  }

  Optional values such portal user and group can be used to apply a
  fine-grained user mapping from portal users to the APIServer users
"""


class FGAPIServerPTV:

    portal_endpoint = ''
    portal_tv_user = ''
    portal_tv_pass = ''
    portal_realm = ''
    portal_validate = False
    portal_user = ''
    portal_group = ''
    portal_groups = []
    portal_subject = None

    fgapiserver_db = None

    def __init__(self, *args, **kwargs):
        """
            portal_endpoint - The portal endpoint used to validate the user.
            portal_tv_user  - The portal user name used to perform the token
                              validation
            portal_tv_pass  - The portal token validator user password

        """
        self.portal_endpoint = kwargs.get('endpoint', '')
        self.portal_tv_user = kwargs.get('tv_user', '')
        self.portal_tv_pass = kwargs.get('tv_password', '')
        self.fgapiserver_db = kwargs.get('fgapiserver_db', None)
        self.portal_realm = base64.encodestring(
            '%s:%s' % (self.portal_tv_user,
                       self.portal_tv_pass)).replace('\n', '')

    def validate_token(self, token):
        """
        This call contacts the portal sending to it the incoming token.
        The portal will anwer with token validity and optionally associated
        infrormation

        :param token: The incoming API token
        :return: return a map containing:
        { "portal_validate": true/false - true if the portal says the to
                                          ken is valid
         ,"portal_group"   : groupname  - the name of portal group associated
                                          by the portal (group level mapping)
         ,"portal_user"    : username   - the username recognized from token
                                          by the portal (user level mapping)
         ,"portal_groups"  : groups     - A list of associated portal groups
        }
        The return of user and group field is not mandatory for the portal.
        """
        print "connection: '%s'" % self.portal_endpoint
        # request = urllib2.Request(self.portal_endpoint)
        # #request.add_header("Authorization", "Basic %s" % self.portal_realm)
        # result = urllib2.urlopen(request)
        # token_info = json.load(result)
        # result.close()

        # post_data = {"token": token}
        post_data = "token=%s" % token
        # response = requests.post(self.portal_endpoint
        #                         data=post_data,
        #                         auth=requests.auth.HTTPBasicAuth(
        #                             self.portal_tv_user,
        #                             self.portal_tv_pass))
        response = requests.post(self.portal_endpoint+"?"+post_data,
                                 auth=requests.auth.HTTPBasicAuth(
                                     self.portal_tv_user,
                                     self.portal_tv_pass),
                                 verify=False)
        token_info = response.json()
        response.close()
        print token_info

        # Now fill class values
        self.portal_validate = \
            token_info.get('subject', '') is not None\
            and len(token_info.get('subject', '')) > 0
        self.portal_user = token_info.get('user', '')
        self.portal_group = token_info.get('group', '')
        self.portal_groups = token_info.get('groups', [])
        self.portal_subject = token_info.get('subject', None)

        return {
            "portal_validate": self.portal_validate,
            "portal_user": self.portal_user,
            "portal_group": self.portal_group,
            "portal_groups": self.portal_groups,
            "portal_subject": self.portal_subject
        }

    # def mapUser(self):
    #     return User()
    # The portal user has to be mapped from its name or group with an username
    # registered inside the APIServer database. If no group or name are
    # recognized a default user will be associated (guest)
    # Once the user is recognized the incoming token will be registered as
    # session token
    # self.fgapiserver_db.registerToken(...)
