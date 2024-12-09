# Netrisk serve
_(under development)_

Netrisk-serve is a self-hosted web application designed to manage a network of NETRISK stations. The application contains three main components:
 - an FTP server (vsftpd) to receive the raw data sent by the NETRISK stations at regular intervals.
 - a SeisComP installation to convert and archive the data into an SDS structure, and to serve FDSNWS HTTP requests (stations, dataselect, availability).
 - a user interface for managing the stations FTP accounts and metadata (stationXML), interactive visualization of the data, format conversion, and download.

## Installation
The installation is intended to be user-friendly and platform independent thanks to the use of Docker containers.

_(instructions to come)_
