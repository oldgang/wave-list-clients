from scraper import find_service_gps, find_AP_gps

# Custom class for access points
class AccessPoint:
    ip = None
    nodeID = None
    gps = None
    services = None
    unidentifiedServices = None
    
    def __init__(self, ip):
        self.ip = ip
        self.nodeID = f"{ip.split('.')[1]}-{ip.split('.')[2]}"

    # coordinates format: (lon, lat, height)
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
    
    # coordinates format: (lon, lat, height)
    def get_gps(self):
        self.gps = find_service_gps(self.id, self.url)