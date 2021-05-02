from email.utils import parsedate
from dataclasses import dataclass
import pprint
import datetime

from timeago import relative_format

testlog = open('testlog.log', 'r')
testlog = [line.strip().split() for line in testlog.readlines()]

def rfc_date_to_datetime(s):
    # [parsing - How to parse a RFC 2822 date/time into a Python datetime? - Stack Overflow](https://stackoverflow.com/questions/885015)
    t = parsedate(s)
    return datetime.datetime(*t[:6])

def format_time(d: datetime):
    return str(d).replace('2021-', '') + '  ' + relative_format(d)

def format_seconds(s: float | int):
    s = int(s)
    return f'({s // 3600}.{s % 3600 // 60}.{s % 60 // 1}) {s}s'

@dataclass
class PlotInfo:
    plot_id = ''
    plot_size = 0
    plot_total_count = 0
    start_time = datetime.datetime(2000, 1, 1)
    config_buffer_size = ''
    config_buckets = 0
    config_threads = 0
    config_threads_stripe_size = 0
    dir_tmp1 = ''
    dir_tmp2 = ''
    # dir_dst = ''

    def __str__(self):
        return pprint.pformat(self.__dict__)

# @dataclass
# class PlotState:
#     stage = 0
#     current_bucket = 0
#     error = ''

@dataclass(init=True)
class PlotProgress:
    stages_start_time = {}
    stages_took_seconds = {}
    total_time_seconds = 0
    current_bucket = 0

    def __str__(self):
        return pprint.pformat({
            'total_time_seconds': self.total_time_seconds,
            'current_bucket': self.current_bucket,
            'stages_start_time': { k: format_time(v) for k, v in self.stages_start_time.items()},
        })

    @property
    def current_stage(self):
        """Returns current stage. 0 is not started; 5 is finished
        """
        if self.total_time_seconds:
            return 5
        return max([0, *self.stages_start_time.keys()])

    @property
    def summary(self):
        if self.current_stage == 0:
            status = '-'
        elif self.current_stage == 5:
            status = 'finished'
        else:
            status = 'stage ' + self.current_stage

        stages_strings = []
        for stage_n in range(1, 5):
            start_time = self.stages_start_time.get(stage_n, '')
            if start_time: start_time = format_time(start_time)

            took = self.stages_took_seconds.get(stage_n, '')
            if took: took = format_seconds(took)

            stages_strings.append('Stage ' + str(stage_n) + '   ' + str(took) + '\t  ' + str(start_time))
        stages_strings = '\n'.join(stages_strings)

        total_time = format_seconds(self.total_time_seconds) if self.total_time_seconds else '-'

        return f"""
status: {status}

{stages_strings}

total time: {total_time}
        """

@dataclass
class Plot:
    info = PlotInfo()
    progress = PlotProgress()

    def __str__(self):
        return str(self.info) + '\n' + str(self.progress)

    def consume_line(self, line):
        match line:
            case [timestamp, 'chia.plotting.create_plots', ':', 'INFO', 'Creating', plot_total_count, 'plots', *_]:
                self.info.start_time = datetime.datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f')
                self.info.plot_total_count = int(plot_total_count)

            # Starting plotting progress into temporary dirs
            case ['Starting', 'plotting', *_, 'dirs:', dir_tmp1, 'and', dir_tmp2]:
                self.info.dir_tmp1 = dir_tmp1
                self.info.dir_tmp2 = dir_tmp2

            case ['ID:', x]: self.info.plot_id = x
            case ['Plot', 'size', 'is:', x]: self.info.plot_size = int(x)
            case ['Buffer', 'size', 'is:', x]: self.info.config_buffer_size = x
            case ['Using', x, 'buckets']: self.info.config_buckets = int(x)
            case ['Using', x, 'threads', _, 'size', y]:
                self.info.config_threads = int(x)
                self.info.config_threads_stripe_size = int(y)

            case ['Starting', 'phase', phase, *_, t1, t2, t3, t4, t5]:
                start_time = rfc_date_to_datetime(' '.join([t1, t2, t3, t4, t5]))

                phase_number = phase[0]
                assert phase_number in '1234'
                # breakpoint()
                self.progress.stages_start_time[int(phase_number)] = start_time

            case ['Bucket', x, 'uniform', 'sort.', *_]:
                self.progress.current_bucket = int(x)

            case ['Total', 'time', '=', x, 'seconds.', 'CPU', *_]:
                self.progress.total_time_seconds = float(x)

            case ['Time', 'for', 'phase', phase_number, '=', seconds, *_, t1, t2, t3, t4, t5]:
                # finish_time = rfc_date_to_datetime(' '.join(t1, t2, t3, t4, t5))
                self.progress.stages_took_seconds[int(phase_number)] = float(seconds)

            case [_]:
                pass

p = Plot()
for line in testlog:
    p.consume_line(line)

# print(p)
print(p.progress.summary)
