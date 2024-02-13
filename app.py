from flask import Flask
import requests
import datetime
import pytz
from dotmap import DotMap
from keep_alive import keep_alive
import schedule
import threading
import time
from urllib.parse import unquote

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
                map_name = metadata.get("map", "Unknown Map")
                server = metadata.get("cluster", "Unknown Map")
                start_ts = metadata.get("game_start", None)
                game_len = metadata.get("game_length", None)
                
                start_ts += game_len
                show_score = False
                show_mmr = False
                # Agent was picked by player or given by game itself
                pick_or_got = "picked"
                if mode.lower() == "deathmatch" or mode.lower() == "escalation":
                    pick_or_got = "got"
                    show_score = False
                    
                elif mode.lower() == "team deathmatch":
                    show_score = True
                  
                elif mode.lower() == "competitive":
                    mmr_change = " "
                    if lmmr_data.status_code == 200:
                        # Parse JSON data
                        lmmr_json = lmmr_data.json()
                        # Convert JSON data to DotMap
                        lmmr_dotmap = DotMap(lmmr_json)
                        
                        mmr = int(lmmr_dotmap.data.mmr_change_to_last_game)
                        if mmr >= 0:
                            mmr_change = f"[Gained {mmr}RR].. "
                        else:
                            mmr *= -1
                            mmr_change = f"[Lost {mmr}RR].. "
                            
                    show_mmr = True
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
                    
                score = f"Score:{won}-{lost}. "
                
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
                    f".. Stats:{kda}.."
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

