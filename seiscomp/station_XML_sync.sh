#!/bin/bash
if [ $3 = "IN_CLOSE_WRITE" ]; then
    /usr/local/app/seiscomp/bin/seiscomp exec import_inv fdsnxml $1/$2 /usr/local/app/seiscomp/etc/inventory/$2
elif [ $3 = "IN_DELETE" ]; then
    rm /usr/local/app/seiscomp/etc/inventory/$2
fi
/usr/local/app/seiscomp/bin/seiscomp --asroot update-config inventory
/usr/local/app/seiscomp/bin/seiscomp --asroot reload fdsnws
