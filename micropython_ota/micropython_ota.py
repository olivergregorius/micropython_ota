import machine
from urequests import urequests
import os


def check_version(host, project):
    try:
        if 'version' in os.listdir():
            with open('version', 'r') as current_version_file:
                current_version = current_version_file.readline().strip()
        else:
            current_version = ''
        remote_version_response = urequests.get(f'{host}/{project}_version')
        if remote_version_response.status_code != 200:
            print(f'Remote version file {host}/{project}_version not found')
            return False, current_version
        remote_version = remote_version_response.text.strip()
        return current_version != remote_version, remote_version
    except Exception as ex:
        print(f'Something went wrong: {ex}')
        return False, current_version


def ota_update(host, project, filename):
    try:
        version_changed, remote_version = check_version(host, project)
        if version_changed:
            source_file_response = urequests.get(f'{host}/{project}_{remote_version}_{filename}')
            if source_file_response.status_code != 200:
                print(f'Remote source file {host}/{project}_{remote_version}_{filename} not found')
                return
            source_file_content = source_file_response.text
            with open(filename, 'w') as source_file:
                source_file.write(source_file_content)
            with open('version', 'w') as current_version_file:
                current_version_file.write(remote_version)
    except Exception as ex:
        print(f'Something went wrong: {ex}')


def check_for_ota_update(host, project):
    version_changed, remote_version = check_version(host, project)
    if version_changed:
        print(f'Found new version {remote_version}, rebooting device...')
        machine.reset()
