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

def fetch_manifest(host, project, remote_version, prefix_or_path_separator, auth=None, timeout=5):
    if auth:
        response = urequests.get(f'{host}/{project}/{remote_version}{prefix_or_path_separator}manifest', headers={'Authorization': f'Basic {auth}'}, timeout=timeout)
    else:
        response = urequests.get(f'{host}/{project}/{remote_version}{prefix_or_path_separator}manifest', timeout=timeout)
    response_status_code = response.status_code
    response_text = response.text
    response.close()
    if response_status_code != 200:
        print(f'Remote manifest file {host}/{project}/{remote_version}{prefix_or_path_separator}manifest not found')
        raise Exception(f"Missing manifest for {remote_version}")
    return response_text.split()
    
def generate_auth(user=None, passwd=None) -> str | None:
    if not user and not passwd:
        return None
    if (user and not passwd) or (passwd and not user):
        raise ValueError('Either only user or pass given. None or both are required.')
    auth_bytes = ubinascii.b2a_base64(f'{user}:{passwd}'.encode())
    return auth_bytes.decode().strip()


def ota_update(host, project, filenames=None, use_version_prefix=True, user=None, passwd=None, hard_reset_device=True, soft_reset_device=False, timeout=5) -> None:
    all_files_found = True
    auth = generate_auth(user, passwd)
    prefix_or_path_separator = '_' if use_version_prefix else '/'
    try:
        version_changed, remote_version = check_version(host, project, auth=auth, timeout=timeout)
        if version_changed:
            try:
                uos.mkdir('tmp')
            except OSError as e:
                if e.errno != 17:
                    raise
            if filenames is None:
                filenames = fetch_manifest(host, project, remote_version, prefix_or_path_separator, auth=auth, timeout=timeout)
            for filename in filenames:
                if filename.endswith('/'):
                    dir_path="tmp"
                    for dir in filename.split('/'):
                        if len(dir) > 0:
                            built_path=f"{dir_path}/{dir}"
                            try:
                                uos.mkdir(built_path)
                            except OSError as e:
                                if e.errno != 17:
                                    raise
                    continue
                if auth:
                    response = urequests.get(f'{host}/{project}/{remote_version}{prefix_or_path_separator}{filename}', headers={'Authorization': f'Basic {auth}'}, timeout=timeout)
                else:
                    response = urequests.get(f'{host}/{project}/{remote_version}{prefix_or_path_separator}{filename}', timeout=timeout)
                response_status_code = response.status_code
                response_content = response.content
                response.close()
                if response_status_code != 200:
                    print(f'Remote source file {host}/{project}/{remote_version}{prefix_or_path_separator}{filename} not found')
                    all_files_found = False
                    continue
                with open(f'tmp/{filename}', 'wb') as source_file:
                    source_file.write(response_content)
            if all_files_found:
                dirs=[]
                for filename in filenames:
                    if filename.endswith('/'):
                        dir_path=""
                        for dir in filename.split('/'):
                            if len(dir) > 0:
                                built_path=f"{dir_path}/{dir}"
                                try:
                                    uos.mkdir(built_path)
                                except OSError as e:
                                    if e.errno != 17:
                                        raise
                                dirs.append(f"tmp/{built_path}")
                        continue
                    #print(f"tmp/{filename} -> {filename}")
                    with open(f'tmp/{filename}', 'rb') as source_file, open(filename, 'wb') as target_file:
                        target_file.write(source_file.read())
                    uos.remove(f'tmp/{filename}')
                try:
                    while len(dirs) > 0:
                        uos.rmdir(dirs.pop())
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
        raise ex


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
