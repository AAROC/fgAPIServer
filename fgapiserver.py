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
from flask import jsonify
from flask_login import LoginManager, UserMixin, login_required, current_user
from Crypto.Cipher import ARC4
from OpenSSL import SSL
from werkzeug import secure_filename
from fgapiserverdb import FGAPIServerDB
from fgapiserverconfig import FGApiServerConfig
from fgapiserverptv import FGAPIServerPTV
from fgapiserver_user import User
import os
import sys
import uuid
import time
import json
import ConfigParser
import base64
import logging
import logging.config

"""
  FutureGateway APIServer front-end
"""

__author__ = "Riccardo Bruno"
__copyright__ = "2015"
__license__ = "Apache"
__version__ = "v0.0.7-1"
__maintainer__ = "Riccardo Bruno"
__email__ = "riccardo.bruno@ct.infn.it"
__status__ = "release"
__update__ = "23-05-2017 17:23:15"

# setup path
fgapirundir = os.path.dirname(os.path.abspath(__file__)) + '/'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# fgapiserver configuration file
fgapiserver_config_file = fgapirundir + 'fgapiserver.conf'

# Load configuration
fg_config_obj = FGApiServerConfig(fgapiserver_config_file)
fg_config = fg_config_obj.get_config()

# fgapiserver settings
fgapiver = fg_config['fgapiver']
fgapiserver_name = fg_config['fgapiserver_name']
fgapisrv_host = fg_config['fgapisrv_host']
fgapisrv_port = int(fg_config['fgapisrv_port'])
fgapisrv_debug = fg_config['fgapisrv_debug'].lower() == 'true'
fgapisrv_iosandbox = fg_config['fgapisrv_iosandbox']
fgapisrv_geappid = int(fg_config['fgapisrv_geappid'])
fgjson_indent = int(fg_config['fgjson_indent'])
fgapisrv_key = fg_config['fgapisrv_key']
fgapisrv_crt = fg_config['fgapisrv_crt']
fgapisrv_logcfg = fg_config['fgapisrv_logcfg']
fgapisrv_dbver = fg_config['fgapisrv_dbver']
fgapisrv_secret = fg_config['fgapisrv_secret']
fgapisrv_notoken = fg_config['fgapisrv_notoken'].lower() == 'true'
fgapisrv_notokenusr = fg_config['fgapisrv_notokenusr']
fgapisrv_lnkptvflag = fg_config['fgapisrv_lnkptvflag']
fgapisrv_ptvendpoint = fg_config['fgapisrv_ptvendpoint']
fgapisrv_ptvuser = fg_config['fgapisrv_ptvuser']
fgapisrv_ptvpass = fg_config['fgapisrv_ptvpass']
fgapisrv_ptvdefusr = fg_config['fgapisrv_ptvdefusr']
fgapisrv_ptvdefgrp = fg_config['fgapisrv_ptvdefgrp']
fgapisrv_ptvmapfile = fg_config['fgapisrv_ptvmapfile']

# fgapiserver database settings
fgapisrv_db_host = fg_config['fgapisrv_db_host']
fgapisrv_db_port = int(fg_config['fgapisrv_db_port'])
fgapisrv_db_user = fg_config['fgapisrv_db_user']
fgapisrv_db_pass = fg_config['fgapisrv_db_pass']
fgapisrv_db_name = fg_config['fgapisrv_db_name']

# Logging
logging.config.fileConfig(fgapisrv_logcfg)
logger = logging.getLogger(__name__)
logger.debug("fgAPIServer is starting ...")
logger.debug(fg_config_obj.get_messages())

# setup Flask app
app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)

# FutureGateway database object holder
fgapisrv_db = None


#
# Helper functions
#


def get_fgapiserver_db():
    """
    Retrieve the fgAPIServer database object

    :return: Return the fgAPIServer database object or None if the
             database connection fails
    """
    fgapisrv_db = FGAPIServerDB(
        db_host=fgapisrv_db_host,
        db_port=fgapisrv_db_port,
        db_user=fgapisrv_db_user,
        db_pass=fgapisrv_db_pass,
        db_name=fgapisrv_db_name,
        iosandbbox_dir=fgapisrv_iosandbox,
        fgapiserverappid=fgapisrv_geappid)
    db_state = fgapisrv_db.get_state()
    if db_state[0] != 0:
        logger.error("Unbable to connect to the database:\n"
                     "  host: %s\n"
                     "  port: %s\n"
                     "  user: %s\n"
                     "  pass: %s\n"
                     "  name: %s\n"
                     % (fgapisrv_db_host,
                        fgapisrv_db_port,
                        fgapisrv_db_user,
                        fgapisrv_db_pass,
                        fgapisrv_db_name))
        return None
    return fgapisrv_db


def check_db_ver():
    """
    Database versioning check

    :return: This function will check the database connectivity, set the
             fgapisrv_db global variable and terminate with error if the
             database schema version is not aligned with the version
             required by the code; see fgapisrv_dbver in configuration file
    """
    global fgapisrv_db
    fgapisrv_db = get_fgapiserver_db()
    if fgapisrv_db is None:
        msg = "Unable to connect to the database!"
        logger.error(msg)
        print msg
        sys.exit(1)
    else:
        # getDBVersion
        db_ver = fgapisrv_db.get_db_version()
        if fgapisrv_dbver is None or\
           fgapisrv_dbver == '' or\
           fgapisrv_dbver != db_ver:
            msg = ("Current database version '%s' is not compatible "
                   "with this version of the API server front-end; "
                   "version %s is required."
                   "It is suggested to update your database applying "
                   "new available patches" % (db_ver, fgapisrv_dbver))
            logger.error(msg)
            print msg
            sys.exit(1)
    logger.debug("Check database version passed")
    return db_ver


def paginate_response(response, page, per_page, page_url):
    """
    Paginate the incoming response json vector, accordinlgly to page and
    per_page values
    :param response: The whole response text
    :param page: The selected page number
    :param per_page: How many response record per page
    :param page_url: The url to get this page
    :return: The number of specified response records of the selected page
    """
    links = []
    if page is not None and per_page is not None:
        pg = int(page)
        if pg > 0:
            pg -= 1
        ppg = int(per_page)
        if pg > len(response)/ppg:
            pg = len(response)/ppg
        max_pages = len(response)/ppg + (1 * len(response) % ppg)
        record_from = pg * ppg
        record_to = record_from + ppg
        paginated_response = response[record_from:record_to]
        for link_page in range(0, max_pages):
            if link_page == pg:
                rel = "self"
            elif link_page < pg:
                rel = "prev"
            else:
                rel = "next"
            if "?" in page_url:
                filter_char = "&"
            else:
                filter_char = "?"
            href = "%s%spage=%s&per_page=%s" % (page_url,
                                                filter_char,
                                                link_page+1,
                                                ppg)
            links += [{"rel": rel,
                       "href": href}, ]
    else:
        paginated_response = response
        links += [{"rel": "self",
                   "href": page_url}, ]
    return paginated_response, links


def get_task_app_id(task_id):
    """
    Return the application id associated to the given task_id
    :param task_id: Task id
    :return: The associated application id associated to the given task id
    """
    global fgapisrv_db
    task_info = fgapisrv_db.get_task_info(task_id)
    app_record = task_info.get('application', None)
    if app_record is not None:
        logger.debug("Found app_id: '%s' for task_id: '%s'"
                     % (app_record['id'], task_id))
        return app_record['id']
    logger.warn("Could not find app_id for task_id: '%s'" % task_id)
    return None


def process_log_token(logtoken):
    """
    processLogToken retrieve username and password from a given login token

    (!)Override this method to manage more complex and secure algorithms;
       tester code uses the following encrypted string to store user
       credentials:
       username=<username>:password=<password>:timestamp=<timestamp>

    To create such log tokens, please use the following python snippet:

    from Crypto.Cipher import ARC4
    import time
    import base64
    secret = "0123456789ABCDEF" # (!) Please use fgapiserver_secret value
    username = "<username>"
    password = "<password>"
    # Encode
    obj=ARC4.new(secret)
    b64em = base64.b64encode(obj.encrypt("username=%s:password=%s:timestamp=%s"
                             % (username,password,int(time.time()))))
    print b64em
    # Decode
    obj=ARC4.new(secret)
    creds = obj.decrypt(base64.b64decode(b64em))
    print creds

    :param logtoken: The encripted string containing the:
                 username=<username>:password=<password>:timestamp=<timestamp>
                 The key is encripted using a key, see fgapisrv_secret value
                 in configuration file
                 Username and Passord credentials are stored inside in the
                 APIServer users table
    :return: Unencripted triple: (username, password, timestamp)
    """
    username = ""
    password = ""
    timestamp = 0
    obj = ARC4.new(fgapisrv_secret)
    creds = obj.decrypt(base64.b64decode(logtoken))
    credfields = creds.split(":")
    if len(credfields) > 0:
        username = credfields[0].split("=")[1]
        password = credfields[1].split("=")[1]
        timestamp = credfields[2].split("=")[1]
    logger.debug("Logtoken: '%s'\n"
                 "    User: '%s'\n"
                 "    Password: '%s'\n"
                 "    Timestamp: '%s'" % (logtoken,
                                          username,
                                          password,
                                          timestamp))
    return username, password, timestamp


def create_session_token(**kwargs):
    """
    This function accepts login tokens or directly username/password
    credentials returning an access token
    :param kwargs: logtoken - A token containing encrypted credentials
                  plus a timestamp
                  username,password - Credentials of APIServer users
    :return: An access token to be used by any further transaction with
             the APIServer front-end
    """
    global fgapisrv_db
    timestamp = int(time.time())
    sestoken = ""
    logtoken = kwargs.get("logtoken", "")
    username = kwargs.get("username", "")
    password = kwargs.get("password", "")
    if len(logtoken) > 0:
        # Calculate credentials starting from a logtoken
        username, password, timestamp = process_log_token(logtoken)
    if len(username) > 0 and len(password) > 0:
        # Create a new access token starting from given username and password
        # (DBRequired)
        sestoken = fgapisrv_db.create_session_token(username,
                                                    password,
                                                    timestamp)
    logger.debug("Session token is:\n"
                 "logtoken: '%s'\n"
                 "username: '%s'\n"
                 "password: '%s'\n"
                 "timestamp: '%s'\n" % (sestoken,
                                        logtoken,
                                        username,
                                        password))
    return sestoken


def authorize_user(current_user, app_id, user, reqroles):
    """
    This function returns true if the given user is authorized to process the
    requested action
    The request will be checked against user group roles stored in the database

    :param current_user: The user requesting the action
    :param app_id: The application id (if appliable)
    :param user: The user specified by the filter
    :param reqroles: The requested roles: task_view, app_run, ...
    :return:
    """
    logger.debug("AuthUser: (begin)")
    global fgapisrv_db

    # Return True if token management is disabled
    # if fgapisrv_notoken:
    #     return True, 'Authorization disabled'

    message = ''
    user_id = current_user.get_id()
    user_name = current_user.get_name()
    logger.debug(("AuthUser: user_id: '%s' - "
                  "user_name: '%s'" % (user_id, user_name)))

    # Check if requested action is in the user group roles
    auth_z = fgapisrv_db.verify_user_role(user_id, reqroles)
    logger.debug(("AuthUser: Auth for user '%s' "
                  "with roles '%s' is %s")
                 % (user_id, reqroles, auth_z))
    if not auth_z:
        message = ("User '%s' does not have requested '%s' role(s)\n"
                   % (user_name, reqroles))
    # Check current_user and filter user are different
    if user_name != user:
        logger.debug("AuthUser: User name '%s' differs from user '%s'"
                     % (user_name, user))
        user_impersonate = fgapisrv_db.verify_user_role(
            user_id, 'user_impersonate')
        if user != "@":
            group_impersonate = fgapisrv_db.same_group(
                user_name, user) and fgapisrv_db.verify_user_role(
                user_id, 'group_impersonate')
        else:
            group_impersonate = fgapisrv_db.verify_user_role(
                user_id, 'group_impersonate')
        auth_z = auth_z and (user_impersonate or group_impersonate)
        if not auth_z:
            if user == "*":
                user_text = "any user"
            elif user == "@":
                user_text = "group-wide users"
            else:
                user_text = "'%s' user" % user
            message = "User '%s' cannot impersonate %s\n" % (
                user_name, user_text)
    # Check if app belongs to Group apps
    if (app_id is not None):
        logger.debug("AuthUser: checking for app_id '%s'" % app_id)
        auth_z = auth_z and fgapisrv_db.verify_user_app(user_id, app_id)
        if not auth_z:
            message = ("User '%s' cannot perform any activity on application "
                       "having id: '%s'\n") % (user_name, app_id)

    return auth_z, message

##
# flask-login
##

# Retrieve the session token from Header Authorization field or from token in
# the argument list
# This function verifies the session token and return the user object if the
# check is successful
# The User object holds database user id and the associated user name


@login_manager.request_loader
def load_user(request):
    global fgapisrv_db
    logger.debug("LoadUser: begin")
    # Login manager could be disabled in conf file
    if fgapisrv_notoken:
        logger.debug("LoadUser: notoken is true")
        user_info = fgapisrv_db.get_user_info_by_name(fgapisrv_notokenusr)
        user_id = user_info["id"]
        user_name = user_info["name"]
        logger.debug(("LoadUser: Session token disabled; "
                      "behaving has user: '%s' (%s)"
                      % (user_name, user_id)))
        return User(int(user_info["id"]), user_info["name"])

    logger.debug("LoadUser: using token")
    token = request.headers.get('Authorization')
    if token is None:
        token = request.args.get('token')
    logger.debug("LoadUser: token is '%s'" % token)

    if token is not None:
        # Check for Portal Token verification  (PTV) method
        if fgapisrv_lnkptvflag:
            logger.debug("LoadUser: (PTV)")
            token_fields = token.split()
            if token_fields[0] == "Bearer":
                try:
                    token = token_fields[1]
                except IndexError:
                    logger.debug("Passed empty Bearer token")
                    return None
            elif token_fields[0] == "Task":
                # Taks token management
                # Not available
                try:
                    token = token_fields[1]
                except IndexError:
                    logger.debug("Passed empty Task token")
                    return None
                logger.debug("Task token not yet implemented")
                return None
            else:
                token = token_fields[0]
            logger.debug("LoadUser: token field is '%s'" % token)
            ptv = FGAPIServerPTV(endpoint=fgapisrv_ptvendpoint,
                                 tv_user=fgapisrv_ptvuser,
                                 tv_password=fgapisrv_ptvpass)
            result = ptv.validate_token(token)
            logger.debug("LoadUser: validate_token: '%s'" % result)
            # result: valid/invalid and optionally portal username and/or
            # its group from result map the corresponding APIServer username
            # fgapisrv_ptvdefusr
            if result['portal_validate']:
                portal_user = result.get('portal_user', '')
                portal_group = result.get('portal_group', '')
                portal_groups = result.get('portal_groups', [])
                portal_subject = result.get('portal_subject', '')
                logger.debug(("LoadUser: portal_user: %s\n"
                              "portal_group: %s\n"
                              "portal_groups: %s\n"
                              "portal_subject: %s") % (portal_user,
                                                       portal_group,
                                                       portal_groups,
                                                       portal_subject))
                # Before to map users; verify that returned PTV record points
                # to an unregistered subject id (i.e. LiferayIAM).
                # When name is empty and subject value is provided, the name
                # field will be populated with the subject value and the name
                # will be registered if not present in the DB. this allows
                # not registered users to access the APIs in an isolated way
                # The Group/s field will be used to register the subject user
                # in the proper group(s) providing the correct rights
                ptv_subj = None
                ptv_groups = None
                if portal_user == '' and portal_subject is not None:
                    portal_user = portal_subject
                    # Prepare a groups vector containing group(s) associated
                    # to the PTV user. Returned PTV groups should exist in the
                    # fgAPIServer database; otherwise a default group will be
                    # associated
                    if portal_group != '':
                        portal_groups.append(portal_group)
                    fg_groups = fgapisrv_db.get_ptv_groups(portal_groups)
                    if fg_groups == []:
                        # Assign a default FG group
                        fg_groups = [fgapisrv_ptvdefgrp]
                    fg_user = fgapisrv_db.register_ptv_subject(portal_user,
                                                               fg_groups)
                    if fg_user != ():
                        fgapisrv_db.register_token(fg_user[0],
                                                   token,
                                                   portal_subject)
                        logger.debug("LoadUser: '%s' - '%s'"
                                     % (fg_user[0], fg_user[1]))
                        logger.debug("LoadUser: (end)")
                        return User(fg_user[0], fg_user[1])
                # Map the portal user with one of defined APIServer users
                # accordingly to the rules defined in fgapiserver_ptvmap.json
                # file. The json contains the list of possible APIServer
                # users with an associated list of possible portal users and
                # groups names that verify the mapping; below an example:
                #
                # fgapiserver_ptvmap.json: {
                #   "futuregateway":
                #        [ "group_a", ... "group_b", "user_a", "user_b", ... ]
                #   "test":
                #       [ "groupc", ... "group d", "user_c", ... "user d" .. ]
                #   "<APIServer user>":
                #      [ "<associated portal group>",
                #        "<associated portal_user>", ... ]
                # }
                #
                # If the PTV returns "user_a", "futuregateway" user will be
                # mapped, while if no mapping is available or portal_user and
                # groups are  not available a default user will be used,
                # see fgapisrv_ptvdefusr in configuration file
                logger.debug("LoadUser: Mapping user")
                mapped_userid = 0
                mapped_username = ''
                with open(fgapisrv_ptvmapfile) as ptvmap_file:
                    ptvmap = json.load(ptvmap_file)
                # portal_user or group must be not null
                if portal_user != ''\
                   or portal_group != ''\
                   or portal_groups != []:
                    # Scan all futuregateway users in json file
                    for user in ptvmap:
                        logger.debug(("LoadUser: Trying mapping "
                                      "for FG user: '%s'" % user))
                        # Scan the list of users and groups associated to FG
                        # users specified in the json file
                        for ptv_usrgrp in ptvmap[user]:
                            # The portal_user maps a user in the list
                            logger.debug(("LoadUser: Verifying "
                                          "portal_user='%s' "
                                          "matches user '%s'") %
                                         (portal_user, ptv_usrgrp))
                            if ptv_usrgrp == portal_user:
                                logger.debug("LoadUser: mapped user %s <- %s"
                                             % (user, portal_user))
                                mapped_username = user
                                break
                            # The portal_group maps a group in the list
                            logger.debug(("LoadUser: Verifying "
                                          "portal_group='%s' "
                                          "matches group '%s'") %
                                         (ptv_usrgrp, portal_group))
                            if ptv_usrgrp == portal_group:
                                logger.debug("LoadUser: mapped group %s <- %s"
                                             % (user, portal_group))
                                mapped_username = user
                                break
                            # The portal_groups maps a group in the list
                            logger.debug(("LoadUser: Verifying if "
                                          "portal_groups='%s' "
                                          "matches group '%s'") %
                                         (portal_groups, ptv_usrgrp))
                            group_found = ''
                            for group in portal_groups:
                                logger.debug("LoadUser: group '%s' ? '%s'" %
                                             (group, ptv_usrgrp))
                                if group == ptv_usrgrp:
                                    group_found = group
                                    break
                                else:
                                    print "  nomatch"
                            if group_found != '':
                                logger.debug("LoadUser: mapped group %s <- %s"
                                             % (user, group_found))
                                mapped_username = user
                                break
                        if mapped_username != '':
                            user_info = fgapisrv_db.get_user_info_by_name(
                                mapped_username)
                            mapped_userid = user_info["id"]
                            mapped_username = user_info["name"]
                            break
                        logger.debug(("LoadUser: PTV mapped user - "
                                      "user_rec(0): '%s',user_rec(1): '%s'")
                                     % (mapped_userid, mapped_username))
                        fgapisrv_db.register_token(mapped_userid,
                                                   token,
                                                   portal_subject)
                        logger.debug("LoadUser: '%s' - '%s'" %
                                     (mapped_userid, mapped_username))
                        logger.debug("LoadUser: (end)")
                        return User(mapped_userid, mapped_username)
                # No portal user and group are returned or no mapping
                # is available returning default user
                user_info = fgapisrv_db.\
                    get_user_info_by_name(fgapisrv_ptvdefusr)
                default_userid = user_info["id"]
                default_username = user_info["name"]
                logger.debug(("LoadUser: No map on portal user/group "
                              "not availabe, using default user"))
                logger.debug(("LoadUser: PTV mapped user - "
                              "user_id: '%s',user_name: '%s'"
                              % (default_userid, default_username)))
                fgapisrv_db.register_token(default_userid,
                                           token,
                                           portal_subject)
                logger.debug("LoadUser: '%s' - '%s'" %
                             (default_userid, default_username))
                logger.debug("LoadUser: (end)")
                return User(default_userid, default_username)
            else:
                logger.debug("LoadUser: PTV token '%s' is not valid" % token)
                return None
        else:
            logger.debug(("LoadUser: Verifying token with "
                          "baseline token management"))
            user_rec = fgapisrv_db.verify_session_token(token)
            logger.debug("LoadUser: user_id: '%s',user_name: '%s'"
                         % (user_rec[0], user_rec[1]))
            if user_rec is not None and user_rec[0] is not None:
                fgapisrv_db.register_token(user_rec[0], token, None)
                logger.debug("LoadUser: '%s' - '%s'"
                             % (user_rec[0], user_rec[1]))
                logger.debug("LoadUser: (end)")
                return User(user_rec[0], user_rec[1])
            else:
                logger.debug(("LoadUser: No user is associated to "
                              "session token: '%s'" % token))
                logger.debug("LoadUser: (end)")
                return None
    else:
        logger.debug("LoadUser: Unable to find session token from request")
        logger.debug("LoadUser: (end)")
    return None


#
# header_links; take care of _links fields
#               and Location
#
def header_links(req, resp, json):
    if '_links' in json:
        for link in json['_links']:
            resp.headers.add('Link', ('%s; '
                                      'rel="%s", <%s>; '
                                      % (req.url,
                                         link['rel'],
                                         link['href'])))
        resp.headers.add('Location', req.url)

##
# Auth handlers
##


#
# /auth; used to provide a logtoken or username/password credentials and
# receive back an access token
#
@app.route('/auth', methods=['GET', 'POST'])
@app.route('/%s/auth' % fgapiver, methods=['GET', 'POST'])
def auth():
    global logger
    logger.debug('auth(%s): %s' % (request.method, request.values.to_dict()))
    token = ""
    message = ""
    logtoken = request.values.get('token')
    username = request.values.get('username')
    password = request.values.get('password')
    if request.method == 'GET':
        if logtoken is not None or len(token) > 0:
            # Retrieve access token from an login token
            token = create_session_token(logtoken=logtoken)
        elif username is not None and len(username) > 0 \
                and password is not None and len(password) > 0:
            # Retrieve token from given username and password
            token = create_session_token(username=username, password=password)
        else:
            message = "No credentials found!"
        logger.debug('session token: %s' % token)
    elif request.method == 'POST':
        auth = request.headers.get('Authorization')
        auth_bearer = auth.split(" ")  # Authorization: Bearer <Token>
        # Authorization: <Username>/Base64(Password)
        auth_creds0 = auth.split("/")
        # Authorization: <Username>:Base64(Password)
        auth_creds1 = auth.split(":")
        if len(auth_bearer) > 1 and auth_bearer[0] == "Bearer":
            # Retrieve access token from an login token
            token = create_session_token(logtoken=auth_bearer[1])
        elif len(auth_creds0) > 1 \
                and len(auth_creds0[0]) > 0 \
                and len(auth_creds0[1]) > 0:
            # Retrieve token from given username and password
            token = create_session_token(
                username=auth_creds0[0],
                password=base64.b64decode(
                    auth_creds0[1]))
        elif len(auth_creds1) > 1 \
                and len(auth_creds0[1]) > 0 \
                and len(auth_creds1[1]) > 0:
            # Retrieve token from given username and password
            token = create_session_token(
                username=auth_creds1[0],
                password=base64.b64decode(
                    auth_creds1[1]))
        else:
            # No credentials found
            message = "No credentials found!"
        logger.debug('session token: %s' % token)
    else:
        message = "Unhandled method: '%s'" % request.method
        logger.debug(message)
    if len(token) > 0:
        response = {
            "token": token
        }
        log_status = 200
    else:
        response = {
            "message": message
        }
        log_status = 404
    # include _links part
    response["_links"] = [{"rel": "self", "href": "/auth"}, ]
    js = json.dumps(response, indent=fgjson_indent)
    resp = Response(js, status=log_status, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    header_links(request, resp, response)
    return resp

##
# Routes as specified for APIServer at http://docs.csgfapis.apiary.io
##

#
# / path; used retrieve informative or service healty information
#


@app.route('/')
@app.route('/%s/' % fgapiver)
def index():
    global logger
    logger.debug('index(%s): %s' % (request.method, request.values.to_dict()))
    versions = ({"id": fgapiver,
                 "_links": ({"rel": "self",
                            "href": fgapiver},),
                 "media-types": ({"type": "application/json"}),
                 "status": __status__,
                 "updated": __update__,
                 "build:": __version__},)
    response = {
        "versions": versions,
        "_links": ({"rel": "self",
                    "href": "/"},)
    }
    js = json.dumps(response, indent=fgjson_indent)
    resp = Response(js, status=200, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    header_links(request, resp, response)
    return resp

##
# Task handlers
##

# tasks - used to view o create a new task
#
# GET  - View task info
# POST - Create a new task; it only prepares the task for execution


@app.route('/%s/tasks' % fgapiver, methods=['GET', 'POST'])
@login_required
def tasks():
    global fgapisrv_db
    global logger
    logger.debug('tasks(%s): %s' % (request.method, request.values.to_dict()))
    user_name = current_user.get_name()
    user_id = current_user.get_id()
    logger.debug("user_name: '%s'" % user_name)
    logger.debug("user_id: '%s'" % user_id)
    page = request.values.get('page')
    per_page = request.values.get('per_page')
    status = request.values.get('status')
    user = request.values.get('user', user_name)
    app_id = request.values.get('application')
    task_state = 0

    if request.method == 'GET':
        auth_state, auth_msg = authorize_user(
            current_user, app_id, user, "task_view")
        logger.debug("[task_view]: auth_state: '%s', auth_msg: '%s'"
                     % (auth_state, auth_msg))
        if not auth_state:
            state = 402
            response = {
                "message": "Not authorized to perform this request:\n%s" %
                           auth_msg}
        else:
            # Show the whole task list
            # Before call user list check if * means ALL users or group
            # restricted users (@)
            user_impersonate = fgapisrv_db.verify_user_role(
                user_id, 'user_impersonate')
            logger.debug("user_impersonate: '%s'" % user_impersonate)
            group_impersonate = fgapisrv_db.same_group(
                user_name, user) and fgapisrv_db.verify_user_role(
                user_id, 'group_impersonate')
            logger.debug("group_impersonate: '%s'" % group_impersonate)
            if user == "*" \
                    and user_impersonate is False \
                    and group_impersonate is True:
                user = "@"  # Restrict tasks only to group members
            # Add the usernname info in case of * or @ filters
            if user == "*" or user == "@":
                user = user + user_name
            # call to get tasks list
            task_list = fgapisrv_db.get_task_list(user, app_id)
            logger.debug("task_list: '%s'" % task_list)
            # Prepare response
            task_array = []
            for task_id in task_list:
                task_record = fgapisrv_db.get_task_record(task_id)
                db_state = fgapisrv_db.get_state()
                if db_state[0] != 0:
                    # DBError getting TaskRecord
                    # Prepare for 403
                    state = 403
                    response = {
                        "message": db_state[1]
                    }
                else:
                    state = 200
                    task_array += [{
                        "id": task_record['id'],
                        "application": task_record['application'],
                        "description": task_record['description'],
                        "arguments": task_record['arguments'],
                        "input_files": task_record['input_files'],
                        "output_files": task_record['output_files'],
                        "status": task_record['status'],
                        "user": task_record['user'],
                        "date": str(task_record['creation']),
                        "last_change": str(task_record['last_change']),
                        "_links": [
                            {"rel": "self",
                             "href": "/%s/tasks/%s"
                                     % (fgapiver, task_id)
                             },
                            {"rel": "input",
                             "href": "/%s/tasks/%s/input"
                                     % (fgapiver, task_id)
                             }
                        ]},
                    ]
                    paged_tasks, paged_links = paginate_response(
                        task_array,
                        page,
                        per_page,
                        request.url)
                    response = {"tasks": paged_tasks,
                                "_links": paged_links}
    elif request.method == 'POST':
        auth_state, auth_msg = authorize_user(
            current_user, app_id, user, "app_run")
        logger.debug("[app_run]: auth_state: '%s', auth_msg: '%s'"
                     % (auth_state, auth_msg))
        if not auth_state:
            state = 402
            response = {
                "message": "Not authorized to perform this request:\n%s" %
                           auth_msg}
        else:
            # Getting values
            params = request.get_json()
            logger.debug("params: '%s'" % params)
            if params is not None:
                app_id = params.get('application', '')
                app_desc = params.get('description', '')
                app_args = params.get('arguments', [])
                app_inpf = params.get('input_files', [])
                app_outf = params.get('output_files', [])
                # Create task
                task_id = fgapisrv_db.init_task(
                    app_id, app_desc, user, app_args, app_inpf, app_outf)
                logger.debug("task_id: '%s'" % task_id)
                if task_id < 0:
                    db_state = fgapisrv_db.get_state()
                    # Error initializing task
                    # Prepare for 410 error
                    state = 410
                    response = {
                        'message': db_state[1]
                    }
                else:
                    # Prepare response
                    state = 200
                    task_record = fgapisrv_db.get_task_record(task_id)
                    response = {
                        "id": task_record['id'],
                        "application": task_record['application'],
                        "description": task_record['description'],
                        "arguments": task_record['arguments'],
                        "input_files": task_record['input_files'],
                        "output_files": task_record['output_files'],
                        "status": task_record['status'],
                        "user": task_record['user'],
                        "date": str(
                            task_record['last_change']),
                        "_links": [
                            {
                                "rel": "self",
                                "href": "/%s/tasks/%s" %
                                        (fgapiver,
                                         task_id)},
                            {
                                "rel": "input",
                                "href": "/%s/tasks/%s/input" %
                                        (fgapiver,
                                         task_id)}]}
            else:
                state = 404
                response = {
                    "message": ("Did not find any application description "
                                "json input")}
    js = json.dumps(response, indent=fgjson_indent)
    resp = Response(js, status=state, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    header_links(request, resp, response)
    return resp


# This is an informative call
# GET  - shows details
# POST - could reshape the request (Delete/Recreate)

@app.route(
    '/%s/tasks/<task_id>' %
    fgapiver,
    methods=[
        'GET',
        'PUT',
        'POST',
        'DELETE',
        'PATCH'])
@login_required
def task_id(task_id=None):
    global fgapisrv_db
    global logger
    logger.debug('tasks(%s)/%s: %s' % (request.method,
                                       task_id,
                                       request.values.to_dict()))
    user_name = current_user.get_name()
    user_id = current_user.get_id()
    app_id = get_task_app_id(task_id)
    user = request.values.get('user', user_name)
    if request.method == 'GET':
        auth_state, auth_msg = authorize_user(
            current_user, app_id, user, "task_view")
        if not auth_state:
            state = 402
            response = {
                "message": "Not authorized to perform this request:\n%s" %
                           auth_msg}
        else:
            # User should be able to see the given app_id
            if not fgapisrv_db.task_exists(task_id, user_id, user):
                state = 404
                response = {
                    "message": "Unable to find task with id: %s" % task_id
                }
            else:
                # Get task details
                response = fgapisrv_db.get_task_record(task_id)
                db_state = fgapisrv_db.get_state()
                if db_state[0] != 0:
                    # Couldn't get TaskRecord
                    # Prepare for 404 not found
                    state = 404
                    response = {
                        "message": db_state[1]
                    }
                else:
                    # Add links_
                    response['_links'] = [
                        {
                            "rel": "input",
                            "href": "/%s/tasks/%s/input" %
                                    (fgapiver,
                                     task_id)}, ]
                    state = 200
    elif request.method == 'DELETE':
        auth_state, auth_msg = authorize_user(
            current_user, app_id, user, "task_delete")
        if not auth_state:
            state = 402
            response = {
                "message": "Not authorized to perform this request:\n%s" %
                           auth_msg}
        else:
            if not fgapisrv_db.task_exists(task_id, user_id, user):
                state = 404
                response = {
                    "message": "Unable to find task with id: %s" % task_id
                }
            elif not fgapisrv_db.delete(task_id):
                state = 410
                response = {
                    "message": "Unable to delete task with id: %s" % task_id
                }
            else:
                state = 204
                response = {
                    "message": "Successfully removed task with id: %s" %
                               task_id}
                # 204 - NO CONTENT cause no output
                logger.debug(response['message'])
    elif request.method == 'PATCH':
        # PATCH on tasks accepts status change or on runtime_data
        params = request.get_json()
        new_status = params.get('status', None)
        if new_status is not None:
            # status change:
            auth_state, auth_msg = authorize_user(
                current_user, app_id, user, "task_statuschange")
            if not auth_state:
                state = 402
                response = {
                    "message": "Not authorized to perform status change "
                               "request:\n%s" %
                               auth_msg}
            else:
                if not fgapisrv_db.task_exists(task_id, user_id, user):
                    state = 404
                    response = {
                        "message": "Unable to find task with id: %s" % task_id
                    }
                elif not fgapisrv_db.status_change(task_id, new_status):
                    state = 410
                    response = {
                        "message": ("Unable to change status for task having "
                                    "id: %s" % task_id)
                    }
                else:
                    state = 200
                    response = {
                        "message": "Successfully changed status of task with"
                                   " id: %s" % task_id
                    }
        else:
            # runtime_data:
            #
            # The input consists in a json having the form
            # { "runtime_data" : [
            #   { "data_name":  "name"
            #    ,"data_value": "value"
            #    ,"data_desc": "description of the value"
            #    ,"data_type": "how client receives the file"
            #    ,"data_proto": "protocol used to access data"
            #   }, ... ] }
            #
            # The insertion policy will be:
            #  1) data_name does not exists, a new record will be created in
            #     runtime_data table
            #  2) data_name exists the new value will be updated to the
            #     existing name
            #
            auth_state, auth_msg = authorize_user(
                current_user, app_id, user, "task_userdata")
            if not auth_state:
                state = 402
                response = {
                    "message": "Not authorized to perform this request:\n%s" %
                               auth_msg}
            else:
                runtime_data = params.get('runtime_data', [])
                if not fgapisrv_db.task_exists(task_id, user_id, user):
                    state = 404
                    response = {
                        "message": "Unable to find task with id: %s" % task_id
                    }
                elif not fgapisrv_db.patch_task(task_id, runtime_data):
                    state = 410
                    response = {
                        "message": ("Unable store runtime data for task "
                                    "having id: %s" % task_id)
                    }
                else:
                    state = 200
                    response = {
                        "message": "Successfully patched task with id: %s" %
                                   task_id}
    elif (request.method == 'PUT' or
          request.method == 'POST'):
        state = 405
        response = {
            "message": "This method is not allowed for this endpoint"
        }
    js = json.dumps(response, indent=fgjson_indent)
    resp = Response(js, status=state, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    header_links(request, resp, response)
    return resp

# This finalizes the task request allowing to submit the task
# GET  - shows input files
# POST - specify input files


@app.route('/%s/tasks/<task_id>/input' % fgapiver,
           methods=['GET',
                    'POST'])
@login_required
def task_id_input(task_id=None):
    global fgapisrv_db
    global logger
    logger.debug('task_id_input(%s): %s' % (request.method,
                                            request.values.to_dict()))
    user_name = current_user.get_name()
    user_id = current_user.get_id()
    app_id = get_task_app_id(task_id)
    user = request.values.get('user', user_name)
    state = 404
    if request.method == 'GET':
        auth_state, auth_msg = authorize_user(
            current_user, app_id, user, "task_view")
        if not auth_state:
            state = 402
            response = {
                "message": "Not authorized to perform this request:\n%s" %
                           auth_msg}
        else:
            # Display task_input_file details
            if not fgapisrv_db.task_exists(task_id, user_id, user):
                state = 404
                response = {
                    "message": "Unable to find task with id: %s" % task_id
                }
            else:
                state = 200
                response = fgapisrv_db.get_task_record(task_id)[
                    'input_files']
    elif request.method == 'POST':
        auth_state, auth_msg = authorize_user(
            current_user, app_id, user, "app_run")
        if not auth_state:
            state = 402
            response = {
                "message": "Not authorized to perform this request:\n%s" %
                           auth_msg}
        else:
            # First determine IO Sandbox location for this task
            if not fgapisrv_db.task_exists(task_id, user_id, user):
                state = 404
                response = {
                    "message": "Unable to find task with id: %s" % task_id
                }
            elif fgapisrv_db.get_task_record(task_id)['status'] != 'WAITING':
                state = 404
                response = {
                    "message": ("Task with id: %s, "
                                "is no more waiting for inputs") % task_id
                }
            else:
                task_sandbox = fgapisrv_db.get_task_io_sandbox(task_id)
                if task_sandbox is None:
                    state = 404
                    response = {
                        "message": 'Could not find IO Sandbox dir for task: %s'
                                   % task_id}
                else:
                    # Process default application files
                    fgapisrv_db.setup_default_inputs(task_id, task_sandbox)
                    # Now process files to upload
                    uploaded_files = request.files.getlist('file[]')
                    file_list = ()
                    for f in uploaded_files:
                        filename = secure_filename(f.filename)
                        f.save(os.path.join(task_sandbox, filename))
                        fgapisrv_db.update_input_sandbox_file(
                            task_id, filename, os.path.join(task_sandbox))
                        file_list += (filename,)
                    # Now get input_sandbox status
                    if fgapisrv_db.is_input_sandbox_ready(task_id):
                        # The input_sandbox is completed; trigger the GE for
                        # this task
                        if fgapisrv_db.submit_task(task_id):
                            state = 200
                            response = {
                                "task": task_id,
                                "files": file_list,
                                "message": "uploaded",
                                "gestatus": "triggered"}
                            response['_links'] = [
                                {"rel": "task",
                                 "href": "/%s/tasks/%s"
                                         % (fgapiver, task_id)}, ]
                        else:
                            state = 412
                            response = {
                                "message": fgapisrv_db.get_state()[1]
                            }
                    else:
                        state = 200
                        response = {
                            "task": task_id,
                            "files": file_list,
                            "message": "uploaded",
                            "gestatus": "waiting"}
    js = json.dumps(response, indent=fgjson_indent)
    resp = Response(js, status=state, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    header_links(request, resp, response)
    return resp


@app.route('/%s/file' % fgapiver, methods=['GET', ])
@login_required
def file():
    global fgapisrv_db
    global logger
    logger.debug('file(%s): %s' % (request.method, request.values.to_dict()))
    serve_file = None
    user_name = current_user.get_name()
    user_id = current_user.get_id()
    user = request.values.get('user', user_name)
    file_path = request.values.get('path', None)
    file_name = request.values.get('name', None)
    task_id = fgapisrv_db.get_file_task_id(file_name, file_path)
    app_id = get_task_app_id(task_id)
    if request.method == 'GET':
        auth_state, auth_msg = authorize_user(
            current_user, app_id, user, "app_run")
        if not auth_state:
            task_state = 402
            file_response = {
                "message": "Not authorized to perform this request:\n%s" %
                           auth_msg}
        else:
            try:
                serve_file = open('%s/%s' % (file_path, file_name), 'rb')
                serve_file_content = serve_file.read()
                resp = Response(serve_file_content, status=200)
                resp.headers['Content-type'] = 'application/octet-stream'
                resp.headers.add('Content-Disposition',
                                 'attachment; filename="%s"' % file_name)
                return resp
            except:
                file_response = {
                    "message": "Unable to get file: %s/%s" %
                               (file_path, file_name)}
            finally:
                if serve_file is not None:
                    serve_file.close()
        js = json.dumps(file_response, indent=fgjson_indent)
        resp = Response(js, status=404)
        resp.headers['Content-type'] = 'application/json'
        return resp


#
# APPLICATION
#

# application - used to view o create a new application
# GET  - View task info
# POST - Create a new task; it only prepares the task for execution


@app.route('/%s/applications' % fgapiver,
           methods=['GET',
                    'PUT',
                    'POST'])
@login_required
def applications():
    global fgapisrv_db
    global logger
    logger.debug('applications(%s): %s' % (request.method,
                                           request.values.to_dict()))
    user_name = current_user.get_name()
    user_id = current_user.get_id()
    app_id = None
    user = request.values.get('user', user_name)
    page = request.values.get('page')
    per_page = request.values.get('per_page')
    user = request.values.get('user')
    state = 0
    response = {}
    if request.method == 'GET':
        auth_state, auth_msg = authorize_user(
            current_user, app_id, user, "app_view")
        if not auth_state:
            task_state = 402
            task_response = {
                "message": "Not authorized to perform this request:\n%s" %
                           auth_msg}
        else:
            # Show the whole task list
            # call to get tasks
            app_list = fgapisrv_db.get_app_list()
            # Remove special app_id = 0 (Unassigned infrastructure)
            if 0 in app_list:
                app_list.remove(0)
            db_state = fgapisrv_db.get_state()
            if db_state[0] != 0:
                # DBError getting TaskList
                # Prepare for 402
                state = 402
                response = {
                    "message": db_state[1]
                }
            else:
                applications = []
                state = 200
                for app_id in app_list:
                    app_record = fgapisrv_db.get_app_record(app_id)
                    db_state = fgapisrv_db.get_state()
                    if db_state[0] != 0:
                        # DBError getting TaskRecord
                        # Prepare for 403
                        state = 403
                        response = {
                            "message": db_state[1]
                        }
                    else:
                        applications += [
                            {
                                "id":
                                app_record['id'],
                                "name":
                                app_record['name'],
                                "description":
                                app_record['description'],
                                "outcome":
                                app_record['outcome'],
                                "enabled":
                                app_record['enabled'],
                                "parameters":
                                app_record['parameters'],
                                "files":
                                app_record['files'],
                                "infrastructures":
                                app_record['infrastructures'],
                                "_links": [{"rel": "self",
                                            "href": "/%s/applications/%s"
                                                    % (fgapiver, app_id)},
                                           {"rel": "input",
                                            "href": "/%s/applications/%s/input"
                                                    % (fgapiver, app_id)}]
                            },
                        ]
                paged_apps, paged_links = paginate_response(
                    applications,
                    page,
                    per_page,
                    request.url)
                response = {"applications": paged_apps,
                            "_links": paged_links}
    elif request.method == 'PUT':
        state = 405
        response = {
            "message": "This method is not allowed for this endpoint"
        }
    elif request.method == 'POST':
        auth_state, auth_msg = authorize_user(
            current_user, app_id, user, "app_install")
        if not auth_state:
            state = 402
            response = {
                "message": "Not authorized to perform this request:\n%s" %
                           auth_msg}
        else:
            # Getting values
            params = request.get_json()
            name = params.get('name', '')
            description = params.get('description', '')
            outcome = params.get('outcome', 'JOB')
            enabled = params.get('enabled', [])
            parameters = params.get('parameters', [])
            inp_files = params.get('input_files', [])
            files = params.get('files', [])
            infrastructures = params.get('infrastructures', [])
            # Create app
            app_id = fgapisrv_db.init_app(
                name,
                description,
                outcome,
                enabled,
                parameters,
                inp_files,
                files,
                infrastructures)
            if app_id <= 0:
                task_state = fgapisrv_db.get_state()
                # Error initializing task
                # Prepare for 410 error
                state = 410
                response = {
                    "message": task_state[1]
                }
            else:
                # Enable the groups owned by the installing user to
                # execute the app
                fgapisrv_db.enable_app_by_userid(
                    user_id,
                    app_id)
                # Prepare response
                state = 201
                app_record = fgapisrv_db.get_app_record(app_id)
                response = {
                    "id": app_record['id'],
                    "name": app_record['name'],
                    "description": app_record['description'],
                    "enabled": app_record['enabled'],
                    "parameters": app_record['parameters'],
                    "files": app_record['files'],
                    "infrastructures": app_record['infrastructures'],
                    "_links": [{"rel": "input",
                                "href": "/%s/application/%s/input"
                                        % (fgapiver, app_id)}, ]}
    js = json.dumps(response, indent=fgjson_indent)
    resp = Response(js, status=state, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    header_links(request, resp, response)
    return resp


# This is an informative call
# GET  - shows details
# POST - could reshape the request (Delete/Recreate)


@app.route(
    '/%s/applications/<app_id>' % fgapiver,
    methods=[
        'GET',
        'DELETE',
        'PUT',
        'POST'])
@login_required
def app_id(app_id=None):
    global fgapisrv_db
    global logger
    logger.debug('application(%s)/%s: %s' % (request.method,
                                             app_id,
                                             request.values.to_dict()))
    user_name = current_user.get_name()
    user_id = current_user.get_id()
    user = request.values.get('user', user_name)
    if request.method == 'GET':
        auth_state, auth_msg = authorize_user(
            current_user, app_id, user, "app_view")
        if not auth_state:
            status = 402
            response = {
                "message": "Not authorized to perform this request:\n%s" %
                           auth_msg}
        else:
            if not fgapisrv_db.app_exists(app_id):
                status = 404
                response = {
                    "message":
                    "Unable to find application with id: %s"
                    % app_id}
            else:
                # Get application details
                response = fgapisrv_db.get_app_record(app_id)
                db_state = fgapisrv_db.get_state()
                if db_state[0] != 0:
                    # Couldn't get AppRecord
                    # Prepare for 404 not found
                    status = 404
                    response = {
                        "message": db_state[1]
                    }
                else:
                    response['_links'] = [
                        {"rel": "self",
                         "href": "/%s/application/%s/input"
                                 % (fgapiver, app_id)}, ]
                    status = 200
    elif request.method == 'DELETE':
        auth_state, auth_msg = authorize_user(
            current_user, app_id, user, "app_delete")
        if not auth_state:
            status = 402
            response = {
                "message": "Not authorized to perform this request:\n%s" %
                           auth_msg}
        else:
            if not fgapisrv_db.app_exists(app_id):
                status = 404
                response = {
                    "message": "Unable to find application with id: %s" %
                               app_id}
            elif not fgapisrv_db.app_delete(app_id):
                status = 410
                response = {
                    "message": ("Unable to delete application with id: %s; "
                                "reason: '%s'"
                                % (app_id, fgapisrv_db.get_state()[1]))}
            else:
                status = 204
                response = {
                    "message": "Successfully removed application with id: %s" %
                               app_id}
                # 204 - NO CONTENT cause no output
                logger.debug(response['message'])
    elif request.method == 'POST':
        statis = 404
        response = {
            "message": "Not supported method"
        }
    elif request.method == 'PUT':
        auth_state, auth_msg = authorize_user(
            current_user, app_id, user, "app_change")
        if not auth_state:
            status = 402
            response = {
                "message": "Not authorized to perform this request:\n%s" %
                           auth_msg}
        else:
            app_desc = request.get_json()
            if app_desc.get("id", None) is not None\
               and int(app_desc['id']) != int(app_id):
                status = 403
                response = {
                    "message": "JSON application id %s is different than "
                               "URL application id: %s" % (app_desc['id'],
                                                           app_id)}
            elif not fgapisrv_db.app_exists(app_id):
                status = 404
                response = {
                    "message": "Unable to find application with id: %s" %
                               app_id}
            elif not fgapisrv_db.app_change(app_id, app_desc):
                status = 410
                response = {
                    "message": ("Unable to change application with id: %s; "
                                "reason: '%s'"
                                % (app_id, fgapisrv_db.get_state()[1]))}
            else:
                status = 200
                response = {
                    "message": "Successfully changed application with id: %s" %
                               app_id}
    js = json.dumps(response, indent=fgjson_indent)
    resp = Response(js, status=status, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    header_links(request, resp, response)
    return resp


@app.route('/%s/applications/<app_id>/input' % fgapiver,
           methods=['GET', 'POST'])
@login_required
def app_id_input(app_id=None):
    global fgapisrv_db
    global logger
    logger.debug('index(%s)/%s/input: %s' % (request.method,
                                             app_id,
                                             request.values.to_dict()))
    user_name = current_user.get_name()
    user_id = current_user.get_id()
    user = request.values.get('user', user_name)
    state = 404
    if request.method == 'GET':
        auth_state, auth_msg = authorize_user(
            current_user, app_id, user, "app_view")
        if not auth_state:
            state = 402
            response = {
                "message": "Not authorized to perform this request:\n%s" %
                           auth_msg}
        else:
            # Display app_input_file details
            if not fgapisrv_db.app_exists(app_id):
                state = 404
                response = {
                    "message": ("Unable to find application with id: %s"
                                % app_id)
                }
            else:
                state = 200
                esponse =\
                    fgapisrv_db.get_app_record(app_id)['files']
    elif request.method == 'POST':
        auth_state, auth_msg = authorize_user(
            current_user, app_id, user, "app_install")
        if not auth_state:
            state = 402
            response = {
                "message": "Not authorized to perform this request:\n%s" %
                           auth_msg}
        else:
            # First determine IO Sandbox location for this task
            if not fgapisrv_db.app_exists(app_id):
                state = 404
                response = {
                    "message": ("Unable to find application with id: %s"
                                % task_id)
                }
            else:
                # Now process files to upload
                app_dir = 'apps/%s' % app_id
                try:
                    os.stat(app_dir)
                    logger.debug("App dir: '%s' exists" % app_dir)
                except:
                    logger.debug("Creating app dir: '%s'" % app_dir)
                    os.makedirs(app_dir)
                uploaded_files = request.files.getlist('file[]')
                file_list = ()
                logger.debug("uploading file(s):")
                for f in uploaded_files:
                    filename = secure_filename(f.filename)
                    logger.debug("%s -> %s" % (filename, app_dir))
                    f.save(os.path.join(app_dir, filename))
                    fgapisrv_db.insert_or_update_app_file(app_id,
                                                          filename,
                                                          app_dir)
                    file_list += (filename,)
                state = 200
                response = {
                    "application": app_id,
                    "files": file_list,
                    "message": "uploaded successfully"}
    js = json.dumps(response, indent=fgjson_indent)
    resp = Response(js, status=state, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    header_links(request, resp, response)
    return resp

#
# INFRASTRUCTURE
#


@app.route('/%s/infrastructures' % fgapiver,
           methods=['GET',
                    'PUT',
                    'POST'])
@login_required
def infrastructures():
    global fgapisrv_db
    global logger
    logger.debug('infrastructures(%s): %s' % (request.method,
                                              request.values.to_dict()))
    user_name = current_user.get_name()
    user_id = current_user.get_id()
    infra_id = None
    user = request.values.get('user', user_name)
    page = request.values.get('page')
    per_page = request.values.get('per_page')
    user = request.values.get('user')
    state = 0
    if request.method == 'GET':
        auth_state, auth_msg = authorize_user(
            current_user, infra_id, user, "infra_view")
        if not auth_state:
            state = 402
            response = {
                "message": "Not authorized to perform this request:\n%s" %
                           auth_msg}
        else:
            # Show the whole infra list
            # call to get infrastructures
            infra_list = fgapisrv_db.get_infra_list(None)
            db_state = fgapisrv_db.get_state()
            if db_state[0] != 0:
                # DBError getting InfraList
                # Prepare for 402
                state = 402
                response = {
                    "message": db_state[1]
                }
            else:
                # Prepare response
                infra_response = []
                infrastructures = []
                state = 200
                for infra_id in infra_list:
                    infra_record = fgapisrv_db.get_infra_record(infra_id)
                    db_state = fgapisrv_db.get_state()
                    if db_state[0] != 0:
                        # DBError getting InfraRecord
                        # Prepare for 403
                        state = 403
                        response = {
                            "message": db_state[1]
                        }
                    else:
                        infrastructures += [
                            {
                                "id":
                                infra_record['id'],
                                "name":
                                infra_record['name'],
                                "description":
                                infra_record['description'],
                                "date":
                                infra_record['creation'],
                                "enabled":
                                infra_record['enabled'],
                                "virtual":
                                infra_record['virtual'],
                                "_links": [
                                    {"rel": "self",
                                     "href": "/%s/infrastructures/%s"
                                             % (fgapiver, infra_id)}]
                            },
                        ]
                paged_infras, paged_links = paginate_response(
                    infrastructures,
                    page,
                    per_page,
                    request.url)
                response = {
                    "infrastructures": paged_infras,
                    "_links": paged_links}
    elif request.method == 'PUT':
        state = 405
        response = {
            "message": "This method is not allowed for this endpoint"
        }
    elif request.method == 'POST':
        auth_state, auth_msg = authorize_user(current_user,
                                              None,
                                              user,
                                              "infra_add")
        if not auth_state:
            state = 402
            response = {
                "message": "Not authorized to perform this request:\n%s" %
                           auth_msg}
        else:
            # Getting values
            params = request.get_json()
            name = params.get('name', '')
            description = params.get('description', '')
            enabled = params.get('enabled', True)
            vinfra = params.get('virtual', False)
            infrastructure_parameters =\
                params.get('parameters', '')
            # Create infrastructure
            infra_id = fgapisrv_db.init_infra(
                name,
                description,
                enabled,
                vinfra,
                infrastructure_parameters)
            if infra_id < 0:
                init_state = fgapisrv_db.get_state()
                # Error initializing infrastructure
                # Prepare for 410 error
                state = 410
                response = {
                    "message": init_state[1]
                }
            else:
                # Prepare response
                state = 201
                infra_record = fgapisrv_db.get_infra_record(infra_id)
                response = {
                    "id": infra_record['id'],
                    "name": infra_record['name'],
                    "description": infra_record['description'],
                    "date": infra_record['creation'],
                    "enabled": infra_record['enabled'],
                    "virtual": infra_record['virtual'],
                    "_links": [
                        {
                            "rel": "self",
                            "href": "/%s/infrastructure/%s" %
                                    (fgapiver,
                                     infra_record['id'])}]}
    js = json.dumps(response, indent=fgjson_indent)
    resp = Response(js, status=state, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    header_links(request, resp, response)
    return resp


# This is an informative call
# GET  - shows details
# POST - could reshape the request (Delete/Recreate)


@app.route(
    '/%s/infrastructures/<infra_id>' %
    fgapiver,
    methods=[
        'GET',
        'DELETE',
        'POST',
        'PUT'])
@login_required
def infra_id(infra_id=None):
    global fgapisrv_db
    global logger
    logger.debug('infrastructures(%s)/%s: %s' % (request.method,
                                                 infra_id,
                                                 request.values.to_dict()))
    user_name = current_user.get_name()
    user_id = current_user.get_id()
    user = request.values.get('user', user_name)
    if request.method == 'GET':
        auth_state, auth_msg = authorize_user(
            current_user, None, user, "infra_view")
        if not auth_state:
            state = 402
            response = {
                "message": "Not authorized to perform this request:\n%s" %
                           auth_msg}
        else:
            if not fgapisrv_db.infra_exists(infra_id):
                state = 404
                response = {
                    "message": ("Unable to find infrastructure with id: %s"
                                % infra_id)}
            else:
                # Get task details
                infra_record = fgapisrv_db.get_infra_record(infra_id)
                db_state = fgapisrv_db.get_state()
                if db_state[0] != 0:
                    # Couldn't get TaskRecord
                    # Prepare for 404 not found
                    state = 404
                    response = {
                        "message": db_state[1]
                    }
                else:
                    state = 200
                    response = {"id": infra_record['id'],
                                "name": infra_record['name'],
                                "description": infra_record['description'],
                                "date": infra_record['creation'],
                                "enabled": infra_record['enabled'],
                                "virtual": infra_record['virtual'],
                                "parameters": infra_record['parameters'],
                                "_links": [
                                    {"rel": "self",
                                     "href": ("/%s/infrastructure/%s"
                                              % (fgapiver,
                                                 infra_record['id']))}]}
    elif request.method == 'DELETE':
        app_id = request.values.get('app_id', None)
        app_orphan = request.values.get('app_orphan', None)
        auth_state, auth_msg = authorize_user(
            current_user, app_id, user, "infra_delete")
        if not auth_state:
            state = 402
            response = {
                "message": "Not authorized to perform this request:\n%s" %
                           auth_msg}
        else:
            if not fgapisrv_db.infra_exists(infra_id):
                state = 404
                response = {
                    "message": "Unable to find infrastructure with id: %s" %
                               infra_id}
            elif not fgapisrv_db.infra_delete(infra_id, app_id, app_orphan):
                state = 410
                response = {
                    "message": ("Unable to delete infrastructure with id: %s; "
                                "reason: '%s'"
                                % (infra_id, fgapisrv_db.get_state()[1]))}
            else:
                state = 200
                response = {
                    "message":
                    "Successfully removed infrastructure with id: %s" %
                    infra_id}
    elif request.method == 'POST':
        response = {
            "message": "Not supported method"
        }
        infra_state = 404
    elif request.method == 'PUT':
        app_id = request.values.get('app_id', None)
        auth_state, auth_msg = authorize_user(
            current_user, app_id, user, "infra_change")
        if not auth_state:
            state = 402
            response = {
                "message": "Not authorized to perform this request:\n%s" %
                           auth_msg}
        else:
            infra_desc = request.get_json()
            if infra_desc.get("id", None) is not None\
               and int(infra_desc['id']) != int(infra_id):
                state = 403
                response = {
                    "message": "JSON infrastructure id %s is different than "
                               "URL infrastructure id: %s" % (infra_desc['id'],
                                                              infra_id)}
            elif not fgapisrv_db.infra_exists(infra_id):
                state = 404
                response = {
                    "message": "Unable to find infrastructure with id: %s" %
                               infra_id}
            elif not fgapisrv_db.infra_change(infra_id, infra_desc):
                state = 400
                response = {
                    "message": ("Unable to change application with id: %s; "
                                "reason: '%s'"
                                % (app_id, fgapisrv_db.get_state()[1]))}
            else:
                state = 200
                response = {
                    "message":
                    "Infrastructure changed correctly"
                }
    js = json.dumps(response, indent=fgjson_indent)
    resp = Response(js, status=state, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    header_links(request, resp, response)
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

# Get database object and check the DB
check_db_ver()

# Now execute accordingly to the app configuration (stand-alone/wsgi)
if __name__ == "__main__":
    # Inform user about server activity
    print "fgAPIServer running in stand-alone mode ..."

    # Starting-up server
    if len(fgapisrv_crt) > 0 and len(fgapisrv_key) > 0:
        context = SSL.Context(SSL.SSLv23_METHOD)
        context.use_privatekey_file(fgapisrv_key)
        context.use_certificate_file(fgapisrv_crt)
        app.run(host=fgapisrv_host, port=fgapisrv_port,
                ssl_context=context, debug=fgapisrv_debug)
    else:
        app.run(host=fgapisrv_host, port=fgapisrv_port, debug=fgapisrv_debug)
