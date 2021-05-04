def get_commands(device, disk, parallel_id=1):
    log_file_name = f'{device}-disk{disk}-{parallel_id}.log'

    match disk:
        case 1 | 2 | 3:
            disk_name = f'T7-{disk}'
        case 4:
            disk_name = 'ExFAT450'
        case _:
            assert False

    match device:
        case 'mbp2':
            log_path = '/Users/yyin/' + log_file_name
            disk_path = '/Volumes/' + disk_name
            ssh_name = False
            n, buffer, threads = 1, 8000, 3
        case 'mbp':
            log_path = '/Users/yinyifei/' + log_file_name
            disk_path = '/Volumes/' + disk_name
            ssh_name = 'mbp'
            n, buffer, threads = 1, 8000, 5
        case 'j':
            log_path = '/home/yy/' + log_file_name
            disk_path = '/media/yy/' + disk_name
            ssh_name = 'j'
            n, buffer, threads = 1, 8000, 5
        case _:
            assert False

    CHIA_MANAGER_PROGRAM = 'python /Users/yyin/Developer/chia-manager/main.py'
    INTERVAL = 60 * 3  # 3 mins

    if ssh_name:
        command = f"""
        watch -n {INTERVAL} 'ssh {device} cat {log_path} | {CHIA_MANAGER_PROGRAM}'
        """

    else:
        command = f"""
        watch -n {INTERVAL} 'cat {log_path} | {CHIA_MANAGER_PROGRAM}'
        """

    # TODO: add ssh support
    command_tmp = f"""
    nohup /bin/bash -c '2>&1 chia plots create
        -n {n} -b {buffer} -r {threads}
        -t {disk_path} -2 {disk_path} -d {disk_path}
    | ts %Y-%m-%dT%H:%M:%S%z'
    >> {log_path} 2>&1 &
    """

    print(command.strip())
    print(command_tmp.replace('\n', '').strip())

import sys
get_commands(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]) if len(sys.argv) > 3 else 1)

# CHIA_PATH = '/Applications/Chia.app/Contents/Resources/app.asar.unpacked/daemon/chia'
