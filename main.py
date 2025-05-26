
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
    print("🚀 Starting sync job...")

    airtable_url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    headers_airtable = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }

    # 1. Fetch existing Reel Links (to avoid duplicates)
    existing_links = set()
    offset = None
    while True:
        params = {"offset": offset} if offset else {}
        res = requests.get(airtable_url, headers=headers_airtable, params=params)
        data = res.json()
        for record in data.get("records", []):
            link = record.get("fields", {}).get("Reel Link")
            if link:
                existing_links.add(link)
        offset = data.get("offset")
        if not offset:
            break

    # 2. Fetch usernames from Airtable
    res = requests.get(airtable_url, headers=headers_airtable)
    records = res.json().get("records", [])
    usernames = [r["fields"]["Username"] for r in records if "Username" in r["fields"]]

    for username in usernames:
        print(f"🔍 Processing: {username}")

        user_id_res = requests.get(
            f"https://{RAPIDAPI_HOST}/user_id_by_username?username={username}",
            headers={
                "x-rapidapi-key": RAPIDAPI_KEY,
                "x-rapidapi-host": RAPIDAPI_HOST
            }
        )
        user_id = user_id_res.json().get("user_id")
        if not user_id:
            print(f"❌ No user_id found for {username}")
            continue

        reels_res = requests.get(
            f"https://{RAPIDAPI_HOST}/reels?user_id={user_id}&include_feed_video=true",
            headers={
                "x-rapidapi-key": RAPIDAPI_KEY,
                "x-rapidapi-host": RAPIDAPI_HOST
            }
        )
        reels = reels_res.json().get("data", [])
        print(f"📽️ Found {len(reels)} reels. Saving up to 50 new...")

        new_count = 0
        for reel in reels:
            if new_count >= 50:
                break
            link = reel.get("video_url", "")
            if not link or link in existing_links:
                continue  # Skip duplicates

            data = {
                "fields": {
                    "Username": username,
                    "Caption": reel.get("caption", ""),
                    "Reel Link": link,
                    "Thumbnail": reel.get("thumbnail_url", ""),
                    "Views": reel.get("play_count", 0)
                }
            }
            post_res = requests.post(airtable_url, headers=headers_airtable, json=data)
            if post_res.status_code == 200:
                print(f"✅ Added: {link}")
                new_count += 1
            else:
                print(f"⚠️ Failed to add reel: {link}")

    return "✅ Done", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
