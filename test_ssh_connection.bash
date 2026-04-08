#!/usr/bin/env bash
# Test SSH connectivity using the ssh_runner module directly.
set -euo pipefail

python3 -c "
from rl_auto_research.config import config
from rl_auto_research.blueprint_runner.ssh_runner import _run_cmd

if config.get('runner') != 'ssh':
    print('Runner is not ssh, nothing to check.')
    exit(0)

hosts = config.get('ssh', {}).get('hosts', [])
if not hosts:
    print('WARNING: runner is ssh but no hosts configured.')
    exit(1)

failed = False
for host_cfg in hosts:
    label = f\"{host_cfg.get('user', 'root')}@{host_cfg['host']}:{host_cfg.get('port', 22)}\"
    print(f'Testing SSH connection to {label} ... ', end='', flush=True)
    result = _run_cmd(host_cfg, 'echo ok')
    if result.returncode == 0:
        print('OK')
    else:
        print('FAILED')
        print(f'  stdout: {result.stdout.strip()}')
        print(f'  stderr: {result.stderr.strip()}')
        failed = True

if failed:
    print()
    print('ERROR: Some SSH connections failed.')
    exit(1)
else:
    print()
    print('All SSH connections OK.')
"
