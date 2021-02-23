/usr/local/bin/envoy -c /etc/envoy/envoy.yaml &
python3 /podscanner.py &
wait -n
