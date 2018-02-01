#!/bin/bash
#
# fgtest.sh
#
FG_ENDPOINT=http://localhost:8888/v1.0
FG_TEST_TOKEN="TEST_TOKEN"
FG_HEAD_AUTH="-H \"Authorization: Bearer $FG_TEST_TOKEN\""
FG_HEAD_JSON="-H \"Content-type: application/json\""

ASD_ENDPOINT=http://localhost:8080
ASD_MAINPAGE=APIServerDaemon/

PTV_ENDPOINT=http://localhost:8889
PTV_USER=tokenver_user
PTV_PASS=tokenver_pass

FGTEST_USR=fgtest_test
FGTEST_PWD=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 8 | head -n 1)
FGTEST_UPW=.$FGTEST_USR.passwd

REPORT_HOMEDIR=www
REPORT_HOME=fgtest
REPORT_INDEX=index.html
REPORT_PDFDIR=pdf
REPORT_MKDPF=1
REPORT_PDFALL=$REPORT_PDFDIR/report.pdf

# Initialize all fgtest resources
fgtest_init() {
    FGTEST_LIST=$(mktemp)
    FGTEST_OUT=$(mktemp)
    FGTEST_ERR=$(mktemp)
    echo $REPORT_HOMEDIR/$REPORT_INDEX >> $FGTEST_LIST
    echo "Generating test index page: $REPORT_HOMEDIR/$REPORT_INDEX" 
    cat >$REPORT_HOMEDIR/$REPORT_INDEX <<EOF
<html>
<title>FutureGateway test report</title>
<head>
  <link rel="shortcut icon" href="images/favicon.ico" type="image/x-icon">
  <link rel="icon" href="images/favicon.ico" type="image/x-icon">
  <link href="css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
<script src="js/jquery.min.js"></script>
<script src="js/bootstrap.min.js"></script>
<div class="container theme-showcase" role="main">
<div class="jumbotron">
<table><tbody><tr>
<td><img src="images/fglogo.png" width="50%"/></td>
<td><h1>FutureGateway test report</h1></td>
</tbody></tr></table>
<p>This is the main page for tests executed on top of a baseline FutureGateway installation</p>
</div>
<table class="table table-bordered">
<thead>
<tr><th>Test</th><th>Status</th><th>Description</th></tr>
</thead>
<!-- Test list -->
</table>
<div class="page-header"><h1>Notes</h1></div>
<div class="well">
<p>This test better operates on fresh FutureGateway baseline installations</p>
<!-- PDF report -->
</div>
</div>
</body>
</html>
EOF
}

###
### Testing FutureGateway baseline environment
###

# Verify and create the fgtest user
# This is a pre-requisite and no report is foreseen for this test
fgtest_user() {
    TEST_PKG="Creating SSH test environment"

    CHK_FGTEST_USR=$(cat /etc/passwd | grep $FGTEST_USR)
    if [ "$CHK_FGTEST_USR" == "" ]; then
        echo "FutureGateway test user does not exists"
        adduser --disabled-password --gecos "" $FGTEST_USR
        echo "$FGTEST_USR:$FGTEST_PWD" | chpasswd
        echo "Test user $FGTEST_USR has been created"
        echo "SSH keyscanning"
        ssh-keyscan -H localhost >> /root/.ssh/known_hosts
        echo "Test user password is: $FGTEST_PWD"
        echo $FGTEST_PWD > $FGTEST_UPW
    else
        echo "FutureGateway test user exists"
    fi
    CHK_FGTEST_USR=$(cat /etc/ssh/sshd_config | grep $FGTEST_USR)
    if [ "$CHK_FGTEST_USR" == "" ]; then
        echo "Adding ssh password authentication for the user: '"$FGTEST_USR"'"
        cat >> /etc/ssh/sshd_config <<EOF
# FutureGateway test user ${FGTEST_USR} (begin)
Match User ${FGTEST_USR}
PasswordAuthentication yes
# FutureGateway test user ${FGTEST_USR} (end)
EOF
        echo "Restarting ssh"
        /etc/init.d/ssh restart
    else
        echo "Test user already setup in ssh config"
    fi
    PUBKEY=$(cat $HOME/.ssh/id_rsa.pub)
    su - $FGTEST_USR -c "mkdir -p .ssh && touch .ssh/authorized_keys"
    su - $FGTEST_USR -c "cat .ssh/authorized_keys | grep \"$PUBKEY\" || echo \"$PUBKEY\" > /home/$FGTEST_USR/.ssh/authorized_keys"
    # Check connection
    CHK_FGTEST_USR=$(sshpass -p "$(cat $FGTEST_UPW)" ssh $FGTEST_USR@localhost whoami)
    if [ "$CHK_FGTEST_USR" != "$FGTEST_USR" ]; then
      echo "SSH connection test to $FGTEST_USR@localhost failed"
      return 1
    fi
    FGTEST_PAS=$(cat $FGTEST_UPW)
    echo "SSH connection test to $FGTEST_USR@localhost passed"
    return 0
}

# PTV and Tosca simulator (needed for test
fgtest_ptv() {
    TEST_PKG="PTV service"
    TEST_TITLE="PTV presence"
    TEST_SHDESC="ptv_home"
    TEST_DESC="\
This test verifies that baseline PTV service is up and running calling \
<span class=\"badge\">/get-token</span> endpoint using <b>GET</b> method"
    TEST_APICALL="(GET) /get-token"
    TEST_CMD="curl -w \"\n%{http_code}\" -u '"$PTV_USER":"$PTV_PASS"' $PTV_ENDPOINT/get-token"
    echo "Executing: '"$TEST_CMD"'"
    eval "$TEST_CMD" >$FGTEST_OUT 2>$FGTEST_ERR
    TEST_HTTPRETCODE=$(cat $FGTEST_OUT | tail -n 1)
    sed -i '$ d' $FGTEST_OUT
    TEST_RES=$?
    TEST_CHK=$(cat $FGTEST_OUT | jq .error | xargs echo)
    echo "$TEST_CHK"
    fgtest_report
    return $? 
}

# Test FutureGateway presence
fgtest_fg() {
    TEST_PKG="FutureGateway endpoint"
    TEST_TITLE="FG endpoint"
    TEST_SHDESC="fg_endpoint"
    TEST_DESC="\
This test verifies that baseline FutureGateway endpoint is up and running calling \
<span class=\"badge\">/</span> endpoint and using <b>GET</b> method"
    TEST_APICALL="(GET) /"
    TEST_CMD="curl -w \"\n%{http_code}\" -f $FG_ENDPOINT/"
    echo "Executing: '"$TEST_CMD"'"
    eval "$TEST_CMD" >$FGTEST_OUT 2>$FGTEST_ERR
    TEST_RES=$?
    TEST_HTTPRETCODE=$(cat $FGTEST_OUT | tail -n 1)
    sed -i '$ d' $FGTEST_OUT
    fgtest_report
    return $? 
}

# Test APIServerDaemon presence
fgtest_asd() {
    TEST_PKG="FutureGateway APIServerDaemon"
    TEST_TITLE="ASD endpoint"
    TEST_SHDESC="asd_endpoint"
    TEST_DESC="\
This test verifies that baseline FutureGateway APIServerDaemon is up and running calling \
<span class=\"badge\">/$ASD_MAINPAGE</span> address"
    TEST_APICALL="(GET) /$ASD_MAINPAGE"
    TEST_CMD="curl -w \"\n%{http_code}\" -f $ASD_ENDPOINT/$ASD_MAINPAGE"
    echo "Executing: '"$TEST_CMD"'"
    eval "$TEST_CMD" >$FGTEST_OUT 2>$FGTEST_ERR
    TEST_RES=$?
    TEST_HTTPRETCODE=$(cat $FGTEST_OUT | tail -n 1)
    sed -i '$ d' $FGTEST_OUT
    fgtest_report
    return $?
}

###
### Testing FutureGateway infrastructures/ endpoint related calls
###

# Setup the SSH infrastructure using the fgtest user
fgtest_newinfra() {
    TEST_PKG="Create infrastructure"
    TEST_TITLE="Infrastructure create"
    TEST_SHDESC="infra_create"
    TEST_DESC="\
This test create a new infrastructure calling \
<span class=\"badge\">/infrastructures</span> endpoint and using <b>POST</b> method"
    TEST_APICALL="(POST) /infrastructures"
    NEW_INFRA_JSON=$(mktemp)
    cat >$NEW_INFRA_JSON <<EOF
{ "name": "SSH Test infrastructure",
  "parameters": [ { "name": "jobservice", 
                    "value": "ssh://localhost" },
                  { "name": "username",
                    "value": "${FGTEST_USR}" },
                  { "name": "password",
                    "value": "${FGTEST_PAS}" } ],
  "description": "SSH Test infrastructure for fgtest",
  "enabled": true,
  "virtual": false }
EOF
    FG_HEADERS=$FG_HEAD_AUTH" "$FG_HEAD_JSON
    TEST_JSON_DATA=$(cat $NEW_INFRA_JSON)
    TEST_CMD="curl -w \"\n%{http_code}\" -f $FG_HEADERS -X POST -d '"$TEST_JSON_DATA"' $FG_ENDPOINT/infrastructures"
    echo "Executing: '"$TEST_CMD"'"
    eval "$TEST_CMD" >$FGTEST_OUT 2>$FGTEST_ERR
    TEST_RES=$?
    TEST_HTTPRETCODE=$(cat $FGTEST_OUT | tail -n 1)
    sed -i '$ d' $FGTEST_OUT
    rm -f $NEW_INFRA_JSON
    TEST_INFRA_ID=$(cat $FGTEST_OUT | jq .id | xargs echo)
    fgtest_report
    return $? 
}

# View all infrastructures
fgtest_viewinfras() {
    TEST_PKG="View infrastructures"
    TEST_TITLE="Infrastructure view all"
    TEST_SHDESC="infra_viewall"
    TEST_DESC="\
This test uses <span class=\"badge\">/infrastructures</span> API call to view \
all defined infrastructures using <b>GET</b> method"
    TEST_APICALL="(GET) /infrastructures"
    FG_HEADERS=$FG_HEAD_AUTH
    TEST_CMD="curl -w \"\n%{http_code}\" -f $FG_HEADERS $FG_ENDPOINT/infrastructures"
    echo "Executing: '"$TEST_CMD"'"
    eval "$TEST_CMD" >$FGTEST_OUT 2>$FGTEST_ERR
    TEST_RES=$?
    TEST_HTTPRETCODE=$(cat $FGTEST_OUT | tail -n 1)
    sed -i '$ d' $FGTEST_OUT
    fgtest_report
    return $? 
}

# View last inserted infrastructure
fgtest_viewinfra() {
    TEST_PKG="View infrastructure"
    TEST_TITLE="Infrastructure view"
    TEST_SHDESC="infra_view"
    TEST_DESC="\
This test uses <span class=\"badge\">/infrastructures</span> API call to view the last \
inserted  infrastructure having id: '${TEST_INFRA_ID}' and using <b>GET</b> method"
    TEST_APICALL="(GET) /infrastructures/$TEST_INFRA_ID"
    FG_HEADERS=$FG_HEAD_AUTH
    TEST_CMD="curl -w \"\n%{http_code}\" -f $FG_HEADERS $FG_ENDPOINT/infrastructures/$TEST_INFRA_ID"
    echo "Executing: '"$TEST_CMD"'"
    eval "$TEST_CMD" >$FGTEST_OUT 2>$FGTEST_ERR
    TEST_RES=$?
    TEST_HTTPRETCODE=$(cat $FGTEST_OUT | tail -n 1)
    sed -i '$ d' $FGTEST_OUT
    fgtest_report
    return $? 
}

# Modify last inserted infrastructure
fgtest_modinfra() {
    TEST_PKG="Modify infrastructure"
    TEST_TITLE="Infrastructure modify"
    TEST_SHDESC="infra_modify"
    TEST_DESC="\
This test modifies the new inserted infrastructure having id: '${TEST_INFRA_ID}' calling \
<span class=\"badge\">/infrastructures</span> endpoint and using <b>PUT</b> method"
    TEST_APICALL="(PUT) /infrastructures/$TEST_INFRA_ID"
    MOD_INFRA_JSON=$(mktemp)
    cat >$MOD_INFRA_JSON <<EOF
{ "id": ${TEST_INFRA_ID},
  "name": "(modified) SSH Test infrastructure",
  "parameters": [ { "name": "jobservice", 
                    "value": "(modified) ssh://localhost" },
                  { "name": "username",
                    "value": "(modified) ${FGTEST_USR}" },
                  { "name": "password",
                    "value": "(modified) ${FGTEST_PAS}" } ],
  "description": "(modified) SSH Test infrastructure for fgtest",
  "enabled": false,
  "virtual": true }
EOF
    FG_HEADERS="$FG_HEAD_AUTH $FG_HEAD_JSON"
    TEST_JSON_DATA=$(cat $MOD_INFRA_JSON)
    TEST_CMD="curl -w \"\n%{http_code}\" -f $FG_HEADERS -X PUT -d '"$TEST_JSON_DATA"' $FG_ENDPOINT/infrastructures/$TEST_INFRA_ID"
    echo "Executing: '"$TEST_CMD"'"
    eval "$TEST_CMD" >$FGTEST_OUT 2>$FGTEST_ERR
    TEST_RES=$?
    TEST_HTTPRETCODE=$(cat $FGTEST_OUT | tail -n 1)
    sed -i '$ d' $FGTEST_OUT
    rm -f $NEW_INFRA_JSON
    fgtest_report
    return $?
}

# Delete last inserted infrastructure
fgtest_delinfra() {
    TEST_PKG="Delete infrastructure"
    TEST_TITLE="Infrastructure delete"
    TEST_SHDESC="infra_delete"
    TEST_DESC="\
This test delete the new inserted infrastructure having id: '${TEST_INFRA_ID}' calling \
<span class=\"badge\">/infrastructures</span> endpoint and using <b>DELETE</b> method"
    TEST_APICALL="(DELETE) /infrastructures/$TEST_INFRA_ID"
    FG_HEADERS="$FG_HEAD_AUTH"
    TEST_CMD="curl -w \"\n%{http_code}\" -f $FG_HEADERS -X DELETE $FG_ENDPOINT/infrastructures/$TEST_INFRA_ID"
    echo "Executing: '"$TEST_CMD"'"
    eval "$TEST_CMD" >$FGTEST_OUT 2>$FGTEST_ERR
    TEST_RES=$?
    TEST_HTTPRETCODE=$(cat $FGTEST_OUT | tail -n 1)
    sed -i '$ d' $FGTEST_OUT
    rm -f $NEW_INFRA_JSON
    fgtest_report
    return $?
}

###
### Testing FutureGateway applications/ endpoint related calls
###
fgtest_newapp() {
    TEST_PKG="Create application"
    TEST_TITLE="Application create"
    TEST_SHDESC="app_create"
    TEST_DESC="\
This test create a new application calling \
<span class=\"badge\">/applications</span> endpoint and using <b>POST</b> method"
    TEST_APICALL="(POST) /applications"
    # The same infrastructure created during infrastructures/
    # tests will be re-created here
    NEW_INFRA_JSON=$(mktemp)
    cat >$NEW_INFRA_JSON <<EOF
{ "name": "SSH Test infrastructure",
  "parameters": [ { "name": "jobservice", 
                    "value": "ssh://localhost" },
                  { "name": "username",
                    "value": "${FGTEST_USR}" },
                  { "name": "password",
                    "value": "${FGTEST_PAS}" } ],
  "description": "SSH Test infrastructure for fgtest",
  "enabled": true,
  "virtual": false }
EOF
    FG_HEADERS=$FG_HEAD_AUTH" "$FG_HEAD_JSON
    TEST_JSON_DATA=$(cat $NEW_INFRA_JSON)
    TEST_CMD="curl -w \"\n%{http_code}\" -f $FG_HEADERS -X POST -d '"$TEST_JSON_DATA"' $FG_ENDPOINT/infrastructures"
    echo "Executing: '"$TEST_CMD"'"
    eval "$TEST_CMD" >$FGTEST_OUT 2>$FGTEST_ERR
    TEST_RES=$?
    # Check that infrastructure has been created succesffully
    if [ $TEST_RES -ne 0 ]; then
        echo "Error test infrastructure for application isntallation"
        return 1
    fi
    TEST_HTTPRETCODE=$(cat $FGTEST_OUT | tail -n 1)
    sed -i '$ d' $FGTEST_OUT
    TEST_INFRA_ID=$(cat $FGTEST_OUT | jq .id | xargs echo)
    rm -f $NEW_INFRA_JSON
    # Now the infrastructure for the new application is available
    NEW_APP_JSON=$(mktemp)
    cat >$NEW_INFRA_JSON <<EOF
{
        "infrastructures": [${TEST_INFRA_ID}],
        "parameters": [{
                "name": "target_executor",
                "value": "GridEngine",
                "description": "Target executor name"
        }, {
                "name": "jobdesc_executable",
                "value": "cp input.txt ouput.txt && hostname | tee -a output.txt",
                "description": "Command to execute"
        }, {
                "name": "jobdesc_output",
                "value": "stdout.txt",
                "description": "Standard output"
        }, {
                "name": "jobdesc_error",
                "value": "stderr.txt",
                "description": "Standard error"
        }],
        "enabled": true,
        "name": "Tester application",
        "description": "FutureGateway tester application"
}
EOF
    FG_HEADERS=$FG_HEAD_AUTH" "$FG_HEAD_JSON
    TEST_JSON_DATA=$(cat $NEW_INFRA_JSON)
    TEST_CMD="curl -w \"\n%{http_code}\" -f $FG_HEADERS -X POST -d '"$TEST_JSON_DATA"' $FG_ENDPOINT/applications"
    echo "Executing: '"$TEST_CMD"'"
    eval "$TEST_CMD" >$FGTEST_OUT 2>$FGTEST_ERR
    TEST_RES=$?
    TEST_HTTPRETCODE=$(cat $FGTEST_OUT | tail -n 1)
    sed -i '$ d' $FGTEST_OUT
    TEST_APP_ID=$(cat $FGTEST_OUT | jq .id | xargs echo)
    rm -f $NEW_INFRA_JSON
    fgtest_report
    return $?
}

# View all applications
fgtest_viewapps() {
    TEST_PKG="View applications"
    TEST_TITLE="Application view all"
    TEST_SHDESC="app_viewall"
    TEST_DESC="\
This test uses <span class=\"badge\">/applications</span> API call to view \
all defined applications using <b>GET</b> method"
    TEST_APICALL="(GET) /applications"
    FG_HEADERS=$FG_HEAD_AUTH
    TEST_CMD="curl -w \"\n%{http_code}\" -f $FG_HEADERS $FG_ENDPOINT/applications"
    echo "Executing: '"$TEST_CMD"'"
    eval "$TEST_CMD" >$FGTEST_OUT 2>$FGTEST_ERR
    TEST_RES=$?
    TEST_HTTPRETCODE=$(cat $FGTEST_OUT | tail -n 1)
    sed -i '$ d' $FGTEST_OUT
    fgtest_report
    return $?
}

# View last inserted application
fgtest_viewapp() {
    TEST_PKG="View application"
    TEST_TITLE="Application view"
    TEST_SHDESC="app_view"
    TEST_DESC="\
This test uses <span class=\"badge\">/applications</span> API call to view the last \
inserted  application having id: '${TEST_APP_ID}' and using <b>GET</b> method"
    TEST_APICALL="(GET) /applications/$TEST_APP_ID"
    FG_HEADERS=$FG_HEAD_AUTH
    TEST_CMD="curl -w \"\n%{http_code}\" -f $FG_HEADERS $FG_ENDPOINT/applications/$TEST_APP_ID"
    echo "Executing: '"$TEST_CMD"'"
    eval "$TEST_CMD" >$FGTEST_OUT 2>$FGTEST_ERR
    TEST_RES=$?
    TEST_HTTPRETCODE=$(cat $FGTEST_OUT | tail -n 1)
    sed -i '$ d' $FGTEST_OUT
    fgtest_report
    return $?
}

# Modify last inserted application 
fgtest_modapp() {
    TEST_PKG="Modify application"
    TEST_TITLE="Application modify"
    TEST_SHDESC="app_modify"
    TEST_DESC="\
This test modifies the new inserted application having id: '${TEST_APP_ID}' calling \
<span class=\"badge\">/applications</span> endpoint and using <b>PUT</b> method"
    TEST_APICALL="(PUT) /applications/$TEST_APP_ID"
    MOD_APP_JSON=$(mktemp)
    cat >$MOD_APP_JSON <<EOF
{
    "files": [], 
    "name": "(modified) Tester application", 
    "parameters": [
        {
            "name": "(modified) target_executor", 
            "value": "(modified) GridEngine", 
            "description": "(modified) Target executor name"
        }, 
        {
            "name": "(modified) jobdesc_executable", 
            "value": "(modified) cp input.txt ouput.txt && hostname | tee -a output.txt", 
            "description": "(modified) Command to execute"
        }, 
        {
            "name": "(modified) jobdesc_output", 
            "value": "(modified) stdout.txt", 
            "description": "(modified) Standard output"
        }, 
        {
            "name": "(modified) jobdesc_error", 
            "value": "(modified) stderr.txt", 
            "description": "(modified) Standard error"
        }
    ], 
    "outcome": "RES", 
    "enabled": false, 
    "id": "${TEST_APP_ID}", 
    "infrastructures": [
        43
    ], 
    "description": "(modified) FutureGateway tester application"
}
EOF
    FG_HEADERS="$FG_HEAD_AUTH $FG_HEAD_JSON"
    TEST_JSON_DATA=$(cat $MOD_APP_JSON)
    TEST_CMD="curl -w \"\n%{http_code}\" -f $FG_HEADERS -X PUT -d '"$TEST_JSON_DATA"' $FG_ENDPOINT/applications/$TEST_APP_ID"
    echo "Executing: '"$TEST_CMD"'"
    eval "$TEST_CMD" >$FGTEST_OUT 2>$FGTEST_ERR
    TEST_RES=$?
    TEST_HTTPRETCODE=$(cat $FGTEST_OUT | tail -n 1)
    sed -i '$ d' $FGTEST_OUT
    rm -f $NEW_APP_JSON
    fgtest_report
    return $?
}

# Delete last inserted application
fgtest_delapp() {
    TEST_PKG="Delete application"
    TEST_TITLE="Application delete"
    TEST_SHDESC="app_delete"
    TEST_DESC="\
This test delete the new inserted application having id: '${TEST_APP_ID}' calling \
<span class=\"badge\">/applications</span> endpoint and using <b>DELETE</b> method"
    TEST_APICALL="(DELETE) /applications/$TEST_APP_ID"
    FG_HEADERS="$FG_HEAD_AUTH"
    TEST_CMD="curl -w \"\n%{http_code}\" -f $FG_HEADERS -X DELETE $FG_ENDPOINT/applications/$TEST_APP_ID"
    echo "Executing: '"$TEST_CMD"'"
    eval "$TEST_CMD" >$FGTEST_OUT 2>$FGTEST_ERR
    TEST_RES=$?
    TEST_HTTPRETCODE=$(cat $FGTEST_OUT | tail -n 1)
    sed -i '$ d' $FGTEST_OUT
    rm -f $NEW_INFRA_JSON
    fgtest_report
    return $?
}

###
### Testing FutureGateway tasks/ endpoint related calls
###
fgtest_newtask() {
    TEST_PKG="Create task"
    TEST_TITLE="Task create"
    TEST_SHDESC="task_create"
    TEST_DESC="\
This test creates a new task calling \
<span class=\"badge\">/tasks</span> endpoint and using <b>POST</b> method"
    TEST_APICALL="(POST) /tasks"
    # The same application created during applications/
    # tests will be re-created here
    NEW_APP_JSON=$(mktemp)
    cat >$NEW_INFRA_JSON <<EOF
{   
        "infrastructures": [${TEST_INFRA_ID}],
        "parameters": [{
                "name": "target_executor",
                "value": "GridEngine",
                "description": "Target executor name"
        }, {
                "name": "jobdesc_executable",
                "value": "cp input.txt ouput.txt && hostname | tee -a output.txt",
                "description": "Command to execute"
        }, {
                "name": "jobdesc_output",
                "value": "stdout.txt",
                "description": "Standard output"
        }, {
                "name": "jobdesc_error",
                "value": "stderr.txt",
                "description": "Standard error"
        }],
        "enabled": true,
        "name": "Tester application",
        "description": "FutureGateway tester application"
}
EOF
    FG_HEADERS=$FG_HEAD_AUTH" "$FG_HEAD_JSON
    TEST_JSON_DATA=$(cat $NEW_INFRA_JSON)
    TEST_CMD="curl -w \"\n%{http_code}\" -f $FG_HEADERS -X POST -d '"$TEST_JSON_DATA"' $FG_ENDPOINT/applications"
    echo "Executing: '"$TEST_CMD"'"
    eval "$TEST_CMD" >$FGTEST_OUT 2>$FGTEST_ERR
    TEST_RES=$?
    # Check that infrastructure has been created succesffully
    if [ $TEST_RES -ne 0 ]; then
        echo "Error test application for task creation"
        return 1
    fi
    TEST_HTTPRETCODE=$(cat $FGTEST_OUT | tail -n 1)
    sed -i '$ d' $FGTEST_OUT
    TEST_APP_ID=$(cat $FGTEST_OUT | jq .id | xargs echo)
    rm -f $NEW_APP_JSON
    # Now the infrastructure for the new application is available
    NEW_TASK_JSON=$(mktemp)
    cat >$NEW_TASK_JSON <<EOF
{"application":"${TEST_APP_ID}",
 "description":"tester application run",
 "arguments": [],
 "input_files": [{"name": "input.txt"}],
 "output_files": [{"name": "output.txt"}]}
EOF
    FG_HEADERS=$FG_HEAD_AUTH" "$FG_HEAD_JSON
    TEST_JSON_DATA=$(cat $NEW_TASK_JSON)
    TEST_CMD="curl -w \"\n%{http_code}\" -f $FG_HEADERS -X POST -d '"$TEST_JSON_DATA"' $FG_ENDPOINT/tasks"
    echo "Executing: '"$TEST_CMD"'"
    eval "$TEST_CMD" >$FGTEST_OUT 2>$FGTEST_ERR
    TEST_RES=$?
    TEST_HTTPRETCODE=$(cat $FGTEST_OUT | tail -n 1)
    sed -i '$ d' $FGTEST_OUT
    TEST_TASK_ID=$(cat $FGTEST_OUT | jq .id | xargs echo)
    rm -f $NEW_TASK_JSON
    fgtest_report
    return $?
}

# View all tasks
fgtest_viewtasks() {
    TEST_PKG="View tasks"
    TEST_TITLE="Tasks view all"
    TEST_SHDESC="task_viewall"
    TEST_DESC="\
This test uses <span class=\"badge\">/tasks</span> API call to view \
all defined tasks using <b>GET</b> method"
    TEST_APICALL="(GET) /tasks"
    FG_HEADERS=$FG_HEAD_AUTH
    TEST_CMD="curl -w \"\n%{http_code}\" -f $FG_HEADERS $FG_ENDPOINT/tasks"
    echo "Executing: '"$TEST_CMD"'"
    eval "$TEST_CMD" >$FGTEST_OUT 2>$FGTEST_ERR
    TEST_RES=$?
    TEST_HTTPRETCODE=$(cat $FGTEST_OUT | tail -n 1)
    sed -i '$ d' $FGTEST_OUT
    fgtest_report
    return $?
}

# View task
fgtest_viewtask() {
    TEST_PKG="View task"
    TEST_TITLE="Task view"
    TEST_SHDESC="task_view"
    TEST_DESC="\
This test uses <span class=\"badge\">/tasks/id</span> API call to view the last \
inserted  task having id: '${TEST_TASK_ID}' and using <b>GET</b> method"
    TEST_APICALL="(GET) /tasks/$TEST_TASK_ID"
    FG_HEADERS=$FG_HEAD_AUTH
    TEST_CMD="curl -w \"\n%{http_code}\" -f $FG_HEADERS $FG_ENDPOINT/tasks/$TEST_TASK_ID"
    echo "Executing: '"$TEST_CMD"'"
    eval "$TEST_CMD" >$FGTEST_OUT 2>$FGTEST_ERR
    TEST_RES=$?
    TEST_HTTPRETCODE=$(cat $FGTEST_OUT | tail -n 1)
    sed -i '$ d' $FGTEST_OUT
    fgtest_report
    return $?
}

# View task input
fgtest_viewtaskinp() {
    TEST_PKG="View task input files"
    TEST_TITLE="Task view input"
    TEST_SHDESC="task_viewinp"
    TEST_DESC="\
This test uses <span class=\"badge\">/tasks/input</span> API call to view input files\
of the last inserted  task having id: '${TEST_TASK_ID}' and using <b>GET</b> method"
    TEST_APICALL="(GET) /tasks/$TEST_TASK_ID/input"
    FG_HEADERS=$FG_HEAD_AUTH
    TEST_CMD="curl -w \"\n%{http_code}\" -f $FG_HEADERS $FG_ENDPOINT/tasks/$TEST_TASK_ID/input"
    echo "Executing: '"$TEST_CMD"'"
    eval "$TEST_CMD" >$FGTEST_OUT 2>$FGTEST_ERR
    TEST_RES=$?
    TEST_HTTPRETCODE=$(cat $FGTEST_OUT | tail -n 1)
    sed -i '$ d' $FGTEST_OUT
    fgtest_report
    return $?
}

# Send task input files
fgtest_taskinpfile() {
    TEST_PKG="Send task input file"
    TEST_TITLE="Task input file"
    TEST_SHDESC="task_sendinpfile"
    TEST_DESC="\
This test sends an input file to an existing task having id: ${TEST_TASK_ID} \
<span class=\"badge\">/tasks/input</span> endpoint and using <b>POST</b> method"
    TEST_APICALL="(POST) /tasks/task_id/input"
    APP_INPUT_FILE=input.txt
    echo "This is the input file for tester application" > $APP_INPUT_FILE
    FG_HEADERS=$FG_HEAD_AUTH
    TEST_CMD="curl -w \"\n%{http_code}\" -f $FG_HEADERS -F \"file[]=@$APP_INPUT_FILE\" $FG_ENDPOINT/tasks/$TEST_TASK_ID/input"
    echo "Executing: '"$TEST_CMD"'"
    eval "$TEST_CMD" >$FGTEST_OUT 2>$FGTEST_ERR
    TEST_RES=$?
    TEST_HTTPRETCODE=$(cat $FGTEST_OUT | tail -n 1)
    sed -i '$ d' $FGTEST_OUT
    # rm -f $APP_INPUT_FILE # This will be removed later
    fgtest_report
    return $?
}

# Download input file
fgtest_dwnldinpfile() {
    TEST_PKG="Download task input file"
    TEST_TITLE="Task download input file"
    TEST_SHDESC="task_dnwldinpfile"
    TEST_DESC="\
This test download an input file of an existing task having id: ${TEST_TASK_ID} \
<span class=\"badge\">/file?path=...</span> endpoint and using <b>GET</b> method"
    TEST_APICALL="(GET) /file?path=..."
    # First retrieve the file endpoint from task JSON
    FG_HEADERS=$FG_HEAD_AUTH
    TEST_CMD="curl -w \"\n%{http_code}\" -f $FG_HEADERS $FG_ENDPOINT/tasks/$TEST_TASK_ID"
    echo "Executing: '"$TEST_CMD"'"
    eval "$TEST_CMD" >$FGTEST_OUT 2>$FGTEST_ERR
    TEST_RES=$?
    if [ $TEST_RES -ne 0 ]; then
        echo "Failed getting info for task: $TEST_TASK_ID"
        return 1
    fi
    sed -i '$ d' $FGTEST_OUT
    APP_INPUT_FGPATH=$(cat $FGTEST_OUT | jq .input_files | grep url | awk -F":" '{print $2}' | xargs echo | sed s/,//)
    FG_HEADERS=$FG_HEAD_AUTH
    TEST_CMD="curl -w \"\n%{http_code}\" -f $FG_HEADERS \"$FG_ENDPOINT/$APP_INPUT_FGPATH\""
    echo "Executing: '"$TEST_CMD"'"
    eval "$TEST_CMD" >$FGTEST_OUT 2>$FGTEST_ERR
    TEST_RES=$?
    TEST_HTTPRETCODE=$(cat $FGTEST_OUT | tail -n 1)
    sed -i '$ d' $FGTEST_OUT
    fgtest_report
    return $?
}

# Set runtime data
fgtest_runtimedataset() {
    TEST_PKG="Set Task runtime data"
    TEST_TITLE="Task runtime data set"
    TEST_SHDESC="task_runtimedataset"
    TEST_DESC="\
This test create runtime data for task having id: $TEST_TASK_ID calling \
<span class=\"badge\">/tasks/id</span> endpoint and using <b>PATCH</b> method"
    TEST_APICALL="(PATCH) /tasks/id"
    RUNTIMEDATA_JSON=$(mktemp)
    cat >$RUNTIMEDATA_JSON <<EOF
{ "runtime_data" : [ { "data_name":  "test_data_field"
                      ,"data_value": "test_data_value"
                      ,"data_desc": "test data for tester application"}]}
EOF
    FG_HEADERS=$FG_HEAD_AUTH" "$FG_HEAD_JSON
    TEST_JSON_DATA=$(cat $RUNTIMEDATA_JSON)
    TEST_CMD="curl -w \"\n%{http_code}\" -f $FG_HEADERS -X PATCH -d '"$TEST_JSON_DATA"' $FG_ENDPOINT/tasks/$TEST_TASK_ID"
    echo "Executing: '"$TEST_CMD"'"
    eval "$TEST_CMD" >$FGTEST_OUT 2>$FGTEST_ERR
    TEST_RES=$?
    TEST_HTTPRETCODE=$(cat $FGTEST_OUT | tail -n 1)
    sed -i '$ d' $FGTEST_OUT
    rm -f $RUNTIMEDATA_JSON
    TEST_INFRA_ID=$(cat $FGTEST_OUT | jq .id | xargs echo)
    fgtest_report
    return $?
}

# Retrieve runtime data
fgtest_runtimedataget() {
    TEST_PKG="Get Task runtime data"
    TEST_TITLE="Task runtime data get"
    TEST_SHDESC="task_runtimedataget"
    TEST_DESC="\
This test uses <span class=\"badge\">/tasks/id</span> API call to view the last \
inserted  task having id: '${TEST_TASK_ID}' and using <b>GET</b> method\
Inside the task information the new inserted runtime_data field should be present"
    TEST_APICALL="(GET) /tasks/$TEST_TASK_ID"
    FG_HEADERS=$FG_HEAD_AUTH
    TEST_CMD="curl -w \"\n%{http_code}\" -f $FG_HEADERS $FG_ENDPOINT/tasks/$TEST_TASK_ID"
    echo "Executing: '"$TEST_CMD"'"
    eval "$TEST_CMD" >$FGTEST_OUT 2>$FGTEST_ERR
    TEST_RES=$?
    TEST_HTTPRETCODE=$(cat $FGTEST_OUT | tail -n 1)
    sed -i '$ d' $FGTEST_OUT
    fgtest_report
    return $?
}

# Download output file
fgtest_dwnldoutfile() {
    TEST_PKG="Download task output file"
    TEST_TITLE="Task download output file"
    TEST_SHDESC="task_dnwldoutfile"
    TEST_DESC="\
This test download an output file of an existing task having id: ${TEST_TASK_ID} \
<span class=\"badge\">/file?path=...</span> endpoint and using <b>GET</b> method"
    TEST_APICALL="(GET) /file?path=..."
    # First wait for task execution termination
    FG_HEADERS=$FG_HEAD_AUTH
    rm -f $APP_INPUT_FILE # Now it is possible to remove input file
    for i in $(seq 1 60); do
        TEST_CMD="curl -w \"\n%{http_code}\" -f $FG_HEADERS $FG_ENDPOINT/tasks/$TEST_TASK_ID"
         echo "Executing: '"$TEST_CMD"'"
         eval "$TEST_CMD" >$FGTEST_OUT 2>$FGTEST_ERR
         TEST_RES=$?
         if [ $TEST_RES -ne 0 ]; then
             echo "Failed getting info for task: $TEST_TASK_ID"
             return 1
         fi
         sed -i '$ d' $FGTEST_OUT
         TEST_TASK_STATUS=$(cat $FGTEST_OUT | jq '.status' | xargs echo)
         case $TEST_TASK_STATUS in
             DONE)
                 echo "Task reached DONE status"
                 break
                 ;;
             ABORTED) 
                 echo "Task aborted"
                 return 1
                 ;;
             *)
                 printf "Status is $TEST_TASK_STATUS waiting ... "
         esac
         sleep 30
         echo "done"
    done
    if [ "$TEST_TASK_STATUS" != "DONE" ]; then
        echo "Test task did not reched DONE status in time"
        echo "Please verify your environment and re-execute"
        echo "the test"
        return 1
    fi
    # Now retrieve the output file endpoint from task JSON
    APP_OUTPUT_FGPATH=$(cat $FGTEST_OUT | jq '.output_files' | grep url | grep output.txt | awk -F":" '{print $2}' | xargs echo)
    TEST_CMD="curl -w \"\n%{http_code}\" -f $FG_HEADERS \"$FG_ENDPOINT/$APP_OUTPUT_FGPATH\""
    echo "Executing: '"$TEST_CMD"'"
    eval "$TEST_CMD" >$FGTEST_OUT 2>$FGTEST_ERR
    TEST_RES=$?
    TEST_HTTPRETCODE=$(cat $FGTEST_OUT | tail -n 1)
    sed -i '$ d' $FGTEST_OUT
    fgtest_report
    return $?
}

fgtest_deletetask() {
    TEST_PKG="Delete task"
    TEST_TITLE="Task delete"
    TEST_SHDESC="task_delete"
    TEST_DESC="\
This test delete the new created task having id: '${TEST_TASK_ID}' calling \
<span class=\"badge\">/tasks/id</span> endpoint and using <b>DELETE</b> method"
    TEST_APICALL="(DELETE) /tasks/$TEST_TASK_ID"
    FG_HEADERS="$FG_HEAD_AUTH"
    TEST_CMD="curl -w \"\n%{http_code}\" -f $FG_HEADERS -X DELETE $FG_ENDPOINT/tasks/$TEST_TASK_ID"
    echo "Executing: '"$TEST_CMD"'"
    eval "$TEST_CMD" >$FGTEST_OUT 2>$FGTEST_ERR
    TEST_RES=$?
    TEST_HTTPRETCODE=$(cat $FGTEST_OUT | tail -n 1)
    sed -i '$ d' $FGTEST_OUT
    rm -f $NEW_INFRA_JSON
    fgtest_report
    return $?
}

###
### Report
###


# Prepares a test report using the following:
#  TEST_TITLE - Title of the test
#  TEST_SHDESC - Short description of the test (used to generate html file)
#  TEST_DESC - Description of the test
#  FGTEST_OUT - File containing the text output of tested command
#  FGTEST_ERR - File containing the text error of tested command
#  TEST_RES - The curl return code (curl must have -f optrion)
#  TEST_HTTPRETCODE - The HTTP/s request return code 
fgtest_report() {
    echo $REPORT_HOMEDIR/${TEST_SHDESC}.html >> $FGTEST_LIST
    TEST_CMD_CLEAN=$(echo $TEST_CMD | sed s/'-w\ "\\n%{http_code}"'// | sed s/-f\ //)
    if [ $TEST_RES -ne 0 ]; then
        # The -f option of curl used inside fgtest_* funcion does not allow to
        # to see the outut recevided by executed statement. In order to see
        # the output of errored tests the curl command have to be re-executed
        echo "Re-executing: '"$TEST_CMD"'"
        eval "$TEST_CMD_CLEAN" >$FGTEST_OUT 2>/dev/null
        TEST_ERR=$(cat $FGTEST_ERR)
        TEST_RES_OUT="<span class=\"label label-danger\">Failed</p>"
    else
        TEST_ERR=""
        TEST_RES_OUT="<span class=\"label label-success\">Passed</span>"        
    fi
    TEST_OUT=$(cat $FGTEST_OUT)
    BACK_LINK="<a href=\"${REPORT_INDEX}\">tests</a>"
    TEST_ROW="<tr><td><a href=\"${TEST_SHDESC}.html\">${TEST_TITLE}</a></td><td>${TEST_RES_OUT}</td><td>${TEST_DESC}</td></tr>"
    cat >$REPORT_HOMEDIR/${TEST_SHDESC}.html <<EOF
<html>
<title>${TEST_TITLE}</title>
<head>
  <link rel="shortcut icon" href="images/favicon.ico" type="image/x-icon">
  <link rel="icon" href="images/favicon.ico" type="image/x-icon">
  <link href="css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
<script src="js/jquery.min.js"></script>
<script src="js/bootstrap.min.js"></script>
<div class="container theme-showcase" role="main">
<div class="jumbotron">
<table><tbody><tr>
<td><img src="images/fglogo.png" width="50%"/></td>
<td><h1>${TEST_TITLE}</h1></td>
</tbody></tr></table>
<p>${TEST_DESC}</p>
</div>
<table class="table table-bordered">
<tr><td>API call</td><td><pre>$TEST_APICALL</pre></td></tr>
<tr><td>Command</td><td><pre style="white-space: normal">${TEST_CMD_CLEAN}</pre></td></tr>
<tr><td>Curl return code</td><td><pre>${TEST_RES}</pre></td></tr>
<tr><td>HTTP return code</td><td><pre>${TEST_HTTPRETCODE}</pre></td></tr>
<tr><td>Output</td><td><pre>${TEST_OUT}</pre></td></tr>
<tr><td>Error</td><td><pre>${TEST_ERR}</pre></td></tr>
</table>
<div class="page-header"><h1>Notes</h1></div>
<div class="well">
<p>You can go back to the ${BACK_LINK} page</p>
</div>
</body>
</html>
EOF
    sed -i "/<!-- Test list -->/a ${TEST_ROW}" $REPORT_HOMEDIR/$REPORT_INDEX
    if [ $TEST_RES -eq 0 ]; then
        echo "Test: $TEST_PKG executed successfully"
    else
        echo "Test: $TEST_PKG failed to execute"
        return 1
    fi
    return 0
}

# Generate PDF files
fgtest_mkpdf() {
    TEST_PKG="Generating PDF files from generated html files"
    wkhtmltopdf --help >/dev/null 2>/dev/null
    CHK_HTML2PDF=$?
    if [ $CHK_HTML2PDF -ne 0 ]; then
        echo "Failed while checking wkhtmltopdf existence"
        return 1
    fi
    xvfb-run --help >/dev/null 2>/dev/null
    CHK_XVFB=$?
    CHK_HTML2PDF=$?
    if [ $CHK_HTML2PDF -ne 0 ]; then
        echo "Failed while checking xvfb-run existence"
        return 1
    fi   
    if [ $REPORT_MKDPF -ne 0 ]; then
       rm -rf $REPORT_PDFDIR
       mkdir -p $REPORT_PDFDIR
       PDF_LIST=""
       while read html_file; do
           HTML_FILE=$html_file
           PDF_FILE=$(echo $html_file | sed s/.html/.pdf/ | sed s/$REPORT_HOMEDIR/$REPORT_PDFDIR/)
           CMD="xvfb-run -a -s \"-screen 0 640x480x16\" wkhtmltopdf $HTML_FILE $PDF_FILE"
           eval $CMD
           RES=$?
           if [ $RES -ne 0 ]; then
               echo "Failed executing command: $CMD"
               return 1
           fi
           PDF_LIST=$PDF_LIST" "$PDF_FILE
       done < $FGTEST_LIST
       CMD=$(pdftk $PDF_LIST cat output $REPORT_PDFALL)
       eval $CMD
       [ -h $REPORT_HOMEDIR/fgtest_report.pdf ] || ln -s ../$REPORT_PDFALL $REPORT_HOMEDIR/fgtest_report.pdf 
       PDF_ROW="<p>You can download a PDF version of this report clicking <a href=\"fgtest_report.pdf\">here</a></p>"
       sed -i "/<!-- PDF report -->/a ${PDF_ROW}" $REPORT_HOMEDIR/$REPORT_INDEX
    fi
    return 0
}

# Close all opened resources before to exit
fgtest_close() {
    rm -f $FGTEST_OUT $FGTEST_ERR $FGTEST_LIST
}

#
# Code
#

# Initialize test environment
fgtest_init

# Perorm tests
fgtest_user &&
fgtest_ptv &&
fgtest_fg &&
fgtest_asd &&
fgtest_newinfra &&
fgtest_viewinfras &&
fgtest_viewinfra &&
fgtest_modinfra &&
fgtest_delinfra &&
fgtest_newapp &&
fgtest_viewapps &&
fgtest_viewapp &&
fgtest_modapp &&
fgtest_delapp &&
fgtest_newtask &&
fgtest_viewtasks &&
fgtest_viewtask &&
fgtest_viewtaskinp &&
fgtest_taskinpfile &&
fgtest_dwnldinpfile &&
fgtest_runtimedataset &&
fgtest_runtimedataget &&
fgtest_dwnldoutfile &&
fgtest_deletetask || echo "Error while perfomring test package: $TEST_PKG"

# Generate PDF reports
fgtest_mkpdf

# Close the test environment
fgtest_close
