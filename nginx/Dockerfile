FROM nginx:1.26.1-bookworm

COPY nginx.conf /etc/nginx/nginx.conf
COPY ./start_nginx.sh ./

RUN apt update && apt upgrade -y

ENTRYPOINT [ "./start_nginx.sh" ]