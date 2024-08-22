#!/bin/bash
# Generate ssl certificate if first start (could also check if expired)
if [[ -f "/etc/ssl/certs/netrisk.key" ]]; then
    echo "Using previously created ssl certificate."
else
    echo "Creating a new ssl certificate..."
    <<EOF openssl req -x509 -nodes -days 3650 -newkey rsa:2048 -keyout /etc/ssl/certs/netrisk.key -out /etc/ssl/certs/netrisk.pem
$COUNTRY_CODE
$STATE
$LOCALITY
$ORGANIZATION
$SECTION
$COMMON_NAME
$EMAIL_ADRESS
EOF
fi

# Start vsftpd as foreground process, exec for replacing bash PID and receive docker signals (works only if init: true in compose(?))
exec /usr/sbin/vsftpd vsftpd.conf

# alternative way to catch TERM signal without init: true (which is better?)
# signal trap function inspired by https://github.com/panubo/docker-vsftpd/blob/main/entry.sh
#vsftpd_stop() {
#  echo "Received SIGINT or SIGTERM. Shutting down vsftpd"
#  # Get PID
#  pid="$(cat /var/run/vsftpd/vsftpd.pid)"
#  # Set TERM
#  kill -SIGTERM $pid
#  # Wait for exit
#  wait $pid
#  # All done.
#  echo "Done"
#}

#trap vsftpd_stop SIGINT SIGTERM
#echo "Starting vsftpd"
#/usr/sbin/vsftpd vsftpd.conf &
#pid=$!
#echo $pid > /var/run/vsftpd/vsftpd.pid
#wait $pid && exit $?
