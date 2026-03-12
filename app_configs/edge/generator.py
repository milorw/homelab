import json
import yaml
from string import Template
from schema import Schema, And, Use, Optional, Or
import re

### TEMPLATES ###

cf_dns_t = Template("""
(cf_${cf_var}) {
  tls {
    dns cloudflare {env.${api_key_path}}
  }
}
""")

service_t = Template("""
(${service}_common) {
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
  import ${common_var}
}
""")

### VALIDATION SCHEMAS ###

IP_REGEX = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$|localhost"

main_yaml = Schema({
    'tailscale_ip': And(str, lambda s: re.match(IP_REGEX, s)),

    'cf_setup': And(
        dict, lambda d: len(d) > 0,
        {
            str: {
                'env_name': str
                }
        }
    ),

    'services': And(
            dict,
            lambda d: len(d) > 0,             
            {
                str: {
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

### MAIN FILE ###

with open('ip.yaml', 'r') as f:
    data = yaml.load(f, Loader=yaml.SafeLoader)


try: 
    main_yaml.validate(data)
except SchemaError as e:
    print(f"Validation failed: {e}")




domain_list = data['cf_setup'].keys()
common_list = data['services'].keys()
TAILSCALE_IP = data['tailscale_ip']

gen_file_str = ""
for key, val in data['cf_setup'].items():
    gen_file_str += cf_dns_t.substitute(cf_var=key, api_key_path=val)




for key, val in data['services'].items():
    rev = ""
    for p in val['reverse_proxy']:
        path=p.get("path", "")
        rev += rproxy_t.safe_substitute(path=path,ip=p["address"],port=p["port"])

    gen_file_str += service_t.substitute(service=key, tailscale_ip=TAILSCALE_IP, encodings=' '.join(val['encodings']), reverse_proxies=rev)





for i in common_list:
    for b in domain_list:
        gen_file_str += mixer_t.substitute(service=i,domain=b,cf_var='cf_'+b,common_var=i+'_common')


print(gen_file_str)
