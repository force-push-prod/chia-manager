from typing import Dict
from plot import *

from helper import *
from time import sleep
import logging


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    filename=f'manager-{now_no_tz_str()}.log',
                    filemode='w')

console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)


logger_manager = logging.getLogger('manager')


class Manager():
    def __init__(self, structure):
        self.structure: Dict[PlotDevice, list[PlotDisk]] = structure
        self.dead_processes: list[Process] = []
        self.running_processes: list[Process] = []

        self.stop_stagger = False
        self.stop_new_plot = False
        self.stop_transfer = False


    def fetch(self):
        for process in self.running_processes:
            process.fetch()

        deads = list(filter(lambda x: not x.is_running_cached, self.running_processes))

        if len(deads) > 0:
            still_running = list(filter(lambda x: x.is_running_cached, self.running_processes))
            self.running_processes = still_running
            self.dead_processes.extend(deads)
            for dead in deads:
                logger_manager.info('Process just died: %s', dead)


    def perform_actions(self):
        for device, disks in self.structure.items():
            for disk in disks:
                has_mv_process_on_same_device = False
                for p in self.running_processes:
                    if isinstance(p, MoveFileToChiaOverSSHProcess):
                        if p._device == device:
                            has_mv_process_on_same_device = True
                            break

                if has_mv_process_on_same_device:
                    logger_manager.debug('Skip checking for finished plots on %s %s', device, disk)
                else:
                    logger_manager.debug('Checking for finished plots on %s %s', device, disk)
                    finished_plots = get_finished_plot_file_paths(device, disk)
                    if len(finished_plots) > 0:
                        if self.stop_transfer:
                            logging.warning('Not moving finished plot due to flag control; on %s: %s', device, finished_plots[0])
                        else:
                            logging.info('Starting to move finished plot on %s: %s', device, finished_plots[0])
                            p = MoveFileToChiaOverSSHProcess(device, finished_plots[0])
                            p.start()
                            self.running_processes.append(p)

                plotting_processes: list[PlotProcess] = []
                for p in self.running_processes:
                    if isinstance(p, PlotProcess) and p._device == device and p._disk == disk:
                        plotting_processes.append(p)

                if len(plotting_processes) == 0:
                    if self.stop_new_plot:
                        logger_manager.warning('Not creating new plots due to flag control. %s %s is idle', device, disk)
                    else:
                        logger_manager.info('%s %s is idle, starting a new plot', device, disk)

                        # TODO: get config
                        if device == mbp2: config = mbp2_config
                        elif device == mbp: config = mbp_config
                        else: config = j_config

                        p = PlotProcess(device, disk, config)
                        p.start()
                        self.running_processes.append(p)

                elif len(plotting_processes) == 1:
                    progress = plotting_processes[0].progress

                    if progress.current_stage >= 3 and progress.current_table >= 4:
                        if device == mbp:
                            logger_manager.debug('Not staggering on mbp')
                            continue

                        if self.stop_stagger or self.stop_new_plot:
                            logger_manager.warning('Not staggering due to flag control on %s %s', device, disk)
                        else:
                            logger_manager.info('Start staggering plot on %s %s', device, disk)
                            # TODO: get config
                            if device == mbp2: config = mbp2_config
                            else: config = j_config
                            p = PlotProcess(device, disk, config)
                            p.start()
                            self.running_processes.append(p)


    def print_processes(self):
        logger_manager.debug('--------- PROCESSES ----------')

        for device, _ in self.structure.items():
            logger_manager.debug('')
            logger_manager.debug('Device %s', device)
            logger_manager.debug('')

            for x in self.dead_processes[-8:]:  # Only show last 8 dead processes
                if x._device == device:
                    logger_manager.debug('  -   %s', x)
                    if isinstance(x, PlotProcess):
                        logger_manager.debug('  -     %s', x.progress)


            for x in self.running_processes:
                if x._device == device:
                    logger_manager.debug('  +   %s', x)
                    if isinstance(x, PlotProcess):
                        logger_manager.debug('  +     %s', x.progress)

        logger_manager.debug('-' * 30)


    def main_loop(self):
        while True:
            self.fetch()
            self.perform_actions()
            self.print_processes()
            auto_save()
            sleep(5 * 60)


    def discover_chia_process(self):
        for device in self.structure.keys():
            processes = discover_chia_process(device, self.running_processes)
            self.running_processes.extend(processes)


def get_finished_plot_file_paths(device: PlotDevice, disk: PlotDisk):
    command = f'ls -1 {device.disk_dir_path}{disk.disk_volume_name}/*.plot'
    stderr, stdout = device.execute_and_wait_command_shell(command)
    if stderr != '' and stdout == '':
        return []
    elif stderr == '' and stdout != '':
        return stdout.strip().split('\n')
    else:
        logger_manager.warning('Do not expect this case. stderr: %s, stdout: %s', stderr, stdout)
        return []


def discover_chia_process(device: PlotDevice, existing_processes: list[Process]=[]):
    stderr, stdout = device.execute_and_wait_command_shell('pgrep chia')
    if stderr != '':
        logger_manager.critical('Expect stderr to be empty, got: %s', stderr)

    try:
        pids = list(map(int, stdout.strip().split('\n')))
    except Exception as e:
        logger_manager.exception(e)
        return []

    processes = []
    DummyDisk = PlotDisk('dummy')
    DummyConfig = PlotConfig(-1, -1)
    for pid in pids:
        print(f'We found chia process on {device} with pid = {pid}')
        if pid in [p._pid for p in existing_processes]:
            print('We already know about this process')
            continue
        p = PlotProcess(device, DummyDisk, DummyConfig)
        p._pid = pid
        p._log_file_name = input('log file name? ')
        if p._log_file_name == '':
            print('Ignored')
            continue
        p._disk = PlotDisk(input('for volume name? '))
        processes.append(p)

    return processes



mbp2 = PlotDevice(
    human_friendly_name='mbp2',
    ssh_name=None,
    log_dir_path='/Users/yyin/log/',
    disk_dir_path='/Volumes/',
    chia_path='/Applications/Chia.app/Contents/Resources/app.asar.unpacked/daemon/chia',
    python_path='/Users/yyin/.pyenv/shims/python',
    bootstrap_path='/Users/yyin/Developer/chia-manager/bootstrap.py',
)

j = PlotDevice(
    human_friendly_name='j',
    ssh_name='j',
    log_dir_path='/home/yy/log/',
    disk_dir_path='/media/yy/',
    chia_path='/home/yy/chia-blockchain/venv/bin/chia',
    python_path='/home/yy/chia-blockchain/venv/bin/python',
    bootstrap_path='/home/yy/bootstrap.py',
)

mbp = PlotDevice(
    human_friendly_name='mbp',
    ssh_name='mbp',
    log_dir_path='/Users/yinyifei/log/',
    disk_dir_path='/Volumes/',
    chia_path='/Applications/Chia.app/Contents/Resources/app.asar.unpacked/daemon/chia',
    python_path='/usr/bin/python',
    bootstrap_path='/Users/yinyifei/bootstrap.py',
)

sp = PlotDevice(
    human_friendly_name='sp',
    ssh_name='sp',
    log_dir_path='/Users/stellarpan/log/',
    disk_dir_path='/Volumes/',
    chia_path='/Users/stellarpan/chia-blockchain/venv/bin/chia',
    python_path='/usr/bin/python3',
    bootstrap_path='/Users/stellarpan/bootstrap.py',
)

disk1 = PlotDisk(disk_volume_name='T7-1')
disk2 = PlotDisk(disk_volume_name='T7-2')
disk3 = PlotDisk(disk_volume_name='T7-3')
disk4 = PlotDisk(disk_volume_name='ExFAT450')
disk5 = PlotDisk(disk_volume_name='SP')


mbp2_config = PlotConfig(buffer=8000, threads=3)
mbp_config = PlotConfig(buffer=3360, threads=2)
j_config = PlotConfig(buffer=8000, threads=6)

sp_config = PlotConfig(buffer=8000, threads=3)


structure = {
    mbp2: [disk1, disk2],
    j: [disk3],
    sp: [disk5],
    # mbp: [disk4],
}

m = Manager(structure)


import pickle
def save():
    logging.shutdown()
    with open('manager.pickle', 'wb') as p:
        pickle.dump(m, p)

def load():
    global m
    with open('manager.pickle', 'rb') as p:
        m = pickle.load(p)


def auto_save():
    global m
    with open('manager-auto.pickle', 'wb') as p:
        pickle.dump(m, p)
    logging.debug('Saved to auto-save file')


def auto_load():
    global m
    with open('manager-auto.pickle', 'rb') as p:
        m = pickle.load(p)
    logging.debug('Loaded from auto-save file')

auto_load()
