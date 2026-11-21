#!/usr/bin/env python3
"""Report local IPv4 and tunnel IPv4 without calling external services."""
import json
import os
from pathlib import Path
import re
import subprocess


def ip_json(*args):
    try:
        return json.loads(subprocess.check_output(['ip', '-j', *args], timeout=3, stderr=subprocess.DEVNULL))
    except (OSError, subprocess.SubprocessError, ValueError):
        return []


def settings():
    root = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
    try:
        return json.loads((root / 'kali-dragon-ice/settings.json').read_text())
    except (OSError, ValueError):
        return {}


def vpn_link(link):
    name = link.get('ifname', '')
    kind = link.get('linkinfo', {}).get('info_kind', '')
    return kind in {'tun', 'wireguard', 'ppp'} or bool(re.match(r'^(tun|tap|wg|ppp|tailscale|proton|nordlynx)', name)) or (Path('/sys/class/net') / name / 'tun_flags').exists()


def choose(links, addresses, routes, config):
    active = {x['ifname']: x for x in links if 'UP' in x.get('flags', [])}
    ipv4 = {}
    for row in addresses:
        values = [x['local'] for x in row.get('addr_info', []) if x.get('family') == 'inet' and x.get('scope') == 'global' and 'local' in x]
        if values and row.get('ifname') in active:
            ipv4[row['ifname']] = values[0]
    tunnels = {name for name, link in active.items() if vpn_link(link)}
    if config.get('vpn_interface'):
        tunnels.add(config['vpn_interface'])
    vpn_names = [config['vpn_interface']] if config.get('vpn_interface') else sorted(tunnels)
    vpn = next((ipv4[n] for n in vpn_names if n in ipv4), 'desconectada')
    if config.get('lan_interface'):
        lan_names = [config['lan_interface']]
    else:
        preferred = [r['dev'] for r in sorted(routes, key=lambda x: x.get('metric', 0)) if 'dev' in r and r.get('dst') in ('default', '0.0.0.0/0')]
        physical = [n for n in ipv4 if not re.match(r'^(lo$|docker|br-|virbr|veth|vboxnet|vmnet)', n)]
        lan_names = preferred + physical
    lan = next((ipv4[n] for n in lan_names if n in ipv4 and n not in tunnels), 'sin red')
    return lan, vpn


if __name__ == '__main__':
    lan, vpn = choose(ip_json('-d', 'link', 'show'), ip_json('address', 'show'), ip_json('route', 'show', 'default'), settings())
    vpn = 'OFF' if vpn == 'desconectada' else vpn
    lan = '--' if lan == 'sin red' else lan
    print(f'LAN: {lan} | VPN: {vpn}')
