"""
INCIZO AI v3.0 — Elite Trading Intelligence
Cut through the noise. Win more. Lose less.
"""

import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
import threading
import time
import base64
import io
import json
import os
import re
if os.name == 'nt':
    import winsound
else:
    winsound = None
from datetime import datetime
from PIL import Image, ImageTk, ImageGrab
import urllib.request

# ─── CONSTANTS ───────────────────────────────────────────────────
VERSION     = "3.0.0"
APP_NAME    = "INCIZO AI"
CONFIG_FILE = "incizo_config.json"
PAIRS       = ["BTC/USD","ETH/USD","SOL/USD","BNB/USD","XRP/USD","GOLD","NAS100"]

# ─── COLORS — Elite dark palette ─────────────────────────────────
BG      = "#000000"
BG1     = "#0A0A0A"
BG2     = "#111111"
BG3     = "#1A1A1A"
BG4     = "#222222"
BORDER  = "#2C2C2E"
GREEN   = "#30D158"
RED     = "#FF453A"
AMBER   = "#FFD60A"
BLUE    = "#0A84FF"
PURPLE  = "#BF5AF2"
WHITE   = "#F2F2F7"
GRAY    = "#8E8E93"
DIM     = "#3A3A3C"

# ─── FONTS ───────────────────────────────────────────────────────
F_TITLE  = ("Helvetica Neue", 20, "bold")
F_HEAD   = ("Helvetica Neue", 15, "bold")
F_BODY   = ("Helvetica Neue", 13)
F_BODY_B = ("Helvetica Neue", 13, "bold")
F_SMALL  = ("Helvetica Neue", 11)
F_SMALL_B= ("Helvetica Neue", 11, "bold")
F_MONO   = ("Menlo", 12)
F_MONO_S = ("Menlo", 11)
F_MONO_L = ("Menlo", 14)

# ─── SYSTEM PROMPTS ──────────────────────────────────────────────
CHART_PROMPT = """You are INCIZO — an elite institutional crypto trader with $3M+ in verified profits. You read charts like a surgeon.

ANALYSIS RULES:
- Only signal LONG or SHORT when 3+ indicators align. Otherwise say WAIT.
- Never signal consecutive trades — trader needs time to execute properly
- Quality over quantity — 1 perfect trade beats 10 mediocre ones
- Always protect the funded account first

INDICATORS TO CHECK (in order of importance):
1. RSI (14) — overbought >70, oversold <30, divergence
2. EMA 9/21 crossover — trend direction and momentum
3. VWAP — price above = bullish bias, below = bearish bias  
4. Support/Resistance — key horizontal levels
5. Volume — confirm moves with volume spike
6. Candle pattern — engulfing, doji, pin bar, inside bar
7. Market structure — higher highs/lows or lower highs/lows

Respond in this EXACT format — clean, no extra text:

━━━ INCIZO SIGNAL ━━━
BIAS: [LONG / SHORT / WAIT]
CONFIDENCE: [HIGH / MEDIUM / LOW]
PRICE: [$XX,XXX]

━━━ INDICATORS ━━━
RSI: [value] [▲/▼/─] [status]
EMA: [9/21 position — above/below/crossing]
STRUCTURE: [bullish/bearish/ranging]
PATTERN: [candle pattern or NONE]
VOLUME: [high/normal/low]

━━━ TRADE SETUP ━━━
ENTRY: [$XX,XXX — exact trigger]
STOP LOSS: [$XX,XXX]
TARGET: [$XX,XXX]
R:R RATIO: [1:X]

━━━ VERDICT ━━━
[2-3 sentences max. Direct. No fluff. Tell the trader exactly what to do and why.]

WAIT CRITERIA — say WAIT if:
- RSI between 45-55 (no edge)
- Price mid-range with no clear direction
- Less than 2 indicators align
- Recent signal within last 3 scans"""

MARCUS_PROMPT = """You are Marcus Reed — a professional crypto trader with $1M+ in verified profits over 10 years. You mentor funded account traders.

PERSONALITY:
- Direct and honest. No hype. No fluff.
- You speak like a seasoned pro who's seen it all
- Short sharp answers — max 3-4 sentences unless explaining a concept
- You call out bad habits and emotional trading immediately
- You reference real trading concepts naturally
- Occasionally motivating but always brutally honest

TRADER CONTEXT:
- $5,000 Hydrotrader funded account
- Trading BTC/USD on 5M chart  
- Target: $500 profit (10%)
- Daily loss limit: $200 (4%)
- Max risk per trade: $50 (1%)
- Platform: CLEO

RULES YOU ENFORCE:
- Never risk more than 1% per trade
- Stop after 2 losses in a day
- Quality setups only — wait for confluence
- Protect the account above everything

Answer their question like a mentor sitting right next to them."""

# ─── CONFIG ──────────────────────────────────────────────────────
class Config:
    defaults = {
        "api_key": "", "account_size": 5000,
        "max_risk_pct": 1, "daily_loss_pct": 4,
        "target_pct": 10, "scan_interval": 30,
        "sound_alerts": True
    }
    def __init__(self):
        self.data = self.defaults.copy()
        self.load()
    def load(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE) as f:
                    self.data.update(json.load(f))
        except: pass
    def save(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.data, f, indent=2)
        except: pass
    def get(self, k): return self.data.get(k, self.defaults.get(k))
    def set(self, k, v): self.data[k] = v; self.save()

# ─── CLAUDE API ──────────────────────────────────────────────────
def call_claude(api_key, prompt, image_b64=None, system=None):
    url = "https://api.anthropic.com/v1/messages"
    content = []
    if image_b64:
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/jpeg", "data": image_b64}
        })
    content.append({"type": "text", "text": prompt})
    payload = {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": content}]
    }
    if system:
        payload["system"] = system
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data,
        headers={
            'Content-Type': 'application/json',
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01'
        }, method='POST')
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode('utf-8'))
        return result['content'][0]['text']

# ─── MAIN APP ────────────────────────────────────────────────────
class IncizoApp:
    def __init__(self, root):
        self.root = root
        self.config = Config()
        self.api_key = self.config.get("api_key")
        self.running = False
        self.scan_count = 0
        self.last_signal_scan = 0
        self.chat_history = []

        self.root.title(f"INCIZO AI  v{VERSION}")
        self.root.geometry("560x860")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)
        self.root.attributes('-topmost', True)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()
        self._start_clock()

        if self.api_key:
            self._log("✓  Claude AI connected — ready to trade.\n", "ok")

    # ─── BUILD UI ────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self.root, bg=BG, pady=14)
        hdr.pack(fill="x", padx=20)

        left = tk.Frame(hdr, bg=BG)
        left.pack(side="left")

        row1 = tk.Frame(left, bg=BG)
        row1.pack(anchor="w")

        self.dot = tk.Canvas(row1, width=10, height=10, bg=BG, highlightthickness=0)
        self.dot.pack(side="left", padx=(0,8), pady=(4,0))
        self.dot_id = self.dot.create_oval(1,1,9,9, fill=DIM, outline="")

        tk.Label(row1, text="INCIZO", font=("Helvetica Neue", 22, "bold"),
                fg=WHITE, bg=BG).pack(side="left")
        tk.Label(row1, text=f"  AI  v{VERSION}", font=F_SMALL,
                fg=DIM, bg=BG).pack(side="left", pady=(5,0))

        tk.Label(left, text="ELITE TRADING INTELLIGENCE  ·  FUNDED TRADER EDITION",
                font=("Helvetica Neue", 9), fg=DIM, bg=BG).pack(anchor="w", pady=(3,0))

        right = tk.Frame(hdr, bg=BG)
        right.pack(side="right", anchor="n")
        self.clock = tk.Label(right, text="--:-- UTC",
                             font=F_MONO_S, fg=GREEN,
                             bg=BG1, padx=12, pady=6,
                             relief="flat")
        self.clock.pack()

        # Separator
        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x")

        # Notebook
        style = ttk.Style()
        style.theme_use('default')
        style.configure('E.TNotebook', background=BG, borderwidth=0, tabmargins=[0,0,0,0])
        style.configure('E.TNotebook.Tab',
            background=BG1, foreground=GRAY,
            padding=[22, 11], font=F_SMALL_B,
            borderwidth=0)
        style.map('E.TNotebook.Tab',
            background=[('selected', BG2)],
            foreground=[('selected', WHITE)])

        self.nb = ttk.Notebook(self.root, style='E.TNotebook')
        self.nb.pack(fill="both", expand=True)

        self.tab_watch    = tk.Frame(self.nb, bg=BG)
        self.tab_chat     = tk.Frame(self.nb, bg=BG)
        self.tab_indicators = tk.Frame(self.nb, bg=BG)
        self.tab_settings = tk.Frame(self.nb, bg=BG)

        self.nb.add(self.tab_watch,      text="  WATCH  ")
        self.nb.add(self.tab_chat,       text="  MARCUS  ")
        self.nb.add(self.tab_indicators, text="  INDICATORS  ")
        self.nb.add(self.tab_settings,   text="  SETTINGS  ")

        self._build_watch()
        self._build_chat()
        self._build_indicators()
        self._build_settings()

    def _build_watch(self):
        t = self.tab_watch

        # Signal cards
        cards = tk.Frame(t, bg=BG, padx=14, pady=12)
        cards.pack(fill="x")

        self.c_bias  = self._signal_card(cards, "BIAS",       "—",  WHITE)
        self.c_conf  = self._signal_card(cards, "CONFIDENCE", "—",  WHITE)
        self.c_rsi   = self._signal_card(cards, "RSI",        "—",  WHITE)
        self.c_scans = self._signal_card(cards, "SCANS",      "0",  WHITE)

        tk.Frame(t, bg=BORDER, height=1).pack(fill="x")

        # Controls
        ctrl = tk.Frame(t, bg=BG, padx=14, pady=12)
        ctrl.pack(fill="x")

        row1 = tk.Frame(ctrl, bg=BG)
        row1.pack(fill="x", pady=(0,10))

        tk.Label(row1, text="Pair", font=F_SMALL_B, fg=GRAY, bg=BG).pack(side="left")
        self.pair_var = tk.StringVar(value="BTC/USD")
        pair_cb = ttk.Combobox(row1, textvariable=self.pair_var,
            values=PAIRS, width=10, state="readonly", font=F_BODY)
        pair_cb.pack(side="left", padx=(8,20))

        tk.Label(row1, text="Scan every", font=F_SMALL_B, fg=GRAY, bg=BG).pack(side="left")
        self.interval_var = tk.StringVar(value="30")
        int_cb = ttk.Combobox(row1, textvariable=self.interval_var,
            values=["15","30","45","60","90","120"],
            width=4, state="readonly", font=F_BODY)
        int_cb.pack(side="left", padx=(8,6))
        tk.Label(row1, text="sec", font=F_SMALL_B, fg=GRAY, bg=BG).pack(side="left")

        row2 = tk.Frame(ctrl, bg=BG)
        row2.pack(fill="x")

        self.start_btn = tk.Button(row2,
            text="▶  START WATCHING",
            font=F_BODY_B, bg=GREEN, fg="#000",
            relief="flat", bd=0, padx=16, pady=12,
            cursor="hand2", command=self.toggle_watching)
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0,8))

        self.snap_btn = tk.Button(row2,
            text="📷  SNAP",
            font=F_BODY, bg=BG3, fg=WHITE,
            relief="flat", bd=0, padx=16, pady=12,
            cursor="hand2", command=self.manual_scan)
        self.snap_btn.pack(side="left")

        self.cd_label = tk.Label(t, text="",
            font=F_SMALL_B, fg=DIM, bg=BG)
        self.cd_label.pack(pady=(4,0))

        tk.Frame(t, bg=BORDER, height=1).pack(fill="x", pady=(6,0))

        # Preview
        prev = tk.Frame(t, bg=BG, padx=14, pady=8)
        prev.pack(fill="x")
        tk.Label(prev, text="SCREEN PREVIEW", font=F_SMALL_B, fg=GRAY, bg=BG).pack(anchor="w")

        self.preview = tk.Label(t, bg=BG1, text="Waiting for first scan…",
            font=F_BODY, fg=DIM)
        self.preview.pack(padx=14, fill="x")

        tk.Frame(t, bg=BORDER, height=1).pack(fill="x", pady=(8,0))

        # Analysis
        ana = tk.Frame(t, bg=BG, padx=14, pady=8)
        ana.pack(fill="x")
        ana_row = tk.Frame(ana, bg=BG)
        ana_row.pack(fill="x")
        tk.Label(ana_row, text="AI ANALYSIS", font=F_SMALL_B, fg=GRAY, bg=BG).pack(side="left")
        self.ts_label = tk.Label(ana_row, text="", font=F_MONO_S, fg=DIM, bg=BG)
        self.ts_label.pack(side="right")

        self.analysis = scrolledtext.ScrolledText(t,
            font=F_MONO, bg=BG1, fg=WHITE,
            insertbackground=GREEN,
            relief="flat", bd=0,
            padx=16, pady=14,
            wrap=tk.WORD, height=12,
            spacing1=2, spacing2=4, spacing3=2)
        self.analysis.pack(fill="both", expand=True, padx=14, pady=(0,10))

        # Text tags
        self.analysis.tag_config("ok",     foreground=GREEN,  font=F_MONO)
        self.analysis.tag_config("bad",    foreground=RED,    font=F_MONO)
        self.analysis.tag_config("warn",   foreground=AMBER,  font=F_MONO)
        self.analysis.tag_config("head",   foreground=BLUE,   font=("Menlo", 12, "bold"))
        self.analysis.tag_config("purple", foreground=PURPLE, font=("Menlo", 12, "bold"))
        self.analysis.tag_config("dim",    foreground=DIM,    font=F_MONO)
        self.analysis.tag_config("white",  foreground=WHITE,  font=F_MONO)
        self.analysis.tag_config("sep",    foreground=BG3,    font=F_MONO)

        self._log("INCIZO AI v3.0  —  Elite Trading Intelligence\n\n", "head")
        self._log("Powered by Claude AI — the most accurate chart reader available.\n", "white")
        self._log("Add your API key in Settings, then click Start Watching.\n\n", "dim")
        self._log("SIGNAL LOGIC:\n", "purple")
        self._log("• Minimum 3 indicators must align before a signal fires\n", "white")
        self._log("• 30 second minimum between scans — quality over speed\n", "white")
        self._log("• WAIT is the most common signal — that's correct behaviour\n", "white")
        self._log("• Only take HIGH confidence signals on funded accounts\n\n", "white")

    def _build_chat(self):
        t = self.tab_chat

        # Header
        hdr = tk.Frame(t, bg=BG2, padx=16, pady=14)
        hdr.pack(fill="x")

        top = tk.Frame(hdr, bg=BG2)
        top.pack(fill="x")
        tk.Label(top, text="MARCUS REED", font=F_HEAD, fg=WHITE, bg=BG2).pack(side="left")

        status = tk.Frame(hdr, bg=BG2)
        status.pack(anchor="w", pady=(6,0))
        tk.Canvas(status, width=8, height=8, bg=BG2, highlightthickness=0).pack(side="left", padx=(0,6), pady=2)
        self._draw_dot(status, GREEN)
        tk.Label(status, text="Online  ·  $1M+ verified profits  ·  10 years trading",
                font=F_SMALL, fg=GREEN, bg=BG2).pack(side="left")

        tk.Label(hdr, text="Elite crypto trader. Brutally honest mentor. Asks nothing. Tells you everything.",
                font=F_SMALL, fg=GRAY, bg=BG2).pack(anchor="w", pady=(4,0))

        tk.Frame(t, bg=BORDER, height=1).pack(fill="x")

        # Chat box
        self.chat = scrolledtext.ScrolledText(t,
            font=F_BODY, bg=BG, fg=WHITE,
            insertbackground=WHITE,
            relief="flat", bd=0,
            padx=16, pady=14,
            wrap=tk.WORD, height=18,
            spacing1=2, spacing2=6, spacing3=4,
            state="disabled")
        self.chat.pack(fill="both", expand=True)

        self.chat.tag_config("marcus_name", foreground=GREEN,  font=F_BODY_B)
        self.chat.tag_config("you_name",    foreground=BLUE,   font=F_BODY_B)
        self.chat.tag_config("marcus_msg",  foreground="#D0F5E8", font=F_BODY)
        self.chat.tag_config("you_msg",     foreground=WHITE,  font=F_BODY)
        self.chat.tag_config("time",        foreground=DIM,    font=F_SMALL)
        self.chat.tag_config("thinking",    foreground=AMBER,  font=("Helvetica Neue", 12, "italic"))

        # Welcome
        self._chat("marcus_name", "\nMARCUS REED\n")
        self._chat("marcus_msg",
            "Yo. Marcus here. 10 years in the markets, over a million in profits. "
            "I've seen traders blow funded accounts in a day and I've seen them turn $5K into $50K.\n\n"
            "Every time you message me I can see your screen — so I'll tell you exactly "
            "what I see on your chart and what I'd do. No guessing.\n\n"
            "Ask me anything. I'll give it to you straight.\n\n")

        # Quick questions
        qs_frame = tk.Frame(t, bg=BG1, padx=12, pady=10)
        qs_frame.pack(fill="x")
        tk.Label(qs_frame, text="Quick ask:", font=F_SMALL_B, fg=GRAY, bg=BG1).pack(anchor="w", pady=(0,8))

        qs_row = tk.Frame(qs_frame, bg=BG1)
        qs_row.pack(fill="x")

        questions = [
            "What do you see on my chart?",
            "Should I enter this trade?",
            "I just took a loss, now what?",
            "Is this a good setup?",
        ]
        for q in questions:
            tk.Button(qs_row, text=q,
                font=F_SMALL, bg=BG3, fg=GRAY,
                relief="flat", bd=0, padx=10, pady=6,
                cursor="hand2",
                command=lambda x=q: self._prefill(x)).pack(side="left", padx=(0,6))

        tk.Frame(t, bg=BORDER, height=1).pack(fill="x")

        # Input
        inp = tk.Frame(t, bg=BG1, padx=14, pady=10)
        inp.pack(fill="x")

        self.chat_entry = tk.Entry(inp,
            font=F_BODY, bg=BG2, fg=WHITE,
            insertbackground=WHITE,
            relief="flat", bd=0)
        self.chat_entry.pack(side="left", fill="x", expand=True, padx=(0,10), ipady=11, ipadx=12)
        self.chat_entry.bind("<Return>", lambda e: self._send())
        self.chat_entry.insert(0, "Ask Marcus anything about your trade…")
        self.chat_entry.config(fg=DIM)
        self.chat_entry.bind("<FocusIn>",  self._focus_in)
        self.chat_entry.bind("<FocusOut>", self._focus_out)

        self.send_btn = tk.Button(inp,
            text="SEND",
            font=F_BODY_B, bg=GREEN, fg="#000",
            relief="flat", bd=0, padx=20, pady=11,
            cursor="hand2", command=self._send)
        self.send_btn.pack(side="left")

    def _build_indicators(self):
        t = self.tab_indicators

        # Header
        hdr = tk.Frame(t, bg=BG, padx=20, pady=16)
        hdr.pack(fill="x")
        tk.Label(hdr, text="INDICATOR GUIDE", font=F_HEAD, fg=WHITE, bg=BG).pack(anchor="w")
        tk.Label(hdr, text="The exact indicators INCIZO AI reads on every scan",
                font=F_SMALL, fg=GRAY, bg=BG).pack(anchor="w", pady=(4,0))

        tk.Frame(t, bg=BORDER, height=1).pack(fill="x")

        # Scrollable content
        canvas = tk.Canvas(t, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(t, orient="vertical", command=canvas.yview)
        frame = tk.Frame(canvas, bg=BG)

        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        indicators = [
            {
                "rank": "01",
                "name": "RSI (14)",
                "color": GREEN,
                "signal": "Primary momentum indicator",
                "how": "Measures speed and magnitude of price movements on a 0-100 scale.",
                "read": [
                    ("Above 70", "Overbought — look for SHORT", RED),
                    ("Below 30", "Oversold — look for LONG", GREEN),
                    ("45–55", "No edge — WAIT for clearer signal", AMBER),
                    ("Divergence", "Price makes new high but RSI doesn't = reversal signal", PURPLE),
                ],
                "tip": "RSI alone is not enough. Wait for price confirmation before entering."
            },
            {
                "rank": "02",
                "name": "EMA 9 / EMA 21",
                "color": BLUE,
                "signal": "Trend direction + momentum",
                "how": "Two exponential moving averages. When 9 crosses above 21 = bullish. Below = bearish.",
                "read": [
                    ("9 above 21", "Bullish momentum — favor LONG", GREEN),
                    ("9 below 21", "Bearish momentum — favor SHORT", RED),
                    ("Crossover happening", "Potential trend change — HIGH priority signal", AMBER),
                    ("Price far from EMAs", "Likely to revert — wait for pullback", PURPLE),
                ],
                "tip": "The 9/21 crossover on the 5M is your trend filter. Never trade against it."
            },
            {
                "rank": "03",
                "name": "VWAP",
                "color": PURPLE,
                "signal": "Institutional price benchmark",
                "how": "Volume Weighted Average Price. Where institutions are buying/selling.",
                "read": [
                    ("Price above VWAP", "Bullish — institutions holding longs", GREEN),
                    ("Price below VWAP", "Bearish — institutions holding shorts", RED),
                    ("Price at VWAP", "Decision zone — wait for breakout", AMBER),
                    ("Bounce off VWAP", "Strong support/resistance — trade the bounce", BLUE),
                ],
                "tip": "VWAP resets daily. Most reliable in the first 2 hours of a session."
            },
            {
                "rank": "04",
                "name": "Support & Resistance",
                "color": AMBER,
                "signal": "Key price levels",
                "how": "Horizontal levels where price has previously reversed or consolidated.",
                "read": [
                    ("Price at support", "Potential LONG — watch for bounce candle", GREEN),
                    ("Price at resistance", "Potential SHORT — watch for rejection candle", RED),
                    ("Level broken + retest", "Strong signal in direction of break", BLUE),
                    ("Multiple touches", "Stronger level — more reliable signal", PURPLE),
                ],
                "tip": "Round numbers ($77,000 / $78,000) are the strongest levels on BTC."
            },
            {
                "rank": "05",
                "name": "Volume",
                "color": GRAY,
                "signal": "Confirmation indicator",
                "how": "Number of contracts traded. High volume confirms moves. Low volume = weak signal.",
                "read": [
                    ("High volume + price up", "Strong bullish move — confirmed LONG", GREEN),
                    ("High volume + price down", "Strong bearish move — confirmed SHORT", RED),
                    ("Low volume + breakout", "Fake breakout — WAIT for confirmation", AMBER),
                    ("Volume spike", "Institutional activity — potential reversal incoming", PURPLE),
                ],
                "tip": "Never enter a breakout on low volume. It's almost always a fake."
            },
            {
                "rank": "06",
                "name": "Candle Patterns",
                "color": WHITE,
                "signal": "Entry timing",
                "how": "Specific candle formations that signal reversals or continuation.",
                "read": [
                    ("Bullish engulfing", "Strong reversal — LONG signal", GREEN),
                    ("Bearish engulfing", "Strong reversal — SHORT signal", RED),
                    ("Pin bar / hammer", "Rejection of level — trade in direction of tail", AMBER),
                    ("Inside bar", "Consolidation — wait for breakout of range", BLUE),
                    ("Doji at S/R", "Indecision at key level — next candle decides", PURPLE),
                ],
                "tip": "On 5M charts, only engulfing candles and pin bars are reliable. Ignore everything else."
            },
            {
                "rank": "07",
                "name": "Market Structure",
                "color": BLUE,
                "signal": "Higher timeframe context",
                "how": "Pattern of highs and lows that defines the overall trend.",
                "read": [
                    ("Higher highs + higher lows", "Uptrend — only take LONG signals", GREEN),
                    ("Lower highs + lower lows", "Downtrend — only take SHORT signals", RED),
                    ("Equal highs/lows", "Ranging — avoid until breakout", AMBER),
                    ("Break of structure", "Potential trend change — HIGH alert", PURPLE),
                ],
                "tip": "Check the 1H and 4H structure before taking any 5M trade. Trade with the bigger trend."
            },
        ]

        for ind in indicators:
            self._ind_card(frame, ind)

    def _ind_card(self, parent, ind):
        card = tk.Frame(parent, bg=BG1, padx=18, pady=16)
        card.pack(fill="x", padx=14, pady=(10,0))

        # Header row
        top = tk.Frame(card, bg=BG1)
        top.pack(fill="x", pady=(0,10))

        rank_bg = tk.Label(top, text=ind["rank"],
            font=("Menlo", 11, "bold"), fg=BG1,
            bg=ind["color"], padx=8, pady=3)
        rank_bg.pack(side="left", padx=(0,12))

        name_col = tk.Frame(top, bg=BG1)
        name_col.pack(side="left")
        tk.Label(name_col, text=ind["name"],
                font=F_BODY_B, fg=WHITE, bg=BG1).pack(anchor="w")
        tk.Label(name_col, text=ind["signal"],
                font=F_SMALL, fg=ind["color"], bg=BG1).pack(anchor="w")

        # How it works
        tk.Label(card, text=ind["how"],
                font=F_SMALL, fg=GRAY, bg=BG1,
                wraplength=480, justify="left").pack(anchor="w", pady=(0,10))

        # Readings
        for label, meaning, color in ind["read"]:
            row = tk.Frame(card, bg=BG2, padx=10, pady=6)
            row.pack(fill="x", pady=(0,4))
            tk.Label(row, text=label, font=F_SMALL_B, fg=color, bg=BG2, width=24, anchor="w").pack(side="left")
            tk.Label(row, text=meaning, font=F_SMALL, fg=WHITE, bg=BG2).pack(side="left", padx=(8,0))

        # Pro tip
        tip_frame = tk.Frame(card, bg=BG3, padx=10, pady=8)
        tip_frame.pack(fill="x", pady=(8,0))
        tk.Label(tip_frame, text="PRO TIP  ", font=F_SMALL_B, fg=AMBER, bg=BG3).pack(side="left")
        tk.Label(tip_frame, text=ind["tip"], font=F_SMALL, fg=GRAY, bg=BG3,
                wraplength=400, justify="left").pack(side="left")

        # Border bottom
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=14, pady=(8,0))

    def _build_settings(self):
        t = self.tab_settings

        # Header
        hdr = tk.Frame(t, bg=BG, padx=20, pady=16)
        hdr.pack(fill="x")
        tk.Label(hdr, text="SETTINGS", font=F_HEAD, fg=WHITE, bg=BG).pack(anchor="w")
        tk.Label(hdr, text="Configure your INCIZO AI",
                font=F_SMALL, fg=GRAY, bg=BG).pack(anchor="w", pady=(4,0))

        tk.Frame(t, bg=BORDER, height=1).pack(fill="x")

        form = tk.Frame(t, bg=BG, padx=20, pady=16)
        form.pack(fill="x")

        self._s_row(form, "Anthropic API Key", "api_key", "", True)
        self._s_row(form, "Account Size ($)", "account_size", "5000")
        self._s_row(form, "Max Risk per Trade (%)", "max_risk_pct", "1")
        self._s_row(form, "Daily Loss Limit (%)", "daily_loss_pct", "4")
        self._s_row(form, "Profit Target (%)", "target_pct", "10")

        # Sound toggle
        self.s_sound = tk.BooleanVar(value=self.config.get("sound_alerts"))
        sound_row = tk.Frame(form, bg=BG, pady=4)
        sound_row.pack(fill="x")
        tk.Checkbutton(sound_row, text="  Sound alerts on new signals",
            variable=self.s_sound,
            font=F_BODY, fg=WHITE, bg=BG,
            selectcolor=BG3, activebackground=BG,
            activeforeground=GREEN).pack(anchor="w")

        tk.Frame(t, bg=BORDER, height=1).pack(fill="x", pady=4)

        tk.Button(t, text="SAVE SETTINGS",
            font=F_BODY_B, bg=GREEN, fg="#000",
            relief="flat", bd=0, padx=20, pady=12,
            cursor="hand2",
            command=self._save).pack(padx=20, anchor="w", pady=(12,4))

        self.save_status = tk.Label(t, text="",
            font=F_BODY_B, fg=GREEN, bg=BG)
        self.save_status.pack(padx=20, anchor="w")

        tk.Frame(t, bg=BORDER, height=1).pack(fill="x", pady=12)

        # Instructions
        info = tk.Frame(t, bg=BG1, padx=16, pady=14, relief="flat")
        info.pack(fill="x", padx=20)
        tk.Label(info, text="HOW TO GET YOUR API KEY",
                font=F_SMALL_B, fg=GRAY, bg=BG1).pack(anchor="w", pady=(0,10))

        steps = [
            ("1", "Go to console.anthropic.com"),
            ("2", "Sign up or log in"),
            ("3", "Click API Keys → Create Key"),
            ("4", "Go to Billing → Add $5 (covers ~500 scans)"),
            ("5", "Copy your key (starts with sk-ant-...)"),
            ("6", "Paste above → Save Settings"),
        ]
        for num, step in steps:
            row = tk.Frame(info, bg=BG1)
            row.pack(anchor="w", pady=2)
            tk.Label(row, text=num, font=("Menlo", 11, "bold"),
                    fg=GREEN, bg=BG3, width=3, pady=2).pack(side="left", padx=(0,10))
            tk.Label(row, text=step, font=F_BODY, fg=WHITE, bg=BG1).pack(side="left")

        tk.Label(info, text="\n~$0.01 per scan  ·  $5 covers 2 full trading sessions",
                font=F_SMALL, fg=DIM, bg=BG1).pack(anchor="w")

    def _s_row(self, parent, label, key, default, secret=False):
        tk.Label(parent, text=label, font=F_SMALL_B, fg=GRAY, bg=BG).pack(anchor="w", pady=(8,3))
        var = tk.StringVar(value=str(self.config.get(key) or default))
        entry = tk.Entry(parent, textvariable=var,
            font=F_BODY, bg=BG2, fg=WHITE,
            insertbackground=GREEN,
            relief="flat", bd=4,
            show="*" if secret else "")
        entry.pack(fill="x", pady=(0,4))
        setattr(self, f"s_{key}", var)

    # ─── HELPERS ─────────────────────────────────────────────────
    def _signal_card(self, parent, label, value, color):
        f = tk.Frame(parent, bg=BG2, padx=10, pady=10)
        f.pack(side="left", expand=True, fill="x", padx=4)
        tk.Label(f, text=label, font=F_SMALL_B, fg=GRAY, bg=BG2).pack()
        v = tk.Label(f, text=value, font=("Helvetica Neue", 17, "bold"), fg=color, bg=BG2)
        v.pack(pady=(4,0))
        return v

    def _draw_dot(self, parent, color):
        c = tk.Canvas(parent, width=8, height=8, bg=BG2, highlightthickness=0)
        c.pack(side="left", padx=(0,6), pady=2)
        c.create_oval(1,1,7,7, fill=color, outline="")

    def _log(self, text, tag="white"):
        self.analysis.insert(tk.END, text, tag)
        self.analysis.see(tk.END)

    def _chat(self, tag, text):
        self.chat.config(state="normal")
        self.chat.insert(tk.END, text, tag)
        self.chat.see(tk.END)
        self.chat.config(state="disabled")

    def _focus_in(self, e):
        if self.chat_entry.get() == "Ask Marcus anything about your trade…":
            self.chat_entry.delete(0, tk.END)
            self.chat_entry.config(fg=WHITE)

    def _focus_out(self, e):
        if not self.chat_entry.get():
            self.chat_entry.insert(0, "Ask Marcus anything about your trade…")
            self.chat_entry.config(fg=DIM)

    def _prefill(self, text):
        self.chat_entry.delete(0, tk.END)
        self.chat_entry.insert(0, text)
        self.chat_entry.config(fg=WHITE)
        self._send()

    # ─── CLOCK ───────────────────────────────────────────────────
    def _start_clock(self):
        def tick():
            while True:
                t = datetime.utcnow().strftime("%H:%M UTC")
                self.root.after(0, lambda x=t: self.clock.config(text=x))
                time.sleep(1)
        threading.Thread(target=tick, daemon=True).start()

    # ─── WATCHING ────────────────────────────────────────────────
    def toggle_watching(self):
        if self.running:
            self.running = False
            self.start_btn.config(text="▶  START WATCHING", bg=GREEN, fg="#000")
            self.dot.itemconfig(self.dot_id, fill=DIM)
            self.cd_label.config(text="")
            self._log("\n—  Watching stopped  —\n", "dim")
        else:
            if not self.api_key:
                messagebox.showerror("No API Key",
                    "Add your Anthropic API key in Settings first.\n\nconsole.anthropic.com")
                self.nb.select(3)
                return
            self.running = True
            self.start_btn.config(text="⏹  STOP WATCHING", bg=RED, fg=WHITE)
            self.dot.itemconfig(self.dot_id, fill=GREEN)
            self._log("\n—  Watching started  —\n", "ok")
            threading.Thread(target=self._watch_loop, daemon=True).start()

    def manual_scan(self):
        if not self.api_key:
            messagebox.showerror("No API Key", "Add your API key in Settings first.")
            self.nb.select(3)
            return
        self._log("\n📷  Manual scan initiated…\n", "dim")
        threading.Thread(target=self._do_scan, daemon=True).start()

    def _watch_loop(self):
        while self.running:
            self._do_scan()
            interval = int(self.interval_var.get())
            for i in range(interval, 0, -1):
                if not self.running: break
                self.root.after(0, lambda s=i: self.cd_label.config(
                    text=f"Next scan in {s}s", fg=DIM))
                time.sleep(1)
            if self.running:
                self.root.after(0, lambda: self.cd_label.config(
                    text="Scanning…", fg=AMBER))

    def _do_scan(self):
        try:
            shot = ImageGrab.grab()
            self._update_preview(shot)

            buf = io.BytesIO()
            shot.convert("RGB").save(buf, format="JPEG", quality=80)
            buf.seek(0)
            b64 = base64.b64encode(buf.read()).decode()

            now = datetime.now().strftime("%H:%M:%S")
            self.scan_count += 1
            self.root.after(0, lambda: self.c_scans.config(text=str(self.scan_count)))
            self.root.after(0, lambda: self.ts_label.config(text=now))

            pair = self.pair_var.get()
            result = call_claude(self.api_key,
                f"Analyze this {pair} chart carefully.",
                image_b64=b64,
                system=CHART_PROMPT)

            self._parse(result, now)

            if self.config.get("sound_alerts") and winsound:
                threading.Thread(target=lambda: winsound.Beep(600,60), daemon=True).start()

        except Exception as e:
            self.root.after(0, lambda: self._log(f"\n✗  Error: {str(e)}\n", "bad"))

    def _parse(self, text, ts):
        def update():
            self._log(f"\n", "dim")
            self._log(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n", "dim")
            self._log(f"  SCAN #{self.scan_count}  ·  {ts}\n", "head")
            self._log(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n", "dim")

            bias = "WAIT"
            rsi_val = None
            conf = "—"

            lines = text.strip().split('\n')
            for line in lines:
                line = line.strip()
                if not line: continue
                u = line.upper()

                if "━━━" in line:
                    self._log(line + "\n", "dim")
                elif u.startswith("BIAS:"):
                    bias = line.split(":", 1)[1].strip().upper()
                    tag = "ok" if "LONG" in bias else "bad" if "SHORT" in bias else "warn"
                    self._log(line + "\n", tag)
                elif u.startswith("CONFIDENCE:"):
                    conf = line.split(":", 1)[1].strip().upper()
                    tag = "ok" if "HIGH" in conf else "warn" if "MEDIUM" in conf else "bad"
                    self._log(line + "\n", tag)
                elif u.startswith("RSI:"):
                    m = re.search(r'(\d+\.?\d*)', line)
                    if m: rsi_val = float(m.group(1))
                    tag = "bad" if rsi_val and rsi_val > 70 else "ok" if rsi_val and rsi_val < 30 else "warn"
                    self._log(line + "\n", tag)
                elif any(u.startswith(k) for k in ["ENTRY:", "STOP LOSS:", "TARGET:", "R:R"]):
                    self._log(line + "\n", "white")
                elif u.startswith("VERDICT") or "━━━" in line:
                    self._log(line + "\n", "purple")
                else:
                    col = "ok" if any(w in u for w in ["BULL","LONG","ABOVE","SUPPORT"]) else \
                          "bad" if any(w in u for w in ["BEAR","SHORT","BELOW","RESIST"]) else \
                          "warn" if "WAIT" in u else "white"
                    self._log(line + "\n", col)

            self._log("\n", "dim")

            # Update cards
            bc = GREEN if "LONG" in bias else RED if "SHORT" in bias else AMBER
            self.c_bias.config(text=bias[:5], fg=bc)
            if rsi_val is not None:
                rc = RED if rsi_val > 70 else GREEN if rsi_val < 30 else AMBER
                self.c_rsi.config(text=f"{rsi_val:.0f}", fg=rc)
            cc = GREEN if "HIGH" in conf else AMBER if "MEDIUM" in conf else RED
            self.c_conf.config(text=conf[:4], fg=cc)

            # Sound on actionable signal
            if "LONG" in bias or "SHORT" in bias:
                if "HIGH" in conf and self.config.get("sound_alerts") and winsound:
                    threading.Thread(target=lambda: [
                        winsound.Beep(880,150), time.sleep(0.08), winsound.Beep(1100,200)
                    ], daemon=True).start()

        self.root.after(0, update)

    def _update_preview(self, shot):
        def update():
            try:
                p = shot.copy()
                p.thumbnail((528,120), Image.LANCZOS)
                ph = ImageTk.PhotoImage(p)
                self.preview.config(image=ph, text="")
                self.preview.image = ph
            except: pass
        self.root.after(0, update)

    # ─── CHAT ────────────────────────────────────────────────────
    def _send(self):
        msg = self.chat_entry.get().strip()
        if not msg or msg == "Ask Marcus anything about your trade…": return
        if not self.api_key:
            messagebox.showerror("No API Key", "Add your API key in Settings first.")
            self.nb.select(3)
            return

        self.chat_entry.delete(0, tk.END)
        self.chat_entry.config(fg=WHITE)

        now = datetime.now().strftime("%H:%M")
        self._chat("you_name", f"\nYOU  ·  {now}\n")
        self._chat("you_msg", f"{msg}\n")

        # Capture screen so Marcus can see the chart
        try:
            shot = ImageGrab.grab()
            buf = io.BytesIO()
            shot.convert("RGB").save(buf, format="JPEG", quality=75)
            buf.seek(0)
            screen_b64 = base64.b64encode(buf.read()).decode()
            self._chat("thinking", "\nMarcus is looking at your chart…\n")
        except:
            screen_b64 = None
            self._chat("thinking", "\nMarcus is thinking…\n")

        self.chat_history.append({"role": "user", "content": msg})
        self.send_btn.config(state="disabled", bg=BG3, fg=GRAY, text="…")

        threading.Thread(target=self._marcus_reply, args=(msg, screen_b64), daemon=True).start()

    def _marcus_reply(self, msg, screen_b64=None):
        try:
            history = "\n".join([
                f"{'Trader' if m['role']=='user' else 'Marcus'}: {m['content']}"
                for m in self.chat_history[-8:]
            ])

            if screen_b64:
                prompt = (
                    f"I can see the trader's screen/chart above.\n\n"
                    f"Conversation so far:\n{history}\n\n"
                    f"Trader just asked: {msg}\n\n"
                    f"Look at their chart and respond as Marcus. "
                    f"Reference what you actually see on screen. "
                    f"Be direct, max 4 sentences:"
                )
            else:
                prompt = (
                    f"Conversation:\n{history}\n\n"
                    f"Trader just said: {msg}\n\n"
                    f"Marcus responds (direct, max 4 sentences):"
                )

            reply = call_claude(self.api_key, prompt,
                               image_b64=screen_b64,
                               system=MARCUS_PROMPT)
            self.chat_history.append({"role": "assistant", "content": reply})
            self.root.after(0, lambda: self._show_reply(reply))
        except Exception as e:
            self.root.after(0, lambda: self._show_reply(f"Connection issue — check your API key. Error: {str(e)}"))

    def _show_reply(self, reply):
        self.chat.config(state="normal")
        content = self.chat.get("1.0", tk.END)
        idx = content.rfind("\nMarcus is typing…\n")
        if idx != -1:
            self.chat.delete(f"1.0 + {idx} chars",
                           f"1.0 + {idx + len(chr(10)+'Marcus is typing…'+chr(10))} chars")
        self.chat.config(state="disabled")

        now = datetime.now().strftime("%H:%M")
        self._chat("marcus_name", f"\nMARCUS  ·  {now}\n")
        self._chat("marcus_msg", f"{reply}\n")
        self.send_btn.config(state="normal", bg=GREEN, fg="#000", text="SEND")

    # ─── SETTINGS ────────────────────────────────────────────────
    def _save(self):
        self.config.set("api_key", self.s_api_key.get())
        self.api_key = self.s_api_key.get()
        try:
            self.config.set("account_size",  float(self.s_account_size.get()))
            self.config.set("max_risk_pct",  float(self.s_max_risk_pct.get()))
            self.config.set("daily_loss_pct",float(self.s_daily_loss_pct.get()))
            self.config.set("target_pct",    float(self.s_target_pct.get()))
        except: pass
        self.config.set("sound_alerts", self.s_sound.get())
        self.save_status.config(text="✓  Settings saved")
        self.root.after(2000, lambda: self.save_status.config(text=""))
        if self.api_key:
            self._log("\n✓  API key updated — Claude AI ready.\n", "ok")

    def _on_close(self):
        self.running = False
        self.config.save()
        self.root.destroy()

# ─── LAUNCH ──────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = IncizoApp(root)
    root.mainloop()
