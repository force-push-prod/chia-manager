import subprocess
import random


class PlotDevice():
    def __init__(self, *, is_ssh, log_dir_path, disk_dir_path, chia_path, python_path, boostrap_path):
        self.is_ssh = is_ssh
        self.log_dir_path = log_dir_path
        self.disk_dir_path = disk_dir_path
        self.chia_path = chia_path
        self.python_path = python_path
        self.boostrap_path = boostrap_path

    def execute_async_command(self, log_file_name, remote_command):
        local_command = []
        if self.is_ssh:
            local_command.extend(['ssh', self.config.device])

        log_file_path = self.log_dir_path + '/' + log_file_name
        local_command.extend([self.python_path, self.bootstrap_path, log_file_path, remote_command])

        log_process = subprocess.run(local_command, text=True, stdout=subprocess.PIPE)

        return log_process.stdout


    def execute_sync_command(self, remote_command):
        local_command = []
        if self.is_ssh:
            local_command.extend(['ssh', self.config.device])

        local_command.extend([remote_command])

        log_process = subprocess.run(local_command, text=True, stdout=subprocess.PIPE)

        return log_process.stdout


mbp2 = PlotDevice(
    is_ssh=False,
    log_dir_path='/Users/yyin/',
    disk_dir_path='/Volumes/',
    chia_path='/Applications/Chia.app/Contents/Resources/app.asar.unpacked/daemon/chia',
    python_path='/Users/yyin/.pyenv/shims/python',
    boostrap_path='/Users/yyin/Developer/chia-manager/bootstrap.py',
)


j = PlotDevice(
    is_ssh=True,
    log_dir_path='/home/yy/',
    disk_dir_path='/media/yy/',
    chia_path='/home/yy/chia-blockchain/venv/bin/chia',
    python_path='/home/yy/chia-blockchain/venv/bin/python',
    boostrap_path='/home/yy/bootstrap.py',
)


class PlotConfig():
    def __init__(self, *, device, disk_id, buffer_size, threads):
        self.device: PlotDevice = device
        self.disk_id = disk_id
        self.buffer_size = buffer_size
        self.threads = threads
        self.log_path = None
        self.random_code = None

    @property
    def disk_name(self):
        match self.disk_id:
            case 1 | 2 | 3:
                return f'T7-{self.disk_id}'
            case 4:
                return 'ExFAT450'
            case _:
                assert False

    @property
    def command_to_start(self):
        if not self.random_code:
            self.random_code = str(100000 + random.randint(0, 10000))[:5]

        log_file_name = f'{self.device}-disk{self.disk_id}-{self.random_code}.log'

        disk_path = self.device.disk_dir_path + '/' + self.disk_name

        command = f"""
        {chia_path} plots create
            -n 1 -b {self.buffer_size} -r {self.threads}
            -t {disk_path} -2 {disk_path} -d {disk_path}
            | ts %Y-%m-%dT%H:%M:%S%z
        """.replace('\n', '').strip()

        stdout = self.device.execute_command(log_file_name, command)




class PlotProgress():
    def __init__(self, log_file_lines=None):
        self.stages_start_time = {}
        self.stages_took_seconds = {}
        self.total_time_seconds = 0.0
        self.current_bucket = 0
        self.current_table = 0
        self.error = ''
        self.stages = []
        self.last_alive = ''
        self.last_3_lines = []

        if log_file_lines:
            for line in log_file_lines:
                self.consume_line(line)

    def consume_line(self, line):
        pass


class Plot():
    def __init__(self, config):
        self.config = config
        self.plot_id = None
        self.process_id = None
        self.plot_process = None
        self.start_time = None
        self.progress = None

    def start(self):
        command = None
        if self.config.is_ssh:
            command = ["ssh", self.config.device, self.config.command_to_start]
        else:
            command = self.config.command_to_start.split()
        self.plot_process = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if self.plot_process.returncode != 0:
            print('*' * 40)
            print(self.plot_process.stderr)
            print('*' * 40)
            return
        self.process_id = int(self.plot_process.stdout.strip()) + 1

        print('Started plotting process. pid=' + str(self.process_id))
        print('Start watching the log with:\n')
        print(self.command_to_watch)


    def update_progress(self):
        pass

    def get_plot_logs(self):
        """Returns text of the logs from remote machine"""
        command = []
        if self.config.is_ssh:
            command.extend(['ssh', self.config.device])
        command.extend(['cat', self.config.log_path])
        log_process = subprocess.run(command, text=True, stdout=subprocess.PIPE)
        return log_process.stdout

    @property
    def command_to_watch(self):
        command = []
        if self.config.is_ssh:
            command.extend(['ssh', self.config.device])
        command.extend(['cat', self.config.log_path or '???'])

        return 'watch -n 180 "' + ' '.join(command) + ' | python ~/Developer/chia-manager/main.py"'
