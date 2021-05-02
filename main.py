import datetime
from dataclasses import dataclass

testlog = open("testlog.log", 'r')
testlog = [line.strip().split() for line in testlog.readlines()]

@dataclass
class Plot:
    id: str = ""
    start_time: datetime = datetime.datetime.now()
    plot_size: int = 0
    buffer_size: str = ""
    buckets: int = 0
    threads: int = 0
    dirs: list = None
    stage: int = 0
    stage_message: str = ""

plot = Plot()

for line in testlog:
    match line:
        case [timestamp, "chia.plotting.create_plots", ":", "INFO", message]:
            parsed_time = datetime.datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f')
            plot.start_time = parsed_time
        case ['Starting', 'plotting', 'progress', 'into', 'temporary', 'dirs:', *dirs]:
            plot.dirs = dirs
        case ['ID:', id_val]:
            plot.id = id_val
        case ['Plot', 'size', 'is:', plot_size]:
            plot.plot_size = int(plot_size)
        case ['Buffer', 'size', 'is:', buffer_size]:
            plot.buffer_size = buffer_size
        case ['Using', buckets, 'buckets']:
            plot.buckets = int(buckets)
        case ['Using', threads, 'threads', 'of', 'stripe', 'size', size]:
            plot.threads = int(threads)
        case ['Starting', 'phase', phase_num, *message]:
            plot.stage = int(phase_num[0])
            plot.stage_message = ' '.join(message)

        case _:
            pass
print(plot)
print(f"Current Stage is: {plot.stage}")
print(plot.stage_message)