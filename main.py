import re
import paramiko
import csv
import simplekml
from scraper import find_service_gps


# Credentials
defaultUsername = ''
defaultPassword = ''
botUsername = ''
botPassword = ''


# Custom class for services
class Service:
    id = None
    url = None
    gps = None
    
    def __init__(self, id, url, gps):
        self.id = id
        self.url = url
        self.gps = gps

    # example url -> # https://panel.wave.com.pl/?co=alias&alias=U6688
    def generate_url(self):
        self.url = f"https://panel.wave.com.pl/?co=alias&alias={self.id}"
    
    def get_gps(self):
        self.gps = find_service_gps(self.id, self.url)


# Get the list of wireless clients' radio names
def get_service_IDs(ip):
    # Read credentials from files
    with open('.venv/defaultpw.txt', 'r') as f:
        defaultUsername, defaultPassword = f.read().splitlines()
    with open('.venv/bot.txt', 'r') as f:
        botUsername, botPassword = f.read().splitlines()
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
        if re.search(r'U[0-9]+', name):
            identified.append(re.findall(r'U[0-9]{1,}', name)[0])
        else:
            unidentified.append(name)
    # Return the identified and unidentified service numbers
    return {'id': identified, 'no-id': unidentified}

# for testing purposes
if __name__ == '__main__':
    clients = get_service_IDs('10.1.54.21')
    serviceIDs = clients['id']
    unidentified = clients['no-id']
    Services = []
    for serviceID in serviceIDs:
        newService = Service(id=serviceID, url='', gps='')
        newService.generate_url()
        newService.get_gps()
        Services.append(newService)
    
    for service in Services:
        print(f"{service.id} -> {service.gps}")
    
    #kml file etc.
    