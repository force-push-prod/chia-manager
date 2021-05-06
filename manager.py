from typing import Dict
from plot import *

from helper import *

class Manager():
    def __init__(self):
        self.devices: Dict[PlotDevice] = {}
        self.logs = []

    def print_logs(self):
        return print(NL.join([ SP.join(log) for log in self.logs ]))

    def warning(self, *components):
        self.logs.append([now_tz_str(), 'WARNING', SP.join(map(str, components))])

    def debug(self, *components):
        self.logs.append([now_tz_str(), 'DEBUG', SP.join(map(str, components))])

    def info(self, *components):
        self.logs.append([now_tz_str(), 'INFO', SP.join(map(str, components))])

    def routine(self):
        new_signals = []
        for device_id, device in self.devices.items():
            for disk_id, disk in device.disks.items():
                for plot_id, plot in disk.plots.items():
                    new_progress = self.fetch_progress(device, plot)
                    plot_singals = plot.set_new_progress_get_signals(new_progress)
                    new_signals.extend(plot_singals)

        self.process_signals(new_signals)


    # def process_signals(self):
    #     for signal in self.signals:
    #         signal


    def fetch_progress(self, device: PlotDevice, plot: Plot):
        log_file_path = device.construct_log_file_path(plot.log_file_name)

        command = ['cat', log_file_path]
        stderr, stdout = device.execute_and_wait_command(command)
        lines = stdout.split('\n')
        self.info(f'Got log file with stdout len={len(stdout)} line={len(lines)}', 'starting with ', stdout[:50])
        if stderr:
            self.warning(f'stderr is not empty:', stderr)
        return PlotProgress(lines)


    def start_plot(self, device: PlotDevice, disk: PlotDisk, config: PlotConfig, plot: Plot):
        disk_path = device.disk_dir_path + disk.disk_volume_name
        command = f"""
        {device.chia_path} plots create
            -n 1 -b {config.buffer} -r {config.threads}
            -t {disk_path} -2 {disk_path} -d {disk_path}
            2>&1 | ts %Y-%m-%dT%H:%M:%S%z
        """.replace('\n', '').strip()

        stderr, stdout = device.execute_no_wait_command(plot.log_file_name, command)

        if stderr != '':
            self.warning('Got non empty stderr', stderr)
        try:
            pid = int(stdout)
        except Exception as e:
            pid = 0
            self.warning('Cannot convert stdout to int; it should be pid:', e, stdout)

        self.info('Plotting started with pid', pid)



mbp2 = PlotDevice(
    ssh_name=None,
    log_dir_path='/Users/yyin/log/',
    disk_dir_path='/Volumes/',
    chia_path='/Applications/Chia.app/Contents/Resources/app.asar.unpacked/daemon/chia',
    python_path='/Users/yyin/.pyenv/shims/python',
    bootstrap_path='/Users/yyin/Developer/chia-manager/bootstrap.py',
)


j = PlotDevice(
    ssh_name='j',
    log_dir_path='/home/yy/log/',
    disk_dir_path='/media/yy/',
    chia_path='/home/yy/chia-blockchain/venv/bin/chia',
    python_path='/home/yy/chia-blockchain/venv/bin/python',
    bootstrap_path='/home/yy/bootstrap.py',
)

mbp = PlotDevice(
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


# mbp2.add_disk(disk1)
# mbp2.add_disk(disk2)
# j.add_disk(disk3)
# # mbp.add_disk(4, disk4)

# config = PlotConfig(buffer=8000, threads=3)
# config2 = PlotConfig(buffer=8000, threads=6)

# manager = Manager()

# print(manager.fetch_progress(j, Plot('0x609360a9.log')))
# # new_plot = Plot()
# # manager.start_plot(mbp2, disk2, config, new_plot)
# # print(new_plot)

# manager.print_logs()
