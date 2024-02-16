from flask import Flask, request
import requests
import datetime
import pytz
from dotmap import DotMap
from keep_alive import keep_alive
import schedule
import threading
import time
import json
import subprocess
from dotenv import load_dotenv
import os
from urllib.parse import unquote, parse_qs
from chat_downloader.sites import YouTubeChatDownloader
# from chat_downloader import ChatDownloader
import scrapetube
import subprocess

app = Flask(__name__)

@app.route("/")
def home():
    return "Use lastmatch/ or lm/"


  
@app.route("/lm/<query>")
@app.route("/lastmatch/<query>")
def lastmatch(query):
    
        
    decoded_query = unquote(query)  # Decode the URL-encoded query
    decoded_query = decoded_query.replace("#", "/")
    decoded_query = decoded_query.replace(" ","")    # Replace / with # in the query parameter
    
    
    if not decoded_query:
        decoded_query = 'ggmotato/onyt'
        query = 'GGMotato#onyt'

    # Split the query into id and tag
    query = unquote(query)
    if "#" in query:
        id, tag = query.split("#")
        id = id.replace(" ","")
        tag = tag.replace(" ","")
    else:
        return f"Mention ID Properly or Try in a while"
      
      
    regions = [ 'br', 'eu', 'kr', 'latam', 'na','ap']
    i = 0 #for testing purpose
    j = 0 #for testing purpose
    for region in regions:
        i += 1
        acc_url = f'https://api.henrikdev.xyz/valorant/v1/account/{decoded_query}'   
        acc_data = requests.get(acc_url)
        if acc_data.status_code == 200:
            j= +1
            acc_json = acc_data.json()
            acc_dotmap = DotMap(acc_json)
            
            reg = acc_dotmap.data.region
            break
        else:
            return f"Invalid Riot ID"
        
    lm_url = f'https://api.henrikdev.xyz/valorant/v3/matches/{reg}/{decoded_query}?size=1'
    lmmr_url = f'https://api.henrikdev.xyz/valorant/v1/mmr/{reg}/{decoded_query}'

    # Fetch JSON data from the external URL
    lm_data = requests.get(lm_url)
    lmmr_data = requests.get(lmmr_url)
    response_message = " "

    if lm_data.status_code == 200:
        # Parse JSON data
        lm_json = lm_data.json()
        # Convert JSON data to DotMap
        lm_dotmap = DotMap(lm_json)

        # Check if the data list is empty
        if lm_dotmap.data and lm_dotmap.data[0].players.all_players:
            # Find player by name (case-insensitive and ignoring spaces)
            player_info = None
            for player in lm_dotmap.data[0].players.all_players:
                # Compare names case-insensitive and ignoring spaces
                if player.name.replace(" ", "").lower() == id.lower() and player.tag.replace(" ", "").lower() == tag.lower():
                    player_info = player
                    break

            if player_info is not None:
                # Extracting useful metadata information
                metadata = lm_dotmap.data[0].metadata
                mode = metadata.get("mode", "Unknown Mode")
                map_name = metadata.get("map", "Unknown Map")
                server = metadata.get("cluster", "Unknown Map")
                start_ts = metadata.get("game_start", None)
                game_len = metadata.get("game_length", None)
                
                start_ts += game_len
                show_score = False
                show_mmr = False
                mmr_change = " "
                # Agent was picked by player or given by game itself
                pick_or_got = "picked"
                if mode.lower() == "deathmatch" or mode.lower() == "escalation":
                    pick_or_got = "got"
                    show_score = False
                    
                elif mode.lower() == "team deathmatch":
                    show_score = True
                    
                elif mode.lower() == "custom game":
                    show_score = True
                    
                elif mode.lower() == "competitive":
                    mmr_change = " "
                    if lmmr_data.status_code == 200:
                        # Parse JSON data
                        lmmr_json = lmmr_data.json()
                        # Convert JSON data to DotMap
                        lmmr_dotmap = DotMap(lmmr_json)
                        try:
                              
                            mmr = int(lmmr_dotmap.data.mmr_change_to_last_game)
                        except:
                            mmr = 0
                        if mmr >= 0:
                            mmr_change = f"[Gained {mmr}RR].. "
                        else:
                            mmr *= -1
                            mmr_change = f"[Lost {mmr}RR].. "
                            
                    show_mmr = True
                    show_score = True
                    pick_or_got = "picked"
                    
                else:
                    show_mmr = True
                    pick_or_got = "picked"

                    
                    
                    
                    
                # Extract player's character (agent) and KDA
                character = player_info.character
                
                stats = player_info.stats
                kda = f"{stats.kills}K/{stats.deaths}D/{stats.assists}A"
               # hs = (stats.headshots/(stats.headshots + stats.bodyshots + stats.legshots))*100
                #hs = round(hs,1)
                
                
                display_name = player_info.name.replace("  ", " ")
                
                team = player_info.team
                teams = lm_dotmap.data[0].teams
                if team == "Red":
                    player_team = teams.red
                    won = teams.red.rounds_won
                    lost = teams.red.rounds_lost
                else:
                    player_team = teams.blue
                    won = teams.blue.rounds_won
                    lost = teams.blue.rounds_lost
                    
                score = f"Score: {won}-{lost}. "
                
#                 if teams.red.has_won == False and teams.blue.has_won == False:
#                     match_outcome = "Draw"
                    
#                 elif player_team.has_won == True:
#                     match_outcome = "Won"
                
#                 else:
#                     match_outcome = "Lose"
                
#                 match_outcome = f"Outcome:{match_outcome}.."

                # Time Since last match played
                start_utc = datetime.datetime.fromtimestamp(start_ts, datetime.timezone.utc)
                ist_tz, now_ist = pytz.timezone('Asia/Kolkata'), datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
                start_ist = start_utc.astimezone(ist_tz)
                elapsed = now_ist - start_ist

                if elapsed.total_seconds() < 60:
                    t = int(elapsed.total_seconds())
                    unit = "s"
                elif elapsed.total_seconds() < 3600:
                    t = int(elapsed.total_seconds() // 60)
                    unit = "m"
                elif elapsed.total_seconds() < 86400:
                    t = round(elapsed.total_seconds() / 3600)
                    unit = "h"
                else:
                    days = elapsed.days
                    weeks = days // 7
                    if weeks > 0:
                        t = weeks
                        unit = "w"
                    elif days > 0:
                        t = days
                        unit = "d"
                        
                if show_score == False:
                    score = ""
                    
                if show_mmr == False:
                    mmr_change = ""
                    #match_outcome = ""
                    
                # Build the response
                response_message = (
                    f"{display_name} last queued for {mode} on {server} server and {pick_or_got} {character} on {map_name}"
                    f".. Stats: {kda}.."
                    f" {score}{mmr_change}"
                    f"({t}{unit} ago)"
                )
            else:
                response_message = f"Player {id}#{tag} not found."
        else:
            response_message = "The Player hasn't been playing for a Long time."
    else:
        response_message = f"Check your ID and Try Again ! Code:{lm_data.status_code} "

    return response_message


  
def get_latest_live(channel_id):
    vids = scrapetube.get_channel(channel_id, content_type="streams", limit=2, sleep=0)
    live_found_flag = False
    for vid in vids:
        if (
            vid["thumbnailOverlays"][0]["thumbnailOverlayTimeStatusRenderer"]["style"]
            == "LIVE"
        ):
            live_found_flag = True
            break
    if not live_found_flag:
        return None
    vid = YouTubeChatDownloader().get_video_data(video_id=vid["videoId"])
    return vid


def load_credentials(filename='accounts.json'):
    with open(filename, 'r') as f:
        return json.load(f)
accounts = load_credentials()


@app.route("/rec/")
@app.route("/record/")
@app.route("/rec")
@app.route("/record")
def record():
    try:
        channel = parse_qs(request.headers["Nightbot-Channel"])
        user = parse_qs(request.headers["Nightbot-User"])
    except KeyError:
        return "Not able to auth"
    
    channel_id = channel.get("providerId", [""])[0]
    user = user.get("displayName", [""])[0]
    latest_live = get_latest_live(channel_id)
    if not latest_live:
        return "No live stream found"
    start_time = latest_live["start_time"] / 1000000
    current_time = time.time()
    stream_start_raw = start_time 
    
    found_account = None
    for account in accounts:
        if account["channel_id"] == channel_id:
            found_account = account
            break
    
    if found_account:
        decoded_query = found_account["decoded_query"]
        streamer_name = found_account["name"]
    else:
        return "Streamer is not registered!!"
    
    regions = ['br', 'eu', 'kr', 'latam', 'na', 'ap']
    for region in regions:
        acc_url = f'https://api.henrikdev.xyz/valorant/v1/account/{decoded_query}'
        acc_data = requests.get(acc_url)
        if acc_data.status_code == 200:
            acc_json = acc_data.json()
            acc_dotmap = DotMap(acc_json)
            reg = acc_dotmap.data.region
            break
        else:
            return "Invalid Riot ID"
        
    mmrhistory_url = f"https://api.henrikdev.xyz/valorant/v1/mmr-history/{reg}/{decoded_query}"

    # Fetch JSON data from the external URL
    mmrhistory_data = requests.get(mmrhistory_url)
    response_message = ""

    if mmrhistory_data.status_code == 200:
        # Parse JSON data
        mmrhistory_json = mmrhistory_data.json()
        # Convert JSON data to DotMap
        mmrhistory_dotmap = DotMap(mmrhistory_json)

        # Provided date_raw for comparison
        # stream_start_raw = 1691924163

        # Initialize win and lost values
        win = 0
        lost = 0
        total_mmr_change = 0

        # Iterate over the data list
        for data in mmrhistory_dotmap.data:
            if data.date_raw > stream_start_raw:
                if data.mmr_change_to_last_game > 0:
                    total_mmr_change += data.mmr_change_to_last_game
                    win += 1
                elif data.mmr_change_to_last_game < 0:
                    total_mmr_change += data.mmr_change_to_last_game
                    lost += 1
                    
        if total_mmr_change >= 0:
            up_or_down = "UP"
        else:
            up_or_down = "DOWN"
            total_mmr_change *= -1
            
            
            
        if win+lost> 1:
            match_or_matches = "matches"      
        else:
            match_or_matches = "match"
            
            
        # response_message = f"{streamer_name} has Wins: {win}, Lost: {lost} {total_mmr_change}RR changed this stream"
        if win+lost== 0:
            response_message = f"{streamer_name} has not finished any valo match yet.."
        else:
            
            response_message = f"{streamer_name} is {up_or_down} {total_mmr_change} RR... Won {win} and Lost {lost} {match_or_matches} this stream..."
        # response_message = f"The RR {up_or_down} this stream is {total_mmr_change}, with {streamer_name} winning {win} and losing {lost} matches."
    else:
        response_message = f"Check your ID and Try Again ! Code: {mmrhistory_data.status_code}"

    return response_message
  
  
load_dotenv()

@app.route('/reload/')
@app.route('/reload/<pas>')
def reload_server(pas = None):
    
    if pas == None:
      return f"Please enter the password"
    
    pas = pas.lower()
    if pas == os.getenv("reload_pas"):
        pass
    else:
        return f"Incorrect password can't reload the server"
      
    try:
        channel = parse_qs(request.headers["Nightbot-Channel"])
        user = parse_qs(request.headers["Nightbot-User"])
    except KeyError:
        return "Not able to auth"
    
    user_id = user.get("providerId", [""])[0]
    user = user.get("displayName", [""])[0]
    
    if user_id == os.getenv("reload_key"):
        subprocess.Popen(["refresh"])
        return f'Server reload requested by @{user}...'
    
    else:
        return f"@{user},You can't use this buddy :)"
