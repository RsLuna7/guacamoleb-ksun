#!/usr/bin/env python3
"""
Apply KernelSU and SUSFS options on top of the OFFICIAL kernel .config.
"""
import sys

ENABLE = [
    'CONFIG_KSU',
    'CONFIG_KSU_MANUAL_HOOK',
    'CONFIG_TMPFS_XATTR',
    'CONFIG_OVERLAY_FS_REDIRECT_DIR',
    'CONFIG_OVERLAY_FS_XINO_AUTO',
    # SUSFS
    'CONFIG_KSU_SUSFS',
    'CONFIG_KSU_SUSFS_SUS_PATH',
    'CONFIG_KSU_SUSFS_SUS_MOUNT',
    'CONFIG_KSU_SUSFS_AUTO_ADD_SUS_KSU_DEFAULT_MOUNT',
    'CONFIG_KSU_SUSFS_AUTO_ADD_SUS_BIND_MOUNT',
    'CONFIG_KSU_SUSFS_SUS_KSTAT',
    'CONFIG_KSU_SUSFS_SUS_OVERLAYFS',
    'CONFIG_KSU_SUSFS_TRY_UMOUNT',
    'CONFIG_KSU_SUSFS_SPOOF_UNAME',
    'CONFIG_KSU_SUSFS_ENABLE_LOG',
    'CONFIG_KSU_SUSFS_HIDE_KSU_SUSFS_SYMBOLS',
    'CONFIG_KSU_SUSFS_SPOOF_CMDLINE_OR_BOOTCONFIG',
    'CONFIG_KSU_SUSFS_OPEN_REDIRECT',
    'CONFIG_KSU_SUSFS_SUS_MAP',
    'CONFIG_KSU_SUSFS_SUS_MEMFD',
    'CONFIG_KSU_SUSFS_HAS_MAGIC_MOUNT',
]
DISABLE = [
    'CONFIG_KSU_DEBUG',
    'CONFIG_KSU_KPROBES_HOOK',
]


def parse(text):
    lines = []
    values = {}
    for raw in text.splitlines():
        line = raw.rstrip('\n')
        lines.append(line)
        s = line.strip()
        if s.startswith('CONFIG_') and '=' in s:
            k, v = s.split('=', 1)
            values[k] = v
        elif s.startswith('# CONFIG_') and s.endswith(' is not set'):
            values[s[2:-11]] = None
    return lines, values


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 1
    src, dst = sys.argv[1], sys.argv[2]
    text = open(src, encoding='utf-8', errors='replace').read()
    lines, values = parse(text)

    touched = {}
    for name in ENABLE:
        touched[name] = 'y'
    for name in DISABLE:
        touched[name] = None

    out = []
    for line in lines:
        s = line.strip()
        key = None
        if s.startswith('CONFIG_') and '=' in s:
            key = s.split('=', 1)[0]
        elif s.startswith('# CONFIG_') and s.endswith(' is not set'):
            key = s[2:-11]
        if key in touched:
            continue
        out.append(line)

    out.append('')
    out.append('# ==== KernelSU + SUSFS delta (added by CI) ====')
    for name in ENABLE:
        out.append('%s=y' % name)
    for name in DISABLE:
        out.append('# %s is not set' % name)

    with open(dst, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out) + '\n')

    print('applied KSU+SUSFS delta: %d enabled, %d disabled'
          % (len(ENABLE), len(DISABLE)))
    return 0


if __name__ == '__main__':
    sys.exit(main())

