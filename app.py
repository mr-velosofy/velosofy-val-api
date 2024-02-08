from flask import Flask
import requests
import datetime
import pytz
from dotmap import DotMap
from keep_alive import keep_alive
import schedule
import threading
import time

app = Flask(__name__)

def job():
    print("Scheduled task running...")
    # Your existing lastmatch() function code here

def schedule_task():
    # Schedule the job to run every minute
    schedule.every(1).minutes.do(job)

    # Run the scheduler continuously in a separate thread
    while True:
        schedule.run_pending()
        time.sleep(1)


@app.route("/")
def home():
    return "Use /lastmatch"


@app.route("/lm/")
@app.route("/lastmatch/")
@app.route("/lm")
@app.route("/lastmatch")
def lastmatch():
    external_url = 'https://api.henrikdev.xyz/valorant/v3/matches/ap/neonfrmbigbzar/sasta?size=1'

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
            # Extract player name from the URL between /ap/ and /onyt/
            url_parts = external_url.split('/')
            player_name_from_url = url_parts[url_parts.index('ap') + 1]
            player_name_from_url = player_name_from_url.replace(" ","")

            # Find player by name (case-insensitive and ignoring spaces)
            player_info = None
            for player in json_dotmap.data[0].players.all_players:
                # Compare names case-insensitive and ignoring spaces
                if player.name.replace(" ", "").lower() == player_name_from_url.lower():
                    player_info = player
                    break

            if player_info is not None:
                
                # Extracting useful metadata information
                
                metadata = json_dotmap.data[0].metadata
                mode = metadata.get("mode", "Unknown Mode")
                map_name = metadata.get("map", "Unknown Map")
                server = metadata.get("cluster", "Unknown Map")
                start_ts = metadata.get("game_start" , None)
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
                kda = f"{player_info.stats.kills}/{player_info.stats.deaths}/{player_info.stats.assists}"
                display_name = player_info.name.replace("  "," ") + "#" + player_info.tag



                # Time Since last match played
            
                start_utc = datetime.datetime.fromtimestamp(start_ts, datetime.timezone.utc)

                ist_tz, now_ist = pytz.timezone('Asia/Kolkata'), datetime.datetime.now(pytz.timezone('Asia/Kolkata'))

                start_ist = start_utc.astimezone(ist_tz)
                elapsed = now_ist - start_ist


                if elapsed.total_seconds() < 60:
                    time = int(elapsed.total_seconds())
                    unit = "s"
                    # print(f"Player's last match was {int(elapsed.total_seconds())} seconds ago (IST)")
                elif elapsed.total_seconds() < 3600:
                    time = int(elapsed.total_seconds() // 60)
                    unit = "m"       
                    # print(f"Player's last match was {int(elapsed.total_seconds() // 60)} minutes ago (IST)")
                elif elapsed.total_seconds() < 86400:
                    
                    time = round(elapsed.total_seconds() / 3600)
                    unit = "h"
                    # print(f"Player's last match was {hours} {'hour' if hours == 1 else 'hours'} ago (IST)")  
                else:
                    days = elapsed.days
                    weeks = days // 7
                    if weeks > 0:
                        time = weeks
                        unit = "w"
                        #print(f"Player's last match was {weeks} {'week' if weeks == 1 else 'weeks'} ago (IST)")
                    elif days > 0:
                        time = days
                        unit = "d"

                # Build the response
                response_message = (
                    f"{display_name} queued for {mode} in {server} server and {pick_or_got} {character} on {map_name}. "
                    f"Their KDA: {kda} "
                    f"({time}{unit} ago)"
                )
            else:
                response_message = f"Player '{player_name_from_url}' not found."
        else:
            response_message = "Player has not been playing from a long ago"
    else:
        response_message = f"Failed to fetch data from the external URL. Status Code: {response.status_code}"
        
    return response_message

if __name__ == "__main__":
    keep_alive()  # Start the keep-alive server
    
    # Start the scheduler in a separate thread
    scheduler_thread = threading.Thread(target=schedule_task)
    scheduler_thread.start()

    app.run(host="localhost", port=8080, debug=True)
