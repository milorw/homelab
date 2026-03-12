import json
import yaml
from string import Template
from textwrap import dedent, indent
from schema import Schema, And, Use, Optional, Or, SchemaError
import re

def strip_and_append(re1, text, append):
    matches = re.search(r"^(.*?)\.\w+$", text)
    return (matches.group(1) + append)

### TEMPLATES ###

cf_dns_t = Template(dedent("""\
(${cf_var}) {
  tls {
    dns cloudflare {env.${api_key_path}}
  }
}
"""))

service_t = Template(dedent("""\
(${service_var}) {
  bind ${tailscale_ip}
  encode ${encodings}
${reverse_proxies}
}
"""))

rproxy_empty_t = Template(dedent("""\
reverse_proxy ${path}${ip}:${port}
"""))

rproxy_t = Template(dedent("""\
reverse_proxy ${path}${ip}:${port} {
${headers}
}\
"""))

transport_http_t = Template(dedent("""\
transport_http {
  ${flag}
}
"""))

header_t = Template(dedent("""\
header_up ${header} ${flag}
"""))

mixer_t = Template(dedent("""\
${service}.${domain} {
  import ${cf_var}
  import ${service_var}
}
"""))

### VALIDATION SCHEMAS ###

IP_REGEX = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$|localhost"

main_yaml = Schema({
    'tailscale_ip': And(str, lambda s: re.match(IP_REGEX, s)),

    'domains': And(
        dict, lambda d: len(d) > 0,
        {
            str: [
                    {
                        'cf_env_name': str
                    }
                ]
        },
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
                            'address': And(str, lambda s: re.fullmatch(IP_REGEX, s) is not None),
                            'port': And(int, lambda p: 1 <= p <= 65535),
                            Optional('path'): str,
                            Optional('transport_http'): And(
                                str,
                                lambda s: s in {'tls_insecure_skip_verify'}
                            ),
                            Optional('headers'): {
                                str: Or(str, int, bool)
                            }
                    }]
                )
            }
        }
    )
})

### MAIN FILE ###

with open('ip.yaml', 'r') as f:
    raw_data = yaml.load(f, Loader=yaml.SafeLoader)

# Validate the yaml file before processing
try: 
    data = main_yaml.validate(raw_data)
except SchemaError as e:
    print(f"Validation failed: {e}")




'''
sanitized domain dictionary, containing a sub-dictionary of each domain's attributes:

EX:
{
    'domain1.me':
        {'cf_env_name': 'CF_API_TOKEN_domain1'},
    'domain2.com':
        {'cf_env_name': 'CF_API_TOKEN_domain2'}
}
'''
domain_attr = {}

for key, value in data['domains'].items():
    attributes = {}
    for atr in value:
        for key1, value1 in atr.items():
            attributes[key1] = value1

    domain_attr[key] = attributes


'''
sanitized services dictionary, containing a sub-dictionary of each services's attributes:

EX:
{
    'service1':
        {'attribute1: 'something'},
    'service2':
        {'attribute1': 'something'}
}
'''
service_attr = {}

for key, value in data['services'].items():
    service_attr[key] = value


TAILSCALE_IP = data['tailscale_ip']

gen_file_str = ""

cf = []
for domain, attr in domain_attr.items():
    cf.append(cf_dns_t.substitute(cf_var=strip_and_append(0, domain, "_cf"), api_key_path=attr['cf_env_name']))



services = []
for service, fields in service_attr.items():
    proxies = []
    for f in fields['reverse_proxy']:


        path = f.get("path","")
        path = f"{path} " if path else ""


        headers = f.get("headers", None)
        t = f.get("transport_http", None)
        hds = []

        if headers:
            for k, v in headers.items():
                hds.append(header_t.substitute(header=k, flag=str(v)))
                
            proxies.append(rproxy_t.safe_substitute(path=path, ip=f['address'], port=f['port'], headers=indent(''.join(hds), "  ")))
        else:
            proxies.append(rproxy_empty_t.substitute(path=path, ip=f['address'], port=f['port']))

    
    services.append(service_t.substitute(service_var=service, tailscale_ip=TAILSCALE_IP, encodings='  '.join(fields['encodings']), reverse_proxies=indent(''.join(proxies), "  ")))

mixers = []

for service in service_attr.keys():
    for key, value in domain_attr.items():
        mixers.append(mixer_t.substitute(service=service,domain=key,cf_var=strip_and_append(0, domain, "_cf"),service_var=service))


for c in cf:
    print(c)

for s in services:
    print(s)
for m in mixers:
    print(m)


