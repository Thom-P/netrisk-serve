#!/bin/bash
/usr/local/app/seiscomp/bin/seiscomp exec import_inv fdsnxml $1/$2 /usr/local/app/seiscomp/etc/inventory/$2
/usr/local/app/seiscomp/bin/seiscomp --asroot update-config inventory
/usr/local/app/seiscomp/bin/seiscomp --asroot reload fdsnws
