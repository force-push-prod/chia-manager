from typing import Dict
from plot import *

from helper import *
from time import sleep
import logging

logging.getLogger().setLevel(logging.DEBUG)

logger_manager = logging.getLogger('manager')

class Manager():
    def __init__(self, structure):
        self.structure: Dict[PlotDevice, list[PlotDisk]] = structure
        self.dead_processes: list[Process]
        self.running_processes: list[Process]


    def update_processes(self):
        for process in self.running_processes:
            process.fetch_updates()

        deads = filter(lambda x: not x.is_running_cached, self.running_processes)

        if len(deads) > 0:
            still_running = filter(lambda x: x.is_running_cached, self.running_processes)
            self.running_processes = still_running
            self.dead_processes.extend(deads)
            for dead in deads:
                logging.info('Process just died: %s', dead)


    def perform_actions(self):
        for device, disks in self.structure.items():
            for disk in disks:
                if any(map(lambda x: isinstance(x, MoveFileToChiaOverSSHProcess), self.running_processes)):
                    logging.debug('Skip checking for finished plots on %s %s', device, disk)
                else:
                    finished_plots = get_finished_plot_file_paths(device, disk)
                    if len(finished_plots) > 0:
                        p = MoveFileToChiaOverSSHProcess(device, disk)
                        p.start()
                        self.running_processes.append(p)

                plotting_processes = filter(
                    lambda x: isinstance(x, PlotProcess) and x._device == device and x._disk == disk,
                    self.running_processes
                )

                if len(plotting_processes) == 0:
                    logging.info('%s %s is idle, starting a new plot')

                    # TODO: get config
                    if device == mbp2:
                        config = mbp2_config
                    else:
                        config = j_config
                    p = PlotProcess(device, disk, config)
                    p.start()

                    self.running_processes.append(p)


    def main_loop(self):
        while True:
            self.update_processes()
            self.perform_actions()

            logger_manager.debug('PROCESSES')
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

            sleep(5 * 60)


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

m = Manager()
m.structure = structure

logging.shutdown()
