Use `pyenv` to install `3.10-dev` version locally: `pyenv install 3.10-dev`

- `brew/apt install moreutils` for `ts`
- `scp bootstrap.py target:~/`
- Ensure target machine can ssh into storage machine
- Ensure `ssh sp 'echo 1 | ts'` does not give error
- macOS: ensure keychain is unlocked `security unlock-keychain -p 'password' ~/Library/Keychains/login.keychain`
