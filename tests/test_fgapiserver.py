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

import unittest
import fgapiserver
import hashlib
import json
import os
import shutil
from fgapiserver import app
from mklogtoken import token_encode, token_decode, token_info

__author__ = "Riccardo Bruno"
__copyright__ = "2015"
__license__ = "Apache"
__version__ = "v0.0.2-30-g37540b8-37540b8-37"
__maintainer__ = "Riccardo Bruno"
__email__ = "riccardo.bruno@ct.infn.it"


class Test_fgAPIServer(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.app.debug = True

    def banner(self, test_name):
        print ""
        print "------------------------------------------------"
        print " Testing: %s" % test_name
        print "------------------------------------------------"

    def md5sum(self, filename, blocksize=65536):
        hash = hashlib.md5()
        with open(filename, "rb") as f:
            for block in iter(lambda: f.read(blocksize), b""):
                hash.update(block)
        return hash.hexdigest()

    def md5sum_str(self, str):
        return hashlib.md5(str).hexdigest()

    #
    # fgapiserver
    #

    def test_User(self):
        self.banner("User class")
        user = fgapiserver.User(2, 'test')
        self.assertEqual(2, user.get_id())
        self.assertEqual('test', user.get_name())

    def test_paginate_reposnse(self):
        self.banner("paginate_response(txt,'2','3')")
        response = ['111111111111111111111111111\n',
                    '222222222222222222222222222\n',
                    '333333333333333333333333333\n',
                    '444444444444444444444444444\n',
                    '555555555555555555555555555\n',
                    '666666666666666666666666666\n',
                    '777777777777777777777777777\n',
                    '888888888888888888888888888\n',
                    '999999999999999999999999999\n',
                    '000000000000000000000000000\n',
                    'AAAAAAAAAAAAAAAAAAAAAAAAAAA\n',
                    'BBBBBBBBBBBBBBBBBBBBBBBBBBB\n', ]
        expected_page = ['444444444444444444444444444\n',
                         '555555555555555555555555555\n',
                         '666666666666666666666666666\n', ]
        received_page = fgapiserver.paginate_response(response, '2', '3')
        self.assertEqual(expected_page, received_page)

    def test_checkDbVer(self):
        self.banner("checkDbVer()")
        self.assertEqual('0.0.10', fgapiserver.check_db_ver())

    def test_fgapiserver(self):
        self.banner("get_task_app_id(1)")
        self.assertEqual('1', fgapiserver.get_task_app_id(1))

    def test_get_file_task_id(self):
        self.banner("get_file_task_id('test_file','/tmp')")
        task_id = fgapiserver.get_file_task_id('test_file', '/tmp')
        print task_id
        self.assertEqual(task_id, '1')

    def test_verify_session_token(self):
        self.banner("verify_session_token("
                    "'AAABBBCCCDDDEEEFFFGGGHHHIIIJJJKKK')")
        result = fgapiserver.verify_session_token(
            'AAABBBCCCDDDEEEFFFGGGHHHIIIJJJKKK')
        self.assertEqual(result[0], '1')
        self.assertEqual(result[1], 'test_user')

    #
    # fgapiserverdb
    #
    fgapisrv_db = fgapiserver.get_fgapiserver_db()

    def test_dbobject(self):
        self.banner("Testing fgapiserverdb get DB object")
        assert self.fgapisrv_db is not None

    def test_dbobj_connect(self):
        self.banner("Testing fgapiserverdb connect")
        conn = self.fgapisrv_db.connect()
        assert conn is not None

    def test_dbobj_test(self):
        self.banner("Testing fgapiserverdb test")
        test = self.fgapisrv_db.test()
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        assert state[0] is False

    def test_dbobj_create_session_token(self):
        self.banner("Testing fgapiserverdb create_session_token")
        self.fgapisrv_db.create_session_token('test', 'test', 'logts')
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        assert state[0] is False

    def test_dbobj_verify_session_token(self):
        self.banner("Testing fgapiserverdb verify_session_token")
        result = self.fgapisrv_db.verify_session_token('TESTSESSIONTOKEN')
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        assert state[0] is False
        assert result[0] == '1'
        assert result[1] == 'test_user'

    def test_dbobj_register_token(self):
        self.banner("Testing fgapiserverdb register_token")
        result = self.fgapisrv_db.register_token(1, 'TESTSESSIONTOKEN', 'SUBJ')
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        assert state[0] is False

    def test_dbobj_verify_user_role(self):
        self.banner("Testing fgapiserverdb verify_user_role")
        result = self.fgapisrv_db.verify_user_role(1, 'test_role')
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        assert state[0] is False
        assert result > 0

    def test_dbobj_verify_user_app(self):
        self.banner("Testing fgapiserverdb verify_user_app")
        result = self.fgapisrv_db.verify_user_app(1, 1)
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        assert state[0] is False
        assert result == '1'

    def test_dbobj_same_group(self):
        self.banner("Testing fgapiserverdb same_group")
        result = self.fgapisrv_db.same_group('test_user1', 'test_user2')
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        assert state[0] is False
        assert result == '1'

    def test_dbobj_get_user_info_by_name(self):
        self.banner("Testing fgapiserverdb get_user_info_by_name")
        result = self.fgapisrv_db.get_user_info_by_name('test_user1')
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        assert state[0] is False
        assert result is not None

    def test_dbobj_get_ptv_groups(self):
        self.banner("Testing fgapiserverdb get_ptv_groups")
        result = self.fgapisrv_db.get_ptv_groups(['test_group1',
                                                  'test_group2'])
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        assert state[0] is False
        assert 'test_group1' in result
        assert 'test_group2' in result

    def test_dbobj_register_ptv_subjec(self):
        self.banner("Testing fgapiserverdb register_ptv_subject")
        result = self.fgapisrv_db.register_ptv_subject('test_user',
                                                       ['test_group1',
                                                        'test_group2'])
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        assert state[0] is False
        assert result[0] == 1
        assert result[1] == 'test_user'

    def test_dbobj_register_task_exists(self):
        self.banner("Testing fgapiserverdb task_exists")
        result = self.fgapisrv_db.task_exists(1, 1)
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        assert state[0] is False
        assert result is True

    def test_dbobj_get_task_record(self):
        self.banner("Testing fgapiserverdb get_task_record")
        result = self.fgapisrv_db.get_task_record(1)
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        assert state[0] is False
        assert result is not None
        print result
        assert result['description'] == 'test task'

    def test_dbobj_get_task_status(self):
        self.banner("Testing fgapiserverdb get_task_status")
        result = self.fgapisrv_db.get_task_status(1)
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        assert state[0] is False
        assert result == 'WAITING'

    def test_dbobj_get_task_input_files(self):
        self.banner("Testing fgapiserverdb get_task_input_files")
        result = self.fgapisrv_db.get_task_input_files(1)
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        assert state[0] is False
        assert result is not None
        assert len(result) == 2

    def test_dbobj_get_task_output_files(self):
        self.banner("Testing fgapiserverdb get_task_output_files")
        result = self.fgapisrv_db.get_task_output_files(1)
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        assert state[0] is False
        assert result is not None
        assert len(result) == 2

    def test_dbobj_get_app_detail(self):
        self.banner("Testing fgapiserverdb get_app_detail")
        result = self.fgapisrv_db.get_app_detail(1)
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        assert state[0] is False
        assert result is not None
        assert result['name'] == 'test application'

    def test_dbobj_get_task_app_detail(self):
        self.banner("Testing fgapiserverdb get_task_app_detail")
        result = self.fgapisrv_db.get_task_app_detail(1)
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        assert state[0] is False
        assert result is not None
        assert result['name'] == 'test application'

    def test_dbobj_get_task_info(self):
        self.banner("Testing fgapiserverdb get_task_info")
        result = self.fgapisrv_db.get_task_info(1)
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        assert state[0] is False
        assert result is not None
        assert result['description'] == 'test task'

    def test_dbobj_get_app_files(self):
        self.banner("Testing fgapiserverdb get_app_files")
        result = self.fgapisrv_db.get_app_files(1)
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        assert state[0] is False
        assert result is not None
        assert len(result) == 2

    test_dir = '/tmp/test'

    def create_test_json(self):
        try:
            os.stat(self.test_dir)
        except:
            os.mkdir(self.test_dir)
        f = open('%s/1.json' % self.test_dir, 'w')
        f.write('{}')
        f.close()

    def destroy_test_json(self):
        shutil.rmtree(self.test_dir)

    def test_dbobj_init_task(self):
        self.banner("Testing fgapiserverdb init_task")
        self.create_test_json()
        result = self.fgapisrv_db.init_task(1,
                                            'test_application',
                                            'test_user',
                                            ['arg 1', 'arg 2'],
                                            [{'name': 'test_ifile1',
                                              'path': '/path/to/file1',
                                              'override': False},
                                             {'name': 'test_ifile2',
                                              'path': '/path/to/file2',
                                              'override': True}, ],
                                            [{'name': 'test_ofile_1'},
                                             {'name': 'test_ofile_2'}, ])
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        self.destroy_test_json()
        assert state[0] is False
        assert result == 1

    def test_dbobj_get_task_io_sandbox(self):
        self.banner("Testing fgapiserverdb get_task_io_sandbox")
        result = self.fgapisrv_db.get_task_io_sandbox(1)
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        assert state[0] is False
        assert result == '/tmp/iosandbox'

    def test_dbobj_update_iniput_sandbox_file(self):
        self.banner("Testing fgapiserverdb update_iniput_sandbox_file")
        result = self.fgapisrv_db.update_input_sandbox_file(1,
                                                            'test_file1',
                                                            '/path/to/file')
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        assert state[0] is False

    def test_dbobj_is_input_sandbox_ready(self):
        self.banner("Testing fgapiserverdb is_input_sandbox_ready")
        result = self.fgapisrv_db.is_input_sandbox_ready(1)
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        assert state[0] is False
        assert result is True

    def test_dbobj_submit_task(self):
        self.banner("Testing fgapiserverdb submit_task")
        self.create_test_json()
        result = self.fgapisrv_db.submit_task(1)
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        self.destroy_test_json()
        assert state[0] is False
        assert result is True

    def test_dbobj_enqueue_task_request(self):
        self.banner("Testing fgapiserverdb enqueue_task_request")
        self.create_test_json()
        result = self.fgapisrv_db.enqueue_task_request(
            {'status': 'WAITING',
             'description': 'test task',
             'creation': '1970-01-01T00:00:00',
             'iosandbox': '/tmp/test',
             'user': 'test user',
             'id': '1',
             'output_files': [
                 {'url': 'file?path=%2Ftmp&name=output_file_1',
                  'name': 'output_file_1'},
                 {'url': 'file?path=%2Ftmp&name=output_file_2',
                  'name': 'output_file_2'}],
             'application': {
                 'infrastructures': [
                     {'status': 'enabled',
                      'description':
                          'test infrastructure for test application',
                      'parameters': [
                          {'name': 'test_infra_param_name_1',
                           'value': 'test_infra_param_value_1'},
                          {'name': 'test_infra_param_name_2',
                           'value': 'test_infra_param_value_2'}],
                      'creation': '1970-01-01T00:00:00',
                      'virtual': 'real',
                      'id': '1',
                      'name': 'test infra'}],
                 'description': 'test application description',
                 'parameters': [
                     {'param_name': 'test_pname1',
                      'param_value': 'test_pvalue1'},
                     {'param_name': 'test_pname2',
                      'param_value': 'test_pvalue2'}],
                 'creation': '1970-01-01T00:00:00',
                 'enabled': True,
                 'outcome': 'JOB',
                 'id': '1',
                 'name': 'test application'},
             'arguments': ['argument'],
             'runtime_data': [
                 {'name': 'userdata_name_1',
                  'proto': 'NULL',
                  'last_change': '1970-01-01T00:00:00',
                  'creation': '1970-01-01T00:00:00',
                  'value': 'userdata_value_1',
                  'type': 'NULL',
                  'description': 'userdata_desc_1'},
                 {'name': 'userdata_name_2',
                  'proto': 'NULL',
                  'last_change': '1970-01-01T00:00:00',
                  'creation': '1970-01-01T00:00:00',
                  'value': 'userdata_value_2',
                  'type': 'NULL',
                  'description': 'userdata_desc_2'}],
             'input_files': [{'status': 'NEEDED',
                              'name': 'input_file_1'},
                             {'status': 'READY',
                              'url': ('file?path=%2Ftmp%2Ftest&name='
                                      'input_file_2'),
                              'name': 'input_file_2'}],
             'last_change': '1970-01-01T00:00:00'})
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        self.destroy_test_json()
        assert state[0] is False
        assert result is True

    def test_dbobj_get_task_list(self):
        self.banner("Testing fgapiserverdb get_task_list")
        result = self.fgapisrv_db.get_task_list((1, 'test_user'), 1)
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        assert state[0] is False
        assert result == [1]

    def test_dbobj_delete(self):
        self.banner("Testing fgapiserverdb delete")
        result = self.fgapisrv_db.delete(1)
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        assert state[0] is False
        assert result is True

    def test_dbobj_patch_task(self):
        self.banner("Testing fgapiserverdb patch_task")
        result = self.fgapisrv_db.patch_task(
            1,
            [{'data_name': 'test_data_name1',
              'data_value': 'test_data_value1',
              'data_desc': 'test_data_desc1',
              'data_type': 'test_data_type1',
              'data_proto': 'test_data_proto1'},
             {'data_name': 'test_data_name2',
              'data_value': 'test_data_value2',
              'data_desc': 'test_data_desc2',
              'data_type': 'test_data_type2',
              'data_proto': 'test_data_proto2'}])
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        assert state[0] is False
        assert result is True

    def test_dbobj_is_overridden_sandbox(self):
        self.banner("Testing fgapiserverdb is_overridden_sandbox")
        result = self.fgapisrv_db.is_overridden_sandbox(1)
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        assert state[0] is False
        assert result is True

    def test_dbobj_get_file_task_id(self):
        self.banner("Testing fgapiserverdb get_file_task_id")
        result = self.fgapisrv_db.get_file_task_id('test_file',
                                                   '/tmp/testdir')
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        assert state[0] is False
        assert result == '1'

    def test_dbobj_status_change(self):
        self.banner("Testing fgapiserverdb status_change")
        result = self.fgapisrv_db.status_change(1, 'TEST')
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        assert state[0] is False

    def test_dbobj_app_exists(self):
        self.banner("Testing fgapiserverdb app_exists")
        result = self.fgapisrv_db.app_exists(1)
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        assert state[0] is False
        assert result is True

    def test_dbobj_get_app_list(self):
        self.banner("Testing fgapiserverdb get_app_list")
        result = self.fgapisrv_db.get_app_list()
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        assert state[0] is False
        assert result == [1]

    def test_dbobj_get_app_record(self):
        self.banner("Testing fgapiserverdb get_app_record")
        result = self.fgapisrv_db.get_app_record(1)
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        assert state[0] is False
        assert result['name'] == 'test_app'

    def test_dbobj_init_app(self):
        self.banner("Testing fgapiserverdb init_app")
        result = self.fgapisrv_db.init_app(
                    'test application',
                    'test application description',
                    'JOB',
                    True,
                    [{'name': 'test_param_name1',
                      'value': 'test_param_value1',
                      'description': 'test_param_desc1'},
                     {'name': 'test_param_name1',
                      'value': 'test_param_value1',
                      'description': 'test_param_desc1'}],
                    [],
                    ['test_app_file1', 'test_app_file2'],
                    [1])
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        assert state[0] is False
        assert result == 1

    def test_dbobj_get_infra_record(self):
        self.banner("Testing fgapiserverdb get_infra_record")
        result = self.fgapisrv_db.get_infra_record(1)
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        assert state[0] is False
        assert result['name'] == 'test infra'

    def test_dbobj_insert_or_update_app_file(self):
        self.banner("Testing fgapiserverdb insert_or_update_app_file")
        result = self.fgapisrv_db.insert_or_update_app_file(1,
                                                            'test_app_file',
                                                            'test/file/path')
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        assert state[0] is False
        assert result is True

    def test_dbobj_init_infra(self):
        self.banner("Testing fgapiserverdb init_infra")
        result = self.fgapisrv_db.init_infra(
                    'Test infrastructure',
                    'Test infrastructure description',
                    True,
                    False,
                    {})
        state = self.fgapisrv_db.get_state()
        print "DB state: %s" % (state,)
        assert state[0] is False
        assert result == '1'

    #
    # mklogtoken
    #
    def test_mklogtoken(self):
        self.banner("Testing tokenEncode/tokenDecode/tokenInfo")
        key = "0123456789ABCDEF"
        username = 'test'
        password = 'testpwd'
        token = token_encode(key, username, password)
        tinfo = token_decode(key, token)
        print ("Token with key: '%s'; "
               "encoding: 'username:=%s:"
               "password=%s:"
               "timestamp=<issue_time>' is '%s'"
               % (key, username, password, token))
        print "Decoded token: '%s' -> '%s'" % (token, tinfo)
        username2, password2, timestamp2 = token_info(token)
        print ("Token info: 'username=%s:password=%s:timestamp=%s'"
               % (username2, password2, timestamp2))
        self.assertEqual("%s:%s" % (username, password), "%s:%s" % (username2,
                                                                    password2))

    #
    # REST APIs - Following tests are functional tests
    #
    # MD5 values are taken from the self.md5sum_str(result.data) value
    # then they are hardcoded in the assertEqual statement
    #

    def test_get_root(self):
        self.banner("GET /v1.0/")
        result = self.app.get('/v1.0/')
        print result
        print result.data
        print "MD5: '%s'" % self.md5sum_str(result.data)
        self.assertEqual("44dc039b64f657cab4f76b95ccdb81fc",
                         self.md5sum_str(result.data))

    def test_get_infrastructures(self):
        self.banner("GET /v1.0/infrastructures")
        result = self.app.get('/v1.0/infrastructures')
        print result
        print result.data
        print "MD5: '%s'" % self.md5sum_str(result.data)
        self.assertEqual("0fa855a95a6d94d759c2bd2c73cb023c",
                         self.md5sum_str(result.data))

    def test_get_infrastructures(self):
        self.banner("GET /v1.0/infrastructures/1")
        result = self.app.get('/v1.0/infrastructures/1')
        print result
        print result.data
        print "MD5: '%s'" % self.md5sum_str(result.data)
        self.assertEqual("0f814c236f26fd5fd5feb6449f9f8afc",
                         self.md5sum_str(result.data))

    def test_post_infrastructures(self):
        post_data = {'virtual': False,
                     'name': 'Test infrastructure',
                     'description': 'Testinfrastructure description',
                     'parameters': [],
                     'enabled': True}
        self.banner("POST /v1.0/infrastructures")
        result = self.app.post(
                    '/v1.0/infrastructures',
                    data=json.dumps(post_data),
                    content_type="application/json")
        print result
        print result.data
        print "MD5: '%s'" % self.md5sum_str(result.data)
        self.assertEqual("0ccd202bbf2ccbcded52eab2a64857bf",
                         self.md5sum_str(result.data))

    def test_delete_infrastructure(self):
        self.banner("DELETE /v1.0/infrastructures/1")
        result = self.app.delete(
                    '/v1.0/infrastructures/1')
        print result.data
        print "MD5: '%s'" % self.md5sum_str(result.data)
        self.assertEqual("8ba55904600d405ea07f71e499ca3aa5",
                         self.md5sum_str(result.data))

if __name__ == '__main__':
    print "----------------------------------"
    print "Starting unit tests ..."
    print "----------------------------------"
    unittest.main()
    print "Tests completed"
