#!/bin/bash

if [ -f "SETUP_COMPLETED" ]; then
    echo "SeisComP setup previously executed, skipping setup step."
else
    # Run seiscomp setup at first container start only (otherwise overwrites inventory)
    seiscomp/bin/seiscomp --asroot setup <<EOF
$SECTION
$COMMON_NAME
$ORGANIZATION
yes
0
no
$DATABASE_NAME
sc_mariadb
$USER_NAME
$USER_PASSWD
sc_mariadb
$USER_NAME
$USER_PASSWD
P
EOF
    touch "SETUP_COMPLETED"
fi

# Enable Web Services
seiscomp/bin/seiscomp --asroot enable fdsnws

# Start all necessary processes
service incron start # Daemon to trigger myo to mseed conversion and SDS archiving routines
seiscomp/bin/seiscomp --asroot start scmaster # Run Seiscomp master as background process
seiscomp/bin/seiscomp --asroot update-config # Only needed for added init data in Dockerfile
seiscomp/bin/seiscomp --asroot exec fdsnws # Run Web services as foreground process to keep container up

# Seiscomp setup questions (for reference)
# Agency ID []:
# Datacenter ID []:
# Organization string []:
# Enable database storage. [yes]:
#  0) mysql/mariadb
#       MySQL/MariaDB server.
#  1) postgresql
#       PostgresSQL server version 9 or later.
#  2) sqlite3
#       SQLite3 database.
# Database backend [0]:
# Create database [yes]:
# Database name. [seiscomp]:
# Database hostname. [localhost]:
# Database read-write user. [sysop]:
# Database read-write password. [sysop]:
# Database public hostname. [localhost]:
# Database read-only user. [sysop]:
# Database read-only password. [sysop]:
#
# Finished setup
# --------------
#
# P) Proceed to apply configuration
# B) Back to last parameter
# Q) Quit without changes
# Command? [P]: p
