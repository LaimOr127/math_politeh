FROM nginx:1.30.6-alpine

COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY site/ /usr/share/nginx/html/site/
COPY lessons/output/ /usr/share/nginx/html/lessons/output/
RUN chmod -R a+rX /usr/share/nginx/html/site /usr/share/nginx/html/lessons/output

EXPOSE 80
