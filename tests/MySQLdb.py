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


#
# MySQLdb.py emulates the MySQL module returning configurable outputs
#            accordingly to pre-defined queries (see queries variable)
#

__author__ = "Riccardo Bruno"
__copyright__ = "2015"
__license__ = "Apache"
__version__ = "v0.0.2-30-g37540b8-37540b8-37"
__maintainer__ = "Riccardo Bruno"
__email__ = "riccardo.bruno@ct.infn.it"


# export PYTHONPATH=\
# $PYTHONPATH:/Users/Macbook/Documents/fgAPIServer_codestyle_changes/tests/..
# from fgapiserver import fgapiserver
queries = [
    {'query': 'SELECT VERSION()',
     'result': [['test', ], ]},
    {'query': 'select version from db_patches order by id desc limit 1;',
     'result': [['0.0.10'], ]},
    {'query': ('select '
               ' id\n'
               ',status\n'
               ',date_format(creation, \'%%Y-%%m-%%dT%%TZ\') creation\n'
               ',date_format(last_change, \'%%Y-%%m-%%dT%%TZ\') last_change\n'
               ',app_id\n'
               ',description\n'
               ',status\n'
               ',user\n'
               ',iosandbox\n'
               'from task\n'
               'where id=%s\n'
               '  and status != "PURGED";'),
     'result': [['1',
                 'DONE',
                 '1970-01-01T00:00:00',
                 '1970-01-01T00:00:00',
                 '1',
                 'test task',
                 'WAITING',
                 'test user',
                 '/tmp/test']], },
    {'query': ('select argument\n'
               'from task_arguments\n'
               'where task_id=%s\n'
               'order by arg_id asc;'),
     'result': [['argument'], ]},
    {'query': ('select file\n'
               '      ,if(path is null or length(path)=0,'
               '          \'NEEDED\','
               '          \'READY\') status\n'
               '      ,if(path is NULL,\'\',path)\n'
               'from task_input_file\n'
               'where task_id=%s\n'
               'order by file_id asc;'),
     'result': [['input_file_1', 'NEEDED', ''],
                ['input_file_2', 'READY', '/tmp/test'], ]},
    {'query': ('select file\n'
               '      ,if(path is NULL,\'\',path)\n'
               'from task_output_file\n'
               'where task_id=%s\n'
               'order by file_id asc;'),
     'result': [['output_file_1', '/tmp'], ['output_file_2', '/tmp'], ]},
    {'query': ('select '
               '  data_name\n'
               ' ,data_value\n'
               ' ,data_desc\n'
               ' ,data_type\n'
               ' ,data_proto\n'
               ' ,date_format(creation,'
               '              \'%%Y-%%m-%%dT%%TZ\') creation\n'
               ' ,date_format(last_change,'
               '              \'%%Y-%%m-%%dT%%TZ\') last_change\n'
               'from runtime_data\n'
               'where task_id=%s\n'
               'order by data_id asc;'),
     'result': [['userdata_name_1',
                 'userdata_value_1',
                 'userdata_desc_1',
                 'NULL',
                 'NULL',
                 '1970-01-01T00:00:00',
                 '1970-01-01T00:00:00'],
                ['userdata_name_2',
                 'userdata_value_2',
                 'userdata_desc_2',
                 'NULL',
                 'NULL',
                 '1970-01-01T00:00:00',
                 '1970-01-01T00:00:00'],
                ]},
    {'query': ('select id\n'
               '      ,name\n'
               '      ,description\n'
               '      ,outcome\n'
               '      ,date_format(creation, \'%%Y-%%m-%%dT%%TZ\') creation\n'
               '      ,enabled\n'
               'from application\n'
               'where id=%s;'),
     'result': [['1',
                 'test application',
                 'test application description',
                 'JOB',
                 '1970-01-01T00:00:00',
                 '1'],
                ]},
    {'query': ('insert into infrastructure_parameter (infra_id\n'
               '                                     ,param_id\n'
               '                                     ,pname\n'
               '                                     ,pvalue\n'
               '                                     ,pdesc)\n'
               'select %s\n'
               '      ,if(max(param_id) is NULL,\n'
               '          1,max(param_id)+1) \n'
               '      ,%s\n'
               '      ,%s\n'
               '      ,%s\n'
               'from infrastructure_parameter\n'
               'where infra_id = %s;'),
     'result': [['test_param_1', 'test_param_value_1', 'test_param_desc_1'],
                ['test_param_2', 'test_param_value_2'], None]},
    {'query': ('select id\n'
               '      ,name\n'
               '      ,description\n'
               '      ,date_format(creation, \'%%Y-%%m-%%dT%%TZ\') creation\n'
               '      ,if(enabled,\'enabled\',\'disabled\') status\n'
               '      ,if(vinfra,\'virtual\',\'real\') status\n'
               'from infrastructure\n'
               'where app_id=%s;'),
     'result': [['1',
                 'test infra',
                 'test infrastructure for test application',
                 '1970-01-01T00:00:00',
                 'enabled',
                 'real'], ]},
    {'query': ('select pname, pvalue\n'
               'from infrastructure_parameter\n'
               'where infra_id=%s\n'
               'order by param_id asc;'),
     'result': [['test_infra_param_name_1', 'test_infra_param_value_1'],
                ['test_infra_param_name_2', 'test_infra_param_value_2'], ]},
    {'query': ('select task_id '
               'from task_output_file '
               'where file=%s and path=%s;'),
     'result': ['1']},
    {'query': ('select if((creation+expiry)-now()>0,user_id,NULL) user_id\n'
               '      ,(select name from fg_user where id=user_id) name\n'
               'from fg_token\n'
               'where token=%s;'),
     'result': [['1', 'test_user'], ]},
    {'query': ('select task_id from task_output_file\n'
               'where file=%s and path=%s\n'
               'union all\n'
               'select task_id from task_input_file\n'
               'where file=%s and path=%s;'),
     'result': ['1']},
    {'query': ('select id        \n'
               '      ,name      \n'
               '      ,password  \n'
               '      ,first_name\n'
               '      ,last_name \n'
               '      ,institute \n'
               '      ,mail      \n'
               '      ,creation  \n'
               '      ,modified  \n'
               'from fg_user     \n'
               'where name=%s;'),
     'result': [['1',
                 'futuregateway',
                 'XXXXYYYYZZZZ',
                 'futuregateway',
                 'futuregateway',
                 'futuregateway',
                 'futuregateway@futuregateway',
                 '1970-01-01T00:00:00',
                 '1970-01-01T00:00:00'], ]},
    {'query': ('select distinct id\n'
               'from infrastructure order by 1 asc;'),
     'result': ['1']},
    {'query': ('select app_id,\n'
               '       name,\n'
               '       description,\n'
               '       date_format(creation,\n'
               '                   \'%%Y-%%m-%%dT%%TZ\') creation,\n'
               '       enabled,\n'
               '       vinfra\n'
               'from infrastructure\n'
               'where id=%s\n'
               'order by 1 asc ,2 asc\n'
               'limit 1;'),
     'result': [['0',
                 'test infra',
                 'test infrastructure',
                 '1970-01-01T00:00:00',
                 0,
                 0]]},
    {'query': ('select pname\n'
               '      ,pvalue\n'
               '      ,pdesc\n'
               'from infrastructure_parameter\n'
               'where infra_id=%s\n'
               'order by param_id asc;'),
     'result': [['test_pname1', 'test_pvalue1', 'test_pdesc1'],
                ['test_pname2', 'test_pvalue2', 'test_pdesc2'],
                ['test_pname3', 'test_pvalue3', None], ]},
    {'query': ('select count(*)\n'
               'from infrastructure\n'
               'where id = %s;'),
     'result': ['1']},
    {'query': ('select count(*)>0      \n'
               'from fg_user        u  \n'
               '    ,fg_group       g  \n'
               '    ,fg_user_group ug  \n'
               '    ,fg_group_role gr  \n'
               '    ,fg_role        r  \n'
               'where u.id=%s          \n'
               '  and u.id=ug.user_id  \n'
               '  and g.id=ug.group_id \n'
               '  and g.id=gr.group_id \n'
               '  and r.id=gr.role_id  \n'
               '  and r.name = %s;'),
     'result': ['1']},
    {'query': ('select count(*)>1               \n'
               'from fg_user_group              \n'
               'where user_id = (select id      \n'
               '                 from fg_user   \n'
               '                 where name=%s) \n'
               '   or user_id = (select id      \n'
               '                 from fg_user   \n'
               '                 where name=%s) \n'
               'group by group_id               \n'
               'having count(*) > 1;'),
     'result': ['1']},
    {'query': ('select pname\n'
               '      ,pvalue\n'
               'from application_parameter\n'
               'where app_id=%s\n'
               'order by param_id asc;'),
     'result': [['test_pname1', 'test_pvalue1'],
                ['test_pname2', 'test_pvalue2'], ]},
    {'query': ('insert into infrastructure (id\n'
               '                           ,app_id\n'
               '                           ,name\n'
               '                           ,description\n'
               '                           ,creation\n'
               '                           ,enabled\n'
               '                           ,vinfra\n'
               '                           )\n'
               'select if(max(id) is NULL,1,max(id)+1) \n'
               '      ,0\n'
               '      ,%s\n'
               '      ,%s\n'
               '      ,now()\n'
               '      ,%s\n'
               '      ,%s\n'
               'from infrastructure;'),
     'result': []},
    {'query': ('select max(id) from infrastructure;'),
     'result': ['1']},
    {'query': ('select count(*)\n'
               'from as_queue q\n'
               '    ,task t\n'
               '    ,application a\n'
               '    ,infrastructure i\n'
               'where i.app_id=a.id\n'
               '  and t.app_id=a.id\n'
               '  and q.task_id=t.id\n'
               '  and t.app_id=a.id\n'
               '  and q.status=\'RUNNING\'\n'
               '  and i.id = %s;'),
     'result': ['0']},
    {'query': ('delete from infrastructure_parameter\n'
               'where infra_id=%s;'),
     'result': []},
    {'query': ('delete from infrastructure where id=%s;'),
     'result': []},
    {'query': ('select count(*)\n'
               'from application a\n'
               '    ,infrastructure i\n'
               'where i.app_id=a.id\n'
               '  and i.id = %s;'),
     'result': ['0']},
    {'query': ('select if(count(*)>0,uuid(),NULL) acctoken \n'
               'from fg_user \n'
               'where name=%s and fg_user.password=password(%s);'),
     'result': ['1']},
    {'query': ('insert into fg_token \n'
               '  select %s, id, now() creation, 24*60*60 \n'
               '  from  fg_user \n'
               '  where name=%s \n'
               '    and fg_user.password=password(%s);'),
     'result': []},
    {'query': ('select count(*)>0      \n'
               'from fg_user        u  \n'
               '    ,fg_group       g  \n'
               '    ,application    a  \n'
               '    ,fg_user_group ug  \n'
               '    ,fg_group_apps ga  \n'
               'where u.id=%s          \n'
               '  and u.id=ug.user_id  \n'
               '  and a.id=%s          \n'
               '  and a.id=ga.app_id   \n'
               '  and g.id=ug.group_id \n'
               '  and g.id=ga.group_id;'),
     'result': ['1']},
    {'query': ('select count(*) from fg_group where lower(name)=%s;'),
     'result': ['1']},
    {'query': ('select id, name from fg_user where name=%s;'),
     'result': [[1, 'test_user'], ]},
    {'query': ('insert into fg_user (name, \n'
               '                     password,\n'
               '                     first_name,\n'
               '                     last_name,\n'
               '                     institute,\n'
               '                     mail,\n'
               '                     creation,\n'
               '                     modified)\n'
               'values (%s,\n'
               '        password(\'NOPASSWORD\'),\n'
               '        \'PTV_TOKEN\',\n'
               '        \'PTV_TOKEN\',\n'
               '        \'PTV_TOKEN\',\n'
               '        \'PTV@TOKEN\',\n'
               '        now(),\n'
               '        now());'),
     'result': []},
    {'query': ('select count(*)\n'
               'from task\n'
               'where id = %s\n'
               '  and user = (select name\n'
               '              from fg_user\n'
               '              where id = %s);'),
     'result': ['1']},
    {'query': ('select file\n'
               '      ,if(path is null,\'NEEDED\',\'READY\') status\n'
               'from task_input_file\n'
               'where task_id = %s;'),
     'result': [['test_ifile_1', 'READY'],
                ['test_ifile_2', 'NEEDED'], ]},
    {'query': ('select file\n'
               '      ,if(path is null,\'waiting\',\'ready\')\n'
               'from task_output_file\n'
               'where task_id = %s;'),
     'result': [['test_ofile_1', 'ready'],
                ['test_ofile_2', 'ready'], ]},
    {'query': ('select file\n'
               '      ,path\n'
               '      ,override\n'
               'from application_file\n'
               'where app_id=%s\n'
               'order by file_id asc;'),
     'result': [['test_app_file1', '/path/to/file1', 0],
                ['test_app_file2', '/path/to/file2', 1], ]},
    {'query': ('select max(id) from task;'),
     'result': [[1], ]},
    {'query': ('insert into task_output_file (task_id\n'
               '                             ,file_id\n'
               '                             ,file)\n'
               'select %s\n'
               '      ,if(max(file_id) is NULL,1,max(file_id)+1)\n'
               '      ,%s\n'
               'from task_output_file\n'
               'where task_id=%s'),
     'result': []},
    {'query': ('select '
               '  sum(if(path is NULL,0,1))=count(*) or count(*)=0 sb_ready\n'
               'from task_input_file\n'
               'where task_id=%s;'),
     'result': ['1']},
    {'query': ('select '
               '  if(sum(override) is NULL,'
               '     TRUE,'
               '     count(*)=sum(override)) override\n'
               'from application_file\n'
               'where app_id=%s;'),
     'result': ['1']},
    {'query': ('select iosandbox from task where id=%s;'),
     'result': [['/tmp/iosandbox'], ]},
    {'query': ('update task_input_file\n'
               'set path=%s\n'
               'where task_id=%s\n'
               '  and file=%s;'),
     'result': []},
    {'query': ('select id\n'
               'from task\n'
               'where status != "PURGED"\n'
               '  and user = %s\n'
               '  and app_id = %s\n'
               ';'),
     'result': [[1], ]},
    {'query': ('insert into as_queue (\n'
               '   task_id\n'
               '  ,target_id\n'
               '  ,target\n'
               '  ,action\n'
               '  ,status\n'
               '  ,target_status\n'
               '  ,creation\n'
               '  ,last_change\n'
               '  ,check_ts\n'
               '  ,action_info\n'
               ') values (%s,\n'
               '          NULL,\n'
               '         \'GridEngine\',\n'
               '         \'CLEAN\',\n'
               '         \'QUEUED\',\n'
               '          NULL,\n'
               '          now(),\n'
               '          now(),\n'
               '          now(),\n'
               '          %s);'),
     'result': []},
    {'query': ('update task set status=\'CANCELLED\', '
               'last_change=now() where id=%s;'),
     'result': []},
    {'query': ('insert into as_queue (\n'
               '   task_id       \n'
               '  ,target_id     \n'
               '  ,target        \n'
               '  ,action        \n'
               '  ,status        \n'
               '  ,target_status \n'
               '  ,creation      \n'
               '  ,last_change   \n'
               '  ,check_ts      \n'
               '  ,action_info   \n'
               ') values (%s,\n'
               '          NULL,\n'
               '          %s,\n'
               '          \'SUBMIT\',\n'
               '          \'QUEUED\',\n'
               '          NULL,\n'
               '          now(),\n'
               '          now(),\n'
               '          now(),\n'
               '          %s);'),
     'result': []},
    {'query': ('insert into task (id\n'
               '                 ,creation\n'
               '                 ,last_change\n'
               '                 ,app_id\n'
               '                 ,description\n'
               '                 ,status\n'
               '                 ,user\n'
               '                 ,iosandbox)\n'
               'select if(max(id) is NULL,1,max(id)+1) -- new id\n'
               '      ,now()                           -- creation date\n'
               '      ,now()                           -- last change\n'
               '      ,%s                              -- app_id\n'
               '      ,%s                              -- description\n'
               '      ,\'WAITING\'                     -- status WAITING\n'
               '      ,%s                              -- user\n'
               '      ,%s                              -- iosandbox\n'
               'from task;\n'),
     'result': []},
    {'query': ('insert into task_arguments (task_id\n'
               '                           ,arg_id\n'
               '                           ,argument)\n'
               'select %s\n'
               '      ,if(max(arg_id) is NULL,1,max(arg_id)+1)\n'
               '      ,%s\n'
               'from task_arguments\n'
               'where task_id=%s'),
     'result': []},
    {'query': ('update task set status=\'SUBMIT\', \n'
               'last_change=now() where id=%s;'),
     'result': []},
    {'query': ('insert into \n'
               'fg_token (token, subject, user_id, creation, expiry)\n'
               'select %s, %s, %s, now(), NULL\n'
               'from dual\n'
               'where (select count(*)\n'
               '       from fg_token\n'
               '       where token=%s) = 0;'),
     'result': []},
    {'query': ('select count(*)\n'
               'from runtime_data\n'
               'where data_name=%s\n'
               '  and task_id=%s;'),
     'result': ['1']},
    {'query': ('update runtime_data\n'
               'set data_value = %s\n'
               '   ,last_change = now()\n'
               'where data_name=%s\n'
               '  and task_id=%s;'),
     'result': []},
    {'query': ('insert into as_queue (task_id,'
               '                      action,'
               '                      status,'
               '                      target,'
               '                      target_status,'
               '                      creation,'
               '                      last_change,'
               '                      check_ts)'
               'values (%s,'
               '        "STATUSCH",'
               '        "QUEUED",'
               '        (select target '
               '         from as_queue '
               '         where task_id=%s '
               '         and action="SUBMIT"),'
               '         %s,'
               '         now(),'
               '         now(),'
               '         now());'),
     'result': []},
    {'query': ('select count(*)\n'
               'from application\n'
               'where id = %s;'),
     'result': ['1']},
    {'query': ('select id\n'
               'from application\n'
               'order by id asc;'),
     'result': [[1], ]},
    {'query': ('select name\n'
               '      ,description\n'
               '      ,outcome\n'
               '      ,date_format(creation, \'%%Y-%%m-%%dT%%TZ\') creation\n'
               '      ,enabled\n'
               'from application\n'
               'where id=%s;'),
     'result': [['test_app',
                 'test_app_desc',
                 'JOB',
                 '1970-01-01T00:00:00',
                 1], ]},
    {'query': ('select pname\n'
               '      ,pvalue\n'
               '      ,pdesc\n'
               'from application_parameter\n'
               'where app_id=%s\n'
               'order by param_id asc;'),
     'result': [['test_param_name1',
                 'test_param_value1',
                 'test_param_desc1'],
                ['test_param_name2',
                 'test_param_value2',
                 'test_param_desc2'], ]},
    {'query': ('select id\n'
               'from infrastructure\n'
               'where app_id = %s order by id asc;'),
     'result': ['1']},
    {'query': None,
     'result': None},
]


class cursor:

    position = 0
    cursor_results = None

    def __getitem__(self, i):
        return self.cursor_results[i]

    def __len__(self):
        return len(self.cursor_results)

    def execute(self, sql, sql_data=None):
        print "Executing: '%s'" % sql
        self.position = 0
        self.cursor_results = None
        for query in queries:
            if query['query'] == sql:
                self.cursor_results = query['result']
                print "Test query found!"
                print "result: '%s'" % self.cursor_results
        if self.cursor_results is None:
            print "Test query not found!"

    def fetchone(self):
        if self.cursor_results is None:
            return ''
        else:
            res = self.cursor_results[self.position]
            self.position += 1
            print "fetchone: %s" % res
            return res

    def close(self):
        print "cursor close"
        return None


class MySQLError(Exception):
    pass


class Error:
    pass


def connect(*args, **kwargs):
    db = MySQLdb()
    return db


class MySQLdb:

    Error = None

    def __init__(self, *args, **kwargs):
        Error = MySQLError()

    def cursor(self):
        cr = cursor()
        return cr

    def close(self):
        print "MySQLdb.close"
        return None

    def commit(self):
        print "MySQLdb.commit"
        return None
