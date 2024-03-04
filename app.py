from flask import Flask, request , jsonify , render_template
import requests
import datetime
from datetime import datetime
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
    return "Contact <a href='https://discordapp.com/users/311519176655241217/' target='_blank'>@mr.velosofy</a> on discord (will add ReadMe soon)"
  


@app.route("/lm/")
@app.route("/lastmatch/")
@app.route("/lm/<query>")
@app.route("/lastmatch/<query>")
def lastmatch(query = None):
    
    
    if query != None:
        decoded_query = unquote(query)  # Decode the URL-encoded query
        
        decoded_query = decoded_query.replace(" ","") 
        if decoded_query == "":
            query = None
            
        decoded_query = decoded_query.replace("#", "/") # Replace / with # in the query parameter
           
    
    try:
        channel = parse_qs(request.headers["Nightbot-Channel"])
        user = parse_qs(request.headers["Nightbot-User"])
    except KeyError:
        return "Not able to auth"
    
    if query == None:
        
        channel_id = channel.get("providerId", [""])[0]
        streamer = channel.get("displayName", [""][0])
        user = user.get("displayName", [""])[0]
        found_account = None
        for account in accounts:
            if account["channel_id"] == channel_id:
                found_account = account
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
    message = f"Lastmatch used on {streamer}'s channel"
    send_to_discord_webhook(os.getenv("webhook_url"), message)
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
    
    try:
        channel = parse_qs(request.headers["Nightbot-Channel"])
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
    response = requests.get(lf_url)
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
    mmrhistory_data = requests.get(mmrhistory_url)
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
    message = f"Record used on {streamer}'s channel"
    send_to_discord_webhook(os.getenv("webhook_url"), message)
    return response_message
    

  
  


@app.route("/edit")
@app.route("/edit/")
@app.route("/edit/<query>")
def edit_query(query = None):
   
    
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
        # subprocess.run(['cat', 'accounts.json'])
        # Example usage:
        return f"Account successfully updated to {query}..(30s downtime🙂)"    
    else:
        return "You are not authorized to edit"


@app.route('/visual/<reg>/<id>/<tag>/')
@app.route('/visual/<reg>/<id>/<tag>')
def visual(reg = None , id = None , tag = None):
    
    url = f"https://api.henrikdev.xyz/valorant/v1/mmr/{reg}/{id}/{tag}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()["data"]
        return render_template("visual.html", data=data)
    elif response.status_code == 404:
        return "Invalid Riot ID"
    else:
        return f"Something went wrong... :({response.status_code}"
      

      
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
