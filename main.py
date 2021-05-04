from dataclasses import dataclass
import pprint
import datetime
import sys

from helper import *

class NextPlotException(Exception): pass


class PlotInfo:
    def __init__(self):
        self.plot_id = ''
        self.plot_size = 0
        self.plot_total_count = 0
        self.start_time = datetime.datetime(2000, 1, 1)
        self.config_buffer_size = ''
        self.config_buckets = 0
        self.config_threads = 0
        self.config_threads_stripe_size = 0
        self.dir_tmp1 = ''
        self.dir_tmp2 = ''

    def __str__(self):
        return pprint.pformat(self.__dict__)

    @property
    def summary(self):
        return self.summary_short

    @property
    def summary_short(self):
        return SPACER.join([
            shorten_plot_id(str(self.plot_id)),
            'buffer: ' + str(self.config_buffer_size.replace('MiB', ' MiB')),
            'threads: ' + str(self.config_threads),
            'dir_tmp: ' + self.dir_tmp1 + '  ' + self.dir_tmp1 + NL,
        ])


MAX_TABLE = 7

class PlotProgress:
    def __init__(self):
        self.stages_start_time = {}
        self.stages_took_seconds = {}
        self.total_time_seconds = 0.0
        self.current_bucket = 0
        self.current_table = 0

    @property
    def current_stage(self):
        """Returns current stage. 0 is not started; 5 is finished
        """
        if self.total_time_seconds != 0.0:
            return 5
        return max([0, *self.stages_start_time.keys()])

    @property
    def current_stage_progress(self):
        def o(a, b, c, d):
            string = f'{a} / {b} of {c} / {d}'.replace(' of 1 / 1', '')
            ratio = c / d + ((1 / d) * (a / b))
            return string, ratio

        match self.current_stage:
            case 1: return o(self.current_bucket, 128, self.current_table, MAX_TABLE)
            case 2: return o(self.current_bucket, 2, self.current_table, MAX_TABLE - 1)
            case 3: return o(self.current_bucket, 110, self.current_table / 2, MAX_TABLE)
            case 4: return o(self.current_bucket, 128, 0, 1)
            case _: return 'N/A', 1

    @property
    def summary_short(self):
        s = ''
        for stage_n in range(1, self.current_stage):
            took = self.stages_took_seconds.get(stage_n, '')
            s += format_seconds(took) + '  |  '

        if self.current_stage == 5:
            start_time = format_time(self.stages_start_time[1])
            took_seconds = format_seconds(self.total_time_seconds)
            end_time = format_time(self.stages_start_time[1] + datetime.timedelta(seconds=self.total_time_seconds // 1))
            s += f'{NL} {start_time}  |   {end_time}  |  {took_seconds}'


        elif self.current_stage != 0:
            seconds_elapsed = (now_tz() - self.stages_start_time[self.current_stage]).total_seconds()

            progress_string, progress_ratio = self.current_stage_progress

            eta_seconds = (seconds_elapsed / (progress_ratio or 0.0001))
            eta_time = self.stages_start_time[self.current_stage] + datetime.timedelta(seconds=eta_seconds)
            s += f'{round(progress_ratio * 100)}% {format_time(eta_time)}'

        else:
            s += 'stage is 0'
        return s



    @property
    def summary(self):
        stages_strings = []
        for stage_n in range(1, self.current_stage):
            start_time = self.stages_start_time.get(stage_n, '')
            if start_time: start_time = format_time(start_time)

            took = self.stages_took_seconds.get(stage_n, '')
            if took: took = format_seconds(took)

            stages_strings.append(f'stage {stage_n}: {TAB} {start_time} {TAB} {took}')
        stages_strings = NL.join(stages_strings)

        current_stage_progress = ''

        if self.current_stage != 0 and self.current_stage != 5:
            started_time = self.stages_start_time[self.current_stage]
            seconds_elapsed = (now_no_tz() - started_time).total_seconds()

            progress_string, progress_ratio = self.current_stage_progress

            progress_ratio = max(0.01, min(progress_ratio, 1))
            assert 0 <= progress_ratio <= 1
            eta_seconds = seconds_elapsed * (1 - progress_ratio) / progress_ratio
            eta_time = now_no_tz() + datetime.timedelta(seconds=eta_seconds)
            current_stage_progress = f'''
stage {self.current_stage}:
    progress  {progress_string}                   {round(progress_ratio * 100)}%
    {progress_bar(progress_ratio)}
    estimated time: {format_seconds(seconds_elapsed / progress_ratio)}
    {format_time(started_time)}                     {format_time(eta_time)}
    {format_seconds(seconds_elapsed)}    {SP*45}    {format_seconds(eta_seconds)}
'''.strip()

        total_time = ''
        if self.current_stage == 5:
            total_time = 'FINISHED'
            start_time = format_time(self.stages_start_time[1])
            took_seconds = format_seconds(self.total_time_seconds)
            end_time = format_time(self.stages_start_time[1] + datetime.timedelta(seconds=self.total_time_seconds // 1))
            total_time += f'{NL} {start_time}  |   {end_time}  |  {took_seconds}'

        return f"""
started: {format_time(self.stages_start_time[1])}
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
        self.last_3_lines = []

    def __str__(self):
        return self.summary

    @property
    def summary(self):
        s = (
            '-' * 80 + NL
            + self.info.summary + NL
            + self.progress.summary + NL
        )

        if self.error != '':
            s += ('*' * 80 + NL) * 3 + self.error

        if self.last_alive != '':
            s += '\nlast alive:    ' + format_time(self.last_alive) + NL

        if len(self.last_3_lines) > 0:
            s += '\nLast 3 lines:' + '\n        '.join(['', *self.last_3_lines]) + NL

        return s

    @property
    def summary_short(self):
        return (
            self.info.summary_short +
            self.progress.summary_short + NL +
            (('*' * 20 + self.error) if self.error != '' else '')
        )

    def consume_line(self, line):
        if len(line) > 0 and line[0].startswith('2021-') and 'chia.plotting' not in ''.join(line):
            self.last_alive = parse_iso(line.pop(0))

        self.last_3_lines.append(SP.join(line))
        if len(self.last_3_lines) > 3:
            self.last_3_lines.pop(0)

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
                start_time = parse_rfc(SP.join([t1, t2, t3, t4, t5]))

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
                s = SP.join(x)
                if 'err' in s.lower():
                    self.error = s


if __name__ == '__main__':
    log_file = open('/dev/stdin', 'r')
    log = [line.strip().split() for line in log_file.readlines()]
    log_file.close()

    plots = [Plot()]
    for line in log:
        try:
            plots[-1].consume_line(line)
        except NextPlotException:
            plots.append(Plot())
            plots[-1].consume_line(line)


    if len(sys.argv) > 1 and sys.argv[1] == 'js':
        s = convert_object_to_str([p.progress for p in plots])
        print(s)

    else:
        for i, p in enumerate(reversed(plots)):
            if i == 0 and p.progress.current_stage != 5:
                print(p.summary)

            else:
                print(NL + '-' * 80)
                print(p.summary_short)
