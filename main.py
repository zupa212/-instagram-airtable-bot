
from flask import Flask, request
import requests

app = Flask(__name__)

# Your credentials
AIRTABLE_BASE_ID = "app9VwN9k00nPmpNC"
AIRTABLE_TABLE_NAME = "Reels"
AIRTABLE_API_KEY = "patCCJQPkpHn8HURJ.ab0c036429d219b5deb8b30ca3c5619c843a1cbb59d199c88ede37139a448182"
RAPIDAPI_KEY = "d2e8898bfemsh86306d337b38bcap193d1djsnbfe332449d9a"
RAPIDAPI_HOST = "instagram-scrapper-posts-reels-stories-downloader.p.rapidapi.com"

@app.route("/", methods=["POST"])
def run_job():
    url_airtable = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    headers_airtable = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }

    res = requests.get(url_airtable, headers=headers_airtable)
    records = res.json().get("records", [])
    usernames = [r["fields"]["Username"] for r in records if "Username" in r["fields"]]

    for username in usernames:
        user_id_res = requests.get(
            f"https://{RAPIDAPI_HOST}/user_id_by_username?username={username}",
            headers={
                "x-rapidapi-key": RAPIDAPI_KEY,
                "x-rapidapi-host": RAPIDAPI_HOST
            }
        )
        user_id = user_id_res.json().get("user_id")
        if not user_id:
            continue

        reels_res = requests.get(
            f"https://{RAPIDAPI_HOST}/reels?user_id={user_id}&include_feed_video=true",
            headers={
                "x-rapidapi-key": RAPIDAPI_KEY,
                "x-rapidapi-host": RAPIDAPI_HOST
            }
        )
        reels = reels_res.json().get("data", [])

        for reel in reels:
            data = {
                "fields": {
                    "Username": username,
                    "Caption": reel.get("caption", ""),
                    "Reel Link": reel.get("video_url", ""),
                    "Thumbnail": reel.get("thumbnail_url", ""),
                    "Views": reel.get("play_count", 0)
                }
            }
            requests.post(url_airtable, headers=headers_airtable, json=data)

    return "✅ Done", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
