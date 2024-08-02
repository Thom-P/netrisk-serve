#!/bin/bash
apt update && apt install procps -y
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

# signal trap function inspired by https://github.com/panubo/docker-vsftpd/blob/main/entry.sh
seiscomp_stop() {
  echo "Received SIGINT or SIGTERM: shutting down Seiscomp and Incron..."

  seiscomp/bin/seiscomp --asroot stop fdsnws
  seiscomp/bin/seiscomp --asroot stop scmaster
  service incron stop
  echo done
  exit
}

trap seiscomp_stop SIGINT SIGTERM

# Start all necessary processes
service incron start # Daemon to trigger myo to mseed conversion and SDS archiving routines
seiscomp/bin/seiscomp --asroot start scmaster # Run Seiscomp master as background process
seiscomp/bin/seiscomp --asroot start fdsnws # Run Web services as background to allow reload when inventory updates
pid_incron=$(cat /var/run/incrond.pid)
pid_scmaster=$(cat seiscomp/var/run/scmaster.pid)
pid_fdsnws=$(cat seiscomp/var/run/fdsnws.pid)
echo $pid_incron $pid_scmaster $pid_fdsnws
self_id=$$
echo $self_id
ps --ppid $self_id
echo "#####"
echo $BASHPID
ps --ppid $BASHPID
echo "#####"

sleep infinity &
pid_sleep1=$!
#wait -f $pid_incron $pid_scmaster $pid_fdsnws  && seiscomp_stop # if any of the process stops, call the stop procedure to exit gracefully
#wait -n $pid_sleep1 && seiscomp_stop
wait $pid_incron

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
