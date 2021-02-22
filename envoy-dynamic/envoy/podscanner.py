from io import StringIO
import kubernetes
import os
import tempfile
from time import sleep
import yaml

CONFIG_FILE = "/podscanner/podscanner.yaml"

cds_filename = None
lds_filename = None
name = None
port = None
poll_s = None

with open (CONFIG_FILE) as f:
  config = yaml.load(f, Loader=yaml.BaseLoader)
  cds_filename = config['cdsfile']
  lds_filename = config['ldsfile']
  poll_s = int(config['poll_seconds'])
  name = config['services'][0]['name']
  port = config['services'][0]['port']

assert cds_filename is not None
assert lds_filename is not None
assert name is not None
assert port is not None
assert poll_s is not None

CDS_INTRO = """resources:
- "@type": type.googleapis.com/envoy.config.cluster.v3.Cluster
  name: {name}
  connect_timeout: 10s
  type: STRICT_DNS
  # Comment out the following line to test on v6 networks
  dns_lookup_family: V4_ONLY
  load_assignment:
    cluster_name: {name}
    endpoints:
    - lb_endpoints:
      - endpoint:
          address:
            socket_address:
              address: {name}
              port_value: {port}"""
CDS_HOST = """- "@type": type.googleapis.com/envoy.config.cluster.v3.Cluster
  name: {name}-{id}
  connect_timeout: 10s
  type: STATIC
  load_assignment:
    cluster_name: {name}-{id}
    endpoints:
    - lb_endpoints:
      - endpoint:
          address:
            socket_address:
              address: {ip}
              port_value: {port}"""

LDS_INTRO = """resources:
- "@type": type.googleapis.com/envoy.config.listener.v3.Listener
  name: listener_0
  address:
    socket_address:
      address: 0.0.0.0
      port_value: 80
  filter_chains:
  - filters:
      - name: envoy.filters.network.http_connection_manager
        typed_config:
          "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
          stat_prefix: ingress_http
          access_log:
          - name: envoy.access_loggers.file
            typed_config:
              "@type": type.googleapis.com/envoy.extensions.access_loggers.file.v3.FileAccessLog
              path: /dev/stdout
          http_filters:
          - name: envoy.filters.http.router
          route_config:
            name: local_route
            virtual_hosts:
            - name: local_service
              domains: ["*"]
              routes:"""

LDS_HOST = """              - match:
                  headers:
                    - name: "X-node"
                      exact_match: "{id}"
                  prefix: "/"
                route:
                  cluster: {name}-{id}"""


LDS_DEFAULT = """              - match:
                  prefix: "/"
                route:
                  cluster: {name}"""

kubernetes.config.load_incluster_config()
v1 = kubernetes.client.CoreV1Api()

lastcds = None
lastlds = None

while True:
  # print ("scan")
  scan = v1.list_pod_for_all_namespaces(watch=False)
  cds = StringIO()
  lds = StringIO()
  print (CDS_INTRO.format(name=name, port=port), file=cds)
  print (LDS_INTRO.format(name=name, port=port), file=lds)
  for i in scan.items:
    #print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))
    if i.metadata.name.startswith(name):
      # str.removeprefix() requires py3.9 :(
      id = i.metadata.name.replace(name+"-", "")
      ip = i.status.pod_ip
      if ip is None:
        # pod still initializing
        continue
      #print("%s\t%s" % (n, ip))
      print (CDS_HOST.format(name=name, port=port, id=id, ip=ip), file=cds)
      print (LDS_HOST.format(name=name, port=port, id=id, ip=ip), file=lds)
  print (LDS_DEFAULT.format(name=name, port=port), file=lds)

  newcds = cds.getvalue()
  newlds = lds.getvalue()

  if newcds != lastcds or newlds != lastlds:
    print("update clusters")
    with tempfile.NamedTemporaryFile(mode='w', prefix='cds', delete=False) as tempcds:
      with tempfile.NamedTemporaryFile(mode='w', prefix='lds', delete=False) as templds:
        print (newcds, file=tempcds)
        print (newlds, file=templds)
        tempcds.close()
        templds.close()
        os.rename(tempcds.name, cds_filename)
        os.rename(templds.name, lds_filename)
        lastcds = newcds
        lastlds = newlds
  sleep(poll_s)

