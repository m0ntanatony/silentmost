# silentmost 🕶️

**silentmost** is a single-file CLI tool for interacting with Mattermost bots and Direct Messages.

It is designed for:
- bot operators
- SRE / DevOps engineers
- automation scripts
- anyone who wants a clean, readable DM workflow without `channel_id`

The focus is **stable layout**, **human-friendly output**, and **DM-first UX**.

---

## ✨ Features

- No `channel_id` required
- Direct Messages only (DM-first)
- Stable column alignment (Unicode / emoji safe)
- Boxed messages for clear visual boundaries
- List DM chats with activity stats
- Read DM by username
- Read all DMs
- Send Direct Messages
- Follow / tail mode (`--follow`)
- JSON output for scripting
- Single Python file
- No cache, no database

---

## 📦 Requirements

- Python **3.9+**
- Mattermost **Bot Token**

Python dependencies:
- `requests`
- `wcwidth`

---

## 📥 Installation

```bash
pip install -r requirements.txt
chmod +x silentmost.py
````

---

## 🔑 Authentication

Create a **Mattermost bot** and copy its token.

The bot must:

* be enabled
* be in the same team as users
* have permissions:

  * `create_post`
  * `create_direct_channel`

---

## 🚀 Usage

### Bot information

```bash
./silentmost.py -u https://chat.company.com -t TOKEN me
```

---

### List DM chats

```bash
./silentmost.py -u https://chat.company.com -t TOKEN chats
```

Example output:

```
USER                     🤖     👤     STATE  LAST MESSAGE
----------------------------------------------------------
john.doe                 3      1      🔥     please check this
alice.smith              0      0      💤
```

Only chats with user replies:

```bash
./silentmost.py ... chats --unread-only
```

---

### Read DM with a user

```bash
./silentmost.py ... read --user john.doe
```

Boxed output:

```
┌─[12:01:03]  👾 silentbot
│  Hello!
│
│  Your VPN configuration is ready.
└────────────────────────────────────
```

---

### Follow / tail mode

```bash
./silentmost.py ... read --user john.doe --follow
```

---

### Read all DM chats

```bash
./silentmost.py ... read --all
```

---

### Send a Direct Message

```bash
./silentmost.py ... send john.doe "Hello 👋"
```

---

### JSON output (for scripts)

```bash
./silentmost.py ... chats --json | jq
./silentmost.py ... read --user john.doe --json
```

---

## 🧠 Design Notes

* All column widths are calculated using **visual width**, not string length
* Emoji, Unicode, and Cyrillic text do **not** break alignment
* Each message is rendered as a **single visual block**
* No caching is used — output always reflects current state

---

## 🛡 License

MIT License
See [`LICENSE`](LICENSE)

---

## 🙌 Contributing

This project is intentionally kept simple:

* single file
* minimal dependencies
* predictable CLI behavior

Ideas, improvements, and PRs are welcome.

---

## ⭐ Why “silentmost”?

Because it speaks quietly — directly and clearly — only where it matters.
