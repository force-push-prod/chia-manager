from plot import *
import sys

from time import sleep
# config = PlotConfig(device='j', disk=3, buffer_size=8000, threads=5)
config = PlotConfig(device='mbp2', disk=2, buffer_size=8000, threads=3)

match sys.argv[1]:
    case 'case1':
        config = PlotConfig(device='mbp2', disk=1, buffer_size=8000, threads=3)
        p = Plot(config)
        sleep(7 * 3600)
        p.start()
    case 'case2':
        config = PlotConfig(device='mbp2', disk=2, buffer_size=8000, threads=3)
        p = Plot(config)
        sleep(5 * 3600)
        p.start()
    case 'case3':
        config = PlotConfig(device='j', disk=3, buffer_size=8000, threads=6)
        p = Plot(config)
        sleep(6 * 3600)
        p.start()
    case 'case-test':
        config = PlotConfig(device='mbp2', disk=3, buffer_size=8000, threads=6)
        p = Plot(config)
        print(p.command_to_watch)

    case _:
        print('Unknown case')
        exit(1)
