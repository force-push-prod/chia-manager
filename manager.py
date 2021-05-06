from plot import *

from helper import *
import time

class Manager():
    def __init__(self):
        self.devices: list[PlotDevice] = []
        self.logs = []
        self.move_file_timeout = 0

    def print_logs(self):
        return print(NL.join([ ' | \t'.join(log) for log in self.logs ]))

    def warning(self, *components):
        self.logs.append([now_tz_str(), '🟠 WARNING', SP.join(map(str, components))])
        print(' | \t'.join(self.logs[-1]))

    def debug(self, *components):
        self.logs.append([now_tz_str(), '⚪️ DEBUG', SP.join(map(str, components))])
        print(' | \t'.join(self.logs[-1]))

    def info(self, *components):
        self.logs.append([now_tz_str(), '🟢 INFO', SP.join(map(str, components))])
        print(' | \t'.join(self.logs[-1]))

    def info2(self, *components):
        self.logs.append([now_tz_str(), '🔵 INFO', SP.join(map(str, components))])
        print(' | \t'.join(self.logs[-1]))

    def update_states(self):
        # new_signals = []
        for device in self.devices:
            for disk in device.disks:
                for plot in disk.plots:
                    self.debug(f'update_states: Checking {device} {disk} {plot}')
                    new_progress = self.fetch_progress(device, plot)
                    signals = plot.set_new_progress_get_signals(new_progress)
                    for signal in signals:
                        self.info2('update_states: Got signal', signal)

    def perform_actions(self):
        for device in self.devices:
            for disk in device.disks:
                self.debug('disk.is_idle: Checking if', disk, 'is idle')
                if disk.is_idle:
                    new_plot = Plot()
                    disk.add_plot(new_plot)
                    # TODO: correlate device with config
                    if device == mbp2: config = mbp2_config
                    else: config = j_config
                    self.start_plot(device, disk, config, new_plot)

                # if disk.has_finished_plots:
                #     pass

                if self.move_file_timeout <= 0:
                    file_names = self.get_finished_plot_file_paths(device, disk)
                    for a in file_names:
                        self.move_file(a, device, disk)
                else:
                    self.debug('move_file_timeout: skip check finished file; timeout', self.move_file_timeout)

    def main_loop(self):
        while True:
            self.debug('============= update_state =============')
            self.update_states()
            self.debug('============= perform_actions =============')
            self.perform_actions()

            if self.move_file_timeout > 0:
                self.move_file_timeout -= 1

            time.sleep(60 * 5)
        # self.process_signals(new_signals)

    # def process_signals(self):
    #     for signal in self.signals:
    #         signal

    def get_finished_plot_file_paths(self, device: PlotDevice, disk: PlotDisk):
        command = f'ls -1 {device.disk_dir_path}{disk.disk_volume_name}/*.plot'
        stderr, stdout = device.execute_and_wait_command_shell(command)
        if stderr != '' and stdout == '':
            return []
        elif stderr == '' and stdout != '':
            return stdout.strip().split('\n')
        else:
            self.warning('Do not expect this case: stderr -->', stderr, 'stdout -->', stdout)
            return []


    def move_file(self, file_path, device: PlotDevice, disk: PlotDisk):
        self.info(f'Moving {file_path} on {device} {disk}')
        if 'plot' not in file_path:
            self.warning('ERROR unexpected file_path', file_path)
            return

        if device == mbp2:
            command = f'scp {file_path} admin@192.168.0.11:/share/Chia01/ && rm {file_path}'
        else:
            command = f'scp {file_path} admin@192.168.0.11:/share/Chia01/ && rm {file_path}'

        stderr, stdout = device.execute_no_wait_command('move', command)
        self.debug('stderr -->', stderr, 'stdout -->', stdout)
        self.move_file_timeout = 18 # NOTE: 18 * 5 mins = 1.5 h


    def fetch_progress(self, device: PlotDevice, plot: Plot):
        log_file_path = device.construct_log_file_path(plot.log_file_name)

        command = ['cat', log_file_path]
        stderr, stdout = device.execute_and_wait_command(command)
        lines = stdout.split('\n')
        self.debug(f'fetch_progress: Got log file with stdout len={len(stdout)} line={len(lines)}', 'starting with ', stdout[:50])
        if stderr:
            self.warning(f'stderr is not empty:', stderr)
        return PlotProgress(lines)


    def start_plot(self, device: PlotDevice, disk: PlotDisk, config: PlotConfig, plot: Plot):
        self.info(f'Starting a new plot on {device} {disk} with {config}')
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
            pid = int(stdout) + 1
            plot.pid = pid
        except Exception as e:
            pid = 0
            self.warning('Cannot convert stdout to int; it should be pid:', e, stdout)

        self.debug('Plotting started with pid', pid)



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

# disk1.add_plot(Plot('0x60934159.log'))
disk2.add_plot(Plot('0x60936278.log'))
disk3.add_plot(Plot('0x609360a9.log'))

mbp2.add_disk(disk1)
mbp2.add_disk(disk2)
j.add_disk(disk3)
# mbp.add_disk(4, disk4)

mbp2_config = PlotConfig(buffer=8000, threads=3)
j_config = PlotConfig(buffer=8000, threads=6)

m = Manager()

m.devices = [mbp2, j]

# print(m.fetch_progress(j, ))
# new_plot = Plot()
# m.start_plot(mbp2, disk2, config, new_plot)
# print(new_plot)

# m.print_logs()
