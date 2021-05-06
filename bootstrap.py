import subprocess
import sys
import base64

def decode(s):
    return base64.b32decode(s.encode()).decode()

if __name__ == '__main__':

    if len(sys.argv) < 2:
        print('Too few arguments.')
        exit(1)

    with open(sys.argv[1], 'wb') as out:
        plot_process = subprocess.Popen(
            decode(sys.argv[2]),
            stdout=out,
            stderr=out,
            shell=True
        )

    # print pid to stdout
    print(plot_process.pid)
