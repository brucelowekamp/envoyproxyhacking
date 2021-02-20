#FROM envoyproxy/envoy-dev:latest
FROM mcr.microsoft.com/oss/envoyproxy/envoy:v1.17.0

COPY ./envoy.yaml /etc/envoy.yaml
RUN chmod go+r /etc/envoy.yaml

#CMD ["envoy.exe", "-c /envoy.yaml", "-l", "trace"]
CMD ["/usr/local/bin/envoy", "-c /etc/envoy.yaml", "-l", "debug"]
