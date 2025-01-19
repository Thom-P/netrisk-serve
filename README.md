# Netrisk serve
_(under development)_

Netrisk-serve is a self-hosted web application designed to manage a network of NETRISK stations. The application contains three main components:
 - an FTP server (vsftpd) to receive the raw data sent by the NETRISK stations at regular intervals.
 - a SeisComP installation to convert and archive the data into an SDS structure, and to serve FDSNWS HTTP requests (stations, dataselect, availability).
 - a user interface for managing the stations FTP accounts and metadata (stationXML), interactive visualization of the data, format conversion, and download.

## Installation
The installation is intended to be user-friendly and platform independent with the use of Docker containers.

### Requirements:

- __Machine:__ access to a self-hosted or cloud-hosted server with admin rights. Recommended minimal configuration: 2 Cores, 16 GB of RAM, and 12GB of storage for the system (plan plenty of extra storage for the data). A static public IP or a domain name pointing to your server IP is needed for the ftp transfers initiated by the stations.

- __Network:__ the firewall should be setup to allow the following network connections: tcp:443 for https, tcp:22 for ssh connection, tcp:21 for passive ftp connection, and a range of ~100 ports between ports 1024 and 65535 for ftp data transfer (e.g: tcp:7000-7100). __Take a note of the chosen ftp port range as it will be reused during the installation process.__

- __Software:__ The two pre-required softwares to be installed are [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) for the cloning of the current repo and [Docker Engine](https://docs.docker.com/engine/install/) for buiding and running the app containers.

### Configuration:

Clone the current repo and enter the app main directory:
 ```sh
 git clone https://github.com/Thom-P/netrisk-serve.git
 cd netrisk-serve
```

Copy the environment template to create your private .env (hidden) file:
```sh
cp .env.template .env
```

Personalize your infos with the terminal editor of your choice (e.g, nano or vim):
```sh
vim .env
```
Keep note of the user interface credentials.






