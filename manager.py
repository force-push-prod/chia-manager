from typing import Dict
from plot import *

from helper import *
from time import sleep
import logging


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    filename='manager.log',
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


    def update_processes(self):
        for process in self.running_processes:
            process.fetch_updates()

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
                if any(list(map(lambda x: isinstance(x, MoveFileToChiaOverSSHProcess), self.running_processes))):
                    logger_manager.debug('Skip checking for finished plots on %s %s', device, disk)
                else:
                    logger_manager.debug('Checking for finished plots on %s %s', device, disk)
                    finished_plots = get_finished_plot_file_paths(device, disk)
                    if len(finished_plots) > 0:
                        p = MoveFileToChiaOverSSHProcess(device, finished_plots[0])
                        p.start()
                        self.running_processes.append(p)

                plotting_processes = list(filter(
                    lambda x: isinstance(x, PlotProcess) and x._device == device and x._disk == disk,
                    self.running_processes
                ))

                if len(plotting_processes) == 0:
                    logger_manager.info('%s %s is idle, starting a new plot', device, disk)

                    # TODO: get config
                    if device == mbp2:
                        config = mbp2_config
                    else:
                        config = j_config
                    p = PlotProcess(device, disk, config)
                    p.start()

                    self.running_processes.append(p)


    def print_processes(self):
        logger_manager.debug('--------- PROCESSES ----------')

        for device, _ in self.structure.items():
            logger_manager.debug('\tDevice %s', device)

            logger_manager.debug('\t\tDead')
            for x in self.dead_processes:
                if x._device == device:
                    logger_manager.debug('\t\t\t%s', x)

            logger_manager.debug('\t\tRunning')
            for x in self.running_processes:
                if x._device == device:
                    logger_manager.debug('\t\t\t%s', x)

        logger_manager.debug('-' * 30)


    def main_loop(self):
        while True:
            self.update_processes()
            self.perform_actions()

            self.print_processes()
            sleep(5 * 60)


    def discover_chia_process(self):
        for device in self.structure.keys():
            processes = discover_chia_process(device)
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


def discover_chia_process(device: PlotDevice):
    stderr, stdout = device.execute_and_wait_command_shell('pgrep chia')
    if stderr != '':
        logger_manager.critical('Expect stderr to be empty, got: %s', stderr)

    try:
        pids = list(map(int, stdout.strip().split('\n')))
    except Exception as e:
        logger_manager.exception(e)
        return

    processes = []
    DummyDisk = PlotDisk('dummy')
    DummyConfig = PlotConfig(-1, -1)
    for pid in pids:
        p = PlotProcess(device, DummyDisk, DummyConfig)
        p._pid = pid
        print(f'We found chia process with pid = {pid}')
        p._log_file_name = input('log file name? ')
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
    log_dir_path='/Users/yinyifei/',
    disk_dir_path='/Volumes/',
    chia_path='/Applications/Chia.app/Contents/Resources/app.asar.unpacked/daemon/chia',
    python_path='/usr/bin/python',
    bootstrap_path='/Users/yyin/Developer/chia-manager/bootstrap.py',
)

disk1 = PlotDisk(disk_volume_name='T7-1')
disk2 = PlotDisk(disk_volume_name='T7-2')
disk3 = PlotDisk(disk_volume_name='T7-3')
disk4 = PlotDisk(disk_volume_name='ExFAT450')


mbp2_config = PlotConfig(buffer=8000, threads=3)
j_config = PlotConfig(buffer=8000, threads=6)

structure = {
    mbp2: [disk1, disk2],
    j: [disk3]
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
