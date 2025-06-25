from datetime import datetime
import json
import requests
from functions.sched.sched_data import get_schedule_data, extract_game_pk, pull_schedule_data
from functions.game.game_data import fetch_game_data, get_detailed_data, filter_and_rank_highlights, line_score_report

def validate_date(date_str: str) -> bool:
    """
    Validate that the input date string is in the correct format (YYYY-MM-DD)
    """
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def main():
    # Get user input
    date = input("Enter date (YYYY-MM-DD): ")
    while not validate_date(date):
        print("Invalid date format. Please use YYYY-MM-DD format.")
        date = input("Enter date (YYYY-MM-DD): ")
    
    try:
        team_id = int(input("Enter team ID: "))
    except ValueError:
        print("Invalid team ID. Please enter a number.")
        return

    # Fetch initial schedule data
    schedule_data = get_schedule_data(date, team_id)
    if not schedule_data:
        return json.dumps({"error": "No data found for the specified date and team."}, indent=4)

    # Get game pk and basic game info
    game_pk = extract_game_pk(schedule_data)
    game_info = pull_schedule_data(schedule_data)

    if not game_pk:
        return json.dumps({"error": "No game PK found for the specified date and team."}, indent=4)

    # Fetch detailed game data
    detailed_data = fetch_game_data(game_pk)
    if not detailed_data:
        return json.dumps({"error": "Could not fetch detailed game data."}, indent=4)

    # Get detailed game info and line score
    game_details = get_detailed_data(detailed_data)
    line_score = line_score_report(detailed_data["liveData"]["linescore"])

    # Get highlights
    all_plays = detailed_data["liveData"]["plays"]["allPlays"]
    highlights = filter_and_rank_highlights(all_plays)

    # Create comprehensive response
    response = {
        "date": date,
        "your_team_id": team_id,
        "game_pk": game_pk,
        "game_info": {
            "teams": {
                "home": {
                    "team_id": game_info.get("home_team_id"),
                    "score": game_info.get("home_score"),
                    "record": game_info.get("home_record")
                },
                "away": {
                    "team_id": game_info.get("away_team_id"),
                    "score": game_info.get("away_score"),
                    "record": game_info.get("away_record")
                }
            },
            "result": {
                "winner": game_info.get("winner"),
                "loser": game_info.get("loser")
            },
            "venue": game_info.get("venue"),
            "content_link": game_info.get("content_link")
        },
        "detailed_info": game_details,
        "line_score": line_score,
        "highlights": highlights[:5]  # Top 5 highlights
    }

    # Convert to formatted JSON string
    json_response = json.dumps(response, indent=4)
    print(json_response)
    with open("C:\Users\jmo24\OneDrive\Desktop\Work\MLB\Draft1\outputsgame.json", "w") as outfile:
        outfile.write(json_response)


    return json_response

if __name__ == "__main__":
    main()