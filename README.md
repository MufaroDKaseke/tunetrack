# TuneTrack

## Sources

1. Git (https://github.com/MufaroDKaseke/tunetrack.git)
2. Folder on raspberry pi
```bash
/home/ctrlaltwin/tunetrack
```

## Creadentials

1. User
    Username : ctrlaltwin
    Password: python2019

2. SSH
    <i>Login with user</i>

3. Wifi
    SSID : ctrlaltwin
    Password: python2019

## Environment Setup

1. Update package sources
```bash
sudo apt update
```

2. Upgrade any packages that are not up to date
```bash
sudo apt upgrade
```

3. Install 3 packages we need
    - ffmpeg
    - chromaprint (for audio fingerprinting)
    - sqlite3 (for SQLite database)

```bash
sudo apt install ffmpeg chromaprint sqlite3
```

