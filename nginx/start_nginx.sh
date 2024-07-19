#!/bin/bash

# Create auth data to access the user interface (SHA-256)
printf "$UI_USER:$(openssl passwd -5 $UI_PASSWD)\n" >> /etc/nginx/.htpasswd

# Start nginx as foreground process
exec nginx -g 'daemon off;'