class PlotConfig():
    def __init__(self, *, device, disk, buffer_size, thread, dir_tmp1, dir_dst, dir_tmp2=None):
        self.device = device
        self.disk = disk
        self.buffer_size = buffer_size
        self.thread = thread
        self.dir_tmp1 = dir_tmp1
        self.dir_tmp2 = dir_tmp2 or dir_tmp1
        self.dir_dst = dir_dst

    @property
    def log_file_path(self):
        pass

    @property
    def is_ssh(self):
        pass

    @property
    def command_to_start(self):
        pass


class Stage1():
    def __init__(self):
        pass


class PlotProgress():
    def __init__(self):
        # self.stages_start_time = {}
        # self.stages_took_seconds = {}
        # self.total_time_seconds = 0.0
        # self.current_bucket = 0
        # self.current_table = 0
        # self.error = ''
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
        pass

    def update_progress(self):
        pass
