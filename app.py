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
    if "#" in query:
        id, tag = query.split("#")
        id = id.replace(" ","")
        tag = tag.replace(" ","")
    else:
        return f"Mention ID Properly. Status Code: 400"
    
    external_url = f'https://api.henrikdev.xyz/valorant/v3/matches/ap/{decoded_query}?size=1'

    # Fetch JSON data from the external URL
    response = requests.get(external_url)
    response_message = " "

    if response.status_code == 200:
        # Parse JSON data
        json_data = response.json()

        # Convert JSON data to DotMap
        json_dotmap = DotMap(json_data)

        # Check if the data list is empty
        if json_dotmap.data and json_dotmap.data[0].players.all_players:
            # Find player by name (case-insensitive and ignoring spaces)
            player_info = None
            for player in json_dotmap.data[0].players.all_players:
                # Compare names case-insensitive and ignoring spaces
                if player.name.replace(" ", "").lower() == id.lower() and player.tag.replace(" ", "").lower() == tag.lower():
                    player_info = player
                    break

            if player_info is not None:
                # Extracting useful metadata information
                metadata = json_dotmap.data[0].metadata
                mode = metadata.get("mode", "Unknown Mode")
                map_name = metadata.get("map", "Unknown Map")
                server = metadata.get("cluster", "Unknown Map")
                start_ts = metadata.get("game_start", None)
                game_len = metadata.get("game_length", None)
                
                start_ts += game_len

                # Agent was picked by player or given by game itself
                pick_or_got = "picked"
                if mode.lower() == "deathmatch" or mode.lower() == "escalation":
                    pick_or_got = "got"
                else:
                    pick_or_got = "picked"

                # Extract player's character (agent) and KDA
                character = player_info.character
                
                stats = player_info.stats
                kda = f"{stats.kills}K/{stats.deaths}D/{stats.assists}A"
                hs = (stats.headshots/(stats.headshots + stats.bodyshots + stats.legshots))*100
                hs = round(hs,1)
                
                
                display_name = player_info.name.replace("  ", " ") + "#" + player_info.tag
                
                team = player_info.team
                teams = json_dotmap.data[0].teams
                if team == "Red":
                    player_team = teams.red
                    won = teams.red.rounds_won
                    lost = teams.red.rounds_lost
                else:
                    player_team = teams.blue
                    won = teams.blue.rounds_won
                    lost = teams.blue.rounds_lost
                    
                
                if teams.red.has_won == False and teams.blue.has_won == False:
                    match_outcome = "Draw"
                    
                elif player_team.has_won == True:
                    match_outcome = "Won"
                
                else:
                    match_outcome = "Lose"
                

                # Time Since last match played
                start_utc = datetime.datetime.fromtimestamp(start_ts, datetime.timezone.utc)
                ist_tz, now_ist = pytz.timezone('Asia/Kolkata'), datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
                start_ist = start_utc.astimezone(ist_tz)
                elapsed = now_ist - start_ist

                if elapsed.total_seconds() < 60:
                    time = int(elapsed.total_seconds())
                    unit = "s"
                elif elapsed.total_seconds() < 3600:
                    time = int(elapsed.total_seconds() // 60)
                    unit = "m"
                elif elapsed.total_seconds() < 86400:
                    time = round(elapsed.total_seconds() / 3600)
                    unit = "h"
                else:
                    days = elapsed.days
                    weeks = days // 7
                    if weeks > 0:
                        time = weeks
                        unit = "w"
                    elif days > 0:
                        time = days
                        unit = "d"

                # Build the response
                response_message = (
                    f"{display_name} last queued for {mode} on {server} server and {pick_or_got} {character} on {map_name}"
                    f".. Stats:{kda}.. HS:{hs}%"
                    f".. Outcome:{match_outcome}.. Score:{won}-{lost}.. "
                    f"({time}{unit} ago)"
                )
            else:
                response_message = f"Player {id}#{tag} not found."
        else:
            response_message = "Player has not been playing from a long ago"
    else:
        response_message = f"Invalid Riot ID. Status Code: {response.status_code}"

    return response_message

