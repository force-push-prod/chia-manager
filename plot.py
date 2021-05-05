import subprocess
import random
class PlotConfig():
    def __init__(self, *, device, disk, buffer_size, thread, dir_tmp1, dir_dst, dir_tmp2=None):
        self.device = device
        self.disk = disk
        self.buffer_size = buffer_size
        self.thread = thread
        self.dir_tmp1 = dir_tmp1
        self.dir_tmp2 = dir_tmp2 or dir_tmp1
        self.dir_dst = dir_dst
        self.log_path = None
        self.random_code = None

    @property
    def is_ssh(self):
        pass

    @property
    def command_to_start(self):
        if not self.random_code:
            self.random_code = str(100000 + random.randint(0, 10000))[:5]
        log_file_name = f'{self.device}-disk{self.disk}-{self.random_code}.log'

        match self.disk:
            case 1 | 2 | 3:
                disk_name = f'T7-{self.disk}'
            case 4:
                disk_name = 'ExFAT450'
            case _:
                assert False

        match self.device:
            case 'mbp2':
                bootstrap_path = '/Users/yyin/Developer/chia-manager/bootstrap.py'
                self.log_path = '/Users/yyin/' + log_file_name
                disk_path = '/Volumes/' + disk_name
                ssh_name = False
            case 'mbp':
                bootstrap_path = '/Users/yinyifei/Developer/chia-manager/bootstrap.py'
                self.log_path = '/Users/yinyifei/' + log_file_name
                disk_path = '/Volumes/' + disk_name
                ssh_name = 'mbp'
            case 'j':
                bootstrap_path = '/home/yy/Developer/chia-manager/bootstrap.py'
                self.log_path = '/home/yy/' + log_file_name
                disk_path = '/media/yy/' + disk_name
                ssh_name = 'j'
            case _:
                assert False

        plot_command = f"""
        python {bootstrap_path} {self.log_path}
        chia plots create
            -n 1 -b {self.buffer_size} -r {self.threads}
            -t {disk_path} -2 {disk_path} -d {disk_path}
        """

        return plot_command.replace('\n', '').strip()


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
        command = ""
        if self.config.is_ssh:
            command = ["ssh", self.config.device, self.config.command_to_start]
        else:
            command = [self.config.command_to_start]
        self.plot_process = subprocess.Popen(command)


    def update_progress(self):
        pass

    def get_plot_logs(self):
        """Returns text of the logs from remote machine"""
        command = []
        if self.config.is_ssh:
            command.extend(['ssh', self.config.device])
        command.extend(['cat', self.config.log_file_path])
        log_process =  subprocess.run(command, stdout=subprocess.PIPE, text=True)
        return log_process.stdout