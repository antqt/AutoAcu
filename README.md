## Automatic Acunetix
```
usage: app.py [-h] [--threads THREADS] [--speed SPEED] [--host HOST] URLs_File

Make the automatic task more automatic.

positional arguments:
  URLs_File          List of urls

optional arguments:
  -h, --help         show this help message and exit
  --threads THREADS  Number of tasks that run simultaneously.
  --speed SPEED      The speed of the scan.
  --host HOST        The host of the acunetix.
```

### Install
```bash
pip3 install -r requirements.txt 
```
### Setup
#### 1.Create API token

#### 2.Create .env

```
API="<Token>"
```

#### 3.Create file list of urls need scan name "urls.txt"

#### 4.Run file

```
python3 app.py
```
