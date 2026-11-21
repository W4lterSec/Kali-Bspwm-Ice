#!/usr/bin/env python3
"""Local status counters. No public-IP services, network probes or telemetry."""
import argparse
from pathlib import Path
import shutil
import subprocess
import time
import network


def cpu_times(text):
    fields = next(line.split()[1:] for line in text.splitlines() if line.startswith('cpu '))
    values = list(map(int, fields))
    return sum(values[:8]), values[3] + (values[4] if len(values) > 4 else 0)


def cpu_percent(before, after):
    total = after[0] - before[0]
    idle = after[1] - before[1]
    return max(0, min(100, round(100 * (total - idle) / total))) if total > 0 else 0


def memory_percent(text):
    values = {line.split(':')[0]: int(line.split()[1]) for line in text.splitlines() if ':' in line}
    total = values.get('MemTotal', 0)
    available = values.get('MemAvailable', values.get('MemFree', 0))
    return max(0, min(100, round(100 * (total - available) / total))) if total else 0


def interface_name():
    config = network.settings()
    if config.get('lan_interface'):
        return config['lan_interface']
    addresses = network.ip_json('address', 'show')
    lan, _ = network.choose(network.ip_json('-d', 'link', 'show'), addresses, network.ip_json('route', 'show', 'default'), config)
    return next((row['ifname'] for row in addresses if any(x.get('local') == lan for x in row.get('addr_info', []))), '')


def net_bytes(text, interface):
    for line in text.splitlines():
        if ':' in line:
            name, fields = line.split(':', 1)
            if name.strip() == interface:
                values = fields.split()
                return int(values[0]), int(values[8])
    return 0, 0


def rates(before, after, seconds):
    return tuple(max(0.0, (a - b) / seconds) if seconds > 0 else 0.0 for b, a in zip(before, after))


def human_rate(value, compact=False):
    if value >= 1024 * 1024:
        return f'{value / (1024 * 1024):.1f}' + ('M' if compact else ' MiB/s')
    return f'{value / 1024:.0f}' + ('K' if compact else ' KiB/s')


def icon(code, color):
    return '%{F' + color + '}%{T3}' + chr(code) + '%{T-}%{F-}'


def link_label(interface):
    if not interface:
        return icon(0xf127, '#607d8d')
    if (Path('/sys/class/net') / interface / 'wireless').exists():
        try:
            for line in Path('/proc/net/wireless').read_text().splitlines():
                if line.strip().startswith(interface + ':'):
                    quality = float(line.split(':', 1)[1].split()[1].rstrip('.'))
                    return icon(0xf012, '#73e5ff') + f' {min(100, round(quality / 70 * 100))}%'
        except (OSError, ValueError, IndexError):
            pass
        return icon(0xf1eb, '#73e5ff')
    return icon(0xf0e8, '#73e5ff')


def stream(compact=False):
    interface = interface_name()
    old_net = net_bytes(Path('/proc/net/dev').read_text(), interface)
    old_cpu = cpu_times(Path('/proc/stat').read_text())
    old_time = time.monotonic()
    tick = 0
    while True:
        time.sleep(2)
        if tick % 5 == 0:
            current = interface_name()
            if current != interface:
                interface = current
                old_net = net_bytes(Path('/proc/net/dev').read_text(), interface)
                old_time = time.monotonic()
        now = time.monotonic()
        new_net = net_bytes(Path('/proc/net/dev').read_text(), interface)
        new_cpu = cpu_times(Path('/proc/stat').read_text())
        download, upload = rates(old_net, new_net, now - old_time)
        disk = shutil.disk_usage('/')
        used_disk = round(100 * disk.used / disk.total) if disk.total else 0
        used_memory = memory_percent(Path('/proc/meminfo').read_text())
        separator = ' ' if compact else '  '
        output = separator.join((
            icon(0xf063, '#73e5ff') + ' ' + human_rate(download, compact),
            icon(0xf062, '#25d9f8') + ' ' + human_rate(upload, compact),
            icon(0xf0a0, '#a8d8ec') + f' {used_disk}%',
            icon(0xf2db, '#73e5ff') + f' {cpu_percent(old_cpu, new_cpu)}%',
            icon(0xf233, '#85d8bf') + f' {used_memory}%',
        ))
        print(output, flush=True)
        old_net, old_cpu, old_time = new_net, new_cpu, now
        tick += 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--stream', action='store_true')
    parser.add_argument('--compact', action='store_true')
    parser.add_argument('--link', action='store_true')
    args = parser.parse_args()
    try:
        if args.link:
            print(link_label(interface_name()))
        else:
            stream(args.compact)
    except (BrokenPipeError, KeyboardInterrupt):
        pass
