import os
import subprocess
import sys
class BootStrap:
    """ First Argument is the location of the log file, next are the actual commands"""
    def __init__(self):
        self.plot_process = None

    def start_plot(self, command=None, log_file=None):
        with open(sys.argv[1], 'wb') as out:
            self.plot_process = subprocess.Popen(' '.join(sys.argv[2:]) + ' | ts %Y-%m-%dT%H:%M:%S%z', stdout=out, stderr=out, shell=True)

    def print_process_info(self):
        print(self.plot_process.pid)

if __name__ == '__main__':
    m = BootStrap()
    m.start_plot()
    m.print_process_info()
