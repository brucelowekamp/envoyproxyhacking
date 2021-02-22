/usr/local/bin/envoy -c /etc/envoy/envoy.yaml -l debug &
python3 /podscanner.py &
wait
