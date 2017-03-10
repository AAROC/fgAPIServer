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

import random
import string
import json
import ConfigParser

__author__ = "Riccardo Bruno"
__copyright__ = "2015"
__license__ = "Apache"
__version__ = "v0.0.2-63-g13196a8-13196a8-77"
__maintainer__ = "Riccardo Bruno"
__email__ = "riccardo.bruno@ct.infn.it"

# GridEngine API Server configuration


class FGApiServerConfig:
    fgConfig = {}

    def __init__(self, config_file):
        # Parse configuration file
        config = ConfigParser.ConfigParser()
        config.read(config_file)

        # fgapiserver
        self.fgConfig['fgapiver'] = config.get('fgapiserver', 'fgapiver')
        self.fgConfig['fgapiserver_name'] = "%s %s" % (config.get(
            'fgapiserver', 'fgapiserver_name'), self.fgConfig['fgapiver'])
        self.fgConfig['fgapisrv_host'] = config.get(
            'fgapiserver', 'fgapisrv_host')
        self.fgConfig['fgapisrv_port'] = config.get(
            'fgapiserver', 'fgapisrv_port')
        self.fgConfig['fgapisrv_debug'] = config.get(
            'fgapiserver', 'fgapisrv_debug')
        self.fgConfig['fgapisrv_iosandbox'] = config.get(
            'fgapiserver', 'fgapisrv_iosandbox')
        self.fgConfig['fgapisrv_geappid'] = config.get(
            'fgapiserver', 'fgapisrv_geappid')
        self.fgConfig['fgjson_indent'] = config.get(
            'fgapiserver', 'fgjson_indent')
        self.fgConfig['fgapisrv_key'] = config.get(
            'fgapiserver', 'fgapisrv_key')
        self.fgConfig['fgapisrv_crt'] = config.get(
            'fgapiserver', 'fgapisrv_crt')
        self.fgConfig['fgapisrv_logcfg'] = config.get(
            'fgapiserver', 'fgapisrv_logcfg')
        self.fgConfig['fgapisrv_secret'] = config.get(
            'fgapiserver', 'fgapisrv_secret')
        self.fgConfig['fgapisrv_notoken'] = config.get(
            'fgapiserver', 'fgapisrv_notoken')
        self.fgConfig['fgapisrv_notokenusr'] = config.get(
            'fgapiserver', 'fgapisrv_notokenusr')
        self.fgConfig['fgapisrv_lnkptvflag'] = config.get(
            'fgapiserver', 'fgapisrv_lnkptvflag')
        self.fgConfig['fgapisrv_ptvendpoint'] = config.get(
            'fgapiserver', 'fgapisrv_ptvendpoint')
        self.fgConfig['fgapisrv_ptvuser'] = config.get(
            'fgapiserver', 'fgapisrv_ptvuser')
        self.fgConfig['fgapisrv_ptvpass'] = config.get(
            'fgapiserver', 'fgapisrv_ptvpass')
        self.fgConfig['fgapisrv_ptvdefusr'] = config.get(
            'fgapiserver', 'fgapisrv_ptvdefusr')
        self.fgConfig['fgapisrv_ptvdefgrp'] = config.get(
            'fgapiserver', 'fgapisrv_ptvdefgrp')
        self.fgConfig['fgapisrv_ptvmapfile'] = config.get(
            'fgapiserver', 'fgapisrv_ptvmapfile')

        # fgapiserver_db
        self.fgConfig['fgapisrv_db_host'] = config.get(
            'fgapiserver_db', 'fgapisrv_db_host')
        self.fgConfig['fgapisrv_db_port'] = config.get(
            'fgapiserver_db', 'fgapisrv_db_port')
        self.fgConfig['fgapisrv_db_user'] = config.get(
            'fgapiserver_db', 'fgapisrv_db_user')
        self.fgConfig['fgapisrv_db_pass'] = config.get(
            'fgapiserver_db', 'fgapisrv_db_pass')
        self.fgConfig['fgapisrv_db_name'] = config.get(
            'fgapiserver_db', 'fgapisrv_db_name')
        # Show configuration
        if self.fgConfig['fgapisrv_debug'] == 'True':
            print self.show_conf()

    def show_conf(self):
        """
          Show the loaded APIServer fron-end configuration
        :return:
        """
        return ("FutureGateway API Server config\n"
                "----------------------------------\n"
                "%s\n" % json.dumps(self.fgConfig,
                                    indent=int(
                                        self.fgConfig['fgjson_indent'])))

    def get_config_value(self, key):
        """
          This function retrieves the given configuration parameter or its
          corresponding default value in case the requested parameter is not
          present in the configuration file.
        :rtype: config value
        :param key: The key name
        :return: The configuration value identified by the kwy entry
        """
        def_value = None
        if key == 'fgapiver':
            def_value = 'v.10'
        elif key == 'fgapiserver_name':
            def_value = 'GridEngine API Server % s' % self.get_config_value(
                'fgapiver')
        elif key == 'fgapisrv_host':
            def_value = 'localhost'
        elif key == 'fgapisrv_port':
            def_value = '8888'
        elif key == 'fgapisrv_debug':
            def_value = 'True'
        elif key == 'fgapisrv_db_host':
            def_value = 'localhost'
        elif key == 'fgapisrv_db_port':
            def_value = '3306'
        elif key == 'fgapisrv_db_user':
            def_value = 'localhost'
        elif key == 'fgapisrv_db_pass':
            def_value = 'fgapiserver_password'
        elif key == 'fgapisrv_db_name':
            def_value = 'fgapiserver'
        elif key == 'fgapisrv_iosandbox':
            def_value = '/tmp'
        elif key == 'fgapisrv_geappid':
            def_value = '10000'
        elif key == 'fgjson_indent':
            def_value = '4'
        elif key == 'fgapisrv_key':
            def_value = ''
        elif key == 'fgapisrv_crt':
            def_value = ''
        elif key == 'fgapisrv_logcfg':
            def_value = 'fgapiserver_log.conf'
        elif key == 'fgapisrv_secret':
            def_value = ''.join(random.choice(string.uppercase)
                                for x in range(16))
        elif key == 'fgapisrv_notoken':
            def_value = 'False'
        elif key == 'fgapisrv_notokenusr':
            def_value = 'futuregateway'
        elif key == 'fgapisrv_lnkptvflag':
            def_value = 'False'
        elif key == 'fgapisrv_ptvendpoint':
            def_value = 'http://localhost/ptv'
        elif key == 'fgapisrv_ptvuser':
            def_value = 'ptvuser'
        elif key == 'fgapisrv_ptvpass':
            def_value = 'ptvpass'
        elif key == 'fgapisrv_ptvdefusr':
            def_value = 'futuregateway'
        elif key == 'fgapisrv_ptvdefgrp':
            def_value = 'administrator'
        elif key == 'fgapisrv_ptvmapfile':
            def_value = 'fgapiserver_ptvmap.json'
        else:
            print "[WARNING] Not found default value for key: '%s'" % key
        return self.fgConfig.get(key, def_value)

    def get_config(self):
        """
         This function returns the object containing loaded configuration
         settings
        :return: the object containing configuration settings
        """
        return self.fgConfig
