# Envoy podscanner hack

Envoy is set up to balance traffic across all pods unless an X-node
header or urlparam is set to a node's id.  If that node exists,
traffic is proxied to it.  Otherwise the header is ignored and the
traffic forwarded randomly.

## Disclaimer
This is proof-of-concept.  Doesn't do TLS at all.  The config is
updated via a scanner in the same pod as envoy using files, which have
race conditions.  Would be better for scanner to be in its own pod and
use ADS between them to avoid race conditions.  (and avoid the current
build where installing pip3 to the envoy pod blows it up).  Runs
everything in the default namespace.  Adds pod read to the default
system serviceaccount rather than adding a different serviceaccount
with that role to the proxy pods.  Can be hardened in many other
ways...

Behavior at shutdown is undesirable because the pod still appears in
apiserver after it has stopped accepting connections (while it's busy
terminating), so requests timeout instead of being sent to an
available pod for a few seconds.  That can probably be fixed by
checking the status field.  But the entire shutdown process needs a
bit of work as in an ideal state a pod might stop taking random new
requests but still receive requests to state it still owns or knows
where to redirect to.

Implementation should fall back to consistent-hashed routing but at
present only does round-robin.

If envoy somehow parses the lds config before the cds config, it will
simply hang.  Moving to an ADS wire protocol would likely fix that.
Right now the runner starts podscanner and then waits 10s, assuming
both files have been written.  (and hoping that solves the problem)

## Structure
  The envoy dir is the docker build dir.  Uses envoy standard image
  and adds podscanner.py + python runtime.  Otherwise the service
  config comes in via k8s deployment tooling (envoy-deploy.yaml adds
  podscanner.yaml when creating the service).

podscanner.py (in the envoy image) is the key logic for updating the
config.  It polls the k8s api-server every 5 seconds and writes out
config files that establishes a "Cluster" that has each pod labeled
with metadata with its id.  The Listener is configured to copy the
urlparam (if present) to the header, then use the node header to route
to a pod with that metadata.  If there is no node header or if the
requested node is not found, round-robin routing is used.

The static config used by Envoy in this setup basically just tells it
to open an admin port (9902) and to read the two dynamic config files.
All services are configured by the dynamic files.  In theory
podscanner could support multiple services but at present it just
supports one.


## Example
```
$ curl -i http://52.224.134.231/hello
HTTP/1.1 200 OK
content-type: text/html; charset=utf-8
content-length: 56
server: envoy
date: Mon, 22 Feb 2021 17:41:42 GMT
x-envoy-upstream-service-time: 203

Hello version: v1, instance: helloworld-6554bc97f-9xqjw

bloweka@BLOWEKA-TPS ~/src/envoyproxyhacking/envoy-dynamic
$ curl -i http://52.224.134.231/hello
HTTP/1.1 200 OK
content-type: text/html; charset=utf-8
content-length: 56
server: envoy
date: Mon, 22 Feb 2021 17:41:43 GMT
x-envoy-upstream-service-time: 163

Hello version: v1, instance: helloworld-6554bc97f-n4sl5

$ curl -i -H "X-node: 6554bc97f-n4sl5" http://52.224.134.231/hello
HTTP/1.1 200 OK
content-type: text/html; charset=utf-8
content-length: 56
server: envoy
date: Mon, 22 Feb 2021 18:17:07 GMT
x-envoy-upstream-service-time: 132

Hello version: v1, instance: helloworld-6554bc97f-n4sl5

$ curl -i http://52.224.134.231/hello?node=6554bc97f-h8ghw
HTTP/1.1 200 OK
content-type: text/html; charset=utf-8
content-length: 56
server: envoy
date: Tue, 23 Feb 2021 19:02:53 GMT
x-envoy-upstream-service-time: 145

Hello version: v1, instance: helloworld-6554bc97f-h8ghw
```

## Configuration

To change the app, update podscanner.yaml then delete and re-add the
configmap.  As long as the service is deployed with <name>-<something>
as the podname, will work.  Note that podscanner.yaml is read and
deployed into the pod at configmap creation time and not every time
envoy is deployed.

## Install

```
kubectl create configmap podscannerconfig --from-file=podscanner.yaml # note changing configmaps is a PITA
kubectl apply -f podrbac.yaml
# runs the proxy but leaves it internal for testing with port-forward
kubectl apply -f envoy-deploy.yaml
# if you want to expose it 
kubectl apply -f envoy-loadbalancer.yaml
kubectl apply -f helloworld-5.yaml
```