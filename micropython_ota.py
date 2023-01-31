import machine
import ubinascii
import uos
import urequests


def check_version(host, project, auth=None, timeout=5) -> (bool, str):
    current_version = ''
    try:
        if 'version' in uos.listdir():
            with open('version', 'r') as current_version_file:
                current_version = current_version_file.readline().strip()

        if auth:
            response = urequests.get(f'{host}/{project}/version', headers={'Authorization': f'Basic {auth}'}, timeout=timeout)
        else:
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


def generate_auth(user=None, passwd=None) -> str | None:
    if not user and not passwd:
        return None
    if (user and not passwd) or (passwd and not user):
        raise ValueError('Either only user or pass given. None or both are required.')
    auth_bytes = ubinascii.b2a_base64(f'{user}:{passwd}'.encode())
    return auth_bytes.decode().strip()


def ota_update(host, project, filenames, use_version_prefix=True, user=None, passwd=None, hard_reset_device=True, soft_reset_device=False, timeout=5) -> None:
    all_files_found = True
    auth = generate_auth(user, passwd)
    prefix_or_path_separator = '_' if use_version_prefix else '/'
    try:
        version_changed, remote_version = check_version(host, project, auth=auth, timeout=timeout)
        if version_changed:
            try:
                uos.mkdir('tmp')
            except:
                pass
            for filename in filenames:
                if auth:
                    response = urequests.get(f'{host}/{project}/{remote_version}{prefix_or_path_separator}{filename}', headers={'Authorization': f'Basic {auth}'}, timeout=timeout)
                else:
                    response = urequests.get(f'{host}/{project}/{remote_version}{prefix_or_path_separator}{filename}', timeout=timeout)
                response_status_code = response.status_code
                response_text = response.text
                response.close()
                if response_status_code != 200:
                    print(f'Remote source file {host}/{project}/{remote_version}{prefix_or_path_separator}{filename} not found')
                    all_files_found = False
                    continue
                with open(f'tmp/{filename}', 'w') as source_file:
                    source_file.write(response_text)
            if all_files_found:
                for filename in filenames:
                    with open(f'tmp/{filename}', 'r') as source_file, open(filename, 'w') as target_file:
                        target_file.write(source_file.read())
                    uos.remove(f'tmp/{filename}')
                try:
                    uos.rmdir('tmp')
                except:
                    pass
                with open('version', 'w') as current_version_file:
                    current_version_file.write(remote_version)
                if soft_reset_device:
                    print('Soft-resetting device...')
                    machine.soft_reset()
                if hard_reset_device:
                    print('Hard-resetting device...')
                    machine.reset()
    except Exception as ex:
        print(f'Something went wrong: {ex}')


def check_for_ota_update(host, project, user=None, passwd=None, timeout=5, soft_reset_device=False):
    auth = generate_auth(user, passwd)
    version_changed, remote_version = check_version(host, project, auth=auth, timeout=timeout)
    if version_changed:
        if soft_reset_device:
            print(f'Found new version {remote_version}, soft-resetting device...')
            machine.soft_reset()
        else:
            print(f'Found new version {remote_version}, hard-resetting device...')
            machine.reset()
