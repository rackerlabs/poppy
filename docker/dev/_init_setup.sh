#!/bin/bash

# "Upsert" sni config
python /poppy/scripts/providers/akamai/san_cert_info/cassandra/upsert_sni_cert_info.py --config-file /etc/poppy.conf


# Create a default flavor
curl --include \
     --request POST \
     --header "Content-Type: application/json" \
     --header "X-Project-ID: 000" \
     --data-binary '{
    "id" : "cdn",
    "limits": [{
        "origins": {
            "min": 1,
            "max": 5
        },
        "domains" : {
            "min": 1,
            "max": 5
        },
        "caching": {
            "min": 3600,
            "max": 604800,
            "incr": 300
        }
    }],
    "providers" : [
        {
            "provider" : "akamai",
            "links": [
                {
                    "href": "http://www.akamai.com",
                    "rel": "provider_url"
                }
            ]
        },

    ]
}' "http://localhost:8888/v1.0/flavors"
