# ⚡ qJackett

> **Lightning-fast interactive TUI torrent searcher powered by Jackett and `fzf`, with 1-click injection into qBittorrent.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform: Linux](https://img.shields.io/badge/Platform-Linux-blue.svg)](https://kernel.org)
[![Shell: Wayland/X11](https://img.shields.io/badge/Wayland-Hyprland%20Ready-green.svg)](https://hyprland.org)

`qjackett` queries all your configured Jackett trackers in parallel (typically in **under 1 second**), sorts results by healthy seeders, displays an interactive fuzzy-search interface with a rich side-preview panel, and injects your chosen torrent directly into **qBittorrent** while copying the magnet link to your clipboard and sending a desktop notification.

---

## ✨ Features

- 🚀 **Parallel Multi-Tracker Search:** Queries dozens of Jackett indexers concurrently using a thread pool.
- 🎯 **Fuzzy Search & Filtering:** Powered by `fzf` — filter titles as you type, or exclude terms easily using `!term`.
- 🗂️ **Multi-Selection Downloads:** Press `Tab` to select multiple torrents and queue them all into qBittorrent with a single `Enter`.
- 🔍 **Category & Quality Badges:** Automatic visual classification (🎬 Películas, 📺 Series, 🎌 Anime, 🎮 Juegos, 🎵 Música, 📚 Libros, 💻 Software, 🔞 Adulto).
- 🏷️ **Smart Metadata & Tech Tags:** Extracts resolution (`4K`, `1080p`, `720p`), source (`Remux`, `BluRay`, `WEB-DL`), codecs (`AV1`, `HEVC/x265`, `x264`), dynamic range (`DV`, `HDR10+`, `HDR`), audio (`Atmos`, `TrueHD`, `DTS-HD`, `FLAC`), and languages (`Dual`, `Castellano`, `Latino`, `VOSE`).
- ⭐ **Freeleech Detection:** Highlights zero-ratio-cost releases (`⭐ Freeleech`).
- 🌱 **Swarm Health Indicator:** Color-coded seeder health warnings with ASCII activity gauge.
- ⏸️ **Paused State Support:** Add torrents directly in paused state (`Ctrl + P` or `--paused`).
- ⬇️ **qBittorrent WebUI Integration:** Injects torrents, categories, and tags automatically with authentication support.
- 📋 **Wayland & X11 Clipboard Support:** Multi-backend fallback (`wl-copy` $\rightarrow$ `xclip` $\rightarrow$ `xsel`).
- 🔔 **Desktop Notifications:** Safe `notify-send` popups with torrent name and size.
- ⚙️ **Config File Support:** JSON config at `~/.config/qjackett/config.json` with env var overrides.
- 🖥️ **Hyprland / Window Manager Ready:** Ideal for a floating terminal window with continuous search loop (`--loop`).

---

## 📦 Requirements

- **Python** $\ge$ 3.8
- **fzf**
- **Jackett** (running locally or remotely)
- **qBittorrent** (with WebUI enabled)
- `wl-clipboard` (for Wayland) or `xclip` / `xsel` (for X11)
- `libnotify` (`notify-send`)

On Arch Linux / CachyOS:
```bash
sudo pacman -S fzf wl-clipboard libnotify python
```

---

## 🚀 Installation

### Option 1: Quick Install
```bash
git clone https://github.com/LaNataliaaa/qjackett.git
cd qjackett
./install.sh
```

Make sure `~/.local/bin` is in your `$PATH`.

### Option 2: Arch Linux (PKGBUILD)
```bash
git clone https://github.com/LaNataliaaa/qjackett.git
cd qjackett
makepkg -si
```

---

## 🎮 Usage

### Interactive Search
Simply run `qjackett` without arguments to enter interactive search mode:
```bash
qjackett
```

### Direct Search Query
```bash
qjackett "Oppenheimer 1080p"
qjackett "Cyberpunk 2077"
qjackett "FLAC 2026"
```

### Advanced Filtering & Options
```bash
# Filter by category
qjackett -c movies "The Matrix"
qjackett -c anime "Chainsaw Man"
qjackett -c games "Resident Evil"
qjackett -c tv "Severance"

# Filter by minimum seeders
qjackett -s 20 "Ubuntu"

# Filter by file size (supports K, M, G, T)
qjackett --min-size 1G --max-size 15GB "Dune"

# Filter specific Jackett indexers
qjackett -i therarbg,yts "Gladiator"

# Sort results by seeds, peers, size, or date
qjackett --sort size "Interstellar"
qjackett --sort date -r "Blade Runner"

# Exclude unwanted keywords
qjackett -x "cam,ts,telesync" "Deadpool"

# Add torrents directly in paused state
qjackett --paused "Top Gun"

# Continuous search loop (great for floating windows)
qjackett --loop
```

---

## ⌨️ Interactive Keybindings (Inside TUI)

| Key | Action |
|---|---|
| **`Enter`** | Send selected torrent(s) to qBittorrent + copy magnet + notify |
| **`Tab`** | Toggle selection of multiple torrents |
| **`Ctrl + P`** | Send selected torrent(s) to qBittorrent in **PAUSED** state |
| **`Ctrl + Y`** | Copy magnet link to clipboard (stays inside TUI) |
| **`Ctrl + T`** | Copy release title to clipboard (stays inside TUI) |
| **`Ctrl + O`** | Open tracker details/comments webpage in default browser |
| **`Ctrl + C`** / **`Esc`** | Exit / cancel |
| **Type text** | Live fuzzy filter |
| **`!word`** | Invert filter (exclude releases containing `word`, e.g. `!cam`) |

---

## ⚙️ Configuration (`config.json`)

Generate a default configuration file with:
```bash
qjackett --init-config
```
This creates `~/.config/qjackett/config.json`:

```json
{
    "jackett_url": "http://127.0.0.1:9117",
    "jackett_api_key": "",
    "qbittorrent_url": "http://127.0.0.1:8080",
    "qbittorrent_username": "",
    "qbittorrent_password": "",
    "auto_category": true,
    "auto_tags": true,
    "default_min_seeds": 0,
    "default_exclude": [
        "cam",
        "ts",
        "telesync"
    ],
    "default_sort": "seeds",
    "max_workers": 16,
    "request_timeout": 5.0,
    "enable_notifications": true,
    "auto_copy_magnet": true,
    "save_paused": false,
    "open_browser_cmd": "xdg-open"
}
```

*Note:* If `jackett_api_key` is empty, `qjackett` automatically extracts it from `~/.config/Jackett/ServerConfig.json`.

### Environment Variables
You can override configuration using environment variables:
- `JACKETT_URL`
- `JACKETT_API_KEY`
- `QBITTORRENT_URL`
- `QBITTORRENT_USER`
- `QBITTORRENT_PASS`
- `QJACKETT_CONFIG` (custom path to `config.json`)

---

## 🪟 Hyprland Integration (Floating Window Shortcut)

Add this keybinding to your `~/.config/hypr/hyprland.conf`:

```ini
# Open floating qjackett TUI with Super + Shift + T
bind = SUPER SHIFT, T, exec, kitty --class qjackett -e qjackett --loop
```

And add the window rule to keep it centered and floating:
```ini
windowrulev2 = float, class:^(qjackett)$
windowrulev2 = center, class:^(qjackett)$
windowrulev2 = size 1280 800, class:^(qjackett)$
```

---

## 🧪 Testing

Run the automated test suite with:
```bash
python3 tests/test_qjackett.py
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE) © 2026 [LaNataliaaa](https://github.com/LaNataliaaa).
