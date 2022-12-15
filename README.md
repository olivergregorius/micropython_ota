# micropython-ota

[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/olivergregorius/micropython_ota/Python%20Build?label=Python%20Build&logo=github)](https://github.com/olivergregorius/micropython_ota/actions/workflows/build.yml)
[![Python Versions](https://img.shields.io/pypi/pyversions/micropython-ota?label=Python)](https://pypi.org/project/micropython-ota/)
[![GitHub](https://img.shields.io/github/license/olivergregorius/micropython_ota?label=License)](https://github.com/olivergregorius/micropython_ota/blob/HEAD/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/micropython-ota?label=PyPI)](https://pypi.org/project/micropython-ota/)

## Introduction

Micropython library for upgrading code over-the-air (OTA)

## Preparation

For OTA updates to work an HTTP/HTTPS server like Apache or nGinx is required to be running and accessible by the device. This server can serve multiple devices
and multiple projects at once. There are two supported directory structures of which one must be provided for the OTA updates to work:

1. Version as prefix (default)
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

2. Version as subdirectory (by setting the parameter `use_version_prefix` to `False`, see [Usage](#usage))
    ```
    server-root/
    |- <project_name>/
    |  |- version
    |  |- <version_subdir>
    |     |- <filename1>
    |     |- <filename2>
    |     |- ...
    |- <project_name>/
       |- version
       |- <version_subdir>
          |- <filename1>
          |- <filename2>
          |- ...
    ```

For each project a directory must exist in the server's document root. Inside this directory a file "version" exists containing the version-tag to be pulled
by the devices, e.g. `v1.0.0`. The source code files to be pulled by the devices are placed either right next to the version-file, prefixed by the version-tag,
or in a subdirectory named with the version-tag.
This structure also provides the ability to do a rollback by simply changing the version-tag in the version-file to an older version-tag, as long as the
relevant source code files still reside in the expected location.

In the following example two projects "sample" and "big_project" are configured, using the default, version-prefixed directory structure:

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

#### Py-file

```python
import mip
mip.install('github:olivergregorius/micropython_ota/micropython_ota.py')
```

#### Cross-compiled mpy-file

**NOTE**: Set the release_version variable accordingly.

```python
import mip
release_version='vX.Y.Z'
mip.install(f'https://github.com/olivergregorius/micropython_ota/releases/download/{release_version}/micropython_ota.mpy')
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

micropython_ota.ota_update(ota_host, project_name, filenames, use_version_prefix=True, hard_reset_device=True, soft_reset_device=False, timeout=5)
```

That's it. On boot the library retrieves the version-file from `http://192.168.2.100/sample/version` and evaluates its content against a locally persisted
version-file. (Of course, on the first run the local version-file does not exist, yet. This is treated as a new version being available.)
If the versions differ, the source code files listed in `filenames` are updated accordingly and on success the local version-file is updated as well. If the
`use_version_prefix` is set to True (default) the library expects the 'Version as prefix' directory structure on the server, otherwise it expects the 'Version
as subdirectory' directory structure (see [Preparation](#preparation)). If the `hard_reset_device`-flag is set to `True` (default) the device will be reset
after the successful update by calling `machine.reset()`. For just soft-resetting the device the flag `soft_reset_device` can be set to `True` (defaults to
`False`), taking precedence. This will call the `machine.soft_reset()`-method. The timeout can be set accordingly, by default its value is 5 seconds.

For regular checking for code updates the method `check_for_ota_update` might be called in the course of the regular application logic in main.py, e.g.:

```python
import micropython_ota
import utime

ota_host = 'http://192.168.2.100'
project_name = 'sample'

while True:
    # do some other stuff
    utime.sleep(10)
    micropython_ota.check_for_ota_update(ota_host, project_name, soft_reset_device=False, timeout=5)
```

In this case on each iteration the library checks for a new version as described above and resets the device if a new version is available. By default a
hard-reset is performed (by calling `machine.reset()`). By setting the flag `soft_reset_device` to `True` (defaults to `False`) the device will just be
soft-reset (by calling `machine.soft_reset()`). After the reset the `ota_update`-method called in the boot.py performs the actual update. This method accepts
the timeout setting, too, by default it is set to 5 seconds.

## HTTP(S) Basic Authentication

`ota_update()` and `check_for_ota_update()` methods allow optional `user` and `passwd` parameters.  When specified the library performs a basic authentication
against the server hosting the source files.  Use of HTTPS (versus HTTP) is very highly recommended when using basic authentication as, otherwise, the resulting
username and password are sent as plain text i.e. completely unsecure.

Here is the same example as above, but using HTTPS and Basic Authentication:

```python
import micropython_ota

# connect to network

ota_host = 'https://example.com'
project_name = 'sample'
filenames = ['boot.py', 'main.py']
user = 'otauser'
passwd = 'topsecret' # it's best to place this credential is a secrets.py file

micropython_ota.ota_update(ota_host, project_name, filenames, user=user, passwd=passwd, use_version_prefix=True, hard_reset_device=True, soft_reset_device=False, timeout=5)
```

There are plenty of tutorials online on how to set up secured HTTP file access on your webserver, but the basic steps are:
- get and install an SSL certificate (Let's Encrypt is by far the best choice)
- enable HTTPS access on your web server
- prevent directories from listing files
- enable HTTP Basic Authentication password protection on target directories
