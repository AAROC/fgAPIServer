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
from flask_login import UserMixin
import logging

"""
  FutureGateway APIServer User class
"""
__author__ = "Riccardo Bruno"
__copyright__ = "2015"
__license__ = "Apache"
__version__ = "v0.0.7-1"
__maintainer__ = "Riccardo Bruno"
__email__ = "riccardo.bruno@ct.infn.it"


class User(UserMixin):
    """
    flask-login User Class
    """

    log = None
    id = 0
    name = ''

    def __init__(self, id, name):
        self.log = logging.getLogger(__name__)
        self.id = id
        self.name = name
        self.log.debug("fgUser - id: '%s' - name: '%s'" % (id, name))

    def get_id(self):
        """
         Get the user identifier
        :return: user_id
        """
        return self.id

    def get_name(self):
        """
         Get the user name
        :return:  user_name
        """
        return self.name
