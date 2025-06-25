import requests

def fetch_game_data(game_pk: int) -> dict:
    """
    Given a gamePk, fetch detailed game data from the MLB API.
    """
    api_url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching game data for gamePk {game_pk}: {response.status_code}")
        return {}

def get_detailed_data(detailed_data: dict) -> dict:
    """
    Extract detailed game information from the provided game data.
    """
    game_info = {
        "date": detailed_data["gameData"]["datetime"]["originalDate"],
        "time": detailed_data["gameData"]["datetime"]["time"],
        "venue": detailed_data["gameData"]["venue"]["name"],
        "venue_id": detailed_data["gameData"]["venue"]["id"],
        "day_night": detailed_data["gameData"]["datetime"]["dayNight"],
        "home_team": detailed_data["gameData"]["teams"]["home"]["name"],
        "home_team_id": detailed_data["gameData"]["teams"]["home"]["id"],
        "away_team": detailed_data["gameData"]["teams"]["away"]["name"],
        "away_team_id": detailed_data["gameData"]["teams"]["away"]["id"],
    }
    
    # Get probable pitchers if available
    game_info["away_pitcher"] = detailed_data["gameData"]["probablePitchers"].get("away", None)
    game_info["home_pitcher"] = detailed_data["gameData"]["probablePitchers"].get("home", None)
    
    return game_info

def rank_play(play):
    """
    Assign a numerical score to a play based on its event type and other criteria.
    Also extract the playId from the playEvents (if present).
    """
    score = 1
    result = play.get("result", {})
    event_type = result.get("eventType", "").lower()

    # Score based on event type
    if event_type == "home_run":
        score = 5
    elif event_type in ["triple", "double", "double_play"]:
        score = 4
    elif event_type in ["strikeout", "walk", "stolen_base"]:
        score = 3

    # Additional scoring criteria
    if result.get("rbi", 0) > 0:
        score += 1
    if play.get("about", {}).get("isScoringPlay", False):
        score += 2
    if play.get("about", {}).get("captivatingIndex", 0) > 50:
        score += 1

    # Extract the last playId from playEvents if available
    play_events = play.get("playEvents", [])
    play_id = None
    for event in reversed(play_events):
        if "playId" in event:
            play_id = event["playId"]
            break
    play["playId"] = play_id
    play["score"] = score

    # Extract batter and pitcher information
    matchup = play.get("matchup", {})
    batter = matchup.get("batter", {})
    pitcher = matchup.get("pitcher", {})
    play["batter"] = {
        "id": batter.get("id"),
        "fullName": batter.get("fullName")
    }
    play["pitcher"] = {
        "id": pitcher.get("id"),
        "fullName": pitcher.get("fullName")
    }

    return play

def filter_and_rank_highlights(plays, min_score=3):
    """
    Process a list of play objects: rank each play and filter out those with a score below min_score.
    Returns a sorted list (highest score first) with only the key fields.
    """
    ranked = []
    for play in plays:
        ranked_play = rank_play(play)
        if ranked_play.get("score", 0) >= min_score:
            extracted = {
                "inning": ranked_play.get("about", {}).get("inning"),
                "isTop": ranked_play.get("about", {}).get("isTopInning"),
                "description": ranked_play.get("result", {}).get("description"),
                "event_type": ranked_play.get("result", {}).get("eventType"),
                "playId": ranked_play.get("playId"),
                "score": ranked_play.get("score"),
                "batter": ranked_play.get("batter"),
                "pitcher": ranked_play.get("pitcher")
            }
            ranked.append(extracted)
    ranked.sort(key=lambda x: x.get("score", 0), reverse=True)
    return ranked

def line_score_report(linescore_data: dict) -> dict:
    """
    Extracts and formats the linescore report from the given JSON data.
    """
    current_inning = linescore_data["currentInning"]
    current_inning_ordinal = linescore_data["currentInningOrdinal"]
    inning_state = linescore_data["inningState"]
    scheduled_innings = linescore_data["scheduledInnings"]
    
    linescore_report = {
        "current_inning": f"{current_inning_ordinal} ({inning_state})",
        "scheduled_innings": scheduled_innings,
        "innings": [],
        "totals": {
            "home": {"runs": 0, "hits": 0, "errors": 0, "left_on_base": 0},
            "away": {"runs": 0, "hits": 0, "errors": 0, "left_on_base": 0}
        }
    }
    
    for inning in linescore_data["innings"]:
        num = inning["num"]
        home = inning["home"]
        away = inning["away"]
        
        # Sum up total stats
        for team in ["home", "away"]:
            current_team = locals()[team]
            linescore_report["totals"][team]["runs"] += current_team.get("runs", 0)
            linescore_report["totals"][team]["hits"] += current_team.get("hits", 0)
            linescore_report["totals"][team]["errors"] += current_team.get("errors", 0)
            linescore_report["totals"][team]["left_on_base"] += current_team.get("leftOnBase", 0)
        
        linescore_report["innings"].append({
            "inning": num,
            "home": {
                "runs": home.get("runs", 0),
                "hits": home.get("hits", 0),
                "errors": home.get("errors", 0),
                "left_on_base": home.get("leftOnBase", 0)
            },
            "away": {
                "runs": away.get("runs", 0),
                "hits": away.get("hits", 0),
                "errors": away.get("errors", 0),
                "left_on_base": away.get("leftOnBase", 0)
            }
        })
    
    return linescore_report
