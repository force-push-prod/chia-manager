import os
import subprocess
import datetime

class Manager:
    def __init__(self):
        self.log_file = "temp.log"
        self.plot_process = None
        self.start_time = None
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.command = self.dir_path + "/test_script.sh"

    def start_plot(self, command=None, log_file=None):
        if log_file:
            self.log_file = log_file
        if command:
            self.command = command
        self.start_time = datetime.datetime.now()

        with open(self.log_file, "wb") as out:
            self.plot_process = subprocess.Popen([self.command], stdout=out, stderr=out)

    def print_process_info(self):
        print(f"pid: {self.plot_process.pid}")

if __name__ == '__main__':
    m = Manager()
    m.start_plot()
    m.print_process_info()
