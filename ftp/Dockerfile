FROM debian:12-slim

RUN <<EOF
    apt update && apt upgrade
    apt install -y vsftpd db-util
    rm -rf /var/lib/apt/lists/*
EOF

# Setup vsftpd (v)users and data directory
RUN <<EOF
    mkdir /etc/vsftpd
    mkdir -p -m 600 /var/run/vsftpd/empty
    useradd --home-dir /home/vsftpd --gid nogroup -m --shell /usr/sbin/nologin vsftpd
    mkdir -p /data/ftp && chown vsftpd:nogroup /data/ftp
    echo -n | db_load -T -t hash /etc/vsftpd/vsftpd-virtual-user.db
    chmod 600 /etc/vsftpd/vsftpd-virtual-user.db
EOF
# /etc/vsftpd now mounted to volume in docker compose
# db load creates empty berkeley db file

# PAM configuration for virtual users (stations) authentication
RUN cat > /etc/pam.d/vsftpd <<EOF
auth       required     pam_userdb.so db=/etc/vsftpd/vsftpd-virtual-user
account    required     pam_userdb.so db=/etc/vsftpd/vsftpd-virtual-user
session    required     pam_loginuid.so
EOF

COPY vsftpd.conf start_vsftpd.sh ./

ENTRYPOINT ["./start_vsftpd.sh"]
