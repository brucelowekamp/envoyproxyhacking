python3 /podscanner.py &
sleep 10
/usr/local/bin/envoy -c /etc/envoy/envoy.yaml &
wait -n
