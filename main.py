import re
import paramiko
import csv
import simplekml
import threading
import os
import folium
from models import Service, AccessPoint

# Credentials
defaultUsername = ''
defaultPassword = ''
botUsername = ''
botPassword = ''

# Read credentials from file
def read_credentials():
    with open('.venv/credentials.txt', 'r') as f:
        credentials = f.readlines()
        global defaultUsername, defaultPassword, botUsername, botPassword
        defaultUsername = credentials[0].strip()
        defaultPassword = credentials[1].strip()
        botUsername = credentials[2].strip()
        botPassword = credentials[3].strip()

# Get the list of wireless clients' radio names
def get_service_IDs(accessPoint):
    ip = accessPoint.ip
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

def add_to_kml(kml, accessPoint, lineColor):
    accessPointGps = accessPoint.gps
    listOfServices = accessPoint.services
    # Plot the access point on the map
    apPoint = kml.newpoint(name=accessPoint.ip, coords=[accessPointGps])
    apPoint.style.iconstyle.icon.href = "http://maps.google.com/mapfiles/kml/paddle/N.png"
    apPoint.altitudemode = simplekml.AltitudeMode.relativetoground
    # Plot the clients on the map
    for service in listOfServices:
        clientPoint = kml.newpoint(name=service[0], coords=[service[1]])
        clientPoint.altitudemode = simplekml.AltitudeMode.relativetoground
        clientPoint.style.iconstyle.icon.href = "https://maps.google.com/mapfiles/kml/paddle/K.png"
        clientPoint.style.iconstyle.color = lineColor
        clientPoint.description = f"AP:{accessPoint.ip}\n{service.url}"
        # add lines between AP and clients
        lin = kml.newlinestring(name=f"{service[0]} <-> AP:{accessPoint.ip}")
        lin.coords = [accessPointGps, service[1]]
        lin.style.linestyle.color = lineColor
        lin.style.linestyle.width = 3
        lin.altitudemode = simplekml.AltitudeMode.relativetoground
    return kml

# Create a folium map with the data - currently not working
def create_folium_map(listOfServices, accessPoint):
    # Get the access point location
    lon, lat, height = accessPoint.gps
    apLocation = (float(lat), float(lon))
    # Create the map
    m = folium.Map(location=apLocation, zoom_start=10) 
    # Google Satellite (Hybrid) layer
    googleHybrid = folium.TileLayer('http://{s}.google.com/vt/lyrs=s,h&x={x}&y={y}&z={z}',
         attr='googleHybrid',
         name='Google Satellite',
         subdomains=['mt0', 'mt1', 'mt2', 'mt3'],
         overlay=True,
         control=False                      
        ).add_to(m)
    
    # Add the access point to the map
    folium.Marker(location=apLocation, popup=accessPoint.nodeID, icon=folium.Icon(color='red')).add_to(m)
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
    # m

def get_access_points_data(accessPoints):
    if defaultUsername == '' or defaultPassword == '' or botUsername == '' or botPassword == '':
        read_credentials()

    for accessPoint in accessPoints:
        clients = get_service_IDs(accessPoint)
        services = []

        for serviceID in clients['id']:
            newService = Service(id=serviceID, url='', gps='')
            newService.generate_url()
            services.append(newService)

        for service in services:
            thread = threading.Thread(target=service.get_gps())
            thread.start()
            thread.join()

        identifiedServices = [[service.id, service.gps] for service in services]
        unidentifiedServices = clients['no-id']
        accessPoint.services = identifiedServices
        accessPoint.unidentifiedServices = unidentifiedServices
        accessPoint.get_gps()

# for testing purposes
if __name__ == '__main__':
    accessPoints = [
                    AccessPoint(ip='10.1.13.24'),
                    AccessPoint(ip='10.1.13.21')
                    # AccessPoint(ip='10.1.21.2'),
                    # AccessPoint(ip='10.1.21.21')
                    ]
    # Create a kml object
    kml = simplekml.Kml()
    # Get the data for all access points
    get_access_points_data(accessPoints)
    # Random line colors
    lineColors = ['ff0000ff', 'ff00ffff', 'ffff0000', 'ffff00ff', 'ffffff00', 'ff00ff00', 'ff000000']
    # Add the data to the kml object
    for accessPoint in accessPoints:
        add_to_kml(kml, accessPoint, lineColors.pop(0))

    # Check if the file exists and delete it if it does
    if os.path.exists("data.kmz"):
        os.remove("data.kmz")
    # Save kmz file
    kml.save("data.kmz") 