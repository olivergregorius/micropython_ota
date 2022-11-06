# micropython-ota

[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/olivergregorius/micropython_ota/Python%20Build?label=Python%20Build&logo=github)](https://github.com/olivergregorius/micropython_ota/actions/workflows/build.yml)
[![Python Versions](https://img.shields.io/pypi/pyversions/micropython-ota?label=Python)](https://pypi.org/project/micropython-ota/)
[![GitHub](https://img.shields.io/github/license/olivergregorius/micropython_ota?label=License)](https://github.com/olivergregorius/micropython_ota/blob/HEAD/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/micropython-ota?label=PyPI)](https://pypi.org/project/micropython-ota/)

## Introduction

Micropython library for upgrading code over-the-air (OTA)

## Preparation

For OTA updates to work an HTTP server like Apache or nGinx is required to be running and accessible by the device. This server can serve multiple devices and
multiple projects at once. The following directory structure must be provided for the OTA updates to work:

```
server-root/
|- <project_name>/
|  |- version
|  |- <version>_<filename1>
|  |- <version>_<filename2>
|  |- ...
|- <project_name>/
   |- version
   |- <version>_<filename1>
   |- <version>_<filename2>
   |- ...
```

For each project a directory must exist in the server's document root. Inside this directory a file "version" exists containing the version-tag to be pulled
by the devices, e.g. `v1.0.0`. The source code files to be pulled by the devices are placed right next to the version-file, prefixed by the version-tag.
This structure also provides the ability to do a rollback by simply changing the version-tag in the version-file to an older version-tag, as long as the
relevant source code files still reside in the directory.

In the following example two projects "sample" and "big_project" are configured:

```
server-root/
|- sample/
|  |- version <-- containing v1.0.1
|  |- v1.0.0_boot.py
|  |- v1.0.0_main.py
|  |- v1.0.1 boot.py
|  |- v1.0.1 main.py
|- big_project/
   |- version <-- containing v1.0.0
   |- v1.0.0_boot.py
   |- v1.0.0_main.py
   |- v1.0.0_data.py
```

## Installation

The library can be installed using [upip](https://docs.micropython.org/en/latest/reference/glossary.html#term-upip) or
[mip](https://docs.micropython.org/en/latest/reference/packages.html). Ensure that the device is connected to the network.

### Installation using upip (Micropython < 1.19)

```python
import upip
upip.install('micropython-ota')
```

### Installation using mip (Micropython >= 1.19)

```python
import mip
mip.install('github:olivergregorius/micropython_ota/micropython_ota.py')
```

## Usage

This library provides two methods for

1. handling code updates during boot (`ota_update`) and
2. checking for code updates at regular intervals (`check_for_ota_update`).

The `ota_update` method might be called in the boot.py file, right after the network connection has been established:

```python
import micropython_ota

# connect to network

ota_host = 'http://192.168.2.100'
project_name = 'sample'
filenames = ['boot.py', 'main.py']

micropython_ota.ota_update(ota_host, project_name, filenames, reset_device=True, timeout=5)
```

That's it. On boot the library retrieves the version-file from `http://192.168.2.100/sample/version` and evaluates its content against a locally persisted
version-file. (Of course, on the first run the local version-file does not exist, yet. This is treated as a new version being available.)
If the versions differ, the source code files listed in `filenames` are updated accordingly and on success the local version-file is updated as well. If the
`reset_device`-flag is set to `True` the device will be reset after the successful update. The flag defaults to `True`. The timeout can be set accordingly, by
default its value is 5 seconds.

For regular checking for code updates the method `check_for_ota_update` might be called in the course of the regular application logic in main.py, e.g.:

```python
import micropython_ota
import utime

ota_host = 'http://192.168.2.100'
project_name = 'sample'

while True:
    # do some other stuff
    utime.sleep(10)
    micropython_ota.check_for_ota_update(ota_host, project_name, timeout=5)
```

In this case on each iteration the library checks for a new version as described above and resets the device if a new version is available. After the reset
the `ota_update`-method called in the boot.py performs the actual update. This method accepts the timeout setting, too, by default it is set to 5 seconds.
