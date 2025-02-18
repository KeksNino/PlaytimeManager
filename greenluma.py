import re
import requests
import time
import glob
import sqlite3

def extract_appid_playtime(vdf_content):
    appid_playtime = {}
    appid_pattern = re.compile(r'"\d+"')
    playtime_pattern = re.compile(r'"playtime"\s+"(\d+)"')

    lines = vdf_content.splitlines()
    current_appid = None

    for line in lines:
        appid_match = appid_pattern.match(line.strip())
        if appid_match:
            current_appid = appid_match.group().strip('"')
        playtime_match = playtime_pattern.search(line)
        if playtime_match and current_appid:
            appid_playtime[current_appid] = playtime_match.group(1)

    return appid_playtime

def get_game_name(appid):
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
    
    while True:
        response = requests.get(url)
        if response.status_code == 200:
            try:
                data = response.json()
                if data and data.get(str(appid), {}).get('success'):
                    return data[str(appid)]['data']['name']
                else:
                    print(f"Failed to fetch data for AppID: {appid}, Response: {data}")
            except ValueError:
                print(f"Invalid JSON response for AppID: {appid}")
            break
        elif response.status_code == 429:
            print("Rate limit exceeded. Waiting before retrying...")
            time.sleep(5)  # Wait for 5 seconds before retrying
        else:
            print(f"Failed to fetch data for AppID: {appid}, Status Code: {response.status_code}")
            break
    return None

# Read the .vdf file
with open('localconfig.vdf', 'r') as file:
    vdf_content = file.read()

appid_playtime = extract_appid_playtime(vdf_content)

appids = "appids/*.txt"

# Function to extract numbers from a string
def extract_numbers(text):
    return re.findall(r'\d+', text)

# Read the content of each file and store the numbers in an array
numbers = []
for filepath in glob.glob(appids):
    with open(filepath, 'r') as file:
        content = file.read()
        numbers.extend(extract_numbers(content))
print(numbers)
# Filter the numbers to only include those from the appids folder
filtered_appid_playtime = {appid: playtime for appid, playtime in appid_playtime.items() if appid in numbers}

import sqlite3
#from greenluma import game_name, playtime_hours

# Path to the database
db_path = "~/.local/share/lutris/pga.db"

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# print the results
for appid, playtime in filtered_appid_playtime.items():
    game_name = get_game_name(appid)
    if game_name:
        playtime_hours = int(playtime) / 60
        print(f"Game Name: {game_name}, AppID: {appid}, Playtime: {playtime_hours}")
        cursor.execute("UPDATE games SET playtime = ? WHERE name = ?", (playtime_hours, game_name))    
    else:
        print(f"Game not found or invalid appid: {appid}")

conn.commit()
conn.close()

