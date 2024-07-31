#!/bin/bash
# Add initial station if defined in .env
#if [[ -z "$STATION_NAME" ]] || [[ -z "$STATION_PASSWD" ]]; then
#    echo "Initial station name or password empty, skipping station creation..."
#else
#    echo -n "Creating $STATION_NAME virtual vsftpd user..."
#    mkdir "/data/ftp/$STATION_NAME" && chown vsftpd:nogroup "/data/ftp/$STATION_NAME"
#    cat > /etc/vsftpd/vusers.txt <<EOF
#$STATION_NAME
#$STATION_PASSWD
#EOF
#    db_load -T -t hash -f /etc/vsftpd/vusers.txt /etc/vsftpd/vsftpd-virtual-user.db # todo need to save user database in persistent volume!
#    chmod 600 /etc/vsftpd/vsftpd-virtual-user.db
#    rm /etc/vsftpd/vusers.txt
#    echo "done"
#fi

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


# Start vsftpd as foreground process, exec for replacing bash PID and receive docker signals
exec /usr/sbin/vsftpd vsftpd.conf
