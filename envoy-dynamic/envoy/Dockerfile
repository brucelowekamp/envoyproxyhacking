#FROM envoyproxy/envoy-dev:latest
FROM mcr.microsoft.com/oss/envoyproxy/envoy:v1.17.0

# installing python3-pip brings in insane cruft!!!
RUN apt-get update && \
  apt-get install -y apt-utils && \
  apt-get install -y python3-pip curl dnsutils
RUN pip3 install kubernetes

COPY ./envoy.yaml /etc/envoy/envoy.yaml
COPY ./cds.yaml /var/lib/envoy/cds.yaml
COPY ./lds.yaml /var/lib/envoy/lds.yaml
COPY ./runboth.sh /runboth.sh
COPY ./podscanner.py /podscanner.py
RUN chmod go+r /etc/envoy/envoy.yaml
RUN chmod go+r /var/lib/envoy/cds.yaml
RUN chmod go+r /var/lib/envoy/lds.yaml
RUN chmod go+r /runboth.sh
RUN chmod go+r /podscanner.py

ENTRYPOINT ["/bin/bash", "/runboth.sh"]
