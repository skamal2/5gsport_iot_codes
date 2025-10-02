
WIFI_SSID = "****"
WIFI_PASSWORD = "****"


# password.py
NTRIP_CONFIG = {
    "host": "caster",
    "port": 2101,
    "mountpoint": "VRS",
    "username_ntrip": "user",
    "password_ntrip": "pass",
    "enabled": True
}

MQTT_CONFIG = {
    "server": "5gsport.duckdns.org",
    "port": 443,   # or 8883 for LAN
    "username": "****",
    "password": "*****",
    "ssl_params": {
        "server_hostname": "5gsport.duckdns.org",
        "ca_path": "certs/isrgrootx1.der"  # <--- Add this
    },
    "wan_ip": "194.110.231.219",  # optional fallback or ip can be 194.110.231.222
}

























