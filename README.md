# Chia Plotting Manager

Manage chia plotting on different devices & disks over SSH.

More specifically,
- Keep tracks of plotting processes
- Create new plotting process when certain conditions are met (for example, when idle)
- Move finished plots to storage device
- Print the plotting progress by parsing plotting log
- All of these works for macOS/Linux machine, locally, or over ssh
- No plotting process "relies" on the manager node; if network is down, or this software crashed, existing plotting process still continues
- Have 0 python dependencies


**This is in no way a finished product. A small number of things are hard-coded. Modifying  code is necessary if you want to use it yourself.**


## Files
- `helper/`: mostly date-related functions:
    - get date (with | without) timezone, as (datetime | string)
    - parse datetime from (iso8601 | rfc2822) format
    - format relative datetime, time range, etc
    - and other misc functions

- `bootstrap.py`: a bootstrap file that help to execute remote commands.
- `manager.py`: the manager that puts everything together. Modify the configs or the conditions for your setup.
- `plot.py`: all data structures, classes.


## Prerequisites

### Manager Node
This manager process needs Python 3.10, due to its heavy use of structural pattern matching.

Use `pyenv` to install `3.10-dev` version locally.
```
pyenv install 3.10-dev
```

### Worker Node

The following configuration is required for each worker node machine.


#### SSH
- Manager node can ssh into each worker node, without prompt of a password.
- Each worker node can ssh into the final storage, without prompt of a password.

#### Chia
Install chia, import your private key. Don't start full node.

#### `ts`
The program relies on the `ts` program from [`moreutils`](https://joeyh.name/code/moreutils/) to add timestamps to every line of the log. Use the appropriate package manager for your distro to install it.

```
brew/apt/etc install moreutils
```

#### Python
Python is needed to run the `bootstrap.py` file. Any modern version should be fine.


#### `bootstrap.py`
Each worker node need a copy of the `bootstrap.py`. The path of the file can be arbitrary and needs to be specified in the config.

```
scp bootstrap.py target:~/
```

#### For macOS
Because chia uses the macOS keychain to storage your private key, when you ssh into the machine, the keychain is not unlocked. To unlock it automatically, add the following command to your `.bashrc` (or the rc file for your shell).

```
security unlock-keychain -p '<your login password>' ~/Library/Keychains/login.keychain`
```

> Be advised that your login password will be and needs to be stored in plain text, in that file. Evaluate the risk for yourself.


## Start

It is recommend to start the interactive python repl, so that it's easier to inspect/modify things on the fly.

```
python -i manager.py
```

Assuming you have updated your configurations, start the main event loop:
```
>>> m.main_loop()
```
