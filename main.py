
from flask import Flask, request
import requests

app = Flask(__name__)

AIRTABLE_BASE_ID = "app9VwN9k00nPmpNC"
AIRTABLE_TABLE_NAME = "Reels"
AIRTABLE_API_KEY = "patCCJQPkpHn8HURJ.ab0c036429d219b5deb8b30ca3c5619c843a1cbb59d199c88ede37139a448182"
RAPIDAPI_KEY = "d2e8898bfemsh86306d337b38bcap193d1djsnbfe332449d9a"
RAPIDAPI_HOST = "instagram-scrapper-posts-reels-stories-downloader.p.rapidapi.com"

@app.route("/", methods=["GET", "POST"])
def run_job():
    print("🚀 Starting sync job...")

    try:
        airtable_url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
        headers_airtable = {
            "Authorization": f"Bearer {AIRTABLE_API_KEY}",
            "Content-Type": "application/json"
        }

        # Check Airtable connection
        res = requests.get(airtable_url, headers=headers_airtable)
        print(f"🔁 Airtable fetch status: {res.status_code}")
        print(f"📄 Airtable response preview: {res.text[:500]}")
        if res.status_code != 200:
            return f"Airtable error: {res.text}", 500

        records = res.json().get("records", [])
        usernames = [r["fields"]["Username"] for r in records if "Username" in r["fields"]]
        print(f"📋 Found {len(usernames)} usernames: {usernames}")

        existing_links = set()
        offset = None
        while True:
            params = {"offset": offset} if offset else {}
            link_res = requests.get(airtable_url, headers=headers_airtable, params=params)
            link_data = link_res.json()
            for record in link_data.get("records", []):
                link = record.get("fields", {}).get("Reel Link")
                if link:
                    existing_links.add(link)
            offset = link_data.get("offset")
            if not offset:
                break

        for username in usernames:
            print(f"🔍 Processing: {username}")
            try:
                user_id_res = requests.get(
                    f"https://{RAPIDAPI_HOST}/user_id_by_username?username={username}",
                    headers={
                        "x-rapidapi-key": RAPIDAPI_KEY,
                        "x-rapidapi-host": RAPIDAPI_HOST
                    }
                )
                print(f"🆔 User lookup status: {user_id_res.status_code}")
                print(f"🆔 User lookup response: {user_id_res.text[:500]}")
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
                print(f"📽️ Reels fetch status: {reels_res.status_code}")
                reels = reels_res.json().get("data", [])
                print(f"📽️ Found {len(reels)} reels. Saving up to 50 new...")

                new_count = 0
                for reel in reels:
                    if new_count >= 50:
                        break
                    link = reel.get("video_url", "")
                    if not link or link in existing_links:
                        continue
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
                    print(f"📥 Airtable add status: {post_res.status_code}")
                    if post_res.status_code == 200:
                        print(f"✅ Added: {link}")
                        new_count += 1
                    else:
                        print(f"⚠️ Failed to add: {link}, Response: {post_res.text}")
            except Exception as e:
                print(f"❌ Error processing user {username}: {e}")

    except Exception as e:
        print(f"💥 Fatal error: {e}")
        return f"Error: {e}", 500

    return "✅ Done (Debug Mode)", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
