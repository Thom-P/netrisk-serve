FROM nginx:1.26.1-bookworm

COPY nginx.conf /etc/nginx/nginx.conf
COPY ./start_nginx.sh ./

RUN apt update && apt upgrade -y

# nginx does not react to default docker sigterm, to debug (actually already in nginx image?)
#STOPSIGNAL SIGQUIT

ENTRYPOINT [ "./start_nginx.sh" ]
