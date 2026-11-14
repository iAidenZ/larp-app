import base64
import http.server
import json
import math
import os
import random
import shutil
import subprocess
import sys
import threading
import webbrowser
import time
import tkinter as tk
from tkinter import messagebox

import requests
try:
    import customtkinter as ctk
except ImportError:
    ctk = None
import winsound

try:
    from pypresence import Presence
except ImportError:
    Presence = None

try:
    import pystray
    from PIL import Image as PILImage
except ImportError:
    pystray = None
    PILImage = None

try:
    from pynput import keyboard as pynput_keyboard
except ImportError:
    pynput_keyboard = None

BASE = r"C:\fake"
POWERSHELL = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
API = "https://discord.com/api/v9/applications/detectable"
NO_WINDOW = subprocess.CREATE_NO_WINDOW

SAVE_FILE = os.path.join(BASE, "saved_games.json")
RECENT_FILE = os.path.join(BASE, "recent_games.json")
SETTINGS_FILE = os.path.join(BASE, "settings.json")

PS_SCRIPT = r"""
Add-Type -ReferencedAssemblies System.Windows.Forms, System.Drawing -TypeDefinition @'
using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Text;
using System.Windows.Forms;

public class PresenceWindow : Form
{
    private System.Windows.Forms.Timer timer;
    private float t = 0f;
    private string gameName;
    private DateTime started = DateTime.Now;

    public static void Start(string name)
    {
        Application.EnableVisualStyles();
        Application.Run(new PresenceWindow(name));
    }

    public PresenceWindow(string name)
    {
        gameName = name;
        Text = name;
        ClientSize = new Size(460, 300);
        StartPosition = FormStartPosition.CenterScreen;
        FormBorderStyle = FormBorderStyle.FixedSingle;
        MaximizeBox = false;
        BackColor = Color.FromArgb(20, 22, 34);
        Icon = MakeIcon();
        SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.UserPaint | ControlStyles.OptimizedDoubleBuffer, true);

        timer = new System.Windows.Forms.Timer();
        timer.Interval = 33;
        timer.Tick += delegate { t += 0.033f; Invalidate(); };
        timer.Start();
        FormClosed += delegate { timer.Stop(); };
    }

    private static GraphicsPath RoundedRect(RectangleF r, float rad)
    {
        float d = rad * 2;
        GraphicsPath p = new GraphicsPath();
        p.AddArc(r.X, r.Y, d, d, 180, 90);
        p.AddArc(r.Right - d, r.Y, d, d, 270, 90);
        p.AddArc(r.Right - d, r.Bottom - d, d, d, 0, 90);
        p.AddArc(r.X, r.Bottom - d, d, d, 90, 90);
        p.CloseFigure();
        return p;
    }

    private static System.Drawing.Icon MakeIcon()
    {
        int S = 64;
        Color blurple = Color.FromArgb(88, 101, 242);
        using (Bitmap bmp = new Bitmap(S, S))
        using (Graphics g = Graphics.FromImage(bmp))
        {
            g.SmoothingMode = SmoothingMode.AntiAlias;
            g.Clear(Color.Transparent);

            using (GraphicsPath bgPath = RoundedRect(new RectangleF(0, 0, 63, 63), 14f))
            using (SolidBrush bgBrush = new SolidBrush(blurple))
            {
                g.FillPath(bgBrush, bgPath);
            }

            using (SolidBrush white = new SolidBrush(Color.White))
            using (SolidBrush dark = new SolidBrush(blurple))
            {
                using (GraphicsPath body = RoundedRect(new RectangleF(11.25f, 23.75f, 41.5f, 17.5f), 8.75f))
                {
                    g.FillPath(white, body);
                }
                g.FillEllipse(white, 10f, 28.75f, 16.25f, 21.25f);
                g.FillEllipse(white, 37.75f, 28.75f, 16.25f, 21.25f);
                g.FillRectangle(dark, 16.9f, 31.25f, 8.75f, 3.25f);
                g.FillRectangle(dark, 19.75f, 28.4f, 3f, 9f);
                g.FillEllipse(dark, 39.75f, 29.5f, 4.25f, 4.25f);
                g.FillEllipse(dark, 44.5f, 33.5f, 4.25f, 4.25f);
            }

            using (SolidBrush green = new SolidBrush(Color.FromArgb(59, 165, 92)))
            using (Pen ring = new Pen(blurple, 1.75f))
            {
                g.FillEllipse(green, 43.1f, 5f, 16.25f, 16.25f);
                g.DrawEllipse(ring, 43.1f, 5f, 16.25f, 16.25f);
            }

            return System.Drawing.Icon.FromHandle(bmp.GetHicon());
        }
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        Graphics g = e.Graphics;
        g.SmoothingMode = SmoothingMode.AntiAlias;
        g.TextRenderingHint = TextRenderingHint.AntiAliasGridFit;
        int w = ClientSize.Width;
        int h = ClientSize.Height;
        Rectangle r = new Rectangle(0, 0, w, h);

        int shift = (int)(14 * Math.Sin(t * 0.8));
        using (LinearGradientBrush bg = new LinearGradientBrush(r, Color.FromArgb(20, 22, 34), Color.FromArgb(48 + shift, 36, 96 + shift), 55f))
        {
            g.FillRectangle(bg, r);
        }

        for (int i = 0; i < 14; i++)
        {
            float speed = 12f + (i % 4) * 7f;
            float x = (i * 83) % w;
            float y = h - ((t * speed + i * 41f) % h);
            float s = 2f + (i % 3);
            using (SolidBrush pb = new SolidBrush(Color.FromArgb(40 + (i % 3) * 20, 255, 255, 255)))
            {
                g.FillEllipse(pb, x, y, s, s);
            }
        }

        float cx = w / 2f;
        float cy = 100f;
        for (int i = 0; i < 3; i++)
        {
            float p = (t * 0.5f + i / 3f) % 1f;
            float rad = 28f + p * 62f;
            int a = (int)(150 * (1f - p));
            using (Pen rp = new Pen(Color.FromArgb(a, 59, 165, 92), 2f))
            {
                g.DrawEllipse(rp, cx - rad, cy - rad, rad * 2, rad * 2);
            }
        }

        float pulse = 28f + 2.5f * (float)Math.Sin(t * 3f);
        using (SolidBrush glow = new SolidBrush(Color.FromArgb(40, 59, 165, 92)))
        {
            g.FillEllipse(glow, cx - pulse - 10, cy - pulse - 10, (pulse + 10) * 2, (pulse + 10) * 2);
        }
        using (SolidBrush core = new SolidBrush(Color.FromArgb(59, 165, 92)))
        {
            g.FillEllipse(core, cx - pulse, cy - pulse, pulse * 2, pulse * 2);
        }
        using (Pen tick = new Pen(Color.White, 5f))
        {
            tick.StartCap = LineCap.Round;
            tick.EndCap = LineCap.Round;
            tick.LineJoin = LineJoin.Round;
            g.DrawLines(tick, new PointF[] {
                new PointF(cx - 13, cy + 1),
                new PointF(cx - 4, cy + 10),
                new PointF(cx + 13, cy - 9) });
        }

        using (StringFormat center = new StringFormat())
        {
            center.Alignment = StringAlignment.Center;
            center.LineAlignment = StringAlignment.Center;
            center.FormatFlags = StringFormatFlags.NoWrap;
            center.Trimming = StringTrimming.EllipsisCharacter;

            int ta = 225 + (int)(30 * Math.Sin(t * 2f));
            using (Font f1 = new Font("Segoe UI Semibold", 26f))
            using (SolidBrush tb = new SolidBrush(Color.FromArgb(ta, 255, 255, 255)))
            {
                g.DrawString("Connected", f1, tb, new RectangleF(0, 165, w, 50), center);
            }
            using (Font f2 = new Font("Segoe UI", 11f))
            using (SolidBrush sb = new SolidBrush(Color.FromArgb(170, 176, 205)))
            {
                g.DrawString("Playing " + gameName, f2, sb, new RectangleF(20, 212, w - 40, 30), center);
            }

            TimeSpan ts = DateTime.Now - started;
            string clock = ts.TotalHours >= 1
                ? string.Format("{0}:{1:00}:{2:00}", (int)ts.TotalHours, ts.Minutes, ts.Seconds)
                : string.Format("{0:00}:{1:00}", ts.Minutes, ts.Seconds);
            using (Font f4 = new Font("Segoe UI Semibold", 13f))
            using (SolidBrush mb = new SolidBrush(Color.FromArgb(120, 200, 150)))
            {
                g.DrawString(clock, f4, mb, new RectangleF(20, 240, w - 40, 30), center);
            }
        }

        using (StringFormat far = new StringFormat())
        {
            far.Alignment = StringAlignment.Far;
            far.LineAlignment = StringAlignment.Far;
            using (Font f3 = new Font("Segoe UI", 9f, FontStyle.Italic))
            using (SolidBrush cb = new SolidBrush(Color.FromArgb(140, 146, 175)))
            {
                g.DrawString("By Aiden", f3, cb, new RectangleF(0, 0, w - 14, h - 10), far);
            }
        }
    }
}
'@
[PresenceWindow]::Start('__NAME__')
"""

# ---------------------------------------------------------------- colors
BG = "#0b0b10"
INPUT = "#14141c"
EDGE = "#2a2a38"
FG = "#f2f3f5"
MUTED = "#9da1b3"
CARD = "#1b1b26"
GREEN = "#3ba55d"
RED = "#da373c"
GOLD = "#f5c542"
TOAST_BG = "#171722"

ACCENTS = {
    "Blue": "#5865F2",
    "Green": "#2fb872",
    "Purple": "#9b6bff",
    "Pink": "#ff5fa2",
    "Orange": "#ff8a3d",
    "Custom": "#36c5f0",
}
ACCENT = ACCENTS["Blue"]

# ---------------------------------------------------------------- state
apps = []        # Discord's game list, filled at startup
matches = []     # games shown by the current search
running = {}     # game name -> {"exe": exe name, "start": time}
saved = {}       # game name -> exe path
recent = []      # newest first, each item is [name, exe path]
settings = {"accent": "Blue", "favorites": [], "icons": {}, "ids": {},
            "hotkey": "<ctrl>+<alt>+g", "sound": True, "client_id": "",
            "user_id": "", "seen_welcome": False, "watch_id": "",
            "streamer_mode": False, "accounts": [], "custom_color": ""}

icon_cache = {}
icon_waiters = {}
BUTTONS = []
rpc = {}         # game name -> Presence connection

PRESETS = [
    ("In lobby", "In lobby", "Waiting for players", None),
    ("In game", "In a match", "Playing now", None),
    ("With a friend", "Playing with a friend", "In a party", (2, 2)),
    ("Need 2 more", "Looking for 2 people", "Open party", (1, 3)),
]


# ---------------------------------------------------------------- files
def load_saved():
    try:
        with open(SAVE_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            saved.update({k: v for k, v in data.items()
                          if isinstance(k, str) and isinstance(v, str)})
    except (FileNotFoundError, ValueError, OSError):
        pass


def write_saved():
    os.makedirs(BASE, exist_ok=True)
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(saved, f, indent=2)


def load_recent():
    try:
        with open(RECENT_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            for item in data:
                if (isinstance(item, list) and len(item) == 2
                        and all(isinstance(x, str) for x in item)):
                    recent.append(item)
    except (FileNotFoundError, ValueError, OSError):
        pass


def write_recent():
    os.makedirs(BASE, exist_ok=True)
    with open(RECENT_FILE, "w", encoding="utf-8") as f:
        json.dump(recent, f, indent=2)


def load_settings():
    try:
        with open(SETTINGS_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, ValueError, OSError):
        return
    if not isinstance(data, dict):
        return
    cc = data.get("custom_color")
    if isinstance(cc, str) and len(cc) == 7 and cc.startswith("#"):
        try:
            int(cc[1:], 16)
            settings["custom_color"] = cc
            ACCENTS["Custom"] = cc
        except ValueError:
            pass
    if data.get("accent") in ACCENTS:
        settings["accent"] = data["accent"]
    if isinstance(data.get("client_id"), str):
        settings["client_id"] = data["client_id"].strip()
    if isinstance(data.get("user_id"), str):
        settings["user_id"] = data["user_id"].strip()
    if isinstance(data.get("seen_welcome"), bool):
        settings["seen_welcome"] = data["seen_welcome"]
    if isinstance(data.get("watch_id"), str):
        settings["watch_id"] = data["watch_id"].strip()
    if isinstance(data.get("streamer_mode"), bool):
        settings["streamer_mode"] = data["streamer_mode"]
    accs = data.get("accounts")
    if isinstance(accs, list):
        keys = ("client_id", "user_id")
        settings["accounts"] = [
            {"name": a["name"], **{k: a.get(k, "") for k in keys}}
            for a in accs
            if isinstance(a, dict) and isinstance(a.get("name"), str)
            and all(isinstance(a.get(k, ""), str) for k in keys)]    
    favs = data.get("favorites")
    if isinstance(favs, list):
        settings["favorites"] = [x for x in favs if isinstance(x, str)]
    icons = data.get("icons")
    if isinstance(icons, dict):
        settings["icons"] = {k: v for k, v in icons.items()
                             if isinstance(k, str) and isinstance(v, str)}
    ids = data.get("ids")
    if isinstance(ids, dict):
        settings["ids"] = {k: v for k, v in ids.items()
                           if isinstance(k, str) and isinstance(v, str)}
    if isinstance(data.get("hotkey"), str):
        settings["hotkey"] = data["hotkey"]
    if isinstance(data.get("sound"), bool):
        settings["sound"] = data["sound"]
    presets = data.get("presets")
    if isinstance(presets, list):
        loaded = []
        for p in presets:
            if isinstance(p, list) and len(p) == 4 and all(isinstance(x, str) for x in p[:3]):
                party = p[3]
                if isinstance(party, list) and len(party) == 2 and all(isinstance(n, int) for n in party):
                    loaded.append((p[0], p[1], p[2], tuple(party)))
                else:
                    loaded.append((p[0], p[1], p[2], None))
        if loaded:
            PRESETS[:] = loaded[:4]
            settings["presets"] = presets


def write_settings():
    os.makedirs(BASE, exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)


# ---------------------------------------------------------------- helpers
def pick_exe(app):
    entries = [e for e in app.get("executables", []) if e["os"] == "win32"]
    if not entries:
        return None
    skip = ("trial", "demo", "showcase", "beta", "test")
    entries.sort(key=lambda e: (e["name"].startswith(">"),
                                bool(e.get("is_launcher")),
                                any(w in e["name"].lower() for w in skip),
                                e["name"].count("/")))
    return entries[0]["name"].lstrip(">").replace("/", "\\")


def exe_running(exe_name):
    out = subprocess.run(
        ["tasklist", "/FI", f"IMAGENAME eq {exe_name}"],
        capture_output=True, text=True, creationflags=NO_WINDOW,
    ).stdout
    return exe_name.lower() in out.lower()


def kill(exe_name):
    if not exe_name:
        return
    subprocess.run(["taskkill", "/IM", exe_name, "/F"], creationflags=NO_WINDOW)


def resource(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def mix(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(int(x + (y - x) * t) for x, y in zip(a, b))


def fmt_time(seconds):
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def icon_url(app):
    if app.get("id") and app.get("icon"):
        return f"https://cdn.discordapp.com/app-icons/{app['id']}/{app['icon']}.png?size=64"
    return None

def big_icon(name):
    url = settings["icons"].get(name)
    if url:
        return url.split("?")[0]
    game_id = app_id_for(name)
    if game_id:
        try:
            info = requests.get(
                f"https://discord.com/api/v9/applications/{game_id}/rpc",
                timeout=8).json()
            if info.get("icon"):
                return f"https://cdn.discordapp.com/app-icons/{game_id}/{info['icon']}.png"
        except Exception:
            pass
    return None

def remember_icon(app):
    changed = False
    url = icon_url(app)
    if url and settings["icons"].get(app["name"]) != url:
        settings["icons"][app["name"]] = url
        changed = True
    if app.get("id") and settings["ids"].get(app["name"]) != app["id"]:
        settings["ids"][app["name"]] = app["id"]
        changed = True
    if changed:
        write_settings()


def fetch_icon(url, apply):
    if not url:
        return
    if url in icon_cache:
        apply(icon_cache[url])
        return
    if url in icon_waiters:
        icon_waiters[url].append(apply)
        return
    icon_waiters[url] = [apply]

    def work():
        try:
            data = requests.get(url, timeout=10).content
        except Exception:
            data = None
        root.after(0, finish_icon, url, data)

    threading.Thread(target=work, daemon=True).start()


def finish_icon(url, data):
    waiters = icon_waiters.pop(url, [])
    if not data:
        return
    try:
        img = tk.PhotoImage(data=base64.b64encode(data)).subsample(2)
    except tk.TclError:
        return
    icon_cache[url] = img
    for apply in waiters:
        apply(img)


def round_rect(c, x1, y1, x2, y2, r, **kw):
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
           x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return c.create_polygon(pts, smooth=True, **kw)


def draw_logo(c, ox, oy, k, tag="logo"):
    def box(x1, y1, x2, y2):
        return ox + x1 * k, oy + y1 * k, ox + x2 * k, oy + y2 * k

    round_rect(c, *box(0, 0, 512, 512), 110 * k, fill=ACCENT, outline="", tags=tag)
    round_rect(c, *box(90, 190, 422, 330), 70 * k, fill="white", outline="", tags=tag)
    c.create_oval(*box(80, 230, 210, 400), fill="white", outline="", tags=tag)
    c.create_oval(*box(302, 230, 432, 400), fill="white", outline="", tags=tag)
    c.create_rectangle(*box(135, 250, 205, 276), fill=ACCENT, outline="", tags=tag)
    c.create_rectangle(*box(158, 227, 182, 299), fill=ACCENT, outline="", tags=tag)
    c.create_oval(*box(318, 236, 352, 270), fill=ACCENT, outline="", tags=tag)
    c.create_oval(*box(356, 268, 390, 302), fill=ACCENT, outline="", tags=tag)
    c.create_oval(*box(345, 40, 475, 170), fill=GREEN, outline=ACCENT, width=2, tags=tag)


# ---------------------------------------------------------------- widgets
class HoverButton(tk.Label):
    def __init__(self, parent, text, command, color=None):
        super().__init__(parent, text=text, fg="white", font=("Segoe UI", 10, "bold"),
                         padx=14, pady=6, cursor="hand2")
        self.fixed = color
        self.command = command
        self.job = None
        self.start = self.target = self.base()
        self.config(bg=self.base())
        self.bind("<Enter>", lambda e: self.fade(self.top()))
        self.bind("<Leave>", lambda e: self.fade(self.base()))
        self.bind("<ButtonPress-1>", self.on_press)
        self.bind("<ButtonRelease-1>", self.on_release)
        BUTTONS.append(self)
        self.bind("<Destroy>", self.on_destroy)

    def on_destroy(self, event):
        if self.job:
            self.after_cancel(self.job)
        if self in BUTTONS:
            BUTTONS.remove(self)

    def base(self):
        return self.fixed or ACCENT

    def top(self):
        return mix(self.base(), "#ffffff", 0.18)

    def on_press(self, event):
        if self.job:
            self.after_cancel(self.job)
            self.job = None
        self.config(bg=mix(self.base(), "#000000", 0.3))

    def on_release(self, event):
        inside = 0 <= event.x < self.winfo_width() and 0 <= event.y < self.winfo_height()
        self.fade(self.top() if inside else self.base())
        if inside:
            self.command()

    def fade(self, target):
        if self.job:
            self.after_cancel(self.job)
        self.start = self.cget("bg")
        self.target = target
        self.step(0)

    def step(self, n):
        n += 1
        self.config(bg=mix(self.start, self.target, n / 6))
        self.job = self.after(16, self.step, n) if n < 6 else None


class Tabs(tk.Frame):
    def __init__(self, parent, names):
        super().__init__(parent, bg=BG)
        self.names = names
        self.index = 0
        self.x = 0.0
        self.job = None
        self.snap = True
        self.bar = tk.Canvas(self, height=40, bg=BG, highlightthickness=0)
        self.bar.pack(fill="x")
        self.body = tk.Frame(self, bg=BG, highlightthickness=1, highlightbackground=EDGE)
        self.body.pack(fill="both", expand=True)
        self.pages = {n: tk.Frame(self.body, bg=BG) for n in names}
        self.bar.bind("<Configure>", lambda e: self.layout())
        self.bar.bind("<Button-1>", self.click)
        self.show(0)

    def page(self, name):
        return self.pages[name]

    def layout(self):
        w = self.bar.winfo_width()
        if w < 20:
            return
        seg = w / len(self.names)
        if self.snap:
            self.x = self.index * seg
            self.snap = False
        self.bar.delete("all")
        round_rect(self.bar, self.x + 3, 4, self.x + seg - 3, 36, 10, fill=ACCENT, outline="")
        for i, name in enumerate(self.names):
            self.bar.create_text(seg * i + seg / 2, 20, text=name,
                                 fill="white" if i == self.index else MUTED,
                                 font=("Segoe UI", 10, "bold"))

    def click(self, event):
        seg = self.bar.winfo_width() / len(self.names)
        self.show(min(int(event.x // seg), len(self.names) - 1))

    def show(self, i):
        for p in self.pages.values():
            p.pack_forget()
        self.pages[self.names[i]].pack(fill="both", expand=True)
        self.index = i
        if self.job:
            self.after_cancel(self.job)
        self.slide()

    def slide(self):
        w = self.bar.winfo_width()
        if w < 20:
            self.layout()
            return
        target = self.index * (w / len(self.names))
        self.x += (target - self.x) * 0.3
        if abs(target - self.x) < 0.6:
            self.x = target
            self.job = None
        else:
            self.job = self.after(16, self.slide)
        self.layout()


class CardList(tk.Frame):
    def __init__(self, parent, empty_text, on_open=None, on_star=None, auto=False,
                 height=120, on_menu=None):
        super().__init__(parent, bg=INPUT, highlightthickness=1, highlightbackground=EDGE)
        self.on_open = on_open
        self.on_star = on_star
        self.on_menu = on_menu
        self.auto = auto
        self.rows = {}
        self.order = []
        self.selected = None
        self.canvas = tk.Canvas(self, bg=INPUT, highlightthickness=0,
                                height=height, yscrollincrement=24)
        self.canvas.pack(fill="both", expand=True)
        self.inner = tk.Frame(self.canvas, bg=INPUT)
        self.win = self.canvas.create_window(0, 0, window=self.inner, anchor="nw")
        self.canvas.bind("<Configure>",
                         lambda e: self.canvas.itemconfig(self.win, width=e.width))
        self.inner.bind("<Configure>",
                        lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.empty = tk.Label(self.canvas, text=empty_text, bg=INPUT, fg=MUTED,
                              font=("Segoe UI", 10), justify="center")

    def scroll(self, delta):
        if self.inner.winfo_height() > self.canvas.winfo_height():
            self.canvas.yview_scroll(int(-delta / 120), "units")

    def set_items(self, items):
        for r in self.rows.values():
            r["frame"].destroy()
        self.rows = {}
        self.order = [it["key"] for it in items]
        if self.selected not in self.order:
            self.selected = self.order[0] if (self.order and self.auto) else None
        for it in items:
            self.add_row(it)
        if self.order:
            self.empty.place_forget()
        else:
            self.empty.place(relx=0.5, rely=0.5, anchor="center")
        self.paint()

    def add_row(self, it):
        key = it["key"]
        row = tk.Frame(self.inner, bg=INPUT, padx=8, pady=6)
        row.pack(fill="x")
        holder = tk.Frame(row, width=36, height=36)
        holder.pack(side="left")
        holder.pack_propagate(False)
        holder.keep_bg = True
        icon = tk.Label(holder, text=it["title"][:1].upper(), fg="white",
                        font=("Segoe UI", 12, "bold"))
        icon.place(relx=0.5, rely=0.5, anchor="center")
        parts = {"frame": row, "holder": holder, "icon": icon, "dot": None}

        if it.get("live"):
            dot = tk.Label(row, text="●", fg=GREEN, font=("Segoe UI", 11))
            dot.pack(side="right")
            parts["dot"] = dot
        star = None
        if "star" in it:
            star = tk.Label(row, text="★" if it["star"] else "☆",
                            fg=GOLD if it["star"] else "#5a5a70",
                            font=("Segoe UI", 14), cursor="hand2")
            star.pack(side="right")

        text = tk.Frame(row)
        text.pack(side="left", fill="x", expand=True, padx=(10, 6))
        tk.Label(text, text=it["title"], fg=FG, anchor="w",
                 font=("Segoe UI", 10, "bold")).pack(fill="x")
        parts["sub"] = tk.Label(text, text=it.get("sub", ""), fg=MUTED, anchor="w",
                                font=("Segoe UI", 9))
        parts["sub"].pack(fill="x")

        self.rows[key] = parts
        self.bind_row(row, key)
        if star is not None:
            handler = lambda e, k=key: self.on_star(k)
            star.bind("<Button-1>", handler)
            star.bind("<Double-Button-1>", handler)

        def apply(img):
            try:
                icon.config(image=img, text="")
                icon.image = img
                holder.keep_bg = False
                self.paint()
            except tk.TclError:
                pass

        fetch_icon(it.get("icon"), apply)

    def bind_row(self, widget, key):
        widget.bind("<Button-1>", lambda e, k=key: self.select(k))
        widget.bind("<Double-Button-1>", lambda e, k=key: self.open(k))
        widget.bind("<Button-3>", lambda e, k=key: self.menu(k, e))
        for child in widget.winfo_children():
            self.bind_row(child, key)

    def menu(self, key, event):
        self.select(key)
        if self.on_menu:
            self.on_menu(key, event)

    def select(self, key):
        self.selected = key
        self.paint()

    def open(self, key):
        if self.on_open:
            self.on_open(key)

    def paint(self):
        placeholder = mix(ACCENT, BG, 0.45)
        for key, r in self.rows.items():
            color = mix(INPUT, ACCENT, 0.28) if key == self.selected else INPUT
            self.tint(r["frame"], color)
            if r["holder"].keep_bg:
                r["holder"].config(bg=placeholder)
                r["icon"].config(bg=placeholder)

    def tint(self, widget, color):
        if getattr(widget, "keep_bg", False):
            return
        widget.config(bg=color)
        for child in widget.winfo_children():
            self.tint(child, color)

    def update_sub(self, key, text):
        r = self.rows.get(key)
        if r:
            r["sub"].config(text=text)

    def pulse(self, color):
        for r in self.rows.values():
            if r["dot"] is not None:
                r["dot"].config(fg=color)


# ---------------------------------------------------------------- toasts
toast_state = {"y": -70.0, "target": -70.0, "job": None, "hide": None}


def toast(text, good=True, ms=2800):
    toast_label.config(text=text)
    toast_dot.config(fg=GREEN if good else "#ff6b6b")
    toast_box.config(highlightbackground=ACCENT)
    toast_box.lift()
    toast_state["target"] = 12.0
    if toast_state["hide"]:
        root.after_cancel(toast_state["hide"])
    toast_state["hide"] = root.after(ms, hide_toast)
    toast_step()


def hide_toast():
    toast_state["target"] = -70.0
    toast_step()


def toast_step():
    s = toast_state
    if s["job"]:
        root.after_cancel(s["job"])
    s["y"] += (s["target"] - s["y"]) * 0.25
    if abs(s["target"] - s["y"]) < 0.8:
        s["y"] = s["target"]
        s["job"] = None
    else:
        s["job"] = root.after(16, toast_step)
    toast_box.place(relx=0.5, y=int(s["y"]), anchor="n", width=360)


def set_status(text):
    status.config(text=text)


# ---------------------------------------------------------------- actions
def load_apps():
    try:
        apps.extend(requests.get(API, timeout=20).json())
        root.after(0, set_status, f"Ready. {len(apps)} games loaded.")
    except Exception:
        root.after(0, set_status, "Could not load the game list. Check your internet.")


search_job = {"id": None}


def on_key(event=None):
    if search_job["id"]:
        root.after_cancel(search_job["id"])
    search_job["id"] = root.after(250, search)


def norm(text):
    return "".join(c for c in text.lower() if c.isalnum() or c == " ")


def may_hide(app):
    themes = [str(t).lower() for t in (app.get("themes") or [])]
    return "erotic" in themes


def search(event=None):
    word = entry.get().strip().lower()
    matches.clear()
    if len(word) < 2:
        results_list.set_items([])
        return
    if not apps:
        set_status("The game list isn't loaded yet, try again in a moment.")
        return
    words = norm(word).split()
    if not words:
        results_list.set_items([])
        return
    found = [a for a in apps
             if all(w in norm(a["name"]) for w in words) and (pick_exe(a) or a.get("id"))]
    matches.extend(found[:30])
    results_list.set_items([
        {"key": i, "title": a["name"],
         "sub": (os.path.basename(pick_exe(a) or "") or "Status only (no file to detect)")
                + ("  ·  may be hidden from others" if may_hide(a) else ""),
         "icon": icon_url(a)}
        for i, a in enumerate(matches)
    ])
    if not found:
        set_status("No game found with that name.")
    elif len(found) > 30:
        set_status(f"Showing 30 of {len(found)}. Keep typing to narrow it down.")
    else:
        set_status(f"Found {len(found)} game(s)! Pick one and press Run it.")


def refresh_running():
    now = time.time()
    running_cards.set_items([
        {"key": n, "title": n, "sub": f"Live for {fmt_time(now - r['start'])}",
         "icon": settings["icons"].get(n), "live": True}
        for n, r in running.items()
    ])


def start_game(name, exe_rel, mode="exe"):
    original = exe_rel
    if mode in ("status", "rpc"):
        exe_rel = ""
    if not exe_rel:
        if name in running:
            toast(f"{name} is already running.", False)
            return
        if mode == "rpc" and not settings["client_id"]:
            toast("Add your App ID in the Settings tab first.", False)
            return
        running[name] = {"exe": "", "mode": "rpc" if mode == "rpc" else "status",
                         "start": time.time()}
        refresh_running()
        add_recent(name, original)
        if mode == "rpc":
            set_status("Rich Presence: shown with your own App ID. Use the Status tab for lines.")
        else:
            set_status("Status-only mode: shown through Rich Presence. Use the Status tab for lines.")
        rpc_apply(name, "", "", None)
        play_sound("connect")
        burst_confetti()
        return
    folder = "".join(c for c in name if c.isalnum() or c in " -_").strip()
    path = os.path.join(BASE, folder, exe_rel)
    exe_name = os.path.basename(path)
    if exe_running(exe_name):
        toast(f"{name} is already running.", False)
        return
    try:
        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            shutil.copy(POWERSHELL, path)
        script = os.path.join(os.path.dirname(path), "window.ps1")
        with open(script, "w", encoding="utf-8-sig") as f:
            f.write(PS_SCRIPT.replace("__NAME__", name.replace("'", "''")))
        subprocess.Popen(
            [path, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script],
            creationflags=NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP,
        )
    except OSError as err:
        toast(f"Could not start {name}: {err}", False)
        return
    running[name] = {"exe": exe_name, "start": time.time()}
    refresh_running()
    add_recent(name, exe_rel)
    toast(f"{name} is live. Don't close the new window, just minimize it.", ms=5000)
    set_status("Discord can take 10-20 seconds to show it.")
    play_sound("connect")
    burst_confetti()


def ask_mode(name, callback, has_exe=True):
    dlg = tk.Toplevel(root)
    dlg.title("Run game")
    dlg.configure(bg=BG)
    dlg.resizable(False, False)
    dlg.transient(root)

    def pick(mode):
        dlg.destroy()
        callback(mode)

    tk.Label(dlg, text=name, bg=BG, fg="white", font=("Segoe UI", 12, "bold"),
             wraplength=300).pack(padx=24, pady=(18, 2))
    tk.Label(dlg, text="How do you want to run it?", bg=BG, fg=MUTED,
             font=("Segoe UI", 10)).pack(padx=24)
    if has_exe:
        HoverButton(dlg, text="Run the .exe  (with window)",
                    command=lambda: pick("exe")).pack(fill="x", padx=24, pady=(14, 4))
    HoverButton(dlg, text="Status only  (game's own ID)", color="#2a2a3a",
                command=lambda: pick("status")).pack(fill="x", padx=24, pady=4)
    HoverButton(dlg, text="Rich Presence  (your App ID)", color="#2a2a3a",
                command=lambda: pick("rpc")).pack(fill="x", padx=24, pady=4)
    tk.Label(dlg, text="Status only and Rich Presence need this app to stay open.",
             bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(padx=24, pady=(6, 0))
    HoverButton(dlg, text="Cancel", color=RED, command=dlg.destroy).pack(pady=(10, 16))
    dlg.bind("<Escape>", lambda e: dlg.destroy())

    dlg.update_idletasks()
    w, h = max(dlg.winfo_reqwidth(), 340), dlg.winfo_reqheight()
    x = root.winfo_rootx() + (root.winfo_width() - w) // 2
    y = root.winfo_rooty() + (root.winfo_height() - h) // 2
    dlg.geometry(f"{w}x{h}+{x}+{y}")
    dlg.wait_visibility()
    dlg.grab_set()


def launch(name, exe_rel):
    if name in running:
        toast(f"{name} is already running.", False)
        return
    ask_mode(name, lambda mode: start_game(name, exe_rel, mode), bool(exe_rel))


def run_selected(key=None):
    key = results_list.selected if key is None else key
    if key is None or key >= len(matches):
        toast("Pick a game from the results first.", False)
        return
    app = matches[key]
    remember_icon(app)
    launch(app["name"], pick_exe(app) or "")


def save_selected():
    key = results_list.selected
    if key is None or key >= len(matches):
        toast("Pick a game from the results first.", False)
        return
    app = matches[key]
    exe_rel = pick_exe(app) or ""
    saved[app["name"]] = exe_rel
    write_saved()
    remember_icon(app)
    refresh_saved()
    toast(f"Saved {app['name']}.")


def stop_selected():
    name = running_cards.selected
    if name not in running:
        toast("Pick a game from 'Running now' first.", False)
        return
    stop_rotation()
    stop_party_random()
    kill(running[name]["exe"])
    rpc_clear(name)
    del running[name]
    refresh_running()
    toast(f"Stopped {name}.")
    play_sound("stop")


def stop_all(quiet=False):
    stop_rotation()
    stop_party_random()
    if not running:
        if not quiet:
            toast("Nothing is running.", False)
        return
    for n, r in running.items():
        kill(r["exe"])
        rpc_clear(n)
    running.clear()
    refresh_running()
    if not quiet:
        toast("Stopped everything.")


def detect_running():
    for name, exe_rel in saved.items():
        if not exe_rel:
            continue
        exe_name = os.path.basename(exe_rel)
        if exe_running(exe_name):
            running[name] = {"exe": exe_name, "start": time.time()}
    refresh_running()


def on_close():
    if running:
        message = "Stop them before closing?\n\nYes = stop them\nNo = leave them running\nCancel = go back"
        if rpc:
            message = ("Stop them before closing?\n\nYes = stop them\n"
                       "No = keep the app minimized so your custom lines stay\nCancel = go back")
        answer = messagebox.askyesnocancel("Games still running", message)
        if answer is None:
            return
        if answer:
            stop_all(quiet=True)
        elif rpc:
            root.iconify()
            return
    if hotkey_listener["obj"]:
        hotkey_listener["obj"].stop()
    if tray_icon["obj"]:
        tray_icon["obj"].stop()
    root.destroy()


# saved games
def refresh_saved():
    favs = settings["favorites"]
    names = sorted(saved, key=lambda n: (n not in favs, n.lower()))
    saved_cards.set_items([
        {"key": n, "title": n, "sub": os.path.basename(saved[n]) or "Status only",
         "icon": settings["icons"].get(n), "star": n in favs}
        for n in names
    ])


def toggle_fav(name):
    favs = settings["favorites"]
    if name in favs:
        favs.remove(name)
    else:
        favs.append(name)
    write_settings()
    refresh_saved()


def run_saved(key=None):
    key = saved_cards.selected if key is None else key
    if key not in saved:
        toast("Pick a saved game first.", False)
        return
    launch(key, saved[key])


def remove_saved():
    key = saved_cards.selected
    if key not in saved:
        toast("Pick a saved game first.", False)
        return
    del saved[key]
    write_saved()
    if key in settings["favorites"]:
        settings["favorites"].remove(key)
        write_settings()
    refresh_saved()
    toast(f"Removed {key} from saved games.")


# recent games
def add_recent(name, exe_rel):
    recent[:] = [r for r in recent if r[0] != name]
    recent.insert(0, [name, exe_rel])
    del recent[10:]
    write_recent()
    refresh_recent()


def refresh_recent():
    recent_cards.set_items([
        {"key": n, "title": n, "sub": os.path.basename(rel) or "Status only",
         "icon": settings["icons"].get(n)}
        for n, rel in recent
    ])


def delete_recent(name):
    recent[:] = [r for r in recent if r[0] != name]
    write_recent()
    refresh_recent()
    toast(f"Removed {name} from Recent.")


def recent_menu(key, event):
    menu = tk.Menu(root, tearoff=0, bg=INPUT, fg=FG, activebackground=ACCENT,
                   activeforeground="white", bd=0, font=("Segoe UI", 10))
    menu.add_command(label="Delete from Recent", command=lambda: delete_recent(key))
    try:
        menu.tk_popup(event.x_root, event.y_root)
    finally:
        menu.grab_release()


def exe_of_recent(name):
    for n, rel in recent:
        if n == name:
            return rel
    return None


def run_recent(key=None):
    key = recent_cards.selected if key is None else key
    rel = exe_of_recent(key) if key is not None else None
    if rel is None:
        toast("Pick a recent game first.", False)
        return
    launch(key, rel)


def save_recent():
    key = recent_cards.selected
    rel = exe_of_recent(key) if key is not None else None
    if rel is None:
        toast("Pick a recent game first.", False)
        return
    saved[key] = rel
    write_saved()
    refresh_saved()
    toast(f"Saved {key}.")


# ---------------------------------------------------------------- accent
def log(text):
    try:
        os.makedirs(BASE, exist_ok=True)
        with open(os.path.join(BASE, "log.txt"), "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + text + "\n")
    except OSError:
        pass


def app_id_for(name):
    known = settings["ids"].get(name)
    if known:
        return known
    for a in apps:
        if a["name"] == name:
            return a.get("id")
    return None


rpc_gen = {}   # game name -> generation number, invalidates stale connects


def rpc_apply(name, details, state, party):
    if Presence is None:
        toast("Install pypresence first: pip install pypresence", False)
        return
    custom = name in running and running[name].get("mode") == "rpc"
    app_id = settings["client_id"] if custom else app_id_for(name)
    if custom and not app_id:
        toast("Add your App ID in the Settings tab first.", False)
        return
    if not app_id:
        toast("The game list isn't loaded yet, try again in a moment.", False)
        return
    start = int(running[name]["start"]) if name in running else int(time.time())
    rpc_gen[name] = rpc_gen.get(name, 0) + 1
    my_gen = rpc_gen[name]

    def work():
        try:
            client = rpc.get(name)
            if client is None:
                client = Presence(app_id)
                client.connect()
                if rpc_gen.get(name) != my_gen:
                    try:
                        client.close()
                    except Exception:
                        pass
                    return
                rpc[name] = client
            if rpc_gen.get(name) != my_gen:
                return
            args = {"start": start}
            if custom:
                args["name"] = name
                pic = big_icon(name)
                if pic:
                    args["large_image"] = pic
                    args["large_text"] = name
            if details:
                args["details"] = details
            if state:
                args["state"] = state
            if party:
                args["party_size"] = party
            client.update(**args)
            log(f"{name} ({app_id}): sent {args}")
            root.after(0, toast, f"Status updated for {name}.")
        except Exception as err:
            rpc.pop(name, None)
            log(f"{name} ({app_id}): FAILED {err!r}")
            root.after(0, toast, f"Could not update: {err}", False)

    threading.Thread(target=work, daemon=True).start()


def rpc_clear(name):
    rpc_gen[name] = rpc_gen.get(name, 0) + 1
    client = rpc.pop(name, None)
    if client is None:
        return

    def work():
        try:
            client.clear()
            client.close()
        except Exception:
            pass

    threading.Thread(target=work, daemon=True).start()


rotation = {"job": None, "index": 0, "items": []}


def toggle_rotation():
    if rotation["job"]:
        stop_rotation()
        return
    name = running_cards.selected
    if name not in running:
        toast("Pick a running game in 'Running now' first.", False)
        return
    items = [(d, s, p) for var, d, s, p in rotate_vars if var.get()]
    if len(items) < 2:
        toast("Tick at least 2 presets to rotate between.", False)
        return
    try:
        secs = max(5, int(rotate_seconds.get().strip()))
    except ValueError:
        toast("Rotation seconds must be a number.", False)
        return
    stop_party_random()
    rotation["items"] = items
    rotation["index"] = 0
    rotation["secs"] = secs
    rotate_btn.fixed = RED
    rotate_btn.config(text="Stop rotation", bg=RED)
    rotate_tick()


def rotate_tick():
    items = rotation["items"]
    if not items:
        return
    d, s, p = items[rotation["index"] % len(items)]
    use_preset(d, s, p)
    apply_status()
    rotation["index"] += 1
    rotation["job"] = root.after(rotation["secs"] * 1000, rotate_tick)


def stop_rotation():
    if rotation["job"]:
        root.after_cancel(rotation["job"])
    rotation["job"] = None
    rotate_btn.fixed = "#2a2a3a"
    rotate_btn.config(text="Start rotation", bg="#2a2a3a")


party_rand = {"job": None, "range": (1, 1), "secs": 30, "unit": "sec"}


def toggle_rand_unit():
    party_rand["unit"] = "min" if party_rand["unit"] == "sec" else "sec"
    rand_unit_btn.config(text=party_rand["unit"])


def toggle_party_random():
    if party_rand["job"]:
        stop_party_random()
        return
    name = running_cards.selected
    if name not in running:
        toast("Pick a running game in 'Running now' first.", False)
        return
    if not details_entry.get().strip() and not state_entry.get().strip():
        toast("Type Line 1 or Line 2 first. The party size shows next to the text.", False)
        return
    low, top = rand_min.get().strip(), max_entry.get().strip()
    every = rand_every.get().strip()
    if not (low.isdigit() and top.isdigit() and every.isdigit()):
        toast("Min, max ('of' box) and the time must be numbers.", False)
        return
    low, top, every = int(low), int(top), int(every)
    if low < 1 or low > top:
        toast("Min must be at least 1 and not above the max.", False)
        return
    stop_rotation()
    party_rand["range"] = (low, top)
    party_rand["secs"] = max(5, every * (60 if party_rand["unit"] == "min" else 1))
    rand_btn.fixed = RED
    rand_btn.config(text="Stop random", bg=RED)
    party_random_tick()


def party_random_tick():
    if running_cards.selected not in running:
        stop_party_random()
        return
    low, top = party_rand["range"]
    cur_entry.delete(0, tk.END)
    cur_entry.insert(0, str(random.randint(low, top)))
    update_preview()
    apply_status()
    party_rand["job"] = root.after(party_rand["secs"] * 1000, party_random_tick)


def stop_party_random():
    if party_rand["job"]:
        root.after_cancel(party_rand["job"])
    party_rand["job"] = None
    rand_btn.fixed = "#2a2a3a"
    rand_btn.config(text="Start random", bg="#2a2a3a")


def use_preset(details, state, party):
    fields = ((details_entry, details), (state_entry, state),
              (cur_entry, str(party[0]) if party else ""),
              (max_entry, str(party[1]) if party else ""))
    for field, value in fields:
        field.delete(0, tk.END)
        field.insert(0, value)
    update_preview()


def apply_status():
    name = running_cards.selected
    if name not in running:
        toast("Start a game, then pick it in 'Running now'.", False)
        return
    details = details_entry.get().strip()
    state = state_entry.get().strip()
    if not details and not state:
        toast("Type at least one line.", False)
        return
    if len(details) == 1 or len(state) == 1:
        toast("Each line needs at least 2 characters.", False)
        return
    party = None
    cur, top_size = cur_entry.get().strip(), max_entry.get().strip()
    if cur.isdigit() and top_size.isdigit() and 0 < int(cur) <= int(top_size):
        party = [int(cur), int(top_size)]
    rpc_apply(name, details, state, party)
    play_sound("apply")


def clear_status():
    name = running_cards.selected
    if name not in running:
        toast("Pick a running game first.", False)
        return
    rpc_clear(name)
    toast(f"Custom lines removed for {name}.")


SOUND_FILES = {
    "connect": r"C:\Windows\Media\Windows Notify System Generic.wav",
    "stop": r"C:\Windows\Media\Windows Foreground.wav",
    "apply": r"C:\Windows\Media\Windows Ding.wav",
}


def play_sound(kind):
    if not settings["sound"]:
        return
    wav = SOUND_FILES.get(kind)
    if not wav or not os.path.exists(wav):
        return

    def work():
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 f"(New-Object Media.SoundPlayer '{wav}').PlaySync()"],
                creationflags=NO_WINDOW,
            )
        except Exception as err:
            root.after(0, toast, f"Sound failed: {err!r}", False)

    threading.Thread(target=work, daemon=True).start()


def apply_accent(name):
    global ACCENT
    ACCENT = ACCENTS[name]
    settings["accent"] = name
    write_settings()
    for b in BUTTONS:
        if not b.fixed:
            b.config(bg=b.base())
    bg.delete("logo")
    draw_logo(bg, 18, 19, 46 / 512)
    for i, n in enumerate(ACCENTS):
        swatches.itemconfig(f"sw{i}", outline="white" if n == name else CARD)
    tabs.layout()
    for cards in (results_list, saved_cards, recent_cards, running_cards):
        cards.paint()
    for field in (entry, details_entry, state_entry, cur_entry, max_entry):
        field.config(highlightcolor=ACCENT)


def custom_swatch_click():
    # first click on an already-saved custom color just switches to it;
    # click again (when it's active) or when none is saved to pick a new one
    if settings["custom_color"] and settings["accent"] != "Custom":
        apply_accent("Custom")
        return
    from tkinter import colorchooser
    result = colorchooser.askcolor(color=ACCENTS["Custom"], title="Pick an accent color")
    hex_color = result[1]
    if not hex_color:
        return
    ACCENTS["Custom"] = hex_color
    settings["custom_color"] = hex_color
    swatches.itemconfig(f"sw{list(ACCENTS).index('Custom')}", fill=hex_color)
    apply_accent("Custom")

# ---------------------------------------------------------------- orbs
W, H = 400, 700
LAYERS = [(3.4, 0.10), (2.3, 0.22), (1.5, 0.45), (1.0, 1.0)]
ORBS = []
mood = {"v": 0.0}
clock = {"t": 0.0}
mouse = {"x": -999, "y": -999}
anim = {"t": 0.0}


def palette():
    return [ACCENT, mix(ACCENT, "#ffffff", 0.4), GREEN, "#d6dcff"]


def new_orb(scatter):
    r = random.uniform(2, 6)
    return {
        "x": random.uniform(0, W),
        "y": random.uniform(0, H) if scatter else H + 30,
        "r": r,
        "speed": 60 - r * 7 + random.uniform(-4, 4),
        "amp": random.uniform(6, 18),
        "freq": random.uniform(0.5, 1.4),
        "phase": random.uniform(0, 6.28),
        "ci": random.randrange(4),
        "ox": 0.0,
        "oy": 0.0,
        "shapes": [],
    }


def make_orbs():
    for i in range(26):
        orb = new_orb(True)
        for layer in LAYERS:
            orb["shapes"].append(bg.create_oval(0, 0, 0, 0, outline="", fill=BG))
        ORBS.append(orb)


CONFETTI = []
confetti_colors = lambda: [ACCENT, GREEN, GOLD, "#ffffff", "#ff5fa2",
                           mix(ACCENT, "#ffffff", 0.5)]


def burst_confetti(cx=250, cy=42, count=55):
    for _ in range(count):
        ang = random.uniform(-2.4, -0.7)   # mostly upward cone
        speed = random.uniform(3.5, 9.0)
        tri = random.random() < 0.3
        CONFETTI.append({
            "x": cx, "y": cy,
            "vx": math.cos(ang) * speed + random.uniform(-1, 1),
            "vy": math.sin(ang) * speed,
            "life": 1.0,
            "color": random.choice(confetti_colors()),
            "size": random.uniform(4, 8),
            "spin": random.uniform(0.2, 0.5),
            "phase": random.uniform(0, 6.28),
            "shape": (bg.create_polygon(0, 0, 0, 0, 0, 0, outline="", fill=BG)
                      if tri else bg.create_rectangle(0, 0, 0, 0, outline="", fill=BG)),
            "tri": tri,
        })


def animate_confetti():
    for p in CONFETTI[:]:
        p["vy"] += 0.22
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["phase"] += p["spin"]
        p["life"] -= 0.012
        if p["life"] <= 0 or p["y"] > H + 20:
            bg.delete(p["shape"])
            CONFETTI.remove(p)
            continue
        s = p["size"]
        flutter = max(0.15, abs(math.sin(p["phase"])))
        w = s * flutter
        color = mix(BG, p["color"], min(1.0, p["life"] * 1.6))
        if p["tri"]:
            x, y = p["x"], p["y"]
            bg.coords(p["shape"], x - w, y + s, x + w, y + s, x, y - s)
        else:
            bg.coords(p["shape"], p["x"] - w, p["y"] - s, p["x"] + w, p["y"] + s)
        bg.itemconfig(p["shape"], fill=color)
    root.after(16, animate_confetti)


def on_motion(event):
    mouse["x"] = event.x_root - root.winfo_rootx()
    mouse["y"] = event.y_root - root.winfo_rooty()


def animate_orbs():
    clock["t"] += 0.033
    t = clock["t"]
    mood["v"] += ((1.0 if running else 0.0) - mood["v"]) * 0.04
    m = mood["v"]
    pal = palette()
    mx, my = mouse["x"], mouse["y"]
    for o in ORBS:
        o["y"] -= o["speed"] * (1 + 0.9 * m) * 0.033
        if o["y"] < -30:
            fresh = new_orb(False)
            fresh["shapes"] = o["shapes"]
            o.clear()
            o.update(fresh)
        x = o["x"] + o["amp"] * math.sin(t * o["freq"] + o["phase"]) + o["ox"]
        y = o["y"] + o["oy"]
        dx, dy = x - mx, y - my
        d = math.hypot(dx, dy)
        if 1 < d < 110:
            push = (110 - d) / 110 * 2.4
            o["ox"] += dx / d * push
            o["oy"] += dy / d * push
        o["ox"] *= 0.93
        o["oy"] *= 0.93
        life = (H - o["y"]) / H
        fade = max(0.0, min(life / 0.12, (1 - life) / 0.25, 1.0))
        glow = fade * (0.75 + 0.25 * math.sin(t * 2.2 + o["phase"] * 3))
        base = mix(pal[o["ci"]], GREEN, m * 0.6)
        for shape, (scale, strength) in zip(o["shapes"], LAYERS):
            rad = o["r"] * scale
            bg.coords(shape, x - rad, y - rad, x + rad, y + rad)
            if strength == 1.0:
                color = mix(BG, mix(base, "#ffffff", 0.55), glow)
            else:
                color = mix(BG, base, strength * glow)
            bg.itemconfig(shape, fill=color)
    root.after(33, animate_orbs)


def toggle_last_game():
    if running:
        root.after(0, stop_all)
        return
    if recent:
        name, exe_rel = recent[0]
        root.after(0, launch, name, exe_rel)
    else:
        root.after(0, toast, "No recent game to toggle.", False)


hotkey_listener = {"obj": None}


def start_hotkey_listener():
    if pynput_keyboard is None:
        return
    if hotkey_listener["obj"]:
        hotkey_listener["obj"].stop()
        hotkey_listener["obj"] = None
    try:
        combo = {settings["hotkey"]: toggle_last_game}
        listener = pynput_keyboard.GlobalHotKeys(combo)
        listener.start()
        hotkey_listener["obj"] = listener
    except Exception as err:
        root.after(0, toast, f"Could not set hotkey: {err}", False)


def save_hotkey():
    combo = hotkey_entry.get().strip()
    if not combo:
        toast("Type a hotkey combo first.", False)
        return
    settings["hotkey"] = combo
    write_settings()
    start_hotkey_listener()
    toast(f"Hotkey set to {combo}.")


def toggle_sound():
    settings["sound"] = not settings["sound"]
    write_settings()
    sound_btn.config(text=f"Sound: {'On' if settings['sound'] else 'Off'}")


def apply_streamer_mode():
    user_id_entry.config(show="•" if settings["streamer_mode"] else "")


def toggle_streamer_mode():
    settings["streamer_mode"] = not settings["streamer_mode"]
    write_settings()
    streamer_btn.config(text=f"Streamer Mode: {'On' if settings['streamer_mode'] else 'Off'}")
    apply_streamer_mode()


def save_user_id():
    value = user_id_entry.get().strip()
    if value and not value.isdigit():
        toast("A User ID is only numbers. Right-click your name > Copy User ID.", False)
        return
    settings["user_id"] = value
    write_settings()
    toast("User ID saved." if value else "User ID removed.")


def profile_url():
    uid = settings.get("user_id", "")
    return f"https://discord.com/users/{uid}" if uid else None


def copy_profile_link():
    url = profile_url()
    if not url:
        toast("Add your User ID first.", False)
        return
    root.clipboard_clear()
    root.clipboard_append(url)
    toast("Profile link copied.")


def open_profile_link():
    url = profile_url()
    if not url:
        toast("Add your User ID first.", False)
        return
    webbrowser.open(url)


LANYARD_SERVER = "https://discord.gg/lanyard"
watch_job = {"id": None}


def status_color(s):
    return {"online": GREEN, "idle": GOLD, "dnd": RED}.get(s, "#6d6f78")


def start_watching():
    uid = watch_entry.get().strip()
    if not uid.isdigit():
        toast("Enter a numeric Discord User ID.", False)
        return
    settings["watch_id"] = uid
    write_settings()
    if watch_job["id"]:
        root.after_cancel(watch_job["id"])
    watch_label.config(text="Checking...")
    poll_lanyard(uid)


def stop_watching():
    if watch_job["id"]:
        root.after_cancel(watch_job["id"])
        watch_job["id"] = None
    watch_label.config(text="Not watching.")
    watch_name.config(text="")
    watch_activity.config(text="")
    watch_dot.config(fg="#6d6f78")


def poll_lanyard(uid):
    def work():
        try:
            r = requests.get(f"https://api.lanyard.rest/v1/users/{uid}", timeout=10)
            data = r.json()
        except Exception as err:
            root.after(0, show_watch_error, f"Request failed: {err}")
            return
        root.after(0, show_watch_result, data)

    threading.Thread(target=work, daemon=True).start()
    watch_job["id"] = root.after(5000, poll_lanyard, uid)


def discord_avatar_url(user):
    uid = user.get("id", "")
    av = user.get("avatar")
    if av:
        ext = "gif" if av.startswith("a_") else "png"
        return f"https://cdn.discordapp.com/avatars/{uid}/{av}.{ext}?size=128"
    disc = user.get("discriminator", "0")
    try:
        idx = (int(uid) >> 22) % 6 if disc == "0" else int(disc) % 5
    except ValueError:
        idx = 0
    return f"https://cdn.discordapp.com/embed/avatars/{idx}.png"


def activity_icon_url(act):
    assets = act.get("assets") or {}
    img = assets.get("large_image") or assets.get("small_image")
    app_id = act.get("application_id")
    if img and app_id and not str(img).startswith("mp:"):
        return f"https://cdn.discordapp.com/app-assets/{app_id}/{img}.png?size=64"
    return None


def show_watch_error(msg):
    watch_label.config(text=msg)
    watch_dot.config(fg="#6d6f78")


def show_watch_result(data):
    if not data.get("success"):
        watch_label.config(text=f"Not in the Lanyard server. Join: {LANYARD_SERVER}")
        watch_name.config(text="")
        watch_badges.config(text="")
        watch_avatar.config(image="", text="?", bg=ACCENT)
        watch_avatar.image = None
        watch_avatar_holder.config(bg=ACCENT)
        watch_activity.config(text="Not watching.")
        watch_elapsed.config(text="")
        watch_game_icon.config(image="", text="")
        watch_game_icon.image = None
        watch_game_icon_holder.config(bg="#2a2a3a")
        watch_dot.config(fg="#6d6f78")
        return

    d = data["data"]
    user = d.get("discord_user", {})
    status = d.get("discord_status", "offline")
    watch_label.config(text="Live")
    watch_dot.config(fg=status_color(status))
    watch_name.config(text=user.get("global_name") or user.get("username", "?"))
    watch_badges.config(text=decode_badges(user.get("public_flags", 0)))

    def apply_avatar(img):
        try:
            watch_avatar.config(image=img, text="")
            watch_avatar.image = img
            watch_avatar_holder.config(bg="#1e1f27")
        except tk.TclError:
            pass
    fetch_icon(discord_avatar_url(user), apply_avatar)

    acts = [a for a in d.get("activities", []) if a.get("type") == 0]
    if not acts:
        watch_activity.config(text="No game activity")
        watch_elapsed.config(text="")
        watch_game_icon.config(image="", text="")
        watch_game_icon.image = None
        watch_game_icon_holder.config(bg="#2a2a3a")
        return

    a = acts[0]
    name = a.get("name", "?")
    watch_activity.config(text=name + (f" — {a['details']}" if a.get("details") else ""))
    ts = a.get("timestamps", {})
    if ts.get("start"):
        elapsed = fmt_time(max(0, time.time() - ts["start"] / 1000))
        watch_elapsed.config(text=f"⏱ {elapsed} elapsed")
    else:
        watch_elapsed.config(text="")

    icon_url = activity_icon_url(a)
    if icon_url:
        def apply_game_icon(img):
            try:
                watch_game_icon.config(image=img, text="")
                watch_game_icon.image = img
                watch_game_icon_holder.config(bg="#1e1f27")
            except tk.TclError:
                pass
        fetch_icon(icon_url, apply_game_icon)
    else:
        watch_game_icon.config(image="", text=name[:1].upper())
        watch_game_icon.image = None
        watch_game_icon_holder.config(bg=ACCENT)

UPDATES_SERVER = "https://discord.gg/jbTfVZN7hY"


def show_welcome():
    settings["seen_welcome"] = True
    write_settings()

    dlg = tk.Toplevel(root)
    dlg.title("Game Presence")
    dlg.configure(bg=BG)
    dlg.resizable(False, False)
    dlg.transient(root)

    tk.Label(dlg, text="Welcome!", bg=BG, fg="white",
             font=("Segoe UI", 13, "bold")).pack(padx=28, pady=(20, 4))
    tk.Label(dlg, text="Join the server for updates, new features, and support.",
             bg=BG, fg=MUTED, font=("Segoe UI", 10), wraplength=280,
             justify="center").pack(padx=28)
    HoverButton(dlg, text="Join Server",
                command=lambda: webbrowser.open(UPDATES_SERVER)).pack(
        fill="x", padx=28, pady=(16, 6))
    HoverButton(dlg, text="Maybe later", color="#2a2a3a",
                command=dlg.destroy).pack(fill="x", padx=28, pady=(0, 18))
    dlg.bind("<Escape>", lambda e: dlg.destroy())

    dlg.update_idletasks()
    w, h = dlg.winfo_reqwidth(), dlg.winfo_reqheight()
    x = root.winfo_rootx() + (root.winfo_width() - w) // 2
    y = root.winfo_rooty() + (root.winfo_height() - h) // 2
    dlg.geometry(f"{w}x{h}+{x}+{y}")
    dlg.wait_visibility()
    dlg.grab_set()


def refresh_accounts():
    for w in accounts_frame.winfo_children():
        w.destroy()
    if not settings["accounts"]:
        tk.Label(accounts_frame, text="No saved accounts yet.", bg=CARD, fg=MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w")
        return
    for acc in settings["accounts"]:
        row = tk.Frame(accounts_frame, bg=CARD)
        row.pack(fill="x", pady=2)
        active = (acc["client_id"] == settings["client_id"]
                  and acc["user_id"] == settings["user_id"])
        HoverButton(row, text=("✓ " if active else "") + acc["name"],
                    color=ACCENT if active else "#2a2a3a",
                    command=lambda a=acc: use_account(a)).pack(side="left")
        HoverButton(row, text="✕", color="#2a2a3a",
                    command=lambda a=acc: delete_account(a)).pack(side="left", padx=(6, 0))


def save_account():
    name = account_name_entry.get().strip()
    if len(name) < 2:
        toast("Give the account a name (2+ characters).", False)
        return
    cid = client_entry.get().strip()
    uid = user_id_entry.get().strip()
    if (cid and not cid.isdigit()) or (uid and not uid.isdigit()):
        toast("App ID and User ID are only numbers.", False)
        return
    entry = {"name": name, "client_id": cid, "user_id": uid}
    for i, acc in enumerate(settings["accounts"]):
        if acc["name"].lower() == name.lower():
            settings["accounts"][i] = entry
            break
    else:
        settings["accounts"].append(entry)
    settings["client_id"], settings["user_id"] = cid, uid
    write_settings()
    account_name_entry.delete(0, tk.END)
    refresh_accounts()
    toast(f"Saved account '{name}'.")


def use_account(acc):
    settings["client_id"] = acc["client_id"]
    settings["user_id"] = acc["user_id"]
    for entry, value in ((client_entry, acc["client_id"]),
                         (user_id_entry, acc["user_id"])):
        entry.delete(0, tk.END)
        entry.insert(0, value)
    write_settings()
    for n in list(rpc):
        rpc_clear(n)
    refresh_accounts()
    toast(f"Switched to '{acc['name']}'. Press Apply on the Status tab again.")


def delete_account(acc):
    if messagebox.askyesno("Delete account", f"Delete saved account '{acc['name']}'?"):
        settings["accounts"] = [a for a in settings["accounts"] if a is not acc]
        write_settings()
        refresh_accounts()

BADGE_FLAGS = [
    (1 << 0, "Staff"),
    (1 << 1, "Partner"),
    (1 << 2, "HypeSquad Events"),
    (1 << 3, "Bug Hunter"),
    (1 << 6, "HypeSquad Bravery"),
    (1 << 7, "HypeSquad Brilliance"),
    (1 << 8, "HypeSquad Balance"),
    (1 << 9, "Early Supporter"),
    (1 << 14, "Bug Hunter Gold"),
    (1 << 17, "Early Verified Bot Dev"),
    (1 << 18, "Moderator"),
    (1 << 22, "Active Developer"),
]


def decode_badges(flags):
    if not flags:
        return ""
    names = [name for bit, name in BADGE_FLAGS if flags & bit]
    known_bits = 0
    for bit, _ in BADGE_FLAGS:
        known_bits |= bit
    if flags & ~known_bits:
        names.append("+ other badge(s)")
    return ", ".join(names)


tray_icon = {"obj": None}


def tray_image():
    if PILImage is None:
        return None
    img = PILImage.new("RGBA", (64, 64), (0, 0, 0, 0))
    try:
        return PILImage.open(resource("logo.png") or find_file("logo.png"))
    except Exception:
        return img


def start_tray():
    if pystray is None:
        return
    img = tray_image()
    if img is None:
        return
    menu = pystray.Menu(
        pystray.MenuItem("Show", lambda: root.after(0, show_from_tray)),
        pystray.MenuItem("Stop all", lambda: root.after(0, stop_all)),
        pystray.MenuItem("Quit", lambda: root.after(0, quit_from_tray)),
    )
    icon = pystray.Icon("Game Presence", img, "Game Presence", menu)
    tray_icon["obj"] = icon
    threading.Thread(target=icon.run, daemon=True).start()


def show_from_tray():
    root.deiconify()
    root.lift()
    root.focus_force()

BRIDGE_PORT = 47991


class BridgeHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path != "/now":
            self.send_response(404)
            self.end_headers()
            return
        name, app_id = None, None
        if running:
            latest = max(list(running.items()), key=lambda kv: kv[1]["start"])
            name = latest[0]
            app_id = app_id_for(name)
        body = json.dumps({"name": name, "appId": app_id}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        origin = self.headers.get("Origin", "")
        if origin in ("https://discord.com", "https://canary.discord.com", "https://ptb.discord.com"):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def start_bridge_server():
    try:
        server = http.server.HTTPServer(("127.0.0.1", BRIDGE_PORT), BridgeHandler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
    except OSError as err:
        root.after(0, toast, f"Bridge server failed: {err}", False)

def quit_from_tray():
    if tray_icon["obj"]:
        tray_icon["obj"].stop()
    on_close()


def animate():
    anim["t"] += 0.06
    n = len(running)
    cx, cy = 250, 42
    if n:
        p = (anim["t"] * 0.5) % 1.0
        rad = 5 + p * 11
        elapsed = time.time() - min(r["start"] for r in running.values())
        bg.coords(ring, cx - rad, cy - rad, cx + rad, cy + rad)
        bg.itemconfig(ring, state="normal", outline=mix(GREEN, BG, p))
        bg.itemconfig(dot, fill=GREEN)
        bg.itemconfig(pill_text, text=f"{n} live · {fmt_time(elapsed)}", fill=GREEN)
        running_cards.pulse(mix(GREEN, "#ffffff", 0.35 * (0.5 + 0.5 * math.sin(anim["t"] * 3))))
    else:
        bg.itemconfig(ring, state="hidden")
        bg.itemconfig(dot, fill="#6d6f78")
        bg.itemconfig(pill_text, text="idle", fill=MUTED)
    root.after(40, animate)


def tick_timers():
    now = time.time()
    for name, r in running.items():
        running_cards.update_sub(name, f"Live for {fmt_time(now - r['start'])}")
    update_preview()
    root.after(1000, tick_timers)


def fade_in(a=0.0):
    root.attributes("-alpha", min(a, 1.0))
    if a < 1.0:
        root.after(20, fade_in, a + 0.08)


def show_splash():
    w, h = 320, 220
    sp = tk.Toplevel(root)
    sp.overrideredirect(True)
    sp.geometry(f"{w}x{h}+{(root.winfo_screenwidth() - w) // 2}+{(root.winfo_screenheight() - h) // 2}")
    sp.configure(bg=BG)
    sp.attributes("-alpha", 0.0)
    sp.attributes("-topmost", True)
    c = tk.Canvas(sp, width=w, height=h, bg=BG, highlightthickness=1, highlightbackground=EDGE)
    c.pack()
    rings = [c.create_oval(0, 0, 0, 0, outline=BG, width=2) for _ in range(3)]
    draw_logo(c, w / 2 - 36, 40, 72 / 512)
    c.create_text(w / 2, 140, text="Game Presence", fill="white", font=("Segoe UI", 16, "bold"))
    c.create_text(w / 2, 166, text="By Aiden", fill=MUTED, font=("Segoe UI", 9, "italic"))
    total = 80

    def step(n):
        a = min(n / 14, (total - n) / 14, 1.0)
        sp.attributes("-alpha", max(a, 0.0))
        for i, ring_id in enumerate(rings):
            p = (n * 0.025 + i / 3) % 1.0
            rad = 40 + p * 62
            c.coords(ring_id, w / 2 - rad, 76 - rad, w / 2 + rad, 76 + rad)
            c.itemconfig(ring_id, outline=mix(ACCENT, BG, p))
        if n >= total:
            sp.destroy()
            root.deiconify()
            root.lift()
            fade_in()
            root.after(60, tabs.layout)
            if not settings["seen_welcome"]:
                root.after(400, show_welcome)
        else:
            root.after(22, step, n + 1)

    step(0)


def on_wheel(event):
    try:
        w = root.winfo_containing(event.x_root, event.y_root)
    except KeyError:
        return
    while w is not None:
        if isinstance(w, CardList):
            w.scroll(event.delta)
            return
        if w is settings_canvas:
            scroll_settings(event.delta)
            return
        if w is status_canvas:
            scroll_status(event.delta)
            return
        w = w.master


def make_entry(parent):
    return tk.Entry(parent, bg=INPUT, fg=FG, insertbackground=FG, relief="flat",
                    font=("Segoe UI", 11), highlightthickness=1,
                    highlightbackground=EDGE, highlightcolor=ACCENT)


# ---------------------------------------------------------------- window
load_settings()
ACCENT = ACCENTS[settings["accent"]]

root = tk.Tk()
root.withdraw()
root.attributes("-alpha", 0.0)
root.title("Game Presence")
root.geometry("400x700")
root.resizable(False, False)
def find_file(name):
    candidates = [
        resource(name),
        os.path.join(BASE, name),
        os.path.join(os.path.dirname(sys.executable), name),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


ico_path = find_file("logo.ico")
if ico_path:
    try:
        root.iconbitmap(ico_path)
    except tk.TclError:
        ico_path = None
if not ico_path:
    png_path = find_file("logo.png")
    if png_path:
        try:
            img = tk.PhotoImage(file=png_path)
            root.iconphoto(True, img)
            root._icon_ref = img
        except tk.TclError:
            pass

bg = tk.Canvas(root, bg=BG, highlightthickness=0)
bg.place(x=0, y=0, relwidth=1, relheight=1)
make_orbs()

status = tk.Label(root, text="Loading game list...", bg=BG, fg=MUTED,
                  font=("Segoe UI", 9), wraplength=350)
status.pack(side="bottom", pady=10)

stop_buttons = tk.Frame(root, bg=BG)
stop_buttons.pack(side="bottom")
HoverButton(stop_buttons, text="Stop", command=stop_selected).pack(side="left", padx=4)
HoverButton(stop_buttons, text="Stop all", command=stop_all, color=RED).pack(side="left", padx=4)

running_cards = CardList(root, "Nothing is running.", auto=True, height=96)
running_cards.pack(side="bottom", fill="x", padx=12, pady=8)
tk.Label(root, text="Running now:", bg=BG, fg=FG,
         font=("Segoe UI", 10)).pack(side="bottom", anchor="w", padx=12)

# header, drawn on the same canvas as the orbs
draw_logo(bg, 18, 19, 46 / 512)
bg.create_text(76, 33, text="Game Presence", anchor="w", fill="white",
               font=("Segoe UI", 15, "bold"))
bg.create_text(76, 56, text="By Aiden", anchor="w", fill=MUTED,
               font=("Segoe UI", 9, "italic"))
ring = bg.create_oval(0, 0, 0, 0, outline=GREEN, width=2, state="hidden")
dot = bg.create_oval(245, 37, 255, 47, fill="#6d6f78", outline="")
pill_text = bg.create_text(264, 42, text="idle", anchor="w", fill=MUTED,
                           font=("Segoe UI", 10, "bold"))


tabs = Tabs(root, ["Search", "Saved", "Recent", "Status", "Settings"])
tabs.pack(fill="both", expand=True, padx=14, pady=(92, 8))

# --- search tab
search_page = tabs.page("Search")
tk.Label(search_page, text="Game name:", bg=BG, fg=FG,
         font=("Segoe UI", 10)).pack(anchor="w", padx=6, pady=(8, 0))
top = tk.Frame(search_page, bg=BG)
top.pack(fill="x", padx=6)
entry = tk.Entry(top, bg=INPUT, fg=FG, insertbackground=FG, relief="flat",
                 font=("Segoe UI", 11), highlightthickness=1,
                 highlightbackground=EDGE, highlightcolor=ACCENT)
entry.pack(side="left", fill="x", expand=True, ipady=6)
entry.bind("<KeyRelease>", on_key)
HoverButton(top, text="Search", command=search).pack(side="left", padx=(6, 0))

buttons = tk.Frame(search_page, bg=BG)
buttons.pack(side="bottom", pady=8)
HoverButton(buttons, text="Run it", command=run_selected).pack(side="left", padx=4)
HoverButton(buttons, text="Save", command=save_selected).pack(side="left", padx=4)
results_list = CardList(search_page, "Type a game name to begin.", on_open=run_selected, auto=True)
results_list.pack(fill="both", expand=True, padx=6, pady=(8, 0))

# --- saved tab
saved_page = tabs.page("Saved")
saved_buttons = tk.Frame(saved_page, bg=BG)
saved_buttons.pack(side="bottom", pady=8)
HoverButton(saved_buttons, text="Run it", command=run_saved).pack(side="left", padx=4)
HoverButton(saved_buttons, text="Remove", command=remove_saved).pack(side="left", padx=4)
saved_cards = CardList(saved_page, "Nothing saved yet.\nSearch a game and press Save.",
                       on_open=run_saved, on_star=toggle_fav)
saved_cards.pack(fill="both", expand=True, padx=6, pady=(8, 0))

# --- recent tab
recent_page = tabs.page("Recent")
recent_buttons = tk.Frame(recent_page, bg=BG)
recent_buttons.pack(side="bottom", pady=8)
HoverButton(recent_buttons, text="Run it", command=run_recent).pack(side="left", padx=4)
HoverButton(recent_buttons, text="Save", command=save_recent).pack(side="left", padx=4)
recent_cards = CardList(recent_page, "Games you run will show up here.",
                        on_open=run_recent, on_menu=recent_menu)
recent_cards.pack(fill="both", expand=True, padx=6, pady=(8, 0))

# --- settings tab
settings_page = tabs.page("Settings")

settings_canvas = tk.Canvas(settings_page, bg=BG, highlightthickness=0)
settings_canvas.pack(fill="both", expand=True)
settings_inner = tk.Frame(settings_canvas, bg=BG)
settings_win = settings_canvas.create_window(0, 0, window=settings_inner, anchor="nw")
settings_canvas.bind("<Configure>",
                     lambda e: settings_canvas.itemconfig(settings_win, width=e.width))
settings_inner.bind("<Configure>",
                    lambda e: settings_canvas.configure(scrollregion=settings_canvas.bbox("all")))


def scroll_settings(delta):
    if settings_inner.winfo_height() > settings_canvas.winfo_height():
        settings_canvas.yview_scroll(int(-delta / 120), "units")


def make_card(title):
    if ctk:
        card = ctk.CTkFrame(settings_inner, fg_color=CARD, border_color=EDGE,
                            border_width=1, corner_radius=14, width=10, height=10)
    else:
        card = tk.Frame(settings_inner, bg=CARD, highlightthickness=1,
                        highlightbackground=EDGE)
    card.pack(fill="x", padx=10, pady=(10, 0))
    tk.Label(card, text=title.upper(), bg=CARD, fg=MUTED,
             font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=14, pady=(12, 6))
    return card


look = make_card("Look")
tk.Label(look, text="Accent color", bg=CARD, fg=FG,
         font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=14)
swatches = tk.Canvas(look, width=300, height=40, bg=CARD, highlightthickness=0)
swatches.pack(anchor="w", padx=14, pady=(4, 12))
for i, (cname, col) in enumerate(ACCENTS.items()):
    sx = 20 + i * 44
    swatches.create_oval(sx - 14, 6, sx + 14, 34, fill=col, width=3,
                         outline="white" if cname == settings["accent"] else CARD,
                         tags=(f"sw{i}",))
    swatches.tag_bind(f"sw{i}", "<Button-1>",
                      lambda e, n=cname: custom_swatch_click() if n == "Custom" else apply_accent(n))
    swatches.tag_bind(f"sw{i}", "<Enter>", lambda e: swatches.config(cursor="hand2"))
    swatches.tag_bind(f"sw{i}", "<Leave>", lambda e: swatches.config(cursor=""))

ci = list(ACCENTS).index("Custom")
swatches.create_text(20 + ci * 44, 20, text="+", fill="white",
                     font=("Segoe UI", 14, "bold"), tags=("swplus",))
swatches.tag_bind("swplus", "<Button-1>", lambda e: custom_swatch_click())
swatches.tag_bind("swplus", "<Enter>", lambda e: swatches.config(cursor="hand2"))
swatches.tag_bind("swplus", "<Leave>", lambda e: swatches.config(cursor=""))

def save_client_id():
    value = client_entry.get().strip()
    if value and not value.isdigit():
        toast("An App ID is only numbers. Copy it from the Developer Portal.", False)
        return
    settings["client_id"] = value
    write_settings()
    for n in list(rpc):
        rpc_clear(n)
    toast("App ID saved." if value else "App ID removed.")


acct = make_card("Accounts")
tk.Label(acct, text="App ID", bg=CARD, fg=FG,
         font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=14)
tk.Label(acct, text="Developer Portal > your app > Application ID",
         bg=CARD, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=14)
id_row = tk.Frame(acct, bg=CARD)
id_row.pack(fill="x", padx=14, pady=(6, 12))
id_row.columnconfigure(0, weight=1)
client_entry = make_entry(id_row)
client_entry.grid(row=0, column=0, sticky="ew", ipady=5)
client_entry.insert(0, settings.get("client_id", ""))
client_entry.bind("<Return>", lambda e: save_client_id())
HoverButton(id_row, "Save", save_client_id).grid(row=0, column=1, padx=(8, 0))

tk.Label(acct, text="User ID", bg=CARD, fg=FG,
         font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=14)
tk.Label(acct, text="Right-click your name in Discord > Copy User ID",
         bg=CARD, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=14)
user_id_row = tk.Frame(acct, bg=CARD)
user_id_row.pack(fill="x", padx=14, pady=(6, 0))
user_id_row.columnconfigure(0, weight=1)
user_id_entry = make_entry(user_id_row)
user_id_entry.grid(row=0, column=0, sticky="ew", ipady=5)
user_id_entry.insert(0, settings.get("user_id", ""))
user_id_entry.bind("<Return>", lambda e: save_user_id())
HoverButton(user_id_row, "Save", save_user_id).grid(row=0, column=1, padx=(8, 0))
link_row = tk.Frame(acct, bg=CARD)
link_row.pack(anchor="w", padx=14, pady=(6, 12))
HoverButton(link_row, text="Copy profile link", color="#2a2a3a",
            command=copy_profile_link).pack(side="left", padx=(0, 6))
HoverButton(link_row, text="Open profile", color="#2a2a3a",
            command=open_profile_link).pack(side="left")


tk.Label(acct, text="Saved accounts", bg=CARD, fg=FG,
         font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=14)
tk.Label(acct, text="Fill in the App ID and User ID above, name it, then save",
         bg=CARD, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=14)
acc_row = tk.Frame(acct, bg=CARD)
acc_row.pack(fill="x", padx=14, pady=(6, 0))
acc_row.columnconfigure(0, weight=1)
account_name_entry = make_entry(acc_row)
account_name_entry.grid(row=0, column=0, sticky="ew", ipady=5)
account_name_entry.bind("<Return>", lambda e: save_account())
HoverButton(acc_row, "Save account", save_account).grid(row=0, column=1, padx=(8, 0))
accounts_frame = tk.Frame(acct, bg=CARD)
accounts_frame.pack(fill="x", padx=14, pady=(8, 12))
refresh_accounts()

gen = make_card("General")
tk.Label(gen, text="Hotkey (toggle last game)", bg=CARD, fg=FG,
         font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=14)
hotkey_row = tk.Frame(gen, bg=CARD)
hotkey_row.pack(anchor="w", padx=14, pady=(4, 0))
hotkey_entry = make_entry(hotkey_row)
hotkey_entry.insert(0, settings["hotkey"])
hotkey_entry.pack(side="left", ipady=5)
HoverButton(hotkey_row, text="Save", command=save_hotkey).pack(side="left", padx=(6, 0))
tk.Label(gen, text='example: <ctrl>+<alt>+g', bg=CARD, fg=MUTED,
         font=("Segoe UI", 8)).pack(anchor="w", padx=14, pady=(2, 10))

tk.Label(gen, text="Sound (When running a game)", bg=CARD, fg=FG,
         font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=14)
sound_btn = HoverButton(gen, text=f"Sound: {'On' if settings['sound'] else 'Off'}",
                        command=toggle_sound, color="#2a2a3a")
sound_btn.pack(anchor="w", padx=14, pady=(4, 10))

tk.Label(gen, text="Streamer Mode", bg=CARD, fg=FG,
         font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=14)
tk.Label(gen, text="Hides your User ID.", bg=CARD, fg=MUTED,
         font=("Segoe UI", 8)).pack(anchor="w", padx=14)
streamer_btn = HoverButton(
    gen,
    text=f"Streamer Mode: {'On' if settings['streamer_mode'] else 'Off'}",
    command=toggle_streamer_mode, color="#2a2a3a")
streamer_btn.pack(anchor="w", padx=14, pady=(4, 12))


tk.Frame(settings_inner, bg=BG, height=20).pack()

# --- status tab
status_page = tabs.page("Status")

status_canvas = tk.Canvas(status_page, bg=BG, highlightthickness=0)
status_canvas.pack(fill="both", expand=True)
status_inner = tk.Frame(status_canvas, bg=BG)
status_win = status_canvas.create_window(0, 0, window=status_inner, anchor="nw")
status_canvas.bind("<Configure>",
                   lambda e: status_canvas.itemconfig(status_win, width=e.width))
status_inner.bind("<Configure>",
                  lambda e: status_canvas.configure(scrollregion=status_canvas.bbox("all")))


def scroll_status(delta):
    if status_inner.winfo_height() > status_canvas.winfo_height():
        status_canvas.yview_scroll(int(-delta / 120), "units")


tk.Label(status_inner, text="Pick a game in 'Running now' first.", bg=BG, fg=MUTED,
         font=("Segoe UI", 9)).pack(anchor="w", padx=10, pady=(10, 0))

form = tk.Frame(status_inner, bg=BG)
form.pack(fill="x", padx=10, pady=(6, 4))
form.columnconfigure(1, weight=1)
tk.Label(form, text="Line 1", bg=BG, fg=FG, font=("Segoe UI", 10)).grid(
    row=0, column=0, sticky="w", padx=(0, 8), pady=4)
details_entry = make_entry(form)
details_entry.grid(row=0, column=1, sticky="ew", ipady=5)
tk.Label(form, text="Line 2", bg=BG, fg=FG, font=("Segoe UI", 10)).grid(
    row=1, column=0, sticky="w", padx=(0, 8), pady=4)
state_entry = make_entry(form)
state_entry.grid(row=1, column=1, sticky="ew", ipady=5)
tk.Label(form, text="Party", bg=BG, fg=FG, font=("Segoe UI", 10)).grid(
    row=2, column=0, sticky="w", padx=(0, 8), pady=4)
party_row = tk.Frame(form, bg=BG)
party_row.grid(row=2, column=1, sticky="w")
cur_entry = make_entry(party_row)
cur_entry.config(width=4, justify="center")
cur_entry.pack(side="left", ipady=4)
tk.Label(party_row, text="of", bg=BG, fg=MUTED, font=("Segoe UI", 10)).pack(side="left", padx=6)
max_entry = make_entry(party_row)
max_entry.config(width=4, justify="center")
max_entry.pack(side="left", ipady=4)

presets = tk.Frame(status_inner, bg=BG)
presets.pack(pady=(4, 0))
rotate_vars = []
for i, (label, d, s, p) in enumerate(PRESETS):
    row = tk.Frame(presets, bg=BG)
    row.grid(row=i // 2, column=i % 2, padx=4, pady=4)
    var = tk.BooleanVar(value=False)
    tk.Checkbutton(row, variable=var, bg=BG, activebackground=BG,
                   fg="white", activeforeground="white",
                   selectcolor=INPUT, bd=0, highlightthickness=0).pack(side="left")
    HoverButton(row, text=label, color="#2a2a3a",
                command=lambda d=d, s=s, p=p: use_preset(d, s, p)).pack(side="left")
    rotate_vars.append((var, d, s, p))

rotate_row = tk.Frame(status_inner, bg=BG)
rotate_row.pack(pady=(6, 0))
tk.Label(rotate_row, text="every", bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(side="left")
rotate_seconds = make_entry(rotate_row)
rotate_seconds.config(width=4, justify="center")
rotate_seconds.insert(0, "20")
rotate_seconds.pack(side="left", padx=6, ipady=3)
tk.Label(rotate_row, text="sec", bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(side="left")
rotate_btn = HoverButton(rotate_row, text="Start rotation", color="#2a2a3a",
                         command=lambda: toggle_rotation())
rotate_btn.pack(side="left", padx=(10, 0))

rand_row1 = tk.Frame(status_inner, bg=BG)
rand_row1.pack(pady=(8, 0))
tk.Label(rand_row1, text="Random party:  min", bg=BG, fg=MUTED,
         font=("Segoe UI", 9)).pack(side="left")
rand_min = make_entry(rand_row1)
rand_min.config(width=3, justify="center")
rand_min.insert(0, "2")
rand_min.pack(side="left", padx=6, ipady=3)
tk.Label(rand_row1, text="(max = the 'of' box)", bg=BG, fg=MUTED,
         font=("Segoe UI", 9)).pack(side="left")

rand_row2 = tk.Frame(status_inner, bg=BG)
rand_row2.pack(pady=(4, 0))
tk.Label(rand_row2, text="every", bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(side="left")
rand_every = make_entry(rand_row2)
rand_every.config(width=4, justify="center")
rand_every.insert(0, "30")
rand_every.pack(side="left", padx=6, ipady=3)
rand_unit_btn = HoverButton(rand_row2, text="sec", color="#2a2a3a",
                            command=lambda: toggle_rand_unit())
rand_unit_btn.pack(side="left")
rand_btn = HoverButton(rand_row2, text="Start random", color="#2a2a3a",
                       command=lambda: toggle_party_random())
rand_btn.pack(side="left", padx=(10, 0))

tk.Label(status_inner, text="Live preview", bg=BG, fg=MUTED,
         font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=10, pady=(12, 2))
preview_frame = tk.Frame(status_inner, bg="#1e1f27", highlightthickness=1, highlightbackground=EDGE)
preview_frame.pack(fill="x", padx=10, pady=(0, 6))
preview_row = tk.Frame(preview_frame, bg="#1e1f27")
preview_row.pack(fill="x", padx=10, pady=10)
preview_icon_holder = tk.Frame(preview_row, width=48, height=48, bg=ACCENT)
preview_icon_holder.pack(side="left")
preview_icon_holder.pack_propagate(False)
preview_icon = tk.Label(preview_icon_holder, text="?", fg="white", bg=ACCENT,
                        font=("Segoe UI", 16, "bold"))
preview_icon.place(relx=0.5, rely=0.5, anchor="center")
preview_text = tk.Frame(preview_row, bg="#1e1f27")
preview_text.pack(side="left", fill="both", expand=True, padx=(10, 0))
preview_name = tk.Label(preview_text, text="Pick a running game", bg="#1e1f27", fg=FG,
                        anchor="w", font=("Segoe UI", 10, "bold"))
preview_name.pack(fill="x")
preview_details = tk.Label(preview_text, text="", bg="#1e1f27", fg=MUTED,
                           anchor="w", font=("Segoe UI", 9), wraplength=220, justify="left")
preview_details.pack(fill="x")
preview_state = tk.Label(preview_text, text="", bg="#1e1f27", fg=MUTED,
                         anchor="w", font=("Segoe UI", 9), wraplength=220, justify="left")
preview_state.pack(fill="x")


def update_preview(event=None):
    name = running_cards.selected
    if name not in running:
        preview_name.config(text="Pick a running game")
        preview_details.config(text="")
        preview_state.config(text="")
        preview_icon.config(image="", text="?", bg=ACCENT)
        preview_icon.image = None
        preview_icon_holder.config(bg=ACCENT)
        return
    preview_name.config(text=name)
    url = settings["icons"].get(name)
    if url:
        def apply_icon(img):
            try:
                preview_icon.config(image=img, text="")
                preview_icon.image = img
                preview_icon_holder.config(bg="#1e1f27")
            except tk.TclError:
                pass
        fetch_icon(url, apply_icon)
    else:
        preview_icon.config(image="", text=name[:1].upper(), bg=ACCENT)
        preview_icon.image = None
        preview_icon_holder.config(bg=ACCENT)
    details = details_entry.get().strip()
    state = state_entry.get().strip()
    cur, top_size = cur_entry.get().strip(), max_entry.get().strip()
    elapsed = fmt_time(time.time() - running[name]["start"])
    preview_details.config(text=f"{details or 'Playing'}  ·  {elapsed} elapsed")
    party = f"  ({cur} of {top_size})" if cur.isdigit() and top_size.isdigit() else ""
    preview_state.config(text=(state + party) if (state or party) else "")


for field in (details_entry, state_entry, cur_entry, max_entry):
    field.bind("<KeyRelease>", update_preview)
update_preview()

action_row = tk.Frame(status_inner, bg=BG)
action_row.pack(pady=(8, 16))
HoverButton(action_row, text="Apply", command=apply_status).pack(side="left", padx=4)
HoverButton(action_row, text="Clear", command=clear_status, color=RED).pack(side="left", padx=4)


# toast, drawn above everything
toast_box = tk.Frame(root, bg=TOAST_BG, highlightthickness=1, highlightbackground=ACCENT)
toast_dot = tk.Label(toast_box, text="●", bg=TOAST_BG, fg=GREEN, font=("Segoe UI", 10))
toast_dot.pack(side="left", padx=(12, 6), pady=8)
toast_label = tk.Label(toast_box, text="", bg=TOAST_BG, fg="white", font=("Segoe UI", 10),
                       wraplength=290, justify="left", anchor="w")
toast_label.pack(side="left", fill="x", expand=True, padx=(0, 14), pady=8)
toast_box.place(relx=0.5, y=-70, anchor="n", width=360)

root.bind_all("<Motion>", on_motion)
root.bind_all("<MouseWheel>", on_wheel)
root.protocol("WM_DELETE_WINDOW", on_close)

load_saved()
load_recent()
refresh_saved()
refresh_recent()
results_list.set_items([])
detect_running()
apply_streamer_mode()
threading.Thread(target=load_apps, daemon=True).start()

animate()
animate_orbs()
animate_confetti()
tick_timers()
start_tray()
start_hotkey_listener()
start_bridge_server()
show_splash()
root.mainloop()