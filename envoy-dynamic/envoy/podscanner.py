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
header = None
queryparam = None
poll_s = None

with open (CONFIG_FILE) as f:
  config = yaml.load(f, Loader=yaml.BaseLoader)
  cds_filename = config['cdsfile']
  lds_filename = config['ldsfile']
  header = config['header']
  queryparam = config['queryparam']
  poll_s = int(config['poll_seconds'])
  name = config['services'][0]['name']
  port = config['services'][0]['port']

assert cds_filename is not None
assert lds_filename is not None
assert name is not None
assert port is not None
assert header is not None
assert queryparam is not None
assert poll_s is not None

CDS_INTRO = """resources:
- "@type": type.googleapis.com/envoy.config.cluster.v3.Cluster
  name: {name}-metadata
  connect_timeout: 10s
  type: STATIC
  lb_policy: ROUND_ROBIN
  lb_subset_config:
    fallback_policy: ANY_ENDPOINT
    subset_selectors:
      - keys:
           - node
        single_host_per_subset: true
  load_assignment:
    cluster_name: {name}lbmetadata
    endpoints:
    - lb_endpoints:"""

CDS_HOST = """      - endpoint:
          address:
            socket_address:
              address: {ip}
              port_value: {port}
        metadata:
          filter_metadata:
            envoy.lb:
              node: "{id}"
"""

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
            - name: envoy.lua
              typed_config:
                "@type": type.googleapis.com/envoy.extensions.filters.http.lua.v3.Lua
                inline_code: |
                  function envoy_on_request(request_handle)
                    function urldecode(s)
                      s = s:gsub('+', ' ')
                          :gsub('%%(%x%x)', function(h)
                                              return string.char(tonumber(h, 16))
                                            end)
                      return s
                    end
                    function findnode(s)
                      for k,v in s:gmatch('([^&=?]-)=([^&=?]+)' ) do
                        if k == "{queryparam}" then
                          return urldecode(v)
                        end
                      end
                      return nil
                    end
                    if request_handle:headers():get("{header}") ~= nil then
                      return
                    end
                    local nodespec = findnode(request_handle:headers():get(":path"))
                    if nodespec ~= nil then
                      request_handle:headers():add("{header}", nodespec)
                    end
                  end
            - name: envoy.filters.http.header_to_metadata
              typed_config:
                "@type": type.googleapis.com/envoy.extensions.filters.http.header_to_metadata.v3.Config
                request_rules:
                  - header: "{header}"
                    on_header_present:
                      metadata_namespace: envoy.lb
                      key: node
                      type: STRING
                    remove: false
            - name: envoy.filters.http.router
          route_config:
              name: local_route
              virtual_hosts:
              - name: local_service
                domains: ["*"]
                routes:
                - match:
                    prefix: "/"
                  route:
                    cluster: {name}-metadata
"""

LDS_DEFAULT = ""

kubernetes.config.load_incluster_config()
v1 = kubernetes.client.CoreV1Api()

lastcds = None
lastlds = None

while True:
  # print ("scan")
  scan = v1.list_pod_for_all_namespaces(watch=False)
  cds = StringIO()
  lds = StringIO()
  print (CDS_INTRO.format(name=name, port=port, header=header, queryparam=queryparam), file=cds)
  print (LDS_INTRO.format(name=name, port=port, header=header, queryparam=queryparam), file=lds)
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
      #print (LDS_HOST.format(name=name, port=port, id=id, ip=ip), file=lds)
  print (LDS_DEFAULT.format(name=name, port=port), file=lds)

  newcds = cds.getvalue()
  newlds = lds.getvalue()

  if newcds != lastcds:
    print("update cds")
    with tempfile.NamedTemporaryFile(mode='w', prefix='cds', delete=False) as tempcds:
      print (newcds, file=tempcds)
      tempcds.close()
      os.rename(tempcds.name, cds_filename)
      lastcds = newcds
      sleep(1)
  if newlds != lastlds:
    print("update lds")
    with tempfile.NamedTemporaryFile(mode='w', prefix='lds', delete=False) as templds:
      print (newlds, file=templds)
      templds.close()
      os.rename(templds.name, lds_filename)
      lastlds = newlds
  sleep(poll_s)

