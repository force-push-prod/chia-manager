from helper.date import now_tz_str
import os
import sys
import pathlib

from helper import *


def get_plots_from_disks(disks):
    plots = {}

    for disk_path in disks:
        all_file_names = os.listdir(disk_path)
        plot_file_names = filter(lambda x: x.startswith('plot-'), all_file_names)

        for plot_file_name in plot_file_names:
            plot_disk_path = disk_path / plot_file_name

            if plot_disk_path in plots:
                assert False

            match plot_file_name.split('-'):
                case ['plot', 'k32', year, month, day, hour, minute, plot_id]:
                    plot_id = plot_id.replace('.plot', '')
                case [_]:
                    raise Exception(f'Unmatched plot_file_name: {plot_file_name} {NL}')

            plots[plot_id] = {
                'disk_path': str(disk_path),
                'start_time': [year, month, day, hour, minute],
                'size': plot_disk_path.stat().st_size,
            }
    return plots

def get_new_file_content(old_plots, new_plots):
    import datetime
    results = {}
    for plot_id, plot in new_plots.items():
        size = plot['size']

        old_history = old_plots.get(plot_id, {}).get('history', [])
        new_data_point = [now_tz_str(), size]

        if len(old_history) == 0:
            history = [new_data_point]
        elif old_history[-1][1] != size:
            history = [*old_history, new_data_point]
        else:
            history = old_history

        results[plot_id] = {
            'disk_path': plot['disk_path'],
            'start_time': plot['start_time'],
            'size': size,
            'last_checked': datetime.datetime.now(),
            'history': history,
        }

    return results

if __name__ == '__main__':
    storage_disks_path = [
        pathlib.Path(x) for x in
        [
            '/Volumes/Chia/',
            '/Volumes/Chia2/',
            '/Volumes/Chia01/',
        ]
    ]

    plots = get_plots_from_disks(storage_disks_path)

    if len(sys.argv) > 1 and sys.argv[1] == 'save':
        import json

        try:
            with open('/Users/yyin/farming-disk.json', 'r') as file:
            # NOTE: not using decoder to decode the dates. We don't need them parsed at this point
                content = file.read()
            if len(content) == 0:
                content = '{}'
        except FileNotFoundError:
            content = '{}'

        old_plots = json.loads(content)
        new_saved = get_new_file_content(old_plots, plots)

        with open('/Users/yyin/farming-disk.json', 'w') as file:
            file.write(convert_object_to_str(new_saved))

