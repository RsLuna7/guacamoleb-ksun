#!/usr/bin/env python3
"""
Fix KernelSU-Next build on Linux 4.14 and disable unsafe SELinux context-write hook.
"""
import os
import sys

OLD = """#if KERNEL_VERSION(4, 19, 0) <= LINUX_VERSION_CODE
\tktime_get_boottime_ts64(&ts);
#else
\tget_monotonic_boottime(&ts);
#endif"""

NEW = """/*
 * 4.14 already provides ktime_get_boottime_ts64(); the old guard used
 * get_monotonic_boottime() which takes struct timespec (not timespec64)
 * on this kernel and does not compile.
 */
\tktime_get_boottime_ts64(&ts);"""


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    ksu_dir = sys.argv[1]
    path = os.path.join(ksu_dir, 'kernel/sulog/event.c')
    if os.path.exists(path):
        src = open(path, encoding='utf-8').read()
        n = src.count(OLD)
        if n > 0:
            src = src.replace(OLD, NEW)
            open(path, 'w', encoding='utf-8').write(src)
            print('patch_ksu_tree: fixed %d timespec64 block(s) in %s' % (n, path))
        else:
            print('patch_ksu_tree: event.c does not need boottime patching')

    selinux_path = os.path.join(ksu_dir, 'kernel/feature/selinux_hide.c')
    if os.path.exists(selinux_path):
        selinux_src = open(selinux_path, encoding='utf-8').read()
        old_hook = '\thook_selinux_transaction_write();'
        old_hook_fn = 'ksu_init_hook_selinux_transaction_write();'
        new_hook = ('\t/* Android writes /sys/fs/selinux/context while setting a\n'
                    '\t * zygote child context. Do not intercept this path. */\n'
                    '\t/* hook_selinux_transaction_write(); */')
        new_hook_fn = ('\t/* Android writes /sys/fs/selinux/context while setting a\n'
                       '\t * zygote child context. Do not intercept this path. */\n'
                       '\t/* ksu_init_hook_selinux_transaction_write(); */')
        if old_hook in selinux_src:
            selinux_src = selinux_src.replace(old_hook, new_hook, 1)
            open(selinux_path, 'w', encoding='utf-8').write(selinux_src)
            print('patch_ksu_tree: disabled unsafe SELinux context-write hook')
        elif old_hook_fn in selinux_src:
            selinux_src = selinux_src.replace(old_hook_fn, new_hook_fn, 1)
            open(selinux_path, 'w', encoding='utf-8').write(selinux_src)
            print('patch_ksu_tree: disabled unsafe SELinux context-write hook (fn)')
        elif 'zygote child context' in selinux_src:
            print('patch_ksu_tree: SELinux context-write hook already disabled')
        else:
            print('patch_ksu_tree: WARNING: SELinux hook call not found in %s' % selinux_path)

    profile_path = os.path.join(ksu_dir, 'kernel/policy/allowlist.c')
    if os.path.exists(profile_path):
        profile_src = open(profile_path, encoding='utf-8').read()
        old_setter = """int ksu_set_app_profile(struct app_profile *profile)
{
    struct perm_data *p, *np;"""
        old_setter_alt = """int ksu_set_app_profile(struct app_profile *profile)
{
    struct perm_data *p = NULL, *np;"""
        new_setter = """int ksu_set_app_profile(struct app_profile *profile)
{
    /* v3 Manager profiles predate root_profile.flags (v4). The field is at
     * the end of the root union member, so zero it before ABI migration. */
    if (profile && profile->version == 3) {
        profile->rp_config.profile.flags = 0;
        profile->version = KSU_APP_PROFILE_VER;
    }

    struct perm_data *p, *np;"""
        new_setter_alt = """int ksu_set_app_profile(struct app_profile *profile)
{
    /* v3 Manager profiles predate root_profile.flags (v4). The field is at
     * the end of the root union member, so zero it before ABI migration. */
    if (profile && profile->version == 3) {
        profile->rp_config.profile.flags = 0;
        profile->version = KSU_APP_PROFILE_VER;
    }

    struct perm_data *p = NULL, *np;"""
        if old_setter in profile_src:
            profile_src = profile_src.replace(old_setter, new_setter, 1)
            open(profile_path, 'w', encoding='utf-8').write(profile_src)
            print('patch_ksu_tree: migrated Manager app profile ABI v3 to v4')
        elif old_setter_alt in profile_src:
            profile_src = profile_src.replace(old_setter_alt, new_setter_alt, 1)
            open(profile_path, 'w', encoding='utf-8').write(profile_src)
            print('patch_ksu_tree: migrated Manager app profile ABI v3 to v4 (alt)')
        elif 'root_profile.flags' in profile_src:
            print('patch_ksu_tree: Manager app profile ABI shim already applied')
        else:
            print('patch_ksu_tree: WARNING: app profile setter not found')
    return 0


if __name__ == '__main__':
    sys.exit(main())

