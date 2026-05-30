FROM nginx:1.31-alpine

# Drop default config
RUN rm /etc/nginx/conf.d/default.conf

COPY nginx.conf /etc/nginx/conf.d/wachturm.conf
COPY html/ /usr/share/nginx/html/

# Health check. Probe 127.0.0.1, NOT localhost: in this base image
# `localhost` resolves to IPv6 [::1], but nginx here listens IPv4-only
# (`listen 80;`), so a localhost probe gets Connection refused and the
# container flaps "unhealthy" while serving fine over the published
# IPv4 port. (The stock 10-listen-on-ipv6-by-default.sh no-ops here
# because this image removes the default.conf it would have edited.)
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://127.0.0.1/ || exit 1

EXPOSE 80
