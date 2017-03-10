#!/bin/bash
#
# patch_0.0.10.sh
#
# This patch includes the following features: 
#
# - Enabling infrastructure based APIs 
#

# Include functions
. ./patch_functions.sh

PATCH="0.0.10"
PATCH_DESC="Enabling infrastructure based APIs"
check_patch $PATCH

# Create a temporary SQL file
SQLTMP=$(mktemp /tmp/patch_${PATCH}_XXXXXX)

#
# Alter columns/tables
#

out "Adding unassigned infrastructure application (app_id=0)"
out "Changing group name 'generic user' to 'users'";
out "Adding group developers and assigning all privileges"
out "Adding all applications to developers group"
cat >$SQLTMP <<EOF
set session sql_mode='NO_AUTO_VALUE_ON_ZERO';
insert into application (id,name,description,outcome,creation,enabled) values (0,'infrastructure','unassigned infrastructure','INFRA',now(), false);
update fg_group set name='users' where name='generic user';
insert into fg_group (name,creation,modified) values ('developers',now(),now());
insert into fg_group_role (group_id,role_id,creation)
select (select id from fg_group where name='developers'),id,now() from fg_role;
insert into fg_group_apps (group_id, app_id, creation)
select (select id from fg_group where name='developers'),id,now() from application;
EOF
asdb_file $SQLTMP

out "Removing foreign key in infrastructure_parameter"
out "Adding index to fg_user(name)"
SQLCMD="SELECT CONSTRAINT_NAME FROM information_schema.TABLE_CONSTRAINTS WHERE information_schema.TABLE_CONSTRAINTS.CONSTRAINT_TYPE = 'FOREIGN KEY'AND information_schema.TABLE_CONSTRAINTS.TABLE_SCHEMA = '"$ASDB_NAME"' AND information_schema.TABLE_CONSTRAINTS.TABLE_NAME = 'infrastructure_parameter'"
FKNAME=$(asdb_cmd "$SQLCMD")
out "foreign key name: '"$FKNAME"'"
cat >$SQLTMP <<EOF
alter table infrastructure_parameter drop foreign key $FKNAME;
alter table fg_user add index fg_user(name);
EOF
asdb_file $SQLTMP

out "Database changed"
out ""

# Removing SQL file
rm -f $SQLTMP

out "registering patch $PATCH"
register_patch "$PATCH" "patch_${PATCH}.sh" "$PATCH_DESC"
out "patch registered"

