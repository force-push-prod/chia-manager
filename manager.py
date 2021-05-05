from typing import Dict
from plot import *
import sys

from time import sleep

from helper import *

class Manager():
    def __init__(self):
        self.devices: Dict[str, PlotDevice] = {}
        self.signals = []
        self.logs = []

    def signal(self):
        self.signals.append([])

    def log(self, *components):
        self.logs.append([now_tz_str(), SP.join(map(str, components))])

    def routine(self):
        signals = []
        for device_id, device in self.devices.items():
            for disk_id, disk in device.disks.items():
                for plot_id, plot in disk.plots.items():
                    old_progress = plot.progress
                    new_progress = self.fetch_progress(device_id, disk_id, plot_id)
                    if old_progress.status == new_progress.status:
                        signals.push(['', ''])
                    plot.progress = new_progress
                    # plot.status = status
                # disk.status =
            # disk.status =
        process_signals(signals)

    def fetch_progress(self, device_id, disk_id, plot_id):
        device = self.devices[device_id]
        disk = device.disks[disk_id]
        plot = disk.plots[plot_id]
        log_file_path = '???'

        command = f'cat {log_file_path}'
        entire_log_file_content = device.execute_sync_command(command)
        return PlotProgress(entire_log_file_content)

    def process_signals(self):
        for signal in self.signals:
            signal



"""
Manager
    Device
        Disk
            Plot

device: {
    plotting 2 plots,
    disk1: {
        125 G left on disk,
        plot 1a3b finished,
        plot 1a3b in progress - stage 3,
    }
    disk2: {
        125 G left on disk,
        plot 1a3b finished,
        plot 1a3b in progress - stage 3,
    }
}

if (self disk1 is in stage1) {
    move finished plot to
}


device.routine() = {
    # Update progress
    for each disk:
        for each plot:
            old_status = plot.status
            new_status = get status
            if old_status is not finished and new_status is finished:
                plot.just_finished = true

    if progress changed:
        check what to do: start new one? move file?
}

ALTERNATIVE

device.routine() = {
    # Update progress
    for each plot:
        old_status = plot.status
        new_status = get status
        if old_status is not finished and new_status is finished:
            signal_queue += ['stage_updated', disk_id, plot_id, 3 (changed to stage 3)]
            signal_queue += ['stage_updated', disk_id, plot_id, 5 (finished)]

    # Message queue
    signal_queue += ['', plot_id, 5 (finished)]
}


"""



# config = PlotConfig(device='j', disk=3, buffer_size=8000, threads=5)
# config = PlotConfig(device='mbp2', disk_id=2, buffer_size=8000, threads=3)

# match sys.argv[1]:
#     case 'case1':
#         config = PlotConfig(device='mbp2', disk_id=1, buffer_size=8000, threads=3)
#         p = Plot(config)
#         # sleep(7 * 3600)
#         p.start()
#     case 'case2':
#         config = PlotConfig(device='mbp2', disk_id=2, buffer_size=8000, threads=3)
#         p = Plot(config)
#         p.start()
#         # sleep(5 * 3600)
#     case 'case3':
#         config = PlotConfig(device='j', disk_id=3, buffer_size=8000, threads=6)
#         p = Plot(config)
#         sleep(6 * 3600)
#         p.start()
#     case 'case-test':
#         config = PlotConfig(device='mbp2', disk_id=3, buffer_size=8000, threads=6)
#         p = Plot(config)
#         print(p.command_to_watch)

#     case _:
#         print('Unknown case')
#         exit(1)
