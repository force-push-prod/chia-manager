import subprocess

from helper import *
import base64
import logging
from dataclasses import dataclass


def encode(s):
    return base64.b32encode(s.encode()).decode()

logger_device = logging.getLogger('device')

MAX_TABLE = 7

@dataclass(frozen=True)
class PlotDevice():
    human_friendly_name: str
    ssh_name: str
    log_dir_path: str
    disk_dir_path: str
    chia_path: str
    python_path: str
    bootstrap_path: str

    def __repr__(self):
        return f'<Device {self.human_friendly_name}>'

    def execute_no_wait_command(self, log_file_name, remote_command):
        log_file_path = self.construct_log_file_path(log_file_name)

        local_command = [self.python_path, self.bootstrap_path, log_file_path, encode(remote_command)]

        if self.ssh_name:
            local_command = ['ssh', self.ssh_name, *local_command]

        logger_device.debug('Execute no wait on %s: \'%s\'', self, local_command)
        process = subprocess.run(local_command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process.stderr, process.stdout


    def execute_and_wait_command(self, command_components):
        local_command = command_components

        if self.ssh_name:
            local_command = ['ssh', self.ssh_name, *local_command]

        logger_device.debug('Execute and wait on %s: %s', self, local_command)
        process = subprocess.run(local_command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process.stderr, process.stdout


    def execute_and_wait_command_shell(self, shell_command):
        local_command = shell_command

        if self.ssh_name:
            local_command = SP.join(['ssh', self.ssh_name, local_command])

        logger_device.debug('Execute shell on %s: \'%s\'', self, local_command)
        process = subprocess.run(local_command, text=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process.stderr, process.stdout


    def construct_log_file_path(self, file_name):
        return self.log_dir_path + file_name


@dataclass(frozen=True)
class PlotConfig():
    buffer: int = 0
    threads: int = 0

    def __repr__(self):
        return f"(buffer={self.buffer} threads={self.threads})"


@dataclass(frozen=True)
class PlotDisk():
    disk_volume_name: str

    def __repr__(self):
        return f'<Disk {self.disk_volume_name}>'


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
        return f'<Progress {id_str} alive={format_time_relative_safe(self.last_alive)} [ {self.current_stage} {self.current_stage_progress_str}>'

    @property
    def current_stage(self):
        """
        0 is not started. 5 is finished. 1 to 4 correspond to 4 stages of the mining.
        """
        if self.total_time_seconds != 0.0:
            return 5
        return max([0, *self.stages_start_time.keys()])

    @property
    def current_stage_progress_str(self):
        def o(a, b, c, d):
            string = f'{a} / {b} of {c} / {d}'.replace(' of 1 / 1', '')
            ratio = c / d + ((1 / d) * (a / b))
            return string, ratio

        match self.current_stage:
            case 1: s, r = o(self.current_bucket, 128, self.current_table, MAX_TABLE)
            case 2: s, r = o(self.current_bucket, 2, self.current_table, MAX_TABLE - 1)
            case 3: s, r = o(self.current_bucket, 110, self.current_table / 2, MAX_TABLE)
            case 4: s, r = o(self.current_bucket, 128, 0, 1)
            case _: s, r = 'N/A', 0.0

        return f'{round(r * 100)}% ] \'{s}\''


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



logger_process = logging.getLogger('process')


class Process():
    def __init__(self, device: PlotDevice, log_file_name=None):
        self._device = device
        if log_file_name is not None:
            self._log_file_name = log_file_name.replace('.log', '') + '.log'  # Handles cases with and without '.log'
        else:
            self._log_file_name = unique_file_name() + '.log'
        self._output = None
        self._is_dead: bool = False
        self._started_on: datetime.datetime = None
        self._last_fetched: datetime.datetime = None
        self._last_output_changed: datetime.datetime = None
        self._pid: int = 0

    def __repr__(self):
        match [self._pid, self._is_dead]:
            case [0, _]:
                s = 'NOT STARTED'
            case [_, True]:
                s = 'DEAD'
            case [_, False]:
                s = 'RUNNING'
            case _:
                assert False

        t1 = format_time_relative_safe(self._started_on)
        t2 = format_time_relative_safe(self._last_fetched)
        t3 = format_time_relative_safe(self._last_output_changed)
        return f'<{self.__class__.__name__} {s} {self._log_file_name} pid={self._pid} started={t1} checked={t2} changed={t3}>'

    @property
    def output_cached(self):
        return self._output

    @property
    def is_running_cached(self):
        return self._pid and not self._is_dead

    def fetch(self):
        self._update_output()
        self._check_alive()
        self._last_fetched = now_tz()

    def start(self, command):
        if self._is_dead or self._pid != 0:
            logger_process.error('Cannot start an active or dead process')
            return

        _do_not_run_command = False
        if _do_not_run_command:
            logger_process.critical('NOT ACTUALLY STARTING: %s', command)
            return

        stderr, stdout = self._device.execute_no_wait_command(self._log_file_name, command)
        if stderr != '':
            logger_process.critical('Expect stderr to be empty, got: %s', stderr)
        try:
            pid = int(stdout)
        except Exception as e:
            pid = 0
            logger_process.critical('Cannot convert stdout to int; got error %s', e)
            logger_process.critical('stdout is %s', stdout)

        self._started_on = now_tz()
        self._pid = pid


    def _update_output(self):
        stderr, stdout = self._device.execute_and_wait_command(['cat', self._device.construct_log_file_path(self._log_file_name)])
        if stderr != '':
            logger_process.critical('Expect stderr to be empty, got: %s', stderr)

        if self._output != stdout:
            self._last_output_changed = now_tz()

        self._output = stdout


    def _check_alive(self):
        if self._pid == 0:
            logger_process.debug('Not checking alive for pid = 0')
            return

        if self._is_dead:
            logger_process.debug('Not checking alive for dead process')
            return

        stderr, stdout = self._device.execute_and_wait_command(['ps', str(self._pid)])
        if stderr != '':
            logger_process.critical('Expect stderr to be empty, got: %s', stderr)
            return

        match stdout.strip().split():
            case ['PID', _, 'STAT', 'TIME', 'COMMAND', pid, tt, stat, time, *commands]:
                self._is_dead = False

            case ['PID', _, 'STAT', 'TIME', 'COMMAND']:
                self._is_dead = True

            case _:
                logger_process.critical('Unexpected stdout match: %s', stdout)



class PlotProcess(Process):
    def __init__(self, device: PlotDevice, disk: PlotDisk, config: PlotConfig, log_file_name=None):
        super().__init__(device=device, log_file_name=log_file_name)
        self._disk = disk
        self._config = config
        self.progress = PlotProgress()

    def __repr__(self):
        return super().__repr__().replace('>', f' disk={self._disk} config={self._config}>')

    def fetch(self):
        super().fetch()
        try:
            self.progress = PlotProgress((self.output_cached or '').split('\n'))
        except Exception as e:
            logger_process.error('Unable to parse the output to PlotProgress; Maybe an error was contained in the output')
            logger_process.error('The exception was: %s', e)
            logger_process.error('The entire output was: %s', self.output_cached)
            self.progress = PlotProgress()

    def start(self):
        device = self._device
        disk = self._disk
        config = self._config

        disk_path = device.disk_dir_path + disk.disk_volume_name

        command = f"""

            {device.chia_path} plots create
                -n 1 -b {config.buffer} -r {config.threads}
                -t {disk_path} -2 {disk_path} -d {disk_path}
                2>&1 | ts %Y-%m-%dT%H:%M:%S%z

        """.replace('\n', '').strip()

        super().start(command)


class MoveFileToChiaOverSSHProcess(Process):
    def __init__(self, device: PlotDevice, file_path: str, log_file_name=None):
        super().__init__(device=device, log_file_name=log_file_name)
        self._file_path = file_path

    def fetch(self):
        super().fetch()
        if len(self.output_cached) > 0:
            logger_process.critical('Move had an abnormal output: %s', self.output_cached)

    def start(self):
        file_path = self._file_path

        command = f"""scp {file_path} r1:/share/Chia02/ && rm {file_path}"""

        super().start(command)

