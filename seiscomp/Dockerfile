FROM debian:12

WORKDIR /usr/local/app

RUN <<EOF
    apt update && apt upgrade
    apt install -y \
        sudo \
        python3.11 \
        libpython3.11-dev \
        python3-pip \
        python3.11-venv \
        mariadb-client \
        incron
EOF

#RUN useradd seiscomp
#USER seiscomp

COPY seiscomp-6.4.3-debian-12-x86_64.tar.gz myo2mseed.py start_seiscomp.sh ./

# Install Seiscomp and create SDS archive directory at default location
RUN tar xzf ./seiscomp-6.4.3-debian-12-x86_64.tar.gz \
    && yes | seiscomp/bin/seiscomp install-deps base fdsnws \
    && mkdir -p seiscomp/var/lib/archive \
    && rm -rf /var/lib/apt/lists/*

# tmp: to remove in fine
COPY OG35.mseed ./
RUN seiscomp/bin/seiscomp exec scart -v -I /usr/local/app/OG35.mseed -i --with-filecheck --with-filename
#COPY OG35.xml ./
#RUN seiscomp/bin/seiscomp exec import_inv fdsnxml OG35.xml seiscomp/etc/inventory/OG35.xml

# Incrontab for handling myo files received via FTP from stations (conversion and archiving)
# Also for importing xml files created via UI to Seiscomp inventory
RUN echo root > /etc/incron.allow \
    && cat <<'EOF' | incrontab -
/data/ftp/ IN_CLOSE_WRITE /usr/local/app/obspy/bin/python /usr/local/app/myo2mseed.py $@/$#
/usr/local/app/mseed_segments/ IN_CLOSE_WRITE /usr/local/app/seiscomp/bin/seiscomp exec scart -v -I $@/$# -i /usr/local/app/seiscomp/var/lib/archive
/data/xml/ IN_CLOSE_WRITE /usr/local/app/seiscomp/bin/seiscomp exec import_inv fdsnxml $@/$# seiscomp/etc/inventory/$#
EOF
# need to add sync on xml removal

# Prepare venv for file conversion routine ( . is sh equiv of bash source)
RUN mkdir mseed_segments \
    && python3 -m venv obspy \
    && . obspy/bin/activate \
    && python3 -m pip install --upgrade pip \
    && python3 -m pip install obspy \
    && deactivate

ENTRYPOINT ["./start_seiscomp.sh"]
