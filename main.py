import requests
from pyfiglet import Figlet
import folium
import subprocess
import re


def create_route_map(ips: [str], url: str):
    if url[0].isdigit():
        url_name = ""  # ip address
    else:
        url_name = re.search("[a-z]*\.([a-zA-Z]+)\.[a-z] | ([a-zA-Z]+)\.[a-z]", url).group(1)  # url address
    loc = []
    createdmap = False
    for id_, ip in enumerate(ips):
        try:
            response = requests.get(url=f'http://ip-api.com/json/{ip}').json()
            data = {
                'ip': response.get('query'),
                'org': response.get('org'),
                'city': response.get('city'),
                'lat': response.get('lat'),
                'lon': response.get('lon')
            }

            print(data['city'])

            latitude = response.get('lat')
            longitude = response.get('lon')
            loc.append((latitude, longitude))

            if not createdmap:
                area = folium.Map(location=[latitude, longitude])
                createdmap = True

            popup = "<i>{} server #{}</i>".format(data['org'], id_)
            folium.Marker(
                [latitude, longitude], popup=popup
            ).add_to(area)

        except requests.exceptions.ConnectionError:
            print('Please check your connection!')
            return

    if url[0].isdigit():
        url_name = data['org']
    folium.PolyLine(loc).add_to(area)
    area.save(f'{url_name}.html')


def main():
    preview_text = Figlet(font='slant')
    print(preview_text.renderText('TRACEROUTE INFO'))
    url = input('Please enter a target url or IP: ')
    print("Tracing in progress, please wait...")
    out = subprocess.check_output(["traceroute", "-w", "3", url])
    all_ips = re.findall("\(([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\)", str(out))
    all_ips = all_ips[1:]
    create_route_map(all_ips, url)
    print(preview_text.renderText('DONE'))


if __name__ == '__main__':
    main()
