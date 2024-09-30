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
        incron \
        cron \
        curl \
        procps
EOF

#RUN useradd seiscomp
#USER seiscomp

#COPY seiscomp-6.4.3-debian-12-x86_64.tar.gz ./
RUN curl -O "https://www.seiscomp.de/downloader/seiscomp-6.5.0-debian12-x86_64.tar.gz"

# Install Seiscomp and create SDS archive directory at default location
RUN tar xzf ./seiscomp-6.5.0-debian12-x86_64.tar.gz \
    && mkdir -p seiscomp/var/lib/archive \
    && yes | seiscomp/bin/seiscomp install-deps base fdsnws \
    && rm -rf /var/lib/apt/lists/*

RUN cp seiscomp/etc/defaults/fdsnws.cfg seiscomp/etc/ \
    && echo "dataAvailability.enable = True" >> seiscomp/etc/fdsnws.cfg \
    && echo "serveAvailability = True" >> seiscomp/etc/fdsnws.cfg \
    && echo "serveEvent = False" >> seiscomp/etc/fdsnws.cfg

# Incrontab for handling myo files received via FTP from stations (conversion and archiving)
# Also for importing xml files created via UI to Seiscomp inventory
RUN echo root > /etc/incron.allow \
    && cat <<'EOF' | incrontab -
/data/reload/ IN_CLOSE_WRITE,IN_ATTRIB incrontab --reload
/data/ftp/ IN_CLOSE_WRITE /usr/local/app/obspy/bin/python /usr/local/app/myo2mseed.py $@/$#
/usr/local/app/mseed_segments/ IN_CLOSE_WRITE /usr/local/app/seiscomp/bin/seiscomp exec scart -v -I $@/$# -i /usr/local/app/seiscomp/var/lib/archive
/data/xml/ IN_CLOSE_WRITE,IN_DELETE /usr/local/app/station_XML_sync.sh $@ $# $%
EOF
# first line to reload incron table at every new station dir creation (need to touch file within reload folder)
# need to add sync on xml removal
#/data/xml/ IN_CLOSE_WRITE /usr/local/app/seiscomp/bin/seiscomp exec import_inv fdsnxml $@/$# /usr/local/app/seiscomp/etc/inventory/$#

# Cron tab for running data availability update every hour
RUN cat <<'EOF' | crontab -
0 * * * * /usr/local/app/seiscomp/bin/seiscomp exec scardac
EOF

# Prepare venv for file conversion routine ( . is sh equiv of bash source)
RUN mkdir mseed_segments \
    && python3 -m venv obspy \
    && . obspy/bin/activate \
    && python3 -m pip install --upgrade pip \
    && python3 -m pip install obspy \
    && deactivate

COPY myo2mseed.py start_seiscomp.sh station_XML_sync.sh ./

ENTRYPOINT ["./start_seiscomp.sh"]
