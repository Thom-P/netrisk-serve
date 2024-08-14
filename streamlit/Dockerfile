FROM python:3.11-slim

RUN <<EOF
    apt update && apt upgrade
    apt install -y libdb-dev gcc
    rm -rf /var/lib/apt/lists/*
EOF

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

# might just need python3-dev
#libdb dev, gcc

COPY app ./
#HEALTHCHECK ? see streamlit docker
ENTRYPOINT ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
