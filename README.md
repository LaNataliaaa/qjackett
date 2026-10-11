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
- 🔍 **Category & Quality Badges:** Automatic visual classification (🎬 Movies, 📺 TV Shows, 🎮 Games, 🎵 Music, 📚 Books, 🔞 Adult).
- 🌱 **Swarm Health Indicator:** Color-coded seeder health warnings (Excellent, Good, Low, Dead).
- ⬇️ **Direct qBittorrent Injection:** Sends torrents via qBittorrent's WebUI API seamlessly in the background.
- 📋 **Wayland Clipboard Integration:** Automatically copies magnet links with `wl-copy`.
- 🔔 **Desktop Notifications:** Native `notify-send` popups with torrent name and size.
- 🖥️ **Hyprland / Window Manager Ready:** Designed to pop up in a sleek floating terminal window (e.g. Kitty, Foot, Alacritty).

---

## 📦 Requirements

- **Python** $\ge$ 3.8
- **fzf**
- **Jackett** (running locally or remotely)
- **qBittorrent** (with WebUI enabled on localhost)
- `wl-clipboard` (for Wayland clipboard support) or `xclip` (for X11)
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
install -Dm755 qjackett ~/.local/bin/qjackett
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

### Advanced Filtering
```bash
# Filter by category
qjackett -c movies "The Matrix"
qjackett -c games "Resident Evil"
qjackett -c tv "Severance"

# Filter by minimum seeders
qjackett -s 20 "Ubuntu"

# Exclude unwanted keywords
qjackett -x "cam,ts,telesync" "Deadpool"
```

---

## ⌨️ Interactive Keybindings (Inside TUI)

| Key | Action |
|---|---|
| **`Enter`** | Send selected torrent directly to qBittorrent + copy magnet + notify |
| **`Ctrl + Y`** | Copy magnet link to clipboard only (without downloading) |
| **`Ctrl + C`** / **`Esc`** | Exit without downloading |
| **Type text** | Live fuzzy filter |
| **`!word`** | Invert filter (exclude releases containing `word`) |

---

## 🪟 Hyprland Integration (Floating Window Shortcut)

Add this keybinding to your `~/.config/hypr/hyprland.conf` or `~/.config/hypr/custom/keybinds.lua`:

```ini
# Open floating qjackett TUI with Super + Shift + T
bind = SUPER SHIFT, T, exec, kitty --class qjackett -e qjackett
```

And add the window rule to keep it centered and floating:
```ini
windowrulev2 = float, class:^(qjackett)$
windowrulev2 = center, class:^(qjackett)$
windowrulev2 = size 1200 750, class:^(qjackett)$
```

---

## ⚙️ Configuration

`qjackett` automatically reads your Jackett API key from:
`~/.config/Jackett/ServerConfig.json`

If your Jackett or qBittorrent runs on different ports or remote hosts, edit the constants at the top of `/usr/bin/qjackett` or `~/.local/bin/qjackett`:
```python
JACKETT_URL = "http://127.0.0.1:9117"
QBITTORRENT_URL = "http://127.0.0.1:8080"
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE) © 2026 [LaNataliaaa](https://github.com/LaNataliaaa).
