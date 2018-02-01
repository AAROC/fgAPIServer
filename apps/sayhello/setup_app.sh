#!/bin/bash
#
# Setup script for sayhello application
#
# This example uses API specs to install sayhello application
# Use it to install your own FutureGateway application
#
# Author: Riccardo Bruno <riccardo.bruno@ct.infn.it>
#
TKN="<place token here>"
API_URL="http://localhost:8888/v1.0"
HDR_APPJSON="-H \"Content-Type: application/json\""
HDR_AUTHBRR="-H \"Authorization: Bearer ${TKN}\""
JSON_OUT=$(mktemp)
POST_DATA=$(mktemp)
cat >$POST_DATA <<EOF
{
	"infrastructures": [1],
	"parameters": [{
		"name": "target_executor",
		"value": "GridEngine",
		"description": "CSGF JSAGA Based executor interface"
	}, {
		"name": "jobdesc_executable",
		"value": "sayhello.sh",
		"description": ""
	}, {
		"name": "jobdesc_output",
		"value": "stdout.txt",
		"description": ""
	}, {
		"name": "jobdesc_error",
		"value": "stderr.txt",
		"description": ""
	}],
	"enabled": true,
	"files": [{
		"name": "sayhello.sh"
	}, {
		"name": "sayhello.txt"
	}],
	"name": "sayhello",
	"description": "sayhello tester application"
}
EOF

# Install application
HEADERS=$HDR_APPJSON" "$HDR_AUTHBRR
CMD="curl $HEADERS -X POST -d @$POST_DATA $API_URL/applications"
echo "Executing: '"$CMD"'"
echo "POST_DATA: '"$(cat $POST_DATA)"'"
eval $CMD > $JSON_OUT
echo "Output: '"$(cat $JSON_OUT)"'"
APP_ID=$(cat $JSON_OUT | jq '.id' | xargs echo)
echo "AppId: '"$APP_ID"'"

# View input files
HEADERS=$HDR_AUTHBRR
CMD="curl $HEADERS  $API_URL/applications/$APP_ID/input"
echo "Executing: '"$CMD"'"
eval $CMD > $JSON_OUT
echo "Output: '"$(cat $JSON_OUT)"'"

# Upload input files
FILES=(sayhello.sh\
       sayhello.txt)
for file in ${FILES[*]}; do
    HEADERS=$HDR_AUTHBRR
    CMD="curl $HEADERS -F \"file[]=@$file\" $API_URL/applications/$APP_ID/input"
    echo "Executing: '"$CMD"'"
    eval $CMD > $JSON_OUT
    echo "Output: '"$(cat $JSON_OUT)"'"
done

# View again input files
HEADERS=$HDR_AUTHBRR
CMD="curl $HEADERS  $API_URL/applications/$APP_ID/input"
echo "Executing: '"$CMD"'"
eval $CMD > $JSON_OUT
echo "Output: '"$(cat $JSON_OUT)"'"

# Print how to submit the app
HEADERS=$HDR_APPJSON" "$HDR_AUTHBRR
cat >$POST_DATA <<EOF
{"application":"${APP_ID}", "description":"sayhello ${APP_ID} test run", "arguments": ["this is the argument"], "output_files": [{"name": "sayhello.data"}]}
EOF
CMD="curl $HEADERS -X POST -d '"$(cat $POST_DATA)"' $API_URL/tasks"
echo ""
echo "To execute the application with id: $APP_ID, use:"
echo $CMD
# Print how to view task info
HEADERS=$HDR_AUTHBRR
CMD="curl $HEADERS $API_URL/tasks/<task_id>"
echo ""
echo "To view task details use:"
echo $CMD

rm -f $JSON_OUT
rm -f $POST_DATA
