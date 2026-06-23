import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.json"
STATE_PATH = BASE_DIR / "state.json"
VIDEO_PATH = BASE_DIR / "temp_video.mp4"
LOG_PATH = BASE_DIR / "poster.log"
VIDEO_CACHE_TTL = 3600
MAX_RETRIES = 3


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{ts}  {msg}"
    try:
        print(line)
    except UnicodeEncodeError:
        safe = line.encode(sys.stdout.encoding, errors="replace").decode(sys.stdout.encoding)
        print(safe)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def now_utc():
    return datetime.now(timezone.utc)


def parse_time_iso(s):
    if s is None:
        return None
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


def hours_since(dt):
    if dt is None:
        return float("inf")
    diff = now_utc() - dt
    return diff.total_seconds() / 3600


EXTRACTOR_ARGS = ["--extractor-args", "tiktok:api_hostname=www.tiktok.com"]


def run_youtube_dl(cmd, timeout):
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        log(f"  stderr: {result.stderr.strip()[:500]}")
    return result


def fetch_tiktok_videos(username):
    url = f"https://www.tiktok.com/@{username}"
    for attempt in range(3):
        cmd = [
            sys.executable, "-m", "yt_dlp",
            *EXTRACTOR_ARGS,
            "--flat-playlist",
            "--dump-json",
            "--no-warnings",
            url,
        ]
        result = run_youtube_dl(cmd, 180)
        if result.returncode == 0:
            break
        if attempt < 2:
            log(f"Retrying fetch ({attempt + 1}/3)...")
            time.sleep(5)
    else:
        log("Fetch failed after 3 attempts.")
        return []

    videos = []
    for line in result.stdout.strip().splitlines():
        if not line:
            continue
        try:
            info = json.loads(line)
            vid_id = info.get("id")
            if not vid_id:
                continue
            videos.append({
                "id": str(vid_id),
                "title": info.get("title") or info.get("description", ""),
                "url": info.get("webpage_url") or f"https://www.tiktok.com/@{username}/video/{vid_id}",
            })
        except json.JSONDecodeError:
            continue
    videos.reverse()
    return videos


def download_video(url, output_path):
    if output_path.exists():
        output_path.unlink()
    cmd = [
        sys.executable, "-m", "yt_dlp",
        *EXTRACTOR_ARGS,
        "-f", "best[ext=mp4]/best",
        "-o", str(output_path),
        "--no-warnings",
        url,
    ]
    result = run_youtube_dl(cmd, 300)
    if result.returncode != 0:
        log("Download failed.")
        return False
    return output_path.exists() and output_path.stat().st_size > 0


def upload_to_facebook(page_id, access_token, video_path, description=""):
    url = f"https://graph.facebook.com/v22.0/{page_id}/videos"
    with open(video_path, "rb") as f:
        files = {"source": f}
        data = {
            "access_token": access_token,
            "description": description,
        }
        resp = requests.post(url, files=files, data=data, timeout=600)
    if not resp.ok:
        log(f"Facebook HTTP {resp.status_code}: {resp.text}")
        return False
    try:
        result = resp.json()
    except ValueError:
        log(f"Facebook returned non-JSON: {resp.text}")
        return False
    if "id" in result:
        log(f"Uploaded successfully! Facebook ID: {result['id']}")
        return True
    log(f"Facebook upload error: {result}")
    return False


def get_videos(username, state):
    now = now_utc()
    last_fetch = parse_time_iso(state.get("last_video_fetch_time"))
    if last_fetch and (now - last_fetch).total_seconds() < VIDEO_CACHE_TTL:
        cached = state.get("cached_videos", [])
        if cached:
            log(f"Using cached video list ({len(cached)} videos, fetched {int((now - last_fetch).total_seconds())}s ago)")
            return cached
    log("Fetching TikTok video list...")
    videos = fetch_tiktok_videos(username)
    if videos:
        state["cached_videos"] = videos
        state["last_video_fetch_time"] = now.isoformat()
        save_json(STATE_PATH, state)
        log(f"Fetched {len(videos)} videos")
    return videos


def main():
    start = time.time()
    log("START")

    if not CONFIG_PATH.exists():
        log("config.json not found.")
        sys.exit(1)

    config = load_json(CONFIG_PATH)
    username = config.get("tiktok_username", "").lstrip("@")
    page_id = config.get("facebook_page_id", "")
    token = config.get("facebook_access_token", "")
    interval_hours = config.get("post_interval_hours", 24)
    start_from = config.get("start_from_video_id")

    if not username or not page_id or not token:
        log("config.json incomplete.")
        sys.exit(1)

    state = load_json(STATE_PATH) if STATE_PATH.exists() else {}
    state.setdefault("posted_ids", [])
    state.setdefault("failed_ids", {})
    state.setdefault("last_post_time", None)

    state["posted_ids"] = [str(i) for i in state["posted_ids"]]
    failed_ids_raw = {}
    for k, v in state["failed_ids"].items():
        failed_ids_raw[str(k)] = int(v)
    state["failed_ids"] = failed_ids_raw

    last_time = parse_time_iso(state.get("last_post_time"))
    posted_ids = set(state["posted_ids"])

    if hours_since(last_time) < interval_hours:
        log(f"Next post in {interval_hours - hours_since(last_time):.1f}h. Posted: {len(posted_ids)}. Failed: {len(state['failed_ids'])}. Nothing to do.")
        sys.exit(0)

    videos = get_videos(username, state)
    if not videos:
        log("No videos found.")
        sys.exit(1)

    for v in videos:
        vid = v["id"]
        if vid in posted_ids:
            continue
        if vid in state["failed_ids"] and state["failed_ids"][vid] >= MAX_RETRIES:
            log(f"SKIP  {vid}  (failed {MAX_RETRIES}x, giving up)")
            posted_ids.add(vid)
            continue
        if start_from and vid != start_from:
            posted_ids.add(vid)
            continue
        start_from = None

        log(f"DL    {vid}  {v['title'][:60]}")
        if not download_video(v["url"], VIDEO_PATH):
            retries = state["failed_ids"].get(vid, 0) + 1
            state["failed_ids"][vid] = retries
            log(f"FAIL  {vid}  (download, attempt {retries}/{MAX_RETRIES})")
            save_json(STATE_PATH, state)
            continue

        log(f"UP    {vid}")
        success = upload_to_facebook(page_id, token, VIDEO_PATH, v.get("title", "")[:1000])

        if VIDEO_PATH.exists():
            VIDEO_PATH.unlink()

        if success:
            posted_ids.add(vid)
            state["posted_ids"] = list(posted_ids)
            state["last_post_time"] = now_utc().isoformat()
            if vid in state["failed_ids"]:
                del state["failed_ids"][vid]
            save_json(STATE_PATH, state)
            elapsed = time.time() - start
            log(f"POST  {vid}  (took {elapsed:.0f}s, total posted: {len(posted_ids)})")
            log(f"DONE  (duration: {elapsed:.0f}s)")
            sys.exit(0)
        else:
            retries = state["failed_ids"].get(vid, 0) + 1
            state["failed_ids"][vid] = retries
            log(f"FAIL  {vid}  (upload, attempt {retries}/{MAX_RETRIES})")
            save_json(STATE_PATH, state)

    elapsed = time.time() - start
    log(f"ALL POSTED OR FAILED  (duration: {elapsed:.0f}s)")
    sys.exit(0)


def list_videos():
    config = load_json(CONFIG_PATH) if CONFIG_PATH.exists() else {}
    username = config.get("tiktok_username", "").lstrip("@")
    if not username:
        print("Set tiktok_username in config.json first.")
        sys.exit(1)
    print("Fetching video list...")
    videos = fetch_tiktok_videos(username)
    if not videos:
        print("No videos found.")
        sys.exit(1)
    for i, v in enumerate(videos, 1):
        title = v['title'][:70].encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
        print(f"{i:>4}. {v['id']}  {title}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--list-videos":
        if not CONFIG_PATH.exists():
            print("config.json not found.")
            sys.exit(1)
        list_videos()
    else:
        main()
