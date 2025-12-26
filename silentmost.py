└─$ cat silentmost.py 
#!/usr/bin/env python3
"""
silentmost — Mattermost Direct Message CLI for bots
License: MIT
"""

import argparse
import sys
import time
import json
import requests
import textwrap
from wcwidth import wcswidth

# ================= CONFIG =================

POLL_INTERVAL = 3
CHAT_SCAN_LIMIT = 200

BOT_EMOJI = "🤖"
USER_EMOJI = "👤"
BOT_BOX_EMOJI = "👾"
ACTIVE_EMOJI = "🔥"
SLEEP_EMOJI = "💤"

# table column widths (VISUAL, wcwidth-based)
COL_USER = 24
COL_CNT  = 6

# ================= UTILS =================

def vlen(s: str) -> int:
    return wcswidth(s)

def pad(s: str, width: int) -> str:
    return s + " " * max(0, width - vlen(s))

def hr(width: int) -> str:
    return "─" * width

# ================= HTTP =================

def headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

def get(url, token, params=None):
    r = requests.get(url, headers=headers(token), params=params)
    r.raise_for_status()
    return r.json()

def post(url, token, payload):
    r = requests.post(url, headers=headers(token), json=payload)
    r.raise_for_status()
    return r.json()

# ================= CORE =================

def me(base, token):
    return get(f"{base}/api/v4/users/me", token)

def user_by_username(base, token, username):
    return get(f"{base}/api/v4/users/username/{username}", token)

def user_by_id(base, token, uid):
    return get(f"{base}/api/v4/users/{uid}", token)

def my_channels(base, token, uid):
    return get(f"{base}/api/v4/users/{uid}/channels", token)

def dm_channels(base, token, uid):
    return [c for c in my_channels(base, token, uid) if c["type"] == "D"]

def dm_peer_id(channel, bot_id):
    a, b = channel["name"].split("__")
    return a if b == bot_id else b

def fetch_posts(base, token, channel_id, since=None, limit=CHAT_SCAN_LIMIT):
    params = {"per_page": limit}
    if since:
        params["since"] = since
    data = get(f"{base}/api/v4/channels/{channel_id}/posts", token, params)
    posts = data.get("posts", {})
    order = data.get("order", [])
    for pid in reversed(order):
        yield posts[pid]

def create_dm(base, token, bot_id, user_id):
    ch = post(f"{base}/api/v4/channels/direct", token, [bot_id, user_id])
    return ch["id"]

def send(base, token, channel_id, text):
    post(f"{base}/api/v4/posts", token, {
        "channel_id": channel_id,
        "message": text,
    })

# ================= CHAT STATS =================

def count_and_preview(base, token, channel_id, bot_id):
    data = get(
        f"{base}/api/v4/channels/{channel_id}/posts",
        token,
        params={"per_page": CHAT_SCAN_LIMIT},
    )

    posts = list(data.get("posts", {}).values())

    bot_cnt = sum(1 for p in posts if p["user_id"] == bot_id)
    user_cnt = len(posts) - bot_cnt

    preview = ""
    if posts:
        last = max(posts, key=lambda p: p["create_at"])
        preview = textwrap.shorten(last["message"], width=40, placeholder="…")

    return bot_cnt, user_cnt, preview

# ================= BOXED MESSAGE =================

def print_boxed_message(post, author, is_bot):
    ts = time.strftime("%H:%M:%S", time.localtime(post["create_at"] / 1000))
    emoji = BOT_BOX_EMOJI if is_bot else USER_EMOJI

    header = f"[{ts}]  {emoji} {author}"
    lines = post["message"].splitlines() or [""]

    lines = [l.rstrip() for l in lines]

    content_width = max(
        vlen(header),
        *(vlen(l) for l in lines),
        20
    )

    print(f"┌─{header}")
    for l in lines:
        print(f"│  {l}")
    print("└" + hr(content_width + 1))

# ================= COMMANDS =================

def cmd_me(base, token, json_mode):
    bot = me(base, token)

    if json_mode:
        print(json.dumps(bot, indent=2))
        return

    print("Bot Information")
    print("───────────────")
    print(f"Username : {bot['username']}")
    print(f"ID       : {bot['id']}")
    print(f"Email    : {bot.get('email', '-')}")
    print(f"Roles    : {bot.get('roles', '-')}")
    print(f"Created  : {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(bot['create_at']/1000))}")

def cmd_chats(base, token, json_mode, unread_only):
    bot = me(base, token)

    if not json_mode:
        header = (
            pad("USER", COL_USER) + "  " +
            pad(f"{BOT_EMOJI}", COL_CNT) + "  " +
            pad(f"{USER_EMOJI}", COL_CNT) + "  " +
            "STATE  LAST MESSAGE"
        )
        print(header)
        print("-" * vlen(header))

    for ch in dm_channels(base, token, bot["id"]):
        uid = dm_peer_id(ch, bot["id"])
        user = user_by_id(base, token, uid)

        bot_cnt, user_cnt, preview = count_and_preview(
            base, token, ch["id"], bot["id"]
        )

        if unread_only and user_cnt == 0:
            continue

        badge = ACTIVE_EMOJI if user_cnt > 0 else SLEEP_EMOJI

        if json_mode:
            print(json.dumps({
                "username": user["username"],
                "bot_messages": bot_cnt,
                "user_messages": user_cnt,
                "last_message": preview,
            }))
        else:
            print(
                pad(user["username"], COL_USER) + "  " +
                pad(str(bot_cnt), COL_CNT) + "  " +
                pad(str(user_cnt), COL_CNT) + "  " +
                f"{badge:^5}  {preview}"
            )

def cmd_read_user(base, token, username, limit, follow):
    bot = me(base, token)
    target = user_by_username(base, token, username)

    for ch in dm_channels(base, token, bot["id"]):
        if dm_peer_id(ch, bot["id"]) == target["id"]:
            since = None
            while True:
                for p in fetch_posts(base, token, ch["id"], since, limit):
                    since = max(since or 0, p["create_at"])
                    is_bot = p["user_id"] == bot["id"]
                    author = bot["username"] if is_bot else username
                    print_boxed_message(p, author, is_bot)
                if not follow:
                    return
                time.sleep(POLL_INTERVAL)

    print("DM not found", file=sys.stderr)

def cmd_read_all(base, token, limit):
    bot = me(base, token)

    for ch in dm_channels(base, token, bot["id"]):
        uid = dm_peer_id(ch, bot["id"])
        user = user_by_id(base, token, uid)

        print(f"\n=== DM with {user['username']} ===")

        for p in fetch_posts(base, token, ch["id"], limit=limit):
            is_bot = p["user_id"] == bot["id"]
            author = bot["username"] if is_bot else user["username"]
            print_boxed_message(p, author, is_bot)

def cmd_send(base, token, username, message):
    bot = me(base, token)
    target = user_by_username(base, token, username)
    ch_id = create_dm(base, token, bot["id"], target["id"])
    send(base, token, ch_id, message)
    print("✓ sent")

# ================= CLI =================

def main():
    p = argparse.ArgumentParser("silentmost — Mattermost DM CLI")
    p.add_argument("-u", "--url", required=True)
    p.add_argument("-t", "--token", required=True)
    p.add_argument("--json", action="store_true")

    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("me")

    c = sub.add_parser("chats")
    c.add_argument("--unread-only", action="store_true")

    r = sub.add_parser("read")
    g = r.add_mutually_exclusive_group(required=True)
    g.add_argument("--user")
    g.add_argument("--all", action="store_true")
    r.add_argument("--limit", type=int, default=10)
    r.add_argument("--follow", action="store_true")

    s = sub.add_parser("send")
    s.add_argument("user")
    s.add_argument("message")

    a = p.parse_args()
    base = a.url.rstrip("/")

    try:
        if a.cmd == "me":
            cmd_me(base, a.token, a.json)
        elif a.cmd == "chats":
            cmd_chats(base, a.token, a.json, a.unread_only)
        elif a.cmd == "read":
            if a.user:
                cmd_read_user(base, a.token, a.user, a.limit, a.follow)
            else:
                cmd_read_all(base, a.token, a.limit)
        elif a.cmd == "send":
            cmd_send(base, a.token, a.user, a.message)
    except requests.HTTPError as e:
        print("HTTP error:", e.response.text, file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
