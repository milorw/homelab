import json
import yaml
from string import Template
from schema import Schema, And, Use, Optional, Or
import re

### TEMPLATES ###

cf_dns_t = Template("""
(${cf_var}) {
  tls {
    dns cloudflare {env.${api_key_path}}
  }
}
""")

service_t = Template("""
(${service_var}) {
bind ${tailscale_ip}
encode ${encodings}
${reverse_proxies}
}
""")

rproxy_t = Template("""
reverse_proxy ${path} ${ip}:${port}
""")

mixer_t = Template("""
${service}.${domain} {
  import ${cf_var}
  import ${service_var}
}
""")

### VALIDATION SCHEMAS ###

IP_REGEX = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$|localhost"

main_yaml = Schema({
    'tailscale_ip': And(str, lambda s: re.match(IP_REGEX, s)),

    'cf_setup': And(
        dict, lambda d: len(d) > 0,
        {
            And(str, Use(lambda k: "cf_" + k)): {
                'env_name': str
                }
        }
    ),

    'services': And(
            dict,
            lambda d: len(d) > 0,             
            {
                And(str, Use(lambda k: k + "_common")): {
                    Optional('encodings'): [str], 
                    'reverse_proxy': And(
                        list,
                        lambda l: len(l) > 0,  
                        [{                     
                            'address': And(str, lambda s: re.match(IP_REGEX, s)),
                            'port': int,
                            Optional('path'): str
                        }]
                    )
                }
            }
        )
    })

# TODO: Use() partially works, but I do need the raw service later, so probably adjust this
# might be worth exporting the json structure to a parsed structure with everything I need set up

### MAIN FILE ###

with open('ip.yaml', 'r') as f:
    raw_data = yaml.load(f, Loader=yaml.SafeLoader)

# Validate the yaml file before processing
try: 
    data = main_yaml.validate(raw_data)
except SchemaError as e:
    print(f"Validation failed: {e}")




cf_vars = data['cf_setup'].keys()
services = data['services'].keys()
TAILSCALE_IP = data['tailscale_ip']

gen_file_str = ""

for cf, path in data['cf_setup'].items():
    gen_file_str += cf_dns_t.substitute(cf_var=cf, api_key_path=path['env_name'])

for service, fields in data['services'].items():
    rev = ""
    for raw_path in fields['reverse_proxy']:

        # get path, or empty string if DNE
        path=raw_path.get("path", "")

        rev += rproxy_t.safe_substitute(path=path,ip=raw_path["address"],port=raw_path["port"])

    gen_file_str += service_t.substitute(service_var=service, tailscale_ip=TAILSCALE_IP, encodings=' '.join(fields['encodings']), reverse_proxies=rev)

for service in services:
    for cf in cf_vars:
        gen_file_str += mixer_t.substitute(service=service,domain=cf,cf_var=cf,service_var=service)


print(gen_file_str)
