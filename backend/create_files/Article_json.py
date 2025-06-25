import requests
import json

def fetch_content_data(game_pk: int) -> dict:
    """
    Given a gamePk, fetch content data (videos, highlights) from the MLB API.
    """
    api_url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/content"
    response = requests.get(api_url)
    if response.status_code == 200:
        content_data = response.json()
        articles = content_data.get("editorial", {}).get("recap", {}).get("mlb", {})
        headlines = []
        seo_titles = []
        
        if articles:
            headline = articles.get("headline")
            seo_title = articles.get("seoTitle")
            if headline and seo_title:
                headlines.append(headline)
                seo_titles.append(seo_title)
        
        # Find the video with the duration closest to 90 seconds
        videos = content_data.get("highlights", {}).get("highlights", {}).get("items", [])
        closest_video = None
        closest_duration_diff = float('inf')
        for video in videos:
            if not video.get("noIndex"):
                duration = video.get("duration", "00:00:00")
                # Assuming duration format is HH:MM:SS; we only need minutes and seconds
                minutes, seconds = map(int, duration.split(":")[1:])
                total_seconds = minutes * 60 + seconds
                duration_diff = abs(total_seconds - 90)
                if duration_diff < closest_duration_diff:
                    closest_duration_diff = duration_diff
                    closest_video = video
        
        # Extract the first video URL ending in .mp4 and its associated title and description
        video_url = None
        video_title = None
        video_description = None
        if closest_video:
            playbacks = closest_video.get("playbacks", [])
            for playback in playbacks:
                url = playback.get("url", "")
                if "mp4" in playback.get("name", "").lower():
                    video_url = url
                    video_title = closest_video.get("title")
                    video_description = closest_video.get("description")
                    break
        
        return {
            "headlines": headlines,
            "seo_titles": seo_titles,
            "closest_video_url": video_url,
            "closest_video_title": video_title,
            "closest_video_description": video_description
        }
    else:
        print(f"Error fetching content data for gamePk {game_pk}: {response.status_code}")
        return {}

def main():
    # Hardcoded gamePk for testing
    game_pk = 716362
    
    # Fetch content data for the given gamePk
    content_data = fetch_content_data(game_pk)
    
    # Print the parsed content data in JSON format
    print("\nParsed Content Data in JSON Format:")
    print("-" * 80)
    print(json.dumps(content_data, indent=4))
    
    # Convert to formatted JSON string and write to file
    output_file_path = r"C:\Users\jmo24\OneDrive\Desktop\Work\MLB\Draft1\Article.json"
    with open(output_file_path, 'w') as outfile:
        json.dump(content_data, outfile, indent=4)
    
    print(f"Content data has been written to {output_file_path}")

if __name__ == "__main__":
    main()