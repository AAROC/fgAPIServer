#!/bin/bash
# 
# patch_apply.sh - Apply available patches to APIServerDaemon DB
#
# Author: Riccardo Bruno <riccardo.bruno@ct.infn.it>
#
. patch_functions.sh

DEFAULTDBVER="0.0.1" # Baseline setup version

ts() {
  date +%Y%m%d%H%M%S
}

out() {
  TS=$(ts)
  echo "$TS $*"
}

err() {
  TS=$(ts)
  echo "$TS $*" >&2
}

local_exec() {
  OUT=$(mktemp /tmp/patch_out_XXXXXX)
  ERR=$(mktemp /tmp/patch_err_XXXXXX)
  $* >$OUT 2>$ERR
  while read ln; do
    out "$ln"
  done < $OUT
  while read ln; do
    err "$ln"
  done < $ERR
  rm -f $OUT
  rm -f $ERR
}

get_dbver() {
  DBVER=$(asdb_cmd "select version from db_patches order by id desc limit 1;" 2>/dev/null)
  if [ "$DBVER" = "" ]; then
    DBVER=$DEFAULTDBVER
  fi
  echo $DBVER
}


#
# Apply patches
#

# Get current DB version
DBVER=$(get_dbver)
out "Current DB version: $DBVER"
# Build the list of patches to apply
DBVERVAL=$(echo $DBVER | awk -F'.' '{ print 1000000*$1+1000*$2+$3 }')
DBPATCHES=$(/bin/ls -1 *.sh |\
            grep -E '[0-9]+\.sh' |\
            awk -F'_' '{ print $2 }' |\
            awk -F'.' -v dbverval=$DBVERVAL '{ if(1000000*$1+1000*$2+$3 > dbverval) print $1"."$2"."$3}')
out "Selected patch versions: '"$(echo $DBPATCHES | sed s/\ /,\ /g)"'"
# Apply selected patches
COUNT=0
STOPPED=0
for ver in $DBPATCHES
do
  out "Executing: patch_${ver}.sh"
  chmod +x patch_${ver}.sh
  local_exec "./patch_${ver}.sh" > ./patch_${ver}.log
  # Verify patch
  DBVER=$(get_dbver)
  DBVERVAL=$(echo $DBVER | awk -F'.' '{ print 1000000*$1+1000*$2+$3 }')
  PCVERVAL=$(echo $ver | awk -F'.' '{ print 1000000*$1+1000*$2+$3 }')
  if [ "$DBVERVAL" != "$PCVERVAL" ]; then
    err "An error occurred while applying patch $ver"
    err "Exiting"
    STOPPED=1
    break
  else
    COUNT=$((COUNT+1))
    DBVER=$ver
  fi
done
# Report about execution
if [ $STOPPED -ne 0 ]; then
  err "Patching has been interrupted while executing patch_$ver.sh file"
  err "Please verify its content and the patch_$ver.log file"
  err "Then try to complete its execution manually and retry to"
  err "apply patches"
else
  out "Applied $COUNT patches"
  out "DB is now version $DBVER"
  out "Done"
fi

