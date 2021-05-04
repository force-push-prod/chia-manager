import os
import sys
import pathlib

NL = '\n'

def get_plots_from_disks(disks):
    plots = {}

    for disk_path in disks:
        a = os.open(disk_path, os.O_RDONLY)
        all_file_names = os.listdir(disk_path)
        plot_file_names = filter(lambda x: x.startswith('plot-'), all_file_names)

        for plot_file_name in plot_file_names:
            plot_absolute_path = disk_path / plot_file_name

            if plot_absolute_path in plots:
                assert False

            match plot_file_name.split('-'):
                case ['plot', 'k32', year, month, day, hour, minute, plot_id]:
                    plot_id = plot_id.replace('.plot', '')
                case [_]:
                    raise Exception(f'Unmatched plot_file_name: {plot_file_name} {NL}')

            plots[plot_id] = {
                'absolute_path': str(plot_absolute_path),
                'start_time': [year, month, day, hour, minute],
                'size': plot_absolute_path.stat().st_size,
            }
    return plots

def get_new_file_content(old_plots, new_plots):
    import datetime
    results = {}
    for plot_id, plot in new_plots.items():
        results[plot_id] = {
            'absolute_path': plot['absolute_path'],
            'start_time': plot['start_time'],
            'size': plot['size'],
            'last_checked': datetime.datetime.now()
        }
        # if plot_id not in old_plots:



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

    print('\n'.join(sorted(map(str, zip(plots.keys(), map(lambda x: x['size'], plots.values()))))))

    if len(sys.argv) > 1 and sys.argv[1] == 'save':
        import json
        file = open('/Users/yyin/farming-disk.json', 'w')
        # NOTE: not using decoder to decode the dates. We don't need them parsed at this point
        old_plots = json.load(file)
        new_saved = get_new_file_content(old_plots, plots)

        from json import JSONEncoder
        class MyEncoder(JSONEncoder):
            def default(self, o):
                if isinstance(o, datetime.datetime):
                    return o.isoformat()
                return o.__dict__

        s = MyEncoder().encode(x)

