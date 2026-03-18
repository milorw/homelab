import json
import yaml
from string import Template
from textwrap import dedent, indent
from schema import Schema, And, Use, Optional, Or, SchemaError
import re
import os
from dotenv import load_dotenv, dotenv_values

INDENT = "  "

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
  bind ${ips}
  encode ${encodings}
${reverse_proxies}
}
"""))

rproxy_empty_t = Template(dedent("""\
reverse_proxy ${path}${ip}:${port}\
"""))

rproxy_t = Template(dedent("""\
reverse_proxy ${path}${ip}:${port} {
${headers}
${transport}
}\
"""))

tport_http_t = Template(dedent("""\
transport http {
  ${flag}
}\
"""))

header_t = Template(dedent("""\
header_up ${header} ${flag}\
"""))

mixer_t = Template(dedent("""\
${service}.${domain} {
  import ${cf_var}
  import ${service_var}
}
"""))

corefile_t = Template(dedent("""\
.:53 {
  errors
  log
  health
  ready

  hosts {
${hosts}
    fallthrough
  }
  forward . 1.1.1.1 8.8.8.8
  cache 30
}\
"""))


corefile_host_t = Template(dedent("""\
${tailscale_ip} ${domain_list}\
"""))


### VALIDATION SCHEMAS ###

IP_REGEX = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$|localhost"

def non_empty(x):
    return len(x) > 0

non_empty_list = And(list, non_empty)
non_empty_dict = And(dict, non_empty)

ip_address = And(str, lambda s: re.fullmatch(IP_REGEX, s) is not None)
port_number = And(int, lambda p: 1 <= p <= 65535)

headers_schema = {str: Or(str, int, bool)}

transport_schema = And(
    {
        Optional('tls_server_name'): str,
    },
    non_empty,
)

reverse_proxy_entry = {
    'address': str,
    'port': port_number,
    Optional('path'): str,
    Optional('transport'): transport_schema,
    Optional('headers'): headers_schema,
}

domain_entry = {
    'cf_env_name': str,
    'services': And(non_empty_list, [str]),
}


service_entry = {
    Optional('encodings'): [str],
    'reverse_proxy': And(non_empty_list, [reverse_proxy_entry]),
}

main_yaml = Schema({
    'caddyfile_path': str,
    'corefile_path': str,
    'tailscale_ip': And(str, lambda s: re.match(IP_REGEX, s)),
    'lan_ip': And(str, lambda s: re.match(IP_REGEX, s)),

    'domains': And(
        non_empty_dict,
        {str: domain_entry},
    ),
    'services': And(
        non_empty_dict,
        {str: service_entry},
    ),
})

### MAIN FILE ###

def main():
    load_dotenv()

    # load the yaml data
    with open(os.getenv("edge_router_config_path"), 'r') as f:
        raw_data = yaml.load(f, Loader=yaml.SafeLoader)

    # validate the yaml before processing
    try: 
        data = main_yaml.validate(raw_data)
    except SchemaError as e:
        print(f"Validation failed: {e}")

    TAILSCALE_IP = data['tailscale_ip']
    LAN_IP = data['lan_ip']
    CADDYFILE_PATH = data['caddyfile_path']
    COREFILE_PATH = data['corefile_path']

    domain_attr = {}
    for key, value in data['domains'].items():
        attributes = {}
        for key1, value1 in value.items():
            attributes[key1] = value1
        domain_attr[key] = attributes

    service_attr = {}
    for key, value in data['services'].items():
        service_attr[key] = value

    gen_corefile(service_attr, domain_attr, TAILSCALE_IP, LAN_IP, COREFILE_PATH)
    gen_caddyfile(service_attr, domain_attr, TAILSCALE_IP, LAN_IP, CADDYFILE_PATH)



def gen_corefile(service_attr, domain_attr, TAILSCALE_IP, LAN_IP, pth):
    hosts = []
    for domain, attr in domain_attr.items():
        services = []
        for service in service_attr.keys():
            if service in attr['services']:
                # append valid services for the domain
                services.append(f"{service}.{domain}")

        # create the tailscale ip -> services block for each domain
        hosts.append(
                corefile_host_t.substitute(
                    tailscale_ip=TAILSCALE_IP,
                    domain_list=' '.join(services)
                    ))
        hosts.append(
                corefile_host_t.substitute(
                    tailscale_ip=LAN_IP,
                    domain_list=' '.join(services)
                    ))

    # append each domain's block to main corefile
    with open(pth, 'w') as f:
        f.writelines(corefile_t.substitute(hosts=indent('\n'.join(hosts), "    ")))



def gen_caddyfile(service_attr, domain_attr, TAILSCALE_IP, LAN_IP, pth):
    cf = []
    services = []
    mixers = []
    
    # setup each domain's cloudflare api env block
    for domain, attr in domain_attr.items():
        cf.append(
            cf_dns_t.substitute(
                cf_var=strip_and_append(0, domain, "_cf"),
                api_key_path=attr['cf_env_name'],
            )
        )

    # build each service block
    for service, attr in service_attr.items():
        proxies = []

        # create a list of reverse proxies for the service
        for rproxy in attr['reverse_proxy']:
            path = rproxy.get("path","")
            path = f"{path} " if path else ""

            headers = rproxy.get("headers", None)
            tport = rproxy.get("transport", None)
            hdr_list = []
            tport_list = []

            if headers:
                # add list of headers to reverse proxy
                for hdr, val in headers.items():
                    if val == 'host':
                        val = "{host}"

                    hdr_list.append(
                        header_t.substitute(
                            header=hdr,
                            flag=str(val),
                        )
                    )

            proxy = None
            if tport:
                for key, val in tport.items():
                    tport_list.append(f"{key} {val}")

                headers = '\n'.join(hdr_list)
                transport = tport_http_t.substitute(flag='\n'.join(tport_list))

                # proxy with headers + transport
                proxy = rproxy_t.safe_substitute(
                    path=path,
                    ip=rproxy['address'],
                    port=rproxy['port'],
                    headers=indent(headers, INDENT*1),
                    transport=indent(transport, INDENT*1),
                )

            else:
                # basic proxy
                proxy = rproxy_empty_t.substitute(
                    path=path,
                    ip=rproxy['address'],
                    port=rproxy['port']
                )

            proxies.append(proxy)


        # build list of service blocks 
        ips = ' '.join([TAILSCALE_IP, LAN_IP])
        encodings = ' '.join(attr['encodings'])
        rproxies = '\n'.join(proxies)

        services.append(
            service_t.substitute(
                service_var=service,
                ips=ips,
                encodings=encodings,
                reverse_proxies=indent(rproxies, INDENT*1),
            )
        )

    # build user -> service mapping for each domain and allowed service
    for domain, attr in domain_attr.items():
        cf_var = strip_and_append(0, domain, "_cf")

        for service in attr['services']:
            if service not in service_attr:
                continue

            mixer = mixer_t.substitute(
                service=service,
                domain=domain,
                cf_var=cf_var,
                service_var=service,
            )
            mixers.append(mixer)


    with open(pth, 'w') as f:
        for c in cf:
            f.writelines(c)

        for s in services:
            f.writelines(s)

        for m in mixers:
            f.writelines(m)

main()
