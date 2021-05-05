import subprocess
import sys

    def start_plot(self, command=None, log_file=None):
        with open(sys.argv[1], 'wb') as out:
            self.plot_process = subprocess.Popen(' '.join(sys.argv[2:]) + ' | ts %Y-%m-%dT%H:%M:%S%z', stdout=out, stderr=out, shell=True)

    with open(sys.argv[1], 'wb') as out:
        plot_process = subprocess.Popen(sys.argv[2:], stdout=out, stderr=out)

    print(plot_process.pid)
