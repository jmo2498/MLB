from flask import Flask, make_response, request, jsonify, send_file
from flask_cors import CORS
from datetime import datetime
import json
import os

# Import your custom functions
from functions.sched.sched_data import get_schedule_data, extract_game_pk, pull_schedule_data
from functions.game.game_data import fetch_game_data, get_detailed_data, filter_and_rank_highlights, line_score_report
from create_files.Article_json import fetch_content_data
from vertex_ai.summary_gen import (
    initialize_vertex_ai,
    generate_detailed_summary,
    generate_concise_summary,
    generate_game_summary,
)

app = Flask(__name__)

# Configure CORS for frontend access
CORS(app, resources={
    r"/game-data": {
        "origins": ["https://mlb-final.uk.r.appspot.com"],
        "methods": ["GET", "OPTIONS"],  # Include OPTIONS for preflight requests
        "allow_headers": ["Content-Type", "Accept", "Origin"],
        "expose_headers": ["Content-Type"],
        "supports_credentials": True
    }
})

# Define output directory for file storage
#OUTPUT_DIR = r"none"
#os.makedirs(OUTPUT_DIR, exist_ok=True)

def validate_date(date_str: str) -> bool:
    """Validate that the input date string is in the correct format (YYYY-MM-DD)."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def get_combined_game_data(date: str, team_id: int) -> dict:
    """
    Core function to fetch and combine all game data.
    Used by both file storage and JSON response functions.
    """
    try:
        # Fetch schedule data
        schedule_data = get_schedule_data(date, team_id)
        print("Schedule Data:", json.dumps(schedule_data, indent=4))
        if not schedule_data:
            return None

        # Extract game_pk and basic game info
        game_pk = extract_game_pk(schedule_data)
        if not game_pk:
            print("No gamePk extracted from schedule data for date:", date, "and team_id:", team_id)
            return None
        game_info = pull_schedule_data(schedule_data)

        # Fetch detailed game data
        detailed_data = fetch_game_data(game_pk)
        if not detailed_data:
            return None
        game_details = get_detailed_data(detailed_data)
        line_score = line_score_report(detailed_data["liveData"]["linescore"])
        all_plays = detailed_data["liveData"]["plays"]["allPlays"]
        highlights = filter_and_rank_highlights(all_plays)

        # Fetch content data (Article)
        content_data = fetch_content_data(game_pk)

        # Combine all data
        combined_data = {
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
            "highlights": highlights[:5],  # Top 5 highlights
            "content_data": content_data
        }

        # Generate summaries using Vertex AI
        initialize_vertex_ai()
        detailed_prompt = generate_detailed_summary(combined_data)
        concise_prompt = generate_concise_summary(combined_data)
        detailed_summary = generate_game_summary(detailed_prompt)
        concise_summary = generate_game_summary(concise_prompt)
        combined_data["detailed_summary"] = detailed_summary
        combined_data["concise_summary"] = concise_summary

        return combined_data
    except Exception as e:
        print(f"Error fetching and combining game data: {str(e)}")
        return None

def process_game_data(date: str, team_id: int) -> str:
    """
    Process game data and save to file.
    Used for storage and other functions that need file access.
    Returns the path to the output file.
    """
    combined_data = get_combined_game_data(date, team_id)
    if not combined_data:
        return None

    # Save to output.json (overwrites on each request)
   # output_file_path = os.path.join(OUTPUT_DIR, "output.json")
    #with open(output_file_path, "w") as f:
    #    json.dump(combined_data, f, indent=4)

    #return output_file_path

def process_game_data_json(date: str, team_id: int) -> dict:
    """
    Process game data and return as dictionary.
    Used for API endpoint responses.
    """
    return get_combined_game_data(date, team_id)

@app.route("/game-data", methods=["GET", "OPTIONS"])
def game_data_endpoint():
    if request.method == "OPTIONS":
        # Handle preflight request
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "https://mlb-final.uk.r.appspot.com")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type,Accept,Origin")
        response.headers.add("Access-Control-Allow-Methods", "GET,OPTIONS")
        return response

    # Your existing endpoint code here...
    date = request.args.get("date")
    team_id = request.args.get("team_id")
    
    if not date or not team_id:
        return jsonify({"error": "Please select a date and team first"}), 400

    try:
        combined_data = get_combined_game_data(date, int(team_id))
        
        if not combined_data:
            return jsonify({"error": "No game data found"}), 404

        response = jsonify(combined_data)
        response.headers.add("Access-Control-Allow-Origin", "https://mlb-final.uk.r.appspot.com")
        return response

    except Exception as e:
        print(f"Error processing game data: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)