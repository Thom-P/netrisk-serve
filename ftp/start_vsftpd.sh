#!/bin/bash
# Generate ssl certificate (should do only once before first docker run instead?)
<<EOF openssl req -x509 -nodes -days 1825 -newkey rsa:2048 -keyout /etc/ssl/certs/netrisk.key -out /etc/ssl/certs/netrisk.pem
$COUNTRY_CODE
$STATE
$LOCALITY
$ORGANIZATION
$SECTION
$COMMON_NAME
$EMAIL_ADRESS
EOF

# Start vsftpd as foreground process, exec for replacing bash PID and receive docker signals (does not work)
#exec /usr/sbin/vsftpd vsftpd.conf

# signal trap function inspired by https://github.com/panubo/docker-vsftpd/blob/main/entry.sh
vsftpd_stop() {
  echo "Received SIGINT or SIGTERM. Shutting down vsftpd"
  # Get PID
  pid="$(cat /var/run/vsftpd/vsftpd.pid)"
  # Set TERM
  kill -SIGTERM $pid
  # Wait for exit
  wait $pid
  # All done.
  echo "Done"
}

trap vsftpd_stop SIGINT SIGTERM
echo "Starting vsftpd"
/usr/sbin/vsftpd vsftpd.conf &
#sleep infinity &
pid=$!
echo $pid > /var/run/vsftpd/vsftpd.pid
wait $pid && exit $?
