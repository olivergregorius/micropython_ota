import machine
import urequests
import uos


def check_version(host, project, timeout=5):
    try:
        if 'version' in uos.listdir():
            with open('version', 'r') as current_version_file:
                current_version = current_version_file.readline().strip()
        else:
            current_version = ''
        response = urequests.get(f'{host}/{project}/version', timeout=timeout)
        response_status_code = response.status_code
        response_text = response.text
        response.close()
        if response_status_code != 200:
            print(f'Remote version file {host}/{project}/version not found')
            return False, current_version
        remote_version = response_text.strip()
        return current_version != remote_version, remote_version
    except Exception as ex:
        print(f'Something went wrong: {ex}')
        return False, current_version


def ota_update(host, project, filenames, use_version_prefix=True, reset_device=True, timeout=5):
    all_files_found = True
    prefix_or_path_separator = '_' if use_version_prefix else '/'
    try:
        version_changed, remote_version = check_version(host, project, timeout=timeout)
        if version_changed:
            for filename in filenames:
                response = urequests.get(f'{host}/{project}/{remote_version}{prefix_or_path_separator}{filename}', timeout=timeout)
                response_status_code = response.status_code
                response_text = response.text
                response.close()
                if response_status_code != 200:
                    print(f'Remote source file {host}/{project}/{remote_version}{prefix_or_path_separator}{filename} not found')
                    all_files_found = False
                    continue
                with open(filename, 'w') as source_file:
                    source_file.write(response_text)
            if all_files_found:
                with open('version', 'w') as current_version_file:
                    current_version_file.write(remote_version)
                if reset_device:
                    machine.reset()
    except Exception as ex:
        print(f'Something went wrong: {ex}')


def check_for_ota_update(host, project, timeout=5):
    version_changed, remote_version = check_version(host, project, timeout=timeout)
    if version_changed:
        print(f'Found new version {remote_version}, rebooting device...')
        machine.reset()
