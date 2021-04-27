# Envoy podscanner hack

This repo has code that evolved to dynamically generate a config so
?i=<nodeid> or X-node: <nodeid> could be used for Envoy proxy to route
to a specific instance.  It also shows how to use a consistent hash in
the proxy.  That code is in envoy-dynamic.

helloworld has a super-simple helloworld that also shows
tenant/user/key headers.

It was then extended to demo how a WASM extension could be used to
split megatenants across multiple buckets in the consistent hash.  The
extension code is in envoy-wasm.  That code is C++ and as a quick hack
I compiled it from within the examples/wasm-cc directory in the envoy
build tree.  So something like:

```
docker pull envoyproxy/envoy-build-ubuntu:3d0491e2034287959a292806e3891fd0b7dd2703
docker tag c9df40dfc10c envoyproxy/envoy-build-ubuntu:latest
docker run -it -v c:/cygwin64/home/bloweka/src:/src envoyproxy/envoy-build-ubuntu
<in container in envoy/examples/wasm-cc>
cp /src/envoyproxyhacking/envoy-wasm/* .
bazel build //examples/wasm-cc:tenant_filter_wasm.wasm
cp ~/envoy/bazel-bin/examples/wasm-cc/tenant_filter_wasm.wasm /src/envoyproxyhacking/envoy-wasm/
```

Currently the podscanner.py includes two port configurations with 8000
normal hashing and 8080 with the wasm plugin, which it assumes was
copied locally.

load-demo has some load generators used to show off performance of
user, tenant, and wasm-modified tenant hashing.  It also has the
sample files used during an IC3 presentation.
