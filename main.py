import re
import paramiko
import csv
import simplekml
import threading
import os
import folium
from scraper import find_service_gps, find_AP_gps


# Credentials
defaultUsername = ''
defaultPassword = ''
botUsername = ''
botPassword = ''


# Custom class for access points
class AccessPoint:
    ip = None
    gps = None
    services = None
    
    def __init__(self, ip, gps, services):
        self.ip = ip
        self.gps = gps
        self.services = services

    # (lon, lat, height)
    def get_gps(self):
        self.gps = find_AP_gps(self.ip)
    
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
    
    # (lon, lat, height)
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

# Create a kml file with the data
def create_kml(listOfServices, accessPointIP):
    accessPointGps = find_AP_gps(accessPointIP)
    # Plot the data on the map
    kml = simplekml.Kml()
    # Plot the access point on the map
    apPoint = kml.newpoint(name='AP', coords=[accessPointGps])
    apPoint.style.iconstyle.icon.href = "http://maps.google.com/mapfiles/kml/paddle/N.png"
    apPoint.altitudemode = simplekml.AltitudeMode.relativetoground
    # Plot the clients on the map
    for service in listOfServices:
        clientPoint = kml.newpoint(name=service[0], coords=[service[1]])
        clientPoint.altitudemode = simplekml.AltitudeMode.relativetoground
        clientPoint.style.iconstyle.icon.href = "https://maps.google.com/mapfiles/kml/paddle/K.png"
        clientPoint.style.iconstyle.color = "ff00ff00"
        # add lines between AP and clients
        lin = kml.newlinestring(name=service[0])
        lin.coords = [accessPointGps, service[1]]
        lin.style.linestyle.color = simplekml.Color.red
        lin.style.linestyle.width = 3
        lin.altitudemode = simplekml.AltitudeMode.relativetoground
    # Check if the file exists and delete it if it does
    if os.path.exists("data.kmz"):
        os.remove("data.kmz")
    # Save kmz file
    kml.save("data.kmz") 

# Create a folium map with the data
def create_folium_map(listOfServices, accessPoint):
    # Get the access point location
    lon, lat, height = accessPoint.gps
    apLocation = (float(lat), float(lon))
    # Create the map
    m = folium.Map(location=apLocation, zoom_start=10)
    # Add the access point to the map
    folium.Marker(location=apLocation, popup='AP', icon=folium.Icon(color='red')).add_to(m)
    # Add the clients to the map
    for service in listOfServices:
        # Get the client location
        lon, lat, height = service[1]
        clientLocation = (float(lat), float(lon))
        folium.Marker(location=clientLocation, popup=service[0], icon=folium.Icon(color='green')).add_to(m)
        # Draw lines between each client and the access point
        locations = [
            apLocation,
            clientLocation
        ]
        folium.PolyLine(locations=locations, color='red', weight=2.5, opacity=1).add_to(m)
    # Save the map
    m.save('map.html')
    # Display the map
    m

# for testing purposes
if __name__ == '__main__':
    accessPointIP = '10.1.54.21'
    clients = get_service_IDs(accessPointIP)
    serviceIDs = clients['id']
    unidentified = clients['no-id']

    if len(unidentified) > 0:
        print('Unidentified services (not shown on map):')
        print('\n'.join(unidentified))
        
    services = []
    for serviceID in serviceIDs:
        newService = Service(id=serviceID, url='', gps='')
        newService.generate_url()
        services.append(newService)
    
    for service in services:
        thread = threading.Thread(target=service.get_gps())
        thread.start()
        thread.join()

    listOfServices = [[service.id, service.gps] for service in services]

    ap = AccessPoint(ip=accessPointIP, gps='', services=listOfServices)
    ap.get_gps()
    # print(ap.ip, ap.gps, ap.services)
    # create_kml(listOfServices, accessPointIP)
    create_folium_map(listOfServices, ap)