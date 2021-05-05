import subprocess
import sys

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Too few arguments.')
        exit(1)

    with open(sys.argv[1], 'wb') as out:
        plot_process = subprocess.Popen(
            ' '.join(sys.argv[2:]) + ' | ts %Y-%m-%dT%H:%M:%S%z',
            stdout=out,
            stderr=out,
            shell=True
        )
    print(plot_process.pid)
