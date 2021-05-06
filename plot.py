import subprocess

from helper import *
import base64

def encode(s):
    return base64.b32encode(s.encode()).decode()

class PlotDevice():
    def __init__(self, *, ssh_name, log_dir_path, disk_dir_path, chia_path, python_path, bootstrap_path):
        self.ssh_name = ssh_name
        self.log_dir_path = log_dir_path
        self.disk_dir_path = disk_dir_path
        self.chia_path = chia_path
        self.python_path = python_path
        self.bootstrap_path = bootstrap_path
        self.disks: list[PlotDisk] = []

    def __repr__(self):
        # TODO: hardcoded value
        return 'Device(' + (self.ssh_name or 'mbp2') + ')'

    def add_disk(self, disk):
        self.disks.append(disk)

    def execute_no_wait_command(self, log_file_name, remote_command):
        log_file_path = self.construct_log_file_path(log_file_name)

        local_command = [self.python_path, self.bootstrap_path, log_file_path, encode(remote_command)]

        if self.ssh_name:
            local_command = ['ssh', self.ssh_name, *local_command]

        print('EXECUTING no wait:', local_command)
        process = subprocess.run(local_command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process.stderr, process.stdout


    def execute_and_wait_command(self, command_components):
        local_command = command_components

        if self.ssh_name:
            local_command = ['ssh', self.ssh_name, *local_command]

        print('EXECUTING no shell:', local_command)
        process = subprocess.run(local_command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process.stderr, process.stdout

    def execute_and_wait_command_shell(self, shell_command):
        local_command = shell_command

        if self.ssh_name:
            local_command = SP.join(['ssh', self.ssh_name, local_command])

        print('EXECUTING shell:', local_command)
        process = subprocess.run(local_command, text=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process.stderr, process.stdout


    def construct_log_file_path(self, file_name):
        return self.log_dir_path + file_name


@dataclass(init=True, repr=True, frozen=True)
class PlotConfig():
    buffer: int = 0
    threads: int = 0


class PlotDisk():
    def __init__(self, disk_volume_name):
        assert disk_volume_name in ['T7-1', 'T7-2', 'T7-3', 'ExFAT450']
        self.disk_volume_name: str = disk_volume_name
        self.plots: list[Plot] = []

    def __repr__(self):
        return f'Disk({self.disk_volume_name})'

    def add_plot(self, plot):
        self.plots.append(plot)

    @property
    def is_idle(self):
        for plot in self.plots:
            if plot.current_stage != 5 and plot.current_stage != 0:
                return False
        return True


class PlotProgress():
    def __init__(self, log_file_lines=None):
        self.plot_id = ''
        self.stages_start_time = {}
        self.stages_took_seconds = {}
        self.total_time_seconds = 0.0
        self.current_bucket = 0
        self.current_table = 0
        self.error = ''
        self.last_alive = ''
        self.last_3_lines = []

        if log_file_lines:
            for line in log_file_lines:
                self.consume_line(line)

    def __repr__(self):
        if self.plot_id:
            id_str = shorten_plot_id(self.plot_id)
        else:
            id_str = 'None'
        return f'Progress({id_str}, stage={self.current_stage}, table={self.current_table}, bucket={self.current_bucket})'

    @property
    def current_stage(self):
        """
        0 is not started. 5 is finished. 1 to 4 correspond to 4 stages of the mining.
        """
        if self.total_time_seconds != 0.0:
            return 5
        return max([0, *self.stages_start_time.keys()])


    def consume_line(self, line_raw: str):
        MAX_TABLE = 7
        line: list[str] = line_raw.strip().split()

        if len(line) == 0:
            return

        line_timestamp = parse_iso(line.pop(0))
        self.last_alive = line_timestamp

        self.last_3_lines.append(SP.join(line))
        if len(self.last_3_lines) > 3: self.last_3_lines.pop(0)

        match line:
            case ['Starting', 'plotting', *_, 'dirs:', _, 'and', _]:
                if self.current_stage != 0:
                    raise Exception('NextPlot')

            case ['ID:', x]: self.plot_id = x

            case ['Starting', 'phase', phase, *_]:
                start_time = line_timestamp
                phase_number = phase[0]
                assert phase_number in '1234'
                self.stages_start_time[int(phase_number)] = start_time

            case ['Total', 'time', '=', x, 'seconds.', 'CPU', *_]:
                self.total_time_seconds = float(x)

            case ['Time', 'for', 'phase', phase_number, '=', seconds, *_]:
                self.stages_took_seconds[int(phase_number)] = float(seconds)

            # Phrase 1
            case ['Computing', 'table', x]:
                self.current_table = int(x) - 1

            # Phrase 2
            case ['Backpropagating', 'on', 'table', x]:
                self.current_table = MAX_TABLE - (int(x) - 1)
                self.current_bucket = 0

            # Phrase 2
            case ['scanned', 'table', *_]:
                self.current_bucket = 1

            # Phrase 3
            case ['Compressing tables', x, 'and', _]:
                self.current_table = (int(x) - 1) * 2

            # Phrase 3
            case ['First', 'computation', 'pass', 'time', *_]:
                self.current_table += 1

            # Phrase 1, 3, 4
            case ['Bucket', x, 'uniform', 'sort.', *_]:
                self.current_bucket = int(x)

            case [*x]:
                s = SP.join(x)
                if 'err' in s.lower():
                    self.error = s



class Plot():
    def __init__(self, log_file_name=None):
        if log_file_name is not None:
            self.log_file_name = log_file_name.replace('.log', '') + '.log'  # Handles cases with and without '.log'
        else:
            self.log_file_name = hex(now_epoch_seconds()) + '.log'
        self.progress = PlotProgress()
        self.pid = 0

    def __repr__(self):
        return f'Plot({self.log_file_name}, {self.progress.__repr__()})'

    @property
    def current_stage(self):
        return self.progress.current_stage

    def set_new_progress_get_signals(self, new_progress: PlotProgress):
        old_progress = self.progress
        self.progress = new_progress

        signals = []
        if old_progress.current_stage != new_progress.current_stage:
            # assert new_progress.current_stage - old_progress.current_stage == 1
            signals.append(StageUpdateSignal(before=old_progress.current_stage, after=new_progress.current_stage))

        return signals
