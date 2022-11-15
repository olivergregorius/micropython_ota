import machine
import ubinascii
import urequests
import uos

def check_version(host, project, auth=None):
    try:
        if 'version' in uos.listdir():
            with open('version', 'r') as current_version_file:
                current_version = current_version_file.readline().strip()
        else:
            current_version = ''

        if auth:
            remote_version_response = urequests.get(f'{host}/{project}/version', headers={'Authorization': f'Basic {auth}'})
        else:
            remote_version_response = urequests.get(f'{host}/{project}/version')

        if remote_version_response.status_code != 200:
            print(f'Remote version file {host}/{project}/version not found')
            return False, current_version

        remote_version = remote_version_response.text.strip()
        remote_version_response.close()
        return current_version != remote_version, remote_version

    except Exception as ex:
        print(f'Something went wrong: {ex}')
        return False, current_version

def generate_auth(user=None, pass=None):
    if not user and not pass:
        return None
    if (user and not pass) or (pass and not user):
        raise ValueError('Either only user or pass given. None or both are required.')
    auth_bytes = ubinascii.b2a_base64(f'{user}:{pass}'.encode())
    return auth_bytes.decode().strip()


def ota_update(host, project, filenames, user=None, pass=None, reset_device=True):
    all_files_found = True
    auth = generate_auth(user, pass)
    
    try:
        version_changed, remote_version = check_version(host, project, auth)
        if version_changed:
            for filename in filenames:
                
                if auth:
                    source_file_response = urequests.get(f'{host}/{project}/{remote_version}_{filename}', headers={'Authorization': f'Basic {auth}'})
                else:
                    source_file_response = urequests.get(f'{host}/{project}/{remote_version}_{filename}')
                
                if source_file_response.status_code != 200:
                    print(f'Remote source file {host}/{project}/{remote_version}_{filename} not found')
                    all_files_found = False
                    continue

                source_file_content = source_file_response.text
                source_file_response.close()
                with open(filename, 'w') as source_file:
                    source_file.write(source_file_content)

            if all_files_found:
                with open('version', 'w') as current_version_file:
                    current_version_file.write(remote_version)
                if reset_device:
                    machine.reset()

    except Exception as ex:
        print(f'Something went wrong: {ex}')


def check_for_ota_update(host, project, user=None, pass=None):
    auth = generate_auth(user, pass)
    
    version_changed, remote_version = check_version(host, project, auth)
    if version_changed:
        print(f'Found new version {remote_version}, rebooting device...')
        machine.reset()
