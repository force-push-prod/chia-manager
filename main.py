from email.utils import parsedate
from dataclasses import dataclass
import pprint
import datetime

from timeago import relative_format

testlog = open('/dev/stdin', 'r')
testlog = [line.strip().split() for line in testlog.readlines()]


TAB = '\t'
NL = '\n'

def parse_iso_datetime(s):
    return datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%S')


class NextPlotException(Exception): pass

def rfc_date_to_datetime(s):
    # [parsing - How to parse a RFC 2822 date/time into a Python datetime? - Stack Overflow](https://stackoverflow.com/questions/885015)
    t = parsedate(s)
    return datetime.datetime(*t[:6])

def format_time(d: datetime):
    return str(d).replace('2021-', '') + '  ' + relative_format(d)

def format_seconds(s: float | int):
    s = int(s)
    return f'({s // 3600}.{s % 3600 // 60}.{s % 60 // 1}) {s}s'

class PlotInfo:
    def __init__(self):
        self.plot_id: str = ''
        self.plot_size = 0
        self.plot_total_count = 0
        self.start_time = datetime.datetime(2000, 1, 1)
        self.config_buffer_size = ''
        self.config_buckets = 0
        self.config_threads = 0
        self.config_threads_stripe_size = 0
        self.dir_tmp1 = ''
        self.dir_tmp2 = ''
        # self.dir_dst = ''

    def __str__(self):
        return pprint.pformat(self.__dict__)

    @property
    def summary(self):
        return (
            '     id: ' + str(self.plot_id) + '\n'
            ' buffer: ' + str(self.config_buffer_size.replace('MiB', ' MiB')) + '\n'
            'threads: ' + str(self.config_threads) + '\n'
            '\n'
            'dir_tmp: ' + self.dir_tmp1 + '  ' + self.dir_tmp1 + '\n'
        )




MAX_TABLE = 7

class PlotProgress:
    def __init__(self):
        self.stages_start_time = {}
        self.stages_took_seconds = {}
        self.total_time_seconds = 0.0
        self.current_bucket = 0
        self.current_table = 0
        self.error = ''

    @property
    def current_stage(self):
        """Returns current stage. 0 is not started; 5 is finished
        """
        if self.total_time_seconds != 0.0:
            return 5
        return max([0, *self.stages_start_time.keys()])

    @property
    def current_stage_progress(self):
        # if self.current_stage == 0 or self.current_stage == 5:
        #     return 'N/A'
        def o(a, b, c, d):
            string = f'{a} / {b} of {c} / {d}'.replace(' of 1 / 1', '')
            ratio = c / d + ((1 / d) * (a / b))
            return string, ratio

        match self.current_stage:
            case 1: return o(self.current_bucket, 128, self.current_table, MAX_TABLE)
            case 2: return o(self.current_bucket, 2, 7 - self.current_table, MAX_TABLE - 1)
            case 3: return o(self.current_bucket, 110, self.current_table / 2, MAX_TABLE)
            case 4: return o(self.current_bucket, 128, 0, 1)
            case _: return 'N/A', 1

    @property
    def summary(self):
        stages_strings = []
        for stage_n in range(1, self.current_stage):
            start_time = self.stages_start_time.get(stage_n, '')
            if start_time: start_time = format_time(start_time)

            took = self.stages_took_seconds.get(stage_n, '')
            if took: took = format_seconds(took)

            stages_strings.append(f'stage {stage_n}: {TAB} {start_time} {TAB} {took}')
        stages_strings = '\n'.join(stages_strings)

        current_stage_progress = ''

        if self.current_stage != 0 and self.current_stage != 5:
            seconds_elapsed = (datetime.datetime.now() - self.stages_start_time[1]).total_seconds()

            progress_string, progress_ratio = self.current_stage_progress

            eta_seconds = (seconds_elapsed / (progress_ratio or 0.01))
            eta_time = self.stages_start_time[self.current_stage] + datetime.timedelta(seconds=eta_seconds)
            current_stage_progress = f'''
stage {self.current_stage}:
    progress  {progress_string}                   {int(progress_ratio * 100)}%
    elapsed   {format_seconds(seconds_elapsed)}
    ETA       {format_seconds(eta_seconds)}        on {format_time(eta_time)}
'''.strip()

        total_time = ''
        if self.total_time_seconds:
            total_time = 'total time: ' + format_seconds(self.total_time_seconds)

        return f"""
{stages_strings}

{current_stage_progress}

{total_time}

""".strip().replace('\n\n\n', '\n\n')


@dataclass
class Plot:
    def __init__(self):
        self.info = PlotInfo()
        self.progress = PlotProgress()
        self.error = ''
        self.last_alive = ''

    def __str__(self):
        return self.summary

    @property
    def summary(self):
        s = (
            '-' * 80 + '\n'
            '' + self.info.summary + '\n'
            '' + self.progress.summary + '\n'
        )

        if self.error != '':
            s += ('*' * 80 + '\n') * 3 + self.error

        if self.last_alive != '':
            s += '\nlast alive:    ' + relative_format(self.last_alive) + '\n'

        return s


    def consume_line(self, line):
        if len(line) > 0 and line[0].startswith('2021-') and 'chia.plotting' not in ''.join(line):
            self.last_alive = parse_iso_datetime(line.pop(0))

        match line:
            case [timestamp, 'chia.plotting.create_plots', ':', 'INFO', 'Creating', plot_total_count, 'plots', *_]:
                self.info.start_time = datetime.datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f')
                self.info.plot_total_count = int(plot_total_count)

            # Starting plotting progress into temporary dirs
            case ['Starting', 'plotting', *_, 'dirs:', dir_tmp1, 'and', dir_tmp2]:
                if self.progress.current_stage != 0:
                    raise NextPlotException()
                self.info.dir_tmp1 = dir_tmp1
                self.info.dir_tmp2 = dir_tmp2

            case ['ID:', x]: self.info.plot_id = x
            case ['Plot', 'size', 'is:', x]:    self.info.plot_size = int(x)
            case ['Buffer', 'size', 'is:', x]:  self.info.config_buffer_size = x
            case ['Using', x, 'buckets']:       self.info.config_buckets = int(x)
            case ['Using', x, 'threads', *_, 'size', y]:
                self.info.config_threads = int(x)
                self.info.config_threads_stripe_size = int(y)

            case ['Starting', 'phase', phase, *_, t1, t2, t3, t4, t5]:
                start_time = rfc_date_to_datetime(' '.join([t1, t2, t3, t4, t5]))

                phase_number = phase[0]
                assert phase_number in '1234'
                self.progress.stages_start_time[int(phase_number)] = start_time

            case ['Total', 'time', '=', x, 'seconds.', 'CPU', *_]:
                self.progress.total_time_seconds = float(x)

            case ['Time', 'for', 'phase', phase_number, '=', seconds, *_]:
                self.progress.stages_took_seconds[int(phase_number)] = float(seconds)

            # Phrase 1
            case ['Computing', 'table', x]:
                self.progress.current_table = int(x) - 1

            # Phrase 2
            case ['Backpropagating', 'on', 'table', x]:
                self.progress.current_table = MAX_TABLE - (int(x) - 1)
                self.progress.current_bucket = 0

            # Phrase 2
            case ['scanned', 'table', *_]:
                self.progress.current_bucket = 1

            # Phrase 3
            case ['Compressing tables', x, 'and', _]:
                self.progress.current_table = (int(x) - 1) * 2

            # Phrase 3
            case ['First', 'computation', 'pass', 'time', *_]:
                self.progress.current_table += 1

            # Phrase 1, 3, 4
            case ['Bucket', x, 'uniform', 'sort.', *_]:
                self.progress.current_bucket = int(x)

            case [*x]:
                s = ' '.join(x)
                if 'err' in s.lower():
                    self.error = s


plots = [Plot()]
for i, line in enumerate(testlog):
    try:
        plots[-1].consume_line(line)
    except NextPlotException:
        plots.append(Plot())
        print(plots)
        plots[-1].consume_line(line)


for p in plots:
    print(p.summary)
