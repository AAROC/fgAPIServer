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
__version__ = "v0.0.7-1"
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
    portal_validate = False
    portal_user = ''
    portal_group = ''
    portal_groups = []
    portal_subject = None
    fgapiserver_db = None
    log = None

    def __init__(self, *args, **kwargs):
        """
            portal_endpoint - The portal endpoint used to validate the user.
            portal_tv_user  - The portal user name used to perform the token
                              validation
            portal_tv_pass  - The portal token validator user password

        """
        self.log = logging.getLogger(__name__)
        self.portal_endpoint = kwargs.get('endpoint', '')
        self.portal_tv_user = kwargs.get('tv_user', '')
        self.portal_tv_pass = kwargs.get('tv_password', '')
        self.fgapiserver_db = kwargs.get('fgapiserver_db', None)

        self.log.debug("Initializing PTV with:\n"
                       "  Endpoint: '%s'\n"
                       "  Username: '%s'\n"
                       "  Password: '%s'\n"
                       % (self.portal_endpoint,
                          self.portal_tv_user,
                          self.portal_tv_pass))

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
        self.log.debug("Validating token: '%s'", token)
        self.log.debug("Connecting PTV service: '%s'" % self.portal_endpoint)

        token_info = {}
        post_data = {'token': token}
        try:
            response = requests.post(self.portal_endpoint,
                                     auth=requests.auth.HTTPBasicAuth(
                                         self.portal_tv_user,
                                         self.portal_tv_pass),
                                     data=post_data
                                     verify=False)
            token_info = response.json()
            response.close()
            self.log.debug("Retrieved token info:\n"
                           "%s" % token_info)
        except:
            self.log.error("Unable to get token info")

        # Now fill class values
        self.portal_validate = \
            token_info.get('subject', '') is not None\
            and len(token_info.get('subject', '')) > 0
        self.portal_user = token_info.get('user', '')
        self.portal_group = token_info.get('group', '')
        self.portal_groups = token_info.get('groups', [])
        self.portal_subject = token_info.get('subject', None)

        validated_token = {
            "portal_validate": self.portal_validate,
            "portal_user": self.portal_user,
            "portal_group": self.portal_group,
            "portal_groups": self.portal_groups,
            "portal_subject": self.portal_subject
        }
        self.log.debug("Validated token:\n"
                       "%s" % validated_token)
        return validated_token
