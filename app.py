from flask import Flask, request , jsonify , render_template
import requests
import datetime
from datetime import datetime, timedelta
import pytz
from dotmap import DotMap
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
import re
from pymongo import MongoClient
import json


app = Flask(__name__)

      
load_dotenv()

def send_to_discord_webhook(webhook_url, message):
    data = {
        "content": message
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(webhook_url, data=json.dumps(data), headers=headers)
    if response.status_code != 200:
        # Optionally, you can raise an exception here or handle the error in any other way
        pass


  
@app.route("/")
def home():
    return "Contact <a href='https://discordapp.com/users/311519176655241217/' target='_blank'>@mr.velosofy</a> on discord (will add a Readme soon)"
  
# @app.route("/test")
# def test():
#     try:
#         channel = parse_qs(request.headers["Nightbot-Channel"])
#         user = parse_qs(request.headers["Nightbot-User"])
#         url = parse_qs(request.headers["Nightbot-Response-Url"])
#     except KeyError:
#         return "Not able to auth"
      
#     message = f"user: {user} \nstreamer: {channel} \nurl: {url}"
#     send_to_discord_webhook(os.getenv("webhook_url"), message)
#     return "Message sent to discord <3"
  
@app.route("/rank/<region>/<id>/<tag>")
@app.route("/rank/<region>/<id>/<tag>/")
def rank(region = None,id = None , tag = None):
    
    
    streamer = None
    try:
        channel = parse_qs(request.headers["Nightbot-Channel"])
        streamer = channel.get("displayName", [""][0])
        url = request.headers.get("Nightbot-Response-Url")
    except:
        pass
    lb_url = f""
    mmr_url = f'https://api.henrikdev.xyz/valorant/v1/mmr/{region}/{id}/{tag}'
    header = {
    'Authorization': os.getenv("hdev_key")
    }

    # Fetch JSON data from the external URL
    mmr_data = requests.get(mmr_url, headers=header)
    mmr_json = mmr_data.json()
    response_message = " "

    if mmr_data.status_code == 200:
        # Parse JSON data
        mmr_json = mmr_data.json()
        # Convert JSON data to DotMap
        mmr_dotmap = DotMap(mmr_json)
        
        data = mmr_dotmap.data
        
        rank = data.currenttierpatched
        rr = data.ranking_in_tier
        last_mmr_change = data.mmr_change_to_last_game
        response_message = f"{rank} - {rr}RR" 
        
    elif mmr_data.status_code == 429:
        error = mmr_json['errors'][0]['message']
        response_message = f"{error} Code:{mmr_data.status_code}"
    else:
        error = mmr_json['errors'][0]['message']
        if error.lower() == "not found":
          error = "Check your ID and Try Again"
        response_message = f"{error} Code:{mmr_data.status_code}"
        
    if streamer != None:
        streamer = str(streamer)
        streamer = streamer.replace("'", "").replace('[', '')
        streamer = streamer.replace("]","")
        message = f"* * Rank used on {streamer}'s channel \n`Response: {response_message}`"
        send_to_discord_webhook(os.getenv("webhook_url2"), message)
    return response_message
  
  
# @app.route("/lm/")
# @app.route("/lastmatch/")
# @app.route("/lm/<query>")
# @app.route("/lastmatch/<query>")
def lastmatch(query = None):
    start_time = time.time()
    header = {
    'Authorization': os.getenv("hdev_key")
    }
    is_streamer = False
    if query != None:
        decoded_query = unquote(query)  # Decode the URL-encoded query
        
        decoded_query = decoded_query.replace(" ","") 
        if decoded_query == "":
            query = None
            
        decoded_query = decoded_query.replace("#", "/") # Replace / with # in the query parameter
           
    
    try:
        channel = parse_qs(request.headers["Nightbot-Channel"])
        user = parse_qs(request.headers["Nightbot-User"])
       # url = request.headers.get("Nightbot-Response-Url")
    except KeyError:
        return "Not able to auth"
    
    if query == None:
        
        
        channel_id = channel.get("providerId", [""])[0]
        streamer = channel.get("displayName", [""][0])
        streamer = str(streamer)
        streamer = streamer.replace("'", "").replace('[', '')
        streamer = streamer.replace("]","")
        
        
        user = user.get("displayName", [""])[0]
        found_account = None
        for account in accounts:
            if account["channel_id"] == channel_id:
                found_account = account
                is_streamer = True
                break
    
        if found_account:
            decoded_query = found_account["decoded_query"]
            reg = found_account["reg"]
        else:
            return "Streamer is not registered!!"
        
        query = decoded_query.replace("/","#")
        if "#" in query:
            id, tag = query.split("#")
            id = id.replace(" ","")
            tag = tag.replace(" ","")
        else:
            return f"Mention ID Properly or Try in a while"
        
    else:
    # Split the query into id and tag
        streamer = channel.get("displayName", [""][0])
        streamer = str(streamer)
        streamer = streamer.replace("'", "").replace('[', '')
        streamer = streamer.replace("]","")
        
        
        query = unquote(query)
        if "#" in query:
            id, tag = query.split("#")
            id = id.replace(" ","")
            tag = tag.replace(" ","")
        else:
            return f"Mention ID Properly or Try in a while"
        
        
        regions = ['br', 'eu', 'kr', 'latam', 'na', 'ap']
        i = 0 #for testing purpose
        j = 0 #for testing purpose
        for region in regions:
            i += 1
            acc_url = f'https://api.henrikdev.xyz/valorant/v1/account/{decoded_query}'   
            acc_data = requests.get(acc_url,headers=header)
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
    lm_data = requests.get(lm_url,headers=header)
    lmmr_data = requests.get(lmmr_url,headers=header)
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
                queue = metadata.get("queue", "Unknown Queue")
                map_name = metadata.get("map", "Unknown Map")
                server = metadata.get("cluster", "Unknown Map")
                start_ts = metadata.get("game_start", None)
                game_len = metadata.get("game_length", None)
                
                start_ts += game_len
                show_score = False
                show_mmr = False
                show_custom = False
                mmr_change = " "
                # Agent was picked by player or given by game itself
                pick_or_got = "picked"
                if mode.lower() == "deathmatch" or mode.lower() == "escalation":
                    pick_or_got = "got"
                    show_score = False
                    
                elif mode.lower() == "team deathmatch":
                    show_score = True
                    
                    
                elif mode.lower() == "custom game":
                    if queue.lower() == "deathmatch" or queue.lower() == "escalation":
                        pick_or_got = "got"
                        show_score = False
                        show_custom = True
                    else:   
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
                
                if is_streamer == False:
                    display_name = player_info.name.replace("  ", " ")
                else:
                    display_name = streamer
                
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
                time_now = int(time.time())
                elapsed = time_now - start_ts
                # time_now = time_now

                if elapsed < 60:
                    t = int(elapsed)
                    unit = "s"
                elif elapsed < 3600:
                    t = int(elapsed // 60)
                    unit = "m"
                elif elapsed < 86400:
                    t = round(elapsed / 3600)
                    unit = "h"
                else:
                    days = elapsed // 86400
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
                if show_custom ==  True:
                    queue = f"({queue})"
                else:
                    queue = ""
                    
                # Build the response
                response_message = (
                    f"{display_name} last queued for {mode}{queue} on {server} server and {pick_or_got} {character} on {map_name}"
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
    streamer = str(streamer)
    streamer = streamer.replace("'", "").replace('[', '')
    streamer = streamer.replace("]","")
    message = f">>> **Lastmatch used on {streamer}'s channel ** \n`Response: {response_message}` \n"
    send_to_discord_webhook(os.getenv("webhook_url"), message)
    
    #requests.post(url, data={"message": response_message})
    end_time = time.time()
    print(f"Time taken: {(end_time - start_time) * 1000:.6f} ms")
    return response_message



  
def get_latest_live(channel_id):
    vids = scrapetube.get_channel(channel_id, content_type="streams", limit=3, sleep=0)
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


def load_accounts(filename='accounts.json'):
    with open(filename, 'r') as f:
        return json.load(f)
accounts = load_accounts()


@app.route("/recb/")
@app.route("/recordb/")
@app.route("/recb")
@app.route("/recordb")
def record_bckp():
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
        reg = found_account["reg"]
        streamer_name = found_account["name"]
    else:
        return "Streamer is not registered!!"
    
    
    #REGIONS ARE NOW FETCHED FROM accounts.json FOR SAVING TIME :)
    #
    # regions = ['ap','na','br', 'eu', 'kr', 'latam']
    # for region in regions:
    #     acc_url = f'https://api.henrikdev.xyz/valorant/v1/account/{decoded_query}'
    #     acc_data = requests.get(acc_url)
    #     if acc_data.status_code == 200:
    #         acc_json = acc_data.json()
    #         acc_dotmap = DotMap(acc_json)
    #         reg = acc_dotmap.data.region
    #         break
    #     else:
    #         return "Invalid Riot ID"
        
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
        # stream_start_raw = 1708082310

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
            response_message = f"{streamer_name} has not finished any Compi match yet.."
        else:
            
            response_message = f"{streamer_name} is {up_or_down} {total_mmr_change} RR... Won {win} and Lost {lost} {match_or_matches} this stream..."
        # response_message = f"The RR {up_or_down} this stream is {total_mmr_change}, with {streamer_name} winning {win} and losing {lost} matches."
    else:
        response_message = f"Check your ID and Try Again ! Code: {mmrhistory_data.status_code}"

    return response_message
  
  
def iso8601_to_unix(timestamp_str):
    # Convert ISO 8601 timestamp to a datetime object
    timestamp_dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))

    # Convert datetime object to Unix timestamp and return as an integer
    return int(timestamp_dt.timestamp())


@app.route("/rec/")
@app.route("/record/")
@app.route("/rec")
@app.route("/record")
def record():
    header = {
    'Authorization': os.getenv("hdev_key")
    }
    
    try:
        channel = parse_qs(request.headers["Nightbot-Channel"])
        #url = request.headers.get("Nightbot-Response-Url")
        user = parse_qs(request.headers["Nightbot-User"])
    except KeyError:
        return "Not able to auth"
    streamer = channel.get("displayName", [""][0])
    channel_id = channel.get("providerId", [""])[0]
    user = user.get("displayName", [""])[0]
    latest_live = get_latest_live(channel_id)
    if not latest_live:
        return "No live stream found"
    start_time = latest_live["start_time"] / 1000000
    current_time = time.time()
    stream_start = start_time 
      
    found_account = None
    for account in accounts:
        if account["channel_id"] == channel_id:
            found_account = account
            break
    
    if found_account:
        decoded_query = found_account["decoded_query"]
        streamer_name = found_account["name"]
        reg = found_account["reg"]
    else:
        return "Streamer is not registered!!"
    
    
    lf_url = f'https://api.henrikdev.xyz/valorant/v1/lifetime/matches/{reg}/{decoded_query}?mode=competitive&size=15'
    # stream_start = 1708520834
    # win_count, draw_count, lose_count = analyze_matches(lf_url, stream_start)
    response = requests.get(lf_url,headers=header)
    data = response.json()
    win = 0
    draw = 0
    lose = 0
    
    if data['status'] == 200:
        for match in data['data']:
            match_start = iso8601_to_unix(match['meta']['started_at'])
            if match_start >= stream_start:
                player_team = match['stats']['team']
                if player_team == 'Blue':
                    player_score = match['teams']['blue']
                    opponent_score = match['teams']['red']
                else:
                    player_score = match['teams']['red']
                    opponent_score = match['teams']['blue']

                if player_score > opponent_score:
                    win += 1
                elif player_score == opponent_score:
                    draw += 1
                else:
                    lose += 1
    elif data['status'] == 404:
        invalid = decoded_query.replace("/","#")
        return f"{invalid} is Invalid Account.. Update it"
    else:
        status = data['status']
        return f"Riot API seems to be down..{status}"
        
      
    mmrhistory_url = f"https://api.henrikdev.xyz/valorant/v1/mmr-history/{reg}/{decoded_query}"
    # Fetch JSON data from the external URL
    mmrhistory_data = requests.get(mmrhistory_url,headers=header)
    response_message = ""
    if mmrhistory_data.status_code == 200:
        # Parse JSON data
        mmrhistory_json = mmrhistory_data.json()
        # Convert JSON data to DotMap
        mmrhistory_dotmap = DotMap(mmrhistory_json)
        # Provided date_raw for comparison
        # stream_start = 1708520834
        total_mmr_change = 0
        
        # Iterate over the data list
        for data in mmrhistory_dotmap.data:
            if data.date_raw > stream_start:
                if data.mmr_change_to_last_game > 0:
                    total_mmr_change += data.mmr_change_to_last_game
                elif data.mmr_change_to_last_game < 0:
                    total_mmr_change += data.mmr_change_to_last_game                  
        if total_mmr_change >= 0:
            up_or_down = "UP"
        else:
            up_or_down = "DOWN"
            total_mmr_change *= -1
            
        if win+lose+draw== 0:
            response_message = f"{streamer_name} has not finished any compi match yet.."
        else:
            
            response_message = f"{streamer_name} is {up_or_down} {total_mmr_change} RR, with {win} wins, {lose} losses and {draw} draws this stream.."
    # Return the response
  
    else:
        response_message = f"Riot API seems to be down"
    streamer = str(streamer)
    streamer = streamer.replace("'", "").replace('[', '')
    streamer = streamer.replace("]","")
    message = f"* * Record used on {streamer}'s channel \n`Response: {response_message}`"
    send_to_discord_webhook(os.getenv("webhook_url"), message)
    #requests.post(url, data={"message": response_message})
    return response_message
    

    
    
    
def load_ttv_accounts(filename='.data/ttv_accounts.json'):
    with open(filename, 'r') as f:
        return json.load(f)
ttv_accounts = load_ttv_accounts()


def parse_time_string(time_string):
    time_in_seconds = 0
    time_units = {"hour": 3600, "hours": 3600, "minute": 60, "minutes": 60, "second": 1, "seconds": 1}
    
    # Extract numbers and units from the time string
    matches = re.findall(r'(\d+)\s+(\w+)', time_string)
    
    for number, unit in matches:
        time_in_seconds += int(number) * time_units[unit]
    
    return time_in_seconds

def ttv_start_time(query):
    try:
        total_seconds = parse_time_string(query)
        current_time_unix = int(time.time())
        start_time_unix = current_time_unix - total_seconds
        return start_time_unix
    except Exception as e:
        print("An error occurred while calculating start time:", str(e))
        return None

    
    
@app.route("/twitch/rec/")
@app.route("/twitch/record/")
@app.route("/twitch/rec/<query>")
@app.route("/twitch/record/<query>")
@app.route("/twitch/rec/<query>/")
@app.route("/twitch/record/<query>/")
def ttv_record(query = None):
  
    header = {'Authorization' : os.getenv("hdev_key")}
    if query == None:
        return "Command not added correctly"
        
    try:
        channel = parse_qs(request.headers["Nightbot-Channel"])
        url = request.headers.get("Nightbot-Response-Url")
        user = parse_qs(request.headers["Nightbot-User"])
    except KeyError:
        return "Not able to auth"
    

    streamer = channel.get("displayName", [""][0])
    channel_id = channel.get("providerId", [""])[0]
    user = user.get("displayName", [""])[0]
    streamer = str(streamer)
    streamer = streamer.replace("'", "").replace('[', '')
    streamer = streamer.replace("]","")
      

        
    
    
    # return f"{query}"
  
      
    found_account = None
    for account in ttv_accounts:
        if account["channel_id"] == channel_id:
            found_account = account
            break
    
    if found_account:
        decoded_query = found_account["decoded_query"]
        streamer_name = found_account["name"]
        reg = found_account["reg"]
    else:
        return "Streamer is not registered!!"
      
      
    if "not" in query:
        return f" {streamer} is not live"
      
    else:
        start_time = ttv_start_time(query)
        stream_start = int(start_time)
    
    lf_url = f'https://api.henrikdev.xyz/valorant/v1/lifetime/matches/{reg}/{decoded_query}?mode=competitive&size=25'
    # stream_start = 1711205457
    # win_count, draw_count, lose_count = analyze_matches(lf_url, stream_start)
    response = requests.get(lf_url,headers=header)
    data = response.json()
    win = 0
    draw = 0
    lose = 0
    
    if data['status'] == 200:
        for match in data['data']:
            match_start = iso8601_to_unix(match['meta']['started_at'])
            if match_start >= stream_start:
                player_team = match['stats']['team']
                if player_team == 'Blue':
                    player_score = match['teams']['blue']
                    opponent_score = match['teams']['red']
                else:
                    player_score = match['teams']['red']
                    opponent_score = match['teams']['blue']

                if player_score > opponent_score:
                    win += 1
                elif player_score == opponent_score:
                    draw += 1
                else:
                    lose += 1
    elif data['status'] == 404:
        invalid = decoded_query.replace("/","#")
        return f"{invalid} is Invalid Account.. Update it"
    else:
        status = data['status']
        return f"Riot API seems to be down..{status}"
        
      
    mmrhistory_url = f"https://api.henrikdev.xyz/valorant/v1/lifetime/mmr-history/{reg}/{decoded_query}?mode=competitive&size=25"
    # Fetch JSON data from the external URL
    mmrhistory_data = requests.get(mmrhistory_url,headers=header)
    response_message = ""
    if mmrhistory_data.status_code == 200:
        # Parse JSON data
        mmrhistory_json = mmrhistory_data.json()
        # Convert JSON data to DotMap
        mmrhistory_dotmap = DotMap(mmrhistory_json)
        # Provided date_raw for comparison
        # stream_start = 1708520834
        total_mmr_change = 0
        
        # Iterate over the data list
        for data in mmrhistory_dotmap.data:
            match_start = iso8601_to_unix(data.date)
            if match_start >= stream_start:
                if data.last_mmr_change > 0:
                    total_mmr_change += data.last_mmr_change
                elif data.last_mmr_change < 0:
                    total_mmr_change += data.last_mmr_change
        if total_mmr_change >= 0:
            up_or_down = "UP"
        else:
            up_or_down = "DOWN"
            total_mmr_change *= -1
            
        if win+lose+draw== 0:
            response_message = f"{streamer_name} has not finished any compi match yet.."
        else:
            
            response_message = f"{streamer_name} is {up_or_down} {total_mmr_change} RR, with {win} wins, {lose} losses and {draw} draws this stream.."
    # Return the response
  
    else:
        response_message = f"Riot API seems to be down"
    streamer = str(streamer)
    streamer = streamer.replace("'", "").replace('[', '')
    streamer = streamer.replace("]","")
    message = f"* * Record used on {streamer}'s channel \n`Response: {response_message}`"
    send_to_discord_webhook(os.getenv("webhook_url"), message)
    requests.post(url, data={"message": response_message})
    return ""
    

  


@app.route("/edit")
@app.route("/edit/")
@app.route("/edit/<query>")
def edit(query = None):
   
    
    try:
        channel = parse_qs(request.headers["Nightbot-Channel"])
        user = parse_qs(request.headers["Nightbot-User"])
    except KeyError:
        return "Not able to Auth"

    
    if query != None:
        query = unquote(query)  # Decode the URL-encoded query
        query = query.replace(" ","") 
        if query == "":
            query = None 
            
            
    if query == None:
        return "Kindly mention an account to be updated with.."
    else:
        if '#' in query:
            query = query.replace("#", "/")
        else:
            return f"Mention ID Properly [Id #tag].."
        
        
    channel_id = channel.get("providerId", [""])[0]
    user_id = user.get("providerId", [""])[0]
    user_level = user.get("userLevel", [""])[0]
    
    if user_id == os.getenv("reload_key") or user_level.lower() == 'moderator' or user_level.lower() == 'owner':
        # Load the accounts data from the JSON file
        with open('accounts.json', 'r') as f:
            accounts = json.load(f)
        # Find the account with the matching channel ID
        found = False
        exists = False
        for account in accounts:
            if account["channel_id"] == channel_id:
                if account["decoded_query"].lower() == query.lower():
                    current = account["decoded_query"]
                    current = current.replace("/","#")
                    exists = True
                    break
                # Update the decoded_query for the matching channel
                account["decoded_query"] = query
                streamer = account["name"]
                found = True
                break
                
        if exists == True:
            return f"It's same as Current Acc in database.."
        else:
            pass
          
        if found == False:
            return f"Streamer is not registered!!"
        else:
            pass
          
        # Save the updated accounts data back to the JSON file
        with open('accounts.json', 'w') as f:
            json.dump(accounts, f, indent=2)
        query = query.replace("/","#")
        subprocess.Popen(["refresh"])
        subprocess.run(['cat', 'accounts.json'])
        # Example usage:
        return f"Account successfully updated to {query}..(30s downtime🙂)"    
    else:
        return "You are not authorized to edit"
      
      
@app.route("/twitch/edit")
@app.route("/twitch/edit/")
@app.route("/twitch/edit/<query>")
def twitch_edit(query = None):
   
    
    try:
        channel = parse_qs(request.headers["Nightbot-Channel"])
        user = parse_qs(request.headers["Nightbot-User"])
    except KeyError:
        return "Not able to Auth"

    
    if query != None:
        query = unquote(query)  # Decode the URL-encoded query
        query = query.replace(" ","") 
        if query == "":
            query = None 
            
            
    if query == None:
        return "Kindly mention an account to be updated with.."
    else:
        if '#' in query:
            query = query.replace("#", "/")
        else:
            return f"Mention ID Properly [Id #tag].."
        
        
    channel_id = channel.get("providerId", [""])[0]
    user_id = user.get("providerId", [""])[0]
    user_level = user.get("userLevel", [""])[0]
    
    if user_id == os.getenv("reload_key") or user_level.lower() == 'moderator' or user_level.lower() == 'owner':
        # Load the accounts data from the JSON file
        with open('.data/ttv_accounts.json', 'r') as f:
            ttv_accounts = json.load(f)
        # Find the account with the matching channel ID
        found = False
        exists = False
        for account in ttv_accounts:
            if account["channel_id"] == channel_id:
                if account["decoded_query"].lower() == query.lower():
                    current = account["decoded_query"]
                    current = current.replace("/","#")
                    exists = True
                    break
                # Update the decoded_query for the matching channel
                account["decoded_query"] = query
                streamer = account["name"]
                found = True
                break
                
        if exists == True:
            return f"It's same as Current Acc in database.."
        else:
            pass
          
        if found == False:
            return f"Streamer is not registered!!"
        else:
            pass
          
        # Save the updated accounts data back to the JSON file
        with open('.data/ttv_accounts.json', 'w') as f:
            json.dump(ttv_accounts, f, indent=2)
        query = query.replace("/","#")
        subprocess.Popen(["refresh"])
        subprocess.run(['cat', '.data/ttv_accounts.json'])
        # Example usage:
        return f"Account successfully updated to {query}..(30s downtime🙂)"    
    else:
        return "You are not authorized to edit"



@app.route('/visual/<reg>/<id>/<tag>/')
@app.route('/visual/<reg>/<id>/<tag>')
def visual(reg = None , id = None , tag = None):
    header = {'Authorization' : os.getenv("hdev_key")}
    mmr_url = f"https://api.henrikdev.xyz/valorant/v1/mmr/{reg}/{id}/{tag}"
    rank_url = f"https://valorant-api.com/v1/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04"
    
    mmr_data = requests.get(mmr_url,headers=header)
    rank_data = requests.get(rank_url)
    if mmr_data.status_code == 200:
        mmr_data = mmr_data.json()
        rank_data = rank_data.json()
        
        rank_image = mmr_data['data']['images']['large']
        current_mmr = mmr_data['data']['ranking_in_tier']
        current_tier = mmr_data['data']['currenttier']
        
        for tier in rank_data['data']['tiers']:
            if current_tier == tier['tier']:
                color = "#"
                color += tier['color'][:6]
                BgColor = "#"
                BgColor += tier['backgroundColor'][:6]
                
        data = {
            "rank_image" : rank_image,
            "current_mmr" : current_mmr,
            "color" : color,
            "bgcolor" : BgColor
        }
        return render_template("visual.html", data=data)
    elif mmr_data.status_code == 404:
        return "Invalid Riot ID"
    else:
        return f"Something went wrong... :({mmr_data.status_code}"
      

      
@app.route('/reload')
@app.route('/reload/')
@app.route('/reload/<pas>')
def reload_server(pas = None):
  
    try:
        channel = parse_qs(request.headers["Nightbot-Channel"])
        user = parse_qs(request.headers["Nightbot-User"])
    except KeyError:
        return "Not able to auth"
      
    if pas == None:
        return f"Please enter the password"
    
    pas = pas.lower()
    if pas == os.getenv("reload_pas"):
        pass
    else:
        return f"Incorrect password can't reload the server"
      
    
    user_id = user.get("providerId", [""])[0]
    user = user.get("displayName", [""])[0]
    
    if user_id == os.getenv("reload_key"):
        subprocess.Popen(["refresh"])
        return f'Server reload requested by @{user}...'
    
    else:
        return f"@{user},You can't use this buddy :)"

@app.route('/song')
@app.route('/song/')
def song():
    song_url = os.getenv("spotify")
    # song_url = 'https://groke.se/twitch/spotify/?39e6d7509604f73ee23b7098eb39e9b5'
    song_data = requests.get(song_url).text
    song_string = str(song_data)
    start_quote_index = song_string.find('"')
    end_quote_index = song_string.find('"', start_quote_index + 1)

    if start_quote_index >= 0 and end_quote_index >= 0:
        song_name = song_string[start_quote_index + 1:end_quote_index]

        # Extracting the Artist
        dash_index = song_string.find('-')
        emoji = song_string[0:1]
        artist = song_string[2:dash_index].strip()
        response = f"{emoji} {song_name} - {artist}"
    else:
        response = "At the moment, no song is playing."
        
    return response
  
@app.route("/r")
@app.route("/r/")
def r():
    header = {'Authorization' : os.getenv("hdev_key")}
    try:
        channel = parse_qs(request.headers["Nightbot-Channel"])
        user = parse_qs(request.headers["Nightbot-User"])
    except KeyError:
        return "Not able to auth"

    streamer = channel.get("displayName", [""])[0]
    channel_id = channel.get("providerId", [""])[0]
    user = user.get("displayName", [""])[0]
    latest_live = get_latest_live(channel_id)

    if not latest_live:
        return "No live stream found"

    start_time = latest_live["start_time"] / 1000000
    current_time = time.time()
    stream_start = start_time 
    # stream_start = 1713951060 

    found_account = next((account for account in accounts if account["channel_id"] == channel_id), None)

    if found_account:
        decoded_query = found_account["decoded_query"]
        streamer_name = found_account["name"]
        reg = found_account["reg"]
    else:
        return "Streamer is not registered!!"

    # Fetch MMR history first
    mmrhistory_url = f"https://api.henrikdev.xyz/valorant/v1/lifetime/mmr-history/{reg}/{decoded_query}?mode=competitive&size=25"
    mmrhistory_data = requests.get(mmrhistory_url,headers=header)

    if mmrhistory_data.status_code == 200:
        mmrhistory_json = mmrhistory_data.json()
        mmrhistory_dotmap = DotMap(mmrhistory_json)
        total_mmr_change = 0
        
        for data in mmrhistory_dotmap.data:
            match_start = iso8601_to_unix(data.date)
            if match_start >= stream_start:
                if data.last_mmr_change > 0:
                    total_mmr_change += data.last_mmr_change
                elif data.last_mmr_change < 0:
                    total_mmr_change += data.last_mmr_change
        
        if total_mmr_change >= 0:
            up_or_down = "UP"
        else:
            up_or_down = "DOWN"
            total_mmr_change *= -1
    else:
        # Handle error fetching MMR history
        return "Error fetching MMR history from Riot API"

    lf_url = f'https://api.henrikdev.xyz/valorant/v1/lifetime/matches/{reg}/{decoded_query}?mode=competitive&size=25'
    response = requests.get(lf_url,headers=header)
    data = response.json()
    win = 0
    draw = 0
    lose = 0

    if data['status'] == 200:
        for match in data['data']:
            match_start = iso8601_to_unix(match['meta']['started_at'])
            if match_start >= stream_start:
                # Check if the match timestamp is close to any in MMR history
                match_in_mmr_history = False
                for mmr_match in mmrhistory_dotmap.data:
                    mmr_match_start = iso8601_to_unix(mmr_match.date)
                    if abs(match_start - mmr_match_start) <= 20:
                        match_in_mmr_history = True
                        break

                if match_in_mmr_history:
                    player_team = match['stats']['team']
                    if player_team == 'Blue':
                        player_score = match['teams']['blue']
                        opponent_score = match['teams']['red']
                    else:
                        player_score = match['teams']['red']
                        opponent_score = match['teams']['blue']

                    if player_score > opponent_score:
                        win += 1
                    elif player_score == opponent_score:
                        draw += 1
                    else:
                        lose += 1

    elif data['status'] == 404:
        invalid = decoded_query.replace("/","#")
        return f"{invalid} is Invalid Account.. Update it"
    else:
        status = data['status']
        return f"Riot API seems to be down..{status}"

    if win + lose + draw == 0:
        response_message = f"Accurate walaa : {streamer_name} has not finished any compi match yet.."
    else:
        response_message = f"Accurate walaa : {streamer_name} is {up_or_down} {total_mmr_change} RR, with {win} wins, {lose} losses and {draw} draws this stream.."
    
    streamer = str(streamer)
    streamer = streamer.replace("'", "").replace('[', '')
    streamer = streamer.replace("]","")
    message = f">>> Accurate Record used on {streamer}'s channel \n`Response: {response_message}`"
    send_to_discord_webhook(os.getenv("webhook_url"), message)
    
    return response_message

@app.route("/r2")
def r2():
    header = {'Authorization' : os.getenv("hdev_key")}
    try:
        channel = parse_qs(request.headers["Nightbot-Channel"])
        user = parse_qs(request.headers["Nightbot-User"])
    except KeyError:
        return "Not able to auth"

    streamer = channel.get("displayName", [""])[0]
    channel_id = channel.get("providerId", [""])[0]
    user = user.get("displayName", [""])[0]
    latest_live = get_latest_live(channel_id)

    if not latest_live:
        return "No live stream found"

    start_time = latest_live["start_time"] / 1000000
    current_time = time.time()
    stream_start = start_time 
    # stream_start = 1713951060 

    found_account = next((account for account in accounts if account["channel_id"] == channel_id), None)

    if found_account:
        decoded_query = found_account["decoded_query"]
        streamer_name = found_account["name"]
        reg = found_account["reg"]
    else:
        return "Streamer is not registered!!"

    # Fetch MMR history first
    mmr_history_url = f"https://api.henrikdev.xyz/valorant/v1/lifetime/mmr-history/{reg}/{decoded_query}?&size=25"
    mmr_history_data = requests.get(mmr_history_url,headers=header).json()
    
    match_history_url = f"https://api.henrikdev.xyz/valorant/v1/lifetime/matches/{reg}/{decoded_query}?mode=competitive&size=25"
    match_history_data = requests.get(match_history_url,headers=header).json()

    if mmr_history_data['status'] == 200:
        total_mmr_change, win , lose , draw = 0 , 0 , 0 , 0
        for mmr in mmr_history_data['data']:
            match_start = iso8601_to_unix(mmr['date'])
            if match_start >= stream_start:
                for match in match_history_data['data']:
                    if mmr['match_id'] == match['meta']['id']:
                        
                        player_team = match['stats']['team']
                        if player_team == 'Blue':
                            player_score = match['teams']['blue']
                            opponent_score = match['teams']['red']
                        else:
                            player_score = match['teams']['red']
                            opponent_score = match['teams']['blue']

                        if player_score > opponent_score:
                            win += 1
                        elif player_score == opponent_score:
                            draw += 1
                        else:
                            lose += 1
                            
                            
                        if mmr['last_mmr_change'] > 0:
                            total_mmr_change += mmr['last_mmr_change']
                        elif mmr['last_mmr_change'] < 0:
                            total_mmr_change += mmr['last_mmr_change']
                                
                                
        
        if total_mmr_change >= 0:
            up_or_down = "UP"
        else:
            up_or_down = "DOWN"
            total_mmr_change *= -1
    else:
        # Handle error fetching MMR history
        return "Error fetching MMR history from Riot API"
    return f"R2 : {streamer_name} is {up_or_down} {total_mmr_change} RR, with {win} wins, {lose} losses and {draw} draws this stream.."

   
  
@app.route("/new")
@app.route("/new/")
def new():
    try:
        channel = parse_qs(request.headers["Nightbot-Channel"])
    except KeyError:
        return "Not able to auth"
    channel_id = channel.get("providerId", [""])[0]
    
    vid = scrapetube.get_channel(channel_id=channel_id,content_type="videos", sort_by="newest", limit=1)
    response = ""
    for v in vid:
        # print(v['thumbnail']['thumbnails'][0]['url'])
        response += v['title']['runs'][0]['text']
        response += f" : https://youtu.be/"+v['videoId']
    
    return response
    
    
  

def convert_to_local_time(date_str):
    # Convert to datetime object
    date_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
    # Convert to GMT+5:30 timezone
    local_time = date_obj + timedelta(hours=5, minutes=30)
    # Format the date
    formatted_date = local_time.strftime("%dth %B (%I:%M %p)")
    return formatted_date

@app.route('/live')
def live_match():
    header = {'Authorization' : os.getenv("hdev_key")}
    api_url = "https://api.henrikdev.xyz/valorant/v1/esports/schedule?region=international"
    response = requests.get(api_url,headers=header)
    matches = response.json()['data']
    
    # Find in-progress match
    for match in matches:
        if match['state'] == 'inProgress':
            league_name = match['league']['name']
            team1_name = match['match']['teams'][0]['name']
            team1_code = match['match']['teams'][0]['code']
            team1_score = match['match']['teams'][0]['game_wins']
            team2_name = match['match']['teams'][1]['name']
            team2_code = match['match']['teams'][1]['code']
            team2_score = match['match']['teams'][1]['game_wins']
            game_type = match['match']['game_type']['type']
            game_type_count = match['match']['game_type']['count']
            
            return f"Live Score: {team1_code} [{team1_score} - {team2_score}] {team2_code} ({game_type} {game_type_count})"

    # If no match is in progress, return the last completed match
    try:
            last_match = [match for match in matches if match['state'] == 'completed'][-1]
    except:
            return ("No Live/Previous match found")
    league_name = last_match['league']['name']
    team1_name = last_match['match']['teams'][0]['name']
    team1_code = last_match['match']['teams'][0]['code']
    team1_score = last_match['match']['teams'][0]['game_wins']
    team2_name = last_match['match']['teams'][1]['name']
    team2_code = last_match['match']['teams'][1]['code']
    team2_score = last_match['match']['teams'][1]['game_wins']
    
    return f"Last Completed Match: {league_name} - {team1_code} [{team1_score} - {team2_score}] {team2_code}"

  
@app.route('/upcoming')
def upcoming_matches():
    header = {'Authorization' : os.getenv("hdev_key")}
    api_url = "https://api.henrikdev.xyz/valorant/v1/esports/schedule?region=international&league=vct_masters"
    response = requests.get(api_url,headers=header)
    matches = response.json()['data']
    
    # Find upcoming matches
    upcoming_matches_text = "No Upcoming Matches"
    for match in matches:
        if match['state'] == 'unstarted':
            league_name = match['league']['name']
            date = convert_to_local_time(match['date'])
            team1_code = match['match']['teams'][0]['code']
            team2_code = match['match']['teams'][1]['code']
            game_type = match['match']['game_type']['type']
            game_type_count = match['match']['game_type']['count']
            upcoming_matches_text = f"Upcoming {league_name} match on {date} between {team1_code} and {team2_code} ({game_type} {game_type_count})"
            break
    return upcoming_matches_text
  
  
  
  
  
  
@app.route("/lm/")
@app.route("/lastmatch/")
@app.route("/lm/<query>")
@app.route("/lastmatch/<query>")
def lastmatch2(query = None):
    start_time = time.time()
    header = {'Authorization': os.getenv("hdev_key")}
    is_streamer = False
    if query != None:
        decoded_query = unquote(query)  # Decode the URL-encoded query
        
        decoded_query = decoded_query.replace(" ","") 
        if decoded_query == "":
            query = None
            
        decoded_query = decoded_query.replace("#", "/") # Replace / with # in the query parameter
           
    
    try:
        channel = parse_qs(request.headers["Nightbot-Channel"])
        user = parse_qs(request.headers["Nightbot-User"])
       # url = request.headers.get("Nightbot-Response-Url")
    except KeyError:
        return "Not able to auth"
    
    if query == None:
        
        
        channel_id = channel.get("providerId", [""])[0]
        streamer = channel.get("displayName", [""][0])
        streamer = str(streamer)
        streamer = streamer.replace("'", "").replace('[', '')
        streamer = streamer.replace("]","")
        
        
        user = user.get("displayName", [""])[0]
        found_account = None
        for account in accounts:
            if account["channel_id"] == channel_id:
                found_account = account
                is_streamer = True
                break
    
        if found_account:
            decoded_query = found_account["decoded_query"]
            reg = found_account["reg"]
        else:
            return "Streamer is not registered!!"
        
        query = decoded_query.replace("/","#")
        if "#" in query:
            id, tag = query.split("#")
            id = id.replace(" ","")
            tag = tag.replace(" ","")
        else:
            return f"Mention ID Properly or Try in a while"
        
    else:
    # Split the query into id and tag
        streamer = channel.get("displayName", [""][0])
        streamer = str(streamer)
        streamer = streamer.replace("'", "").replace('[', '')
        streamer = streamer.replace("]","")
        
        
        query = unquote(query)
        if "#" in query:
            id, tag = query.split("#")
            id = id.replace(" ","")
            tag = tag.replace(" ","")
        else:
            return f"Mention ID Properly or Try in a while"

 

        acc_url = f'https://api.henrikdev.xyz/valorant/v1/account/{decoded_query}'
        acc_data = requests.get(acc_url,headers=header).json()
        print(acc_data)
        error_message = ""
        if acc_data['status'] == 200: 
            reg = acc_data['data']['region']
        else:
            error = acc_data['errors'][0]['message']
            details= acc_data['errors'][0]['details']
            code = acc_data['status']
            if details == "null":
                details = ""
                error_message = f"{error} Code:{code}....{details}"    
            else:
                details = f"Details: {details}"
                error_message = f"{error} Code:{code}....{details}"
            return error_message
        
    lm_url = f'https://api.henrikdev.xyz/valorant/v3/matches/{reg}/{decoded_query}?size=1'
    lmmr_url = f'https://api.henrikdev.xyz/valorant/v1/lifetime/mmr-history/{reg}/{decoded_query}?size=1'
    

    # Fetch JSON data from the external URL
    lm_data = requests.get(lm_url,headers=header).json()
    lmmr_data = requests.get(lmmr_url,headers=header).json()
    response_message = ""

    if lm_data['status'] == 200:
        # Check if the data list is empty
        if lm_data['data'] and lm_data['data'][0]['players']['all_players']:
            # Find player by name (case-insensitive and ignoring spaces)
            player_info = None
            for player in lm_data['data'][0]['players']['all_players']:
                # Compare names case-insensitive and ignoring spaces
                if player['name'].replace(" ", "").lower() == id.lower() and player['tag'].replace(" ", "").lower() == tag.lower():
                    player_info = player
                    break

            if player_info is not None:
                # Extracting useful metadata information
                metadata = lm_data['data'][0]['metadata']
                mode = metadata.get("mode", "Unknown Mode")
                queue = metadata.get("queue", "Unknown Queue")
                map_name = metadata.get("map", "Unknown Map")
                server = metadata.get("cluster", "Unknown Map")
                start_ts = metadata.get("game_start", None)
                game_len = metadata.get("game_length", None)
                
                start_ts += game_len
                show_score = False
                show_mmr = False
                show_custom = False
                mmr_change = " "
                # Agent was picked by player or given by game itself
                pick_or_got = "picked"
                if mode.lower() == "deathmatch" or mode.lower() == "escalation":
                    pick_or_got = "got"
                    show_score = False
                    
                elif mode.lower() == "team deathmatch":
                    show_score = True
                    
                    
                elif mode.lower() == "custom game":
                    if queue.lower() == "deathmatch" or queue.lower() == "escalation":
                        pick_or_got = "got"
                        show_score = False
                        show_custom = True
                    else:   
                        show_score = True
                    
                elif mode.lower() == "competitive":  
                    mmr_change = ""
                    if lmmr_data['status'] == 200:
                        # Parse JSON data
                        if lm_data['data'][0]['metadata']['matchid'] == lmmr_data['data'][0]['match_id']:   
                            rr_change = lmmr_data['data'][0]['last_mmr_change']
                            
                            if rr_change >= 0:
                                mmr_change = f"[Gained {rr_change}RR]..."
                            else:
                                rr_change *= -1
                                mmr_change = f"[Lost {rr_change}RR]..."
                            show_mmr = True
                           
                    show_score = True
                    pick_or_got = "picked"
                    
                else:
                    show_mmr = True
                    pick_or_got = "picked"

                    
                        
                # Extract player's character (agent) and KDA
                character = player_info['character']
                
                stats = player_info['stats']
                kda = f"{stats['kills']}K/{stats['deaths']}D/{stats['assists']}A"
                
                if is_streamer == False:
                    display_name = player_info['name'].replace("  ", " ")
                else:
                    display_name = streamer
                
                team = player_info['team']
                teams = lm_data['data'][0]['teams']
                if team == "Red":
                    player_team = teams['red']
                    won = teams['red']['rounds_won']
                    lost = teams['red']['rounds_lost']
                else:
                    player_team = teams['blue']
                    won = teams['blue']['rounds_won']
                    lost = teams['blue']['rounds_lost']
                    
                score = f"Score: {won}-{lost}. "

                # Time Since last match played
                time_now = int(time.time())
                elapsed = time_now - start_ts

                if elapsed < 60:
                    t = int(elapsed)
                    unit = "s"
                elif elapsed < 3600:
                    t = int(elapsed // 60)
                    unit = "m"
                elif elapsed < 86400:
                    t = round(elapsed / 3600)
                    unit = "h"
                else:
                    days = elapsed // 86400
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
                if show_custom ==  True:
                    queue = f"({queue})"
                else:
                    queue = ""
                    
                # Build the response
                response_message = (
                    f"{display_name} last queued for {mode}{queue} on {server} server and {pick_or_got} {character} on {map_name}"
                    f".. Stats: {kda}.."
                    f" {score}{mmr_change}"
                    f"({t}{unit} ago)"
                )
            else:
                response_message = f"Player {id}#{tag} not found."
        else:
            response_message = "The Player hasn't been playing for a Long time."
    else:
        response_message = f"Check your ID and Try Again ! Code:{lm_data['status']} "
    streamer = str(streamer)
    streamer = streamer.replace("'", "").replace('[', '')
    streamer = streamer.replace("]","")
    message = f">>> **Lastmatch used on {streamer}'s channel ** \n`Response: {response_message}` \n"
    send_to_discord_webhook(os.getenv("webhook_url"), message)
    end_time = time.time()
    print(f"Time taken: {(end_time - start_time) * 1000:.6f} ms")
    return response_message

  
@app.route('/status')
def status():
    # Fetch data from the provided URL
    url = "https://status.manuel-hexe.de/api/status-page/heartbeat/henrik-api"
    response = requests.get(url)
    data = response.json()

    # Extract relevant information
    heartbeat_list = data["heartbeatList"]["6"]
    status_data = [{"time": entry["time"], "status": entry["status"], "ping": entry["ping"]} for entry in heartbeat_list]

    # Process data to remove earliest records
    num_records_to_keep = 30
    if len(status_data) > num_records_to_keep:
        status_data = status_data[-num_records_to_keep:]

    return jsonify(status_data)

@app.route('/status-page')
def status_page():
    return render_template('status.html')
