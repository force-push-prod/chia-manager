import os
import subprocess

class Manager:
    def __init__(self):
        self.log_file = "temp.log"
        self.plot_process = None
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
    def start_plot(self):
        with open("temp.log", "wb") as out:
            self.plot_process = subprocess.Popen([self.dir_path + "/test_script.sh"], stdout=out)
    def print_process_info(self):
        print(f"pid: {str(self.plot_process.pid)}")

m = Manager()
m.start_plot()
m.print_process_info()
