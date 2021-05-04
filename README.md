Some places to start:
1. Each plot appears to start with the `<timestamp> chia.plotting.create_plots ... INFO ...`
2. There are 4 phase

I want the program to:
0. most basic stuff: when did this plot start? ID of this plot? Current config (buffer size, # of buckets, # of threads)?
1. report current progress - which stage are we in?
2. report current progress - where are we in the current stage?
3. did anything error happen? See example error log for sample
4. report statistics - how long did previous stages took?
5. report statistics - how long is current stage expected to took?
6. report statistics - how long is current plot expected to took?
6. report statistics - how long did it actually took, for completed plotting logs?
7. how did we change since we last looked at the file? Are we stuck, ie. stuck on some bucket or something?

## Installation
Use `pyenv` to install `3.10-dev` version locally: `pyenv install 3.10-dev`

`pip install livereload`
