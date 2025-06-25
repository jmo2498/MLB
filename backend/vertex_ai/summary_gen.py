import json
import os
import vertexai
from vertexai.preview.generative_models import GenerativeModel

def initialize_vertex_ai():
    """Initialize Vertex AI with credentials."""
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(os.getcwd(), "cred_path")
    vertexai.init(project="projectId", location="location")

def generate_detailed_summary(game_data):
    """
    Build a detailed two-paragraph summary prompt using the provided game data.
    """
    # Extract game information
    game_info = game_data.get("game_info", {})
    detailed_info = game_data.get("detailed_info", {})
    highlights = game_data.get("highlights", [])

    # Extract scores and result details
    home_score = game_info.get("teams", {}).get("home", {}).get("score", "N/A")
    away_score = game_info.get("teams", {}).get("away", {}).get("score", "N/A")
    winner = game_info.get("result", {}).get("winner", "N/A")
    loser = game_info.get("result", {}).get("loser", "N/A")

    # Extract pitcher and team details
    away_pitcher = detailed_info.get("away_pitcher", {}).get("fullName", "N/A")
    home_pitcher = detailed_info.get("home_pitcher", {}).get("fullName", "N/A")
    home_team = detailed_info.get("home_team", "N/A")
    away_team = detailed_info.get("away_team", "N/A")

    # Extract venue and game type
    venue = detailed_info.get("venue", "N/A")
    day_night = detailed_info.get("day_night", "N/A")

    # Use attendance if available, otherwise default to "N/A"
    attendance = game_data.get("attendance", "N/A")

    # Sort highlights by inning and ensure top-half plays come before bottom-half plays.
    sorted_highlights = sorted(highlights, key=lambda x: (x.get('inning', 0), not x.get('isTop', True)))
    highlights_str = "\n".join([
        f"- {'Top' if h.get('isTop') else 'Bottom'} {h.get('inning')}: {h.get('description')} (Score: {h.get('score')}, PlayID: {h.get('playId')})"
        for h in sorted_highlights if h.get('description')
    ])

    prompt = f"""Create a detailed two-paragraph summary of this MLB game:

Game Context:
- Final Score: {winner} {home_score}, {loser} {away_score}
- Starting Pitchers: {away_pitcher} (Away) vs {home_pitcher} (Home)
- Venue: {venue} ({day_night} game)
- Attendance: {attendance}

Chronological Key Plays:
{highlights_str}

Write two detailed paragraphs:
1. The first paragraph should focus on the game flow and early key plays.
2. The second paragraph should cover later developments and the final outcome.
"""
    return prompt

def generate_concise_summary(game_data):
    """
    Build a concise, single-sentence summary prompt using the provided game data.
    """
    game_info = game_data.get("game_info", {})
    detailed_info = game_data.get("detailed_info", {})
    highlights = game_data.get("highlights", [])

    home_score = game_info.get("teams", {}).get("home", {}).get("score", "N/A")
    away_score = game_info.get("teams", {}).get("away", {}).get("score", "N/A")
    winner = game_info.get("result", {}).get("winner", "N/A")
    loser = game_info.get("result", {}).get("loser", "N/A")
    venue = detailed_info.get("venue", "N/A")
    attendance = game_data.get("attendance", "N/A")

    # Choose the first available highlight as the key play
    key_play = highlights[0].get("description", "N/A") if highlights else "N/A"

    prompt = f"""Create a single-sentence summary of this MLB game that captures the key outcome:

Game Context:
- Final Score: {winner} {home_score}, {loser} {away_score}
- Most Impactful Play: {key_play}
- Venue: {venue}
- Attendance: {attendance}

Compose one punchy sentence that includes:
1. The key offensive play,
2. The final score, and
3. The dominant team's performance.
"""
    return prompt

def generate_game_summary(prompt):
    """
    Generate game summary content by sending the prompt to Vertex AI.
    """
    model = GenerativeModel("gemini-1.5-pro-002")
    print(f"Prompt sent to model:\n{prompt}\n")  # Debugging line
    response = model.generate_content(
        contents=[prompt],
        generation_config={
            "temperature": 0.7,
            "max_output_tokens": 512,
            "top_p": 0.8
        }
    )
    print(f"Model response:\n{response.text}\n")  # Debugging line
    return response.text

def main():
    # Get the JSON file path from the user
    file_path = input("Enter the path to the JSON file containing the MLB game data: ").strip()
    
    # Load the JSON data
    with open(file_path, 'r') as f:
        game_data = json.load(f)
    
    # Initialize Vertex AI
    initialize_vertex_ai()

    # Generate the detailed game summary
    detailed_prompt = generate_detailed_summary(game_data)
    detailed_summary = generate_game_summary(detailed_prompt)

    # Generate the concise game summary
    concise_prompt = generate_concise_summary(game_data)
    concise_summary = generate_game_summary(concise_prompt)

    output_data = {
        "detailed_summary": detailed_summary,
        "concise_summary": concise_summary
    }
    
    #output_file_path = r"C:\Users\jmo24\OneDrive\Desktop\Work\MLB\Draft1\outputs\game_summaries.json"
    #with open(output_file_path, 'w') as outfile:
    #    json.dump(output_data, outfile, indent=4)
    
    #print(f"Summaries have been written to {output_file_path}")

if __name__ == "__main__":
    main()
