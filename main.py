import os
import re
import paramiko
import csv
import simplekml

defaultUsername = ''
defaultPassword = ''
botUsername = ''
botPassword = ''

def get_service_numbers(ip):
    # Start the ssh client that connects to the access point
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # Try different credentials
    try:
        ssh.connect(ip, username=botUsername, password=botPassword, port=22)
    except paramiko.ssh_exception.AuthenticationException:
        ssh.connect(ip, username=defaultUsername, password=defaultPassword, port=22)
    except:
        print('Could not connect to access point: ' + ip)
        ssh.close()
        exit()
    # Get the list of wireless clients' radio names
    stdin, stdout, stderr = ssh.exec_command('foreach x in=[/interface/wireless/registration-table/find] do={:put [/interface/wireless/registration-table/get $x radio-name]}')
    radioNames = [o.strip() for o in stdout.readlines()]
    ssh.close()
    # Try to identify the service numbers
    identified = []
    unidentified = []
    for name in radioNames:
        print(name)
        if re.search(r'U[0-9]+', name):
            identified.append(re.findall(r'U[0-9]{1,}', name)[0])
        else:
            unidentified.append(name)
    # Return the identified and unidentified service numbers
    return {'id': identified, 'no-id': unidentified}


#example url -> # https://panel.wave.com.pl/?co=alias&alias=U6688
# def generate_urls(clients):
#     for service in clients['id']:
#         url = f"https://panel.wave.com.pl/?co=alias&alias={service}"


# read credentials from files
with open('.venv/defaultpw.txt', 'r') as f:
    defaultUsername, defaultPassword = f.read().splitlines()
with open('.venv/bot.txt', 'r') as f:
    botUsername, botPassword = f.read().splitlines()

get_service_numbers('10.1.54.21')
