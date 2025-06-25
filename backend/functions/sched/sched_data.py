import requests

def get_schedule_data(date: str, team_id: int) -> dict:
    """
    Fetch the MLB schedule data for a specific team on the specified date.
    Returns the schedule JSON for the team.
    """
    api_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date}&teamId={team_id}"
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching schedule for team {team_id}: {response.status_code}")
        return {}

def extract_game_pk(schedule_data: dict) -> int:
    """
    Extract the gamePk value from the schedule data.
    Returns None if no game is found.
    """
    if schedule_data.get("dates"):
        for date_info in schedule_data["dates"]:
            for game in date_info.get("games", []):
                game_pk = game.get("gamePk")
                if game_pk:
                    return game_pk
    print("No games found for the specified team and date.")
    return None

def pull_schedule_data(schedule_data: dict) -> dict:
    """
    Extract final scores, records, and determine the winner from the schedule data.
    """
    try:
        schedule_game = schedule_data["dates"][0]["games"][0]
        home_score = schedule_game["teams"]["home"]["score"]
        away_score = schedule_game["teams"]["away"]["score"]
        home_record = schedule_game["teams"]["home"]["leagueRecord"]
        away_record = schedule_game["teams"]["away"]["leagueRecord"]
        home_team_id = schedule_game["teams"]["home"]["team"]["id"]
        away_team_id = schedule_game["teams"]["away"]["team"]["id"]

        game_info = {
            "home_score": home_score,
            "away_score": away_score,
            "home_record": f"{home_record['wins']}-{home_record['losses']} ({home_record['pct']})",
            "away_record": f"{away_record['wins']}-{away_record['losses']} ({away_record['pct']})",
            "winner": schedule_game["teams"]["home"]["team"]["name"] if home_score > away_score
                     else schedule_game["teams"]["away"]["team"]["name"],
            "loser": schedule_game["teams"]["away"]["team"]["name"] if home_score > away_score
                    else schedule_game["teams"]["home"]["team"]["name"],
            "content_link": schedule_game["content"]["link"],
            "venue": schedule_game["venue"]["name"],
            "home_team_id": home_team_id,
            "away_team_id": away_team_id
        }
        
        return game_info
    except (KeyError, IndexError) as e:
        print(f"Error extracting schedule data: {e}")
        return {}
