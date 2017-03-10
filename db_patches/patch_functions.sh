#!/bin/bash
#
# Database patch functions
#
export ASDB_USER=fgapiserver
export ASDB_PASS=fgapiserver_password
export ASDB_HOST=localhost
export ASDB_PORT=3306
export ASDB_NAME=fgapiserver


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

asdb_file() {
  SQLFILE=$1
  SQLOUT=$2
  SQLERR=$3
  if [ "$SQLOUT" = "" ]; then
    SQLOUTCMD=""
  else
    SQLOUTCMD="1>$SQLOUT"
  fi
  if [ "$SQLERR" = "" ]; then
    SQLERRCMD=""
  else
    SQLERRCMD="2>$SQLERR"
  fi
  if [ "$SQLFILE" != "" -a -f $SQLFILE ]; then
    mysql -h $ASDB_HOST -P $ASDB_PORT -u $ASDB_USER -p$ASDB_PASS $ASDB_NAME < $SQLFILE $SQLOUTCMD $SQLOUTERR
  fi
}

asdb_cmd() {
  SQLCMD=$1
  if [ "$SQLCMD" != "" ]; then
    mysql -h $ASDB_HOST -P $ASDB_PORT -u $ASDB_USER -p$ASDB_PASS $ASDB_NAME  -s -N -e "$SQLCMD"
  fi
}

register_patch() {
  PATCHVER=$1
  PATCHFILE=$2
  PATCHDESC=$3

  SQL=$(mktemp /tmp/patch_regpatch_XXXXXX)
  cat >$SQL <<EOF
insert into db_patches (id,version,name,file,applied) select if(max(id) is NULL,1,max(id)+1),'${PATCHVER}','${PATCHDESC}','${PATCHFILE}',now() from db_patches;
EOF
  asdb_file $SQL
  rm -f $SQL
}

get_dbver() {
  DBVER=$(ASDB_OPTS="-N -s"; asdb "select max(version) from db_patches;" 2>/dev/null)
  if [ "$DBVER" = "" ]; then
    DBVER=$DEFAULTDBVER
  fi
  echo $DBVER
}

check_patch() {
  VER=$1
  VERCHK=$(asdb_cmd "select count(*) from db_patches where version=\"$VER\"")
  if [ "$FORCE_PATCH" != "" -a "$VERCHK" != "" -a $VERCHK -ne 0 ]; then
    out "Patch $VER already applied"
    exit 1
  else
    out "Appliying patch $VER"
  fi
}
