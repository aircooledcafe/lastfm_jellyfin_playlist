import requests
import os
from dotenv import load_dotenv
import json
from dataclasses import dataclass
from typing import List
from typing import Optional
import random
from colours import *
from datetime import datetime

load_dotenv()

# JF environment
JF_URL = os.getenv("JF_URL")
JF_API_KEY = os.getenv("JF_API_KEY")
JF_USER_ID = os.getenv("JF_USER_ID")

# lastfm environment
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
LASTFM_USER = os.getenv("LASTFM_USER")

# For the following functions.
# period can be one of the following strings:
# overall | 7day | 1month | 3month | 6month | 12month
# Number can be any integer from 1 to 200
# Function to get individual track data from recent_tracks_url api respnse

def lastfm_api_call(url, page):
    # add page to url
    url = f"{url}&page={page}"
    # get initail repsonse
    try:
        res = requests.get(url)
        data = json.loads(res.text)
        return data
    except Exception as e:
        print(f"Failed to get last.fm data. Status code: {e}")


@dataclass
class Track:
    artist_name: str
    track_name: str
    track_id: Optional[str] = None

class TrackManager:
    def __init__(self):
        self.tracks: List[Track] = []

    def add_track(self, artist_name: str, track_name: str, track_id: Optional[str] = None):
        new_track = Track(artist_name, track_name, track_id)
        self.tracks.append(new_track)

top_twenty = TrackManager()
top_300 = TrackManager()
random_fifty = TrackManager()

def process_tracks(item, track_list):
    artist = item['artist']['name']
    track = item['name']
    playcount = item['playcount']
    track_list.add_track(artist, track)

def get_track_chart(number, period, user, api_key, track_list):
    # number = total number of tracks to retreive
    # period = period ot retreive formats overall | 7day | 1month | 3month | 6month | 12month
    # user = the lastfm username
    # api_key = the lastfm api_key
    # dict = dictionary to append data to
    url = f"http://ws.audioscrobbler.com/2.0/?method=user.gettoptracks&user={user}&api_key={api_key}&format=json&limit={number}&period={period}"
    track_data = lastfm_api_call(url, 1)
    for item in track_data['toptracks']['track']:
	    process_tracks(item, track_list)

# -- create list of random 50 from unique artists
def get_random_50():
    i = 50
    while i > 0:
        track_num = random.randrange(1, 301)
        random_fifty.add_track(top_300.tracks[track_num].artist_name, top_300.tracks[track_num].track_name, top_300.tracks[track_num].track_id)
        i -= 1

# Search top tracks in Jellyfin and get track ids
# - get track name to searc from last.fm 20/30 list
# - search for track within JF
# - build dictionary top 20 with trackname/artist name/id
# - build dictionary top 50 with trackname/artist name/id

def get_track_id(url, lastfm_list, jf_user, jf_api):
    url = f"{url}/Search/Hints"
    headers = {"Authorization": f'MediaBrowser Token="{jf_api}"', "Content-Type": "application/json"}
    track_ids = []
    for item in lastfm_list.tracks:
        search_term = f"{item.track_name}"
        params = {
            "searchTerm": search_term,
            "IncludeItemTypes": "Audio",
            "limit": 1
        }
        try:
            res = requests.get(url, headers=headers, params=params)
            data = json.loads(res.text)
            track_ids.append(data['SearchHints'][0]['ItemId'])
        except Exception as e:
            print(f"Failed to get track {item.track_name}. Status code: {e}")
    return track_ids


# Create Playlist in JF
# - create playlist named "Top 20 for month year"
# - add all tracks from JF top 20 to playlist
# - create playlist named "Random 50 for month year"
# - add all tracks from JF top 20 to playlist

def create_playlist(url, user_id, playlist_name, track_ids, jf_api):
    print(f"Creating playlist: {playlist_name}")
    print("-" * 30)
    url = f"{url}/Playlists"
    headers = {"Authorization": f'MediaBrowser Token="{jf_api}"', "Content-Type": "application/json"}
    params = {
        "Name": f"{playlist_name}",
        "Ids": track_ids,
        "UserId": user_id,
        "MediaType": "Audio",
        "Users": [{
            "UserId": user_id,
            "CanEdit": True
        }],
        "IsPublic": True
    }
    try:
        res = requests.post(url, headers=headers, params=params)
        print(f"Playslit named '{playlist_name}' created with the ID: {json.loads(res.text)["Id"]}")
        print("-" * 87)
    except Exception as e:
        print(f"Failed to get track {item.track_name}. Status code: {e}")


def menu():
    print(f"1. Create two playlists from the last month, a top 20 tracks and a random 50 from the top 300 tracks.\n2. Create a top tracks playlist for a given period.\n3. Create a random tracks playlist for a given period.\n100. Quit.\n")
    user_input = True
    while True:
        try:
            user_input = int(input("Please chose and option: "))
        except ValueError:
            print("Invalid selection, please input the number of the item you wish to use.")
            continue
        else:
            return user_input


def main():
    print(f"{RED}-" * 87)
    print(r"""
    ____.___________ __________.__                .__  .__          __                
    |    |\_   _____/ \______   \  | _____  ___.__.|  | |__| _______/  |_  ___________ 
    |    | |    __)    |     ___/  | \__  \<   |  ||  | |  |/  ___/\   __\/ __ \_  __ \
/\__|    | |     \     |    |   |  |__/ __ \\___  ||  |_|  |\___ \  |  | \  ___/|  | \/
\________| \___  /     |____|   |____(____  / ____||____/__/____  > |__|  \___  >__|   
            \/                         \/\/                  \/            \/       
    """)
    print("-" * 87)
    print(f"{END}")
    selection = menu()
    date = datetime.today().strftime('%Y-%m-%d')
    month_year = datetime.today().strftime('%B %Y')
    while selection != 100:
        if selection == 1:
            # print(f"Selection: {selection}")
            print("Getting last months top twenty from last.fm")
            get_track_chart("20", "1month", LASTFM_USER, LASTFM_API_KEY, top_twenty)
            print(f"{RED}-{END}" * 87)
            print("Getting last months random 50 tracks from last.fm")
            get_track_chart("300", "1month", LASTFM_USER, LASTFM_API_KEY, top_300)
            get_random_50()
            print(f"{RED}-{END}" * 87)
            random_50_tracks = get_track_id(JF_URL, random_fifty, JF_USER_ID, JF_API_KEY)
            top_twenty_tracks = get_track_id(JF_URL, top_twenty, JF_USER_ID, JF_API_KEY)
            create_playlist(JF_URL, JF_USER_ID, f"Random 50 {month_year}", random_50_tracks, JF_API_KEY)
            create_playlist(JF_URL, JF_USER_ID, f"Top 20 {month_year}", top_twenty_tracks, JF_API_KEY)
            selection = menu()
        elif selection == 2:
            print(f"Creating a top tracks playlist for a given period")
            period = input("What period do you wish to create a playlist from?\n(Valid periods are 1day, 1week, 1month, 3month, 6mont, 12month, or overall)")
            tracks = input("How many top tracks to you want included in the playlist?\n(Any value up to 100.)")
            print("Getting tracks from last.fm")
            get_track_chart(tracks, period, LASTFM_USER, LASTFM_API_KEY, top_twenty)
            print(f"{RED}-{END}" * 87)
            top_tracks = get_track_id(JF_URL, top_twenty, JF_USER_ID, JF_API_KEY)
            title = f"Top {tracks} tracks from {period} prior to {date}"
            create_playlist(JF_URL, JF_USER_ID, title, top_tracks, JF_API_KEY)
            selection = menu()
        elif selection == 3:
            #print(f"Selection: {selection}")
            print(f"{RED}-{END}" * 87)
            print(f"Creating a playlist of ranomd 50 tracks from top 300 for a given period")
            period = input("What period do you wish to create a playlist from?\n(Valid periods are 1day, 1week, 1month, 3month, 6mont, 12month, or overall)")
            print("Getting tracks from last.fm")
            get_track_chart("300", period, LASTFM_USER, LASTFM_API_KEY, top_twenty)
            print(f"{RED}-{END}" * 87)
            get_random_50()
            random_50_tracks = get_track_id(JF_URL, random_fifty, JF_USER_ID, JF_API_KEY)
            top_tracks = get_track_id(JF_URL, top_twenty, JF_USER_ID, JF_API_KEY)
            title = f"Random 50 tracks from {period} prior to {date}"
            create_playlist(JF_URL, JF_USER_ID, title, random_50_tracks, JF_API_KEY)
            print(f"{RED}-{END}" * 87)
            selection = menu()
        else:
            print(f"Invalid selection")
            selection = menu()

if __name__ == '__main__':
    main()
