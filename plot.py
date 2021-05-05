import subprocess
import random
class PlotConfig():
    def __init__(self, *, device, disk, buffer_size, threads):
        self.device = device
        self.disk = disk
        self.buffer_size = buffer_size
        self.threads = threads
        self.log_path = None
        self.random_code = None

    @property
    def disk_name(self):
        match self.disk:
            case 1 | 2 | 3:
                return f'T7-{self.disk}'
            case 4:
                return 'ExFAT450'
            case _:
                assert False

    @property
    def is_ssh(self):
        return self.device in ['mbp', 'j']

    @property
    def command_to_start(self):
        if not self.random_code:
            self.random_code = str(100000 + random.randint(0, 10000))[:5]
        log_file_name = f'{self.device}-disk{self.disk}-{self.random_code}.log'

        disk_name = self.disk_name

        match self.device:
            case 'mbp2':
                bootstrap_path = '/Users/yyin/Developer/chia-manager/bootstrap.py'
                self.log_path = '/Users/yyin/' + log_file_name
                disk_path = '/Volumes/' + disk_name
                python_path = '/Users/yyin/.pyenv/shims/python'
                chia_path = '/Applications/Chia.app/Contents/Resources/app.asar.unpacked/daemon/chia'
            # case 'mbp':
            #     bootstrap_path = '/Users/yinyifei/bootstrap.py'
            #     self.log_path = '/Users/yinyifei/' + log_file_name
            #     disk_path = '/Volumes/' + disk_name
            #     python_path = '/home/yy/chia-blockchain/venv/bin/python'
            case 'j':
                bootstrap_path = '/home/yy/bootstrap.py'
                self.log_path = '/home/yy/' + log_file_name
                disk_path = '/media/yy/' + disk_name
                python_path = '/home/yy/chia-blockchain/venv/bin/python'
                chia_path = '/home/yy/chia-blockchain/venv/bin/chia'
            case _:
                assert False

        plot_command = f"""
        {python_path} {bootstrap_path} {self.log_path}
        {chia_path} plots create
            -n 1 -b {self.buffer_size} -r {self.threads}
            -t {disk_path} -2 {disk_path} -d {disk_path}
        """

        return plot_command.replace('\n', '').strip()

    # @property
    # def command_to_move(self):
    #     match self.device:
    #         case 'mbp2':
    #             return f'mv {self.disk_name}/*.plot /Volumes/Chia01'
            # case 'j':
                # return f'scp {self.disk_name}/*.plot '


class PlotProgress():
    def __init__(self):
        self.stages_start_time = {}
        self.stages_took_seconds = {}
        self.total_time_seconds = 0.0
        self.current_bucket = 0
        self.current_table = 0
        self.error = ''
        self.stages = []
        self.last_alive = ''
        self.last_3_lines = []

    def update(self, line):
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
