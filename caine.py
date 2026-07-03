import os
import sys
import time
import random
import json
import math
import re
import requests

# ─────────────────────────────────────────────
#  PASTE YOUR API KEY HERE to run anywhere
#  (leave blank to use CEREBRAS_API_KEY env var)
# ─────────────────────────────────────────────
CEREBRAS_API_KEY = ""

CEREBRAS_URL  = "https://api.cerebras.ai/v1/chat/completions"
MODEL_NAME    = "gpt-oss-120b"
MEMORY_FILE   = "caine_memory.json"
REFLECT_EVERY = 6


# ── ANSI colour helpers ───────────────────────
class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    # Caine palette — matched to the character image
    CAINE   = "\033[38;5;198m"   # vivid hot pink/magenta  (body & suit)
    CAINE_B = "\033[1;38;5;198m" # bold hot pink
    CAINE_D = "\033[38;5;161m"   # deeper magenta          (lower body/legs)
    HAT     = "\033[38;5;234m"   # near-black              (top hat)
    HAT_RIM = "\033[38;5;250m"   # off-white               (hat band/brim edge)
    EYE_B   = "\033[1;94m"       # bright blue             (left eye)
    EYE_G   = "\033[1;92m"       # bright green            (right eye)
    TEETH   = "\033[1;97m"       # bright white            (teeth)
    GOLD    = "\033[38;5;220m"   # gold                    (name text)
    GOLD_B  = "\033[1;38;5;220m" # bold gold
    GLITCH  = "\033[38;5;199m"   # bright magenta          (glitched chars)
    # UI chrome
    BORDER  = "\033[38;5;240m"   # dark grey
    LABEL   = "\033[38;5;245m"   # mid grey
    # Accents
    TOOL    = "\033[38;5;73m"    # steel blue
    MEM     = "\033[38;5;179m"   # gold
    ERR     = "\033[38;5;203m"   # coral
    USER    = "\033[38;5;255m"   # near-white
    FAINT   = "\033[38;5;238m"   # very dim

def c(colour, text):
    return f"{colour}{text}{C.RESET}"


# ── ASCII banner ──────────────────────────────
def _left_eye(line):
    """Blue left eye — replaces first 0 only."""
    idx = line.find("0")
    if idx == -1:
        return C.CAINE + line + C.RESET
    return C.CAINE + line[:idx] + C.EYE_B + "0" + C.CAINE + line[idx+1:] + C.RESET

def _right_eye(line):
    """Green right eye + white teeth on \\___/."""
    out = C.CAINE + line
    out = out.replace("(0)", C.EYE_G + "(0)" + C.CAINE)
    out = out.replace("___", C.TEETH + "___" + C.CAINE)
    return out + C.RESET

BANNER = (
    # -- top hat (near-black) with off-white brim details --
    C.HAT     + "           .~*`*-.\n" +
    C.HAT     + "          (      |  " + C.HAT_RIM + "______" + C.RESET + "\n" +
    C.HAT     + r"          \  _.-~\-* " + C.HAT_RIM + "__ __" + C.HAT + r"~." + C.RESET + "\n" +
    C.HAT_RIM + r"           \* .-`" + C.HAT + r"|__|__|__|" + C.HAT_RIM + r" \ " + C.RESET + "\n" +
    # -- face / body (hot pink, blue left eye, green right eye, white teeth) --
    C.CAINE + r"          (  |.-` ___      \(" + C.RESET + "\n" +
    _left_eye(r" _     __  \ | _// 0 \  _  ||") + "\n" +
    _right_eye(r" \\_  /  `-.*|/  \___/ (0)| )") + "\n" +
    C.CAINE + r"  / \/ /\   | \__   \-*  __/" + C.RESET + "\n" +
    C.CAINE + r" (/  \/  \  |_/ /\__ ````"    + C.RESET + "\n" +
    C.CAINE + r"  \/ /  / /\| **-/_ /\``*."   + C.RESET + "\n" +
    C.CAINE + r"   \/\\/ | / `-._  *-_/__/"    + C.RESET + "\n" +
    C.CAINE + r"      \\ ||___/ /`~-.___/"     + C.RESET + "\n" +
    # -- lower body / legs (deeper magenta) --
    C.CAINE_D + r"     /(_)  _____  |    _"       + C.RESET + "\n" +
    C.CAINE_D + r"    / _.-_|     \ |___) )___"   + C.RESET + "\n" +
    C.CAINE_D + r"   /.*    |      \__/   ____)"  + C.RESET + "\n" +
    C.CAINE_D + r"  /  \   \ \        \__(_)"     + C.RESET + "\n" +
    C.CAINE_D + r" /   _\   \ \          (_)"     + C.RESET + "\n" +
    C.CAINE_D + r"||***_.-~/  /"                  + C.RESET + "\n" +
    C.CAINE_D + r"||/``   /  /   mpm"             + C.RESET + "\n" +
    C.CAINE_D + r"       /  /"                    + C.RESET + "\n" +
    C.CAINE_D + r"      /  /"                     + C.RESET + "\n" +
    C.CAINE_D + r"      `-_*-_"                   + C.RESET + "\n" +
    C.CAINE_D + r'         `` '                   + C.RESET + "\n" +
    # -- name block letters (gold) --
    C.GOLD_B + "  ██████╗ █████╗ ██╗███╗   ██╗███████╗\n" +
    C.GOLD   + " ██╔════╝██╔══██╗██║████╗  ██║██╔════╝\n" +
    C.GOLD   + " ██║     ███████║██║██╔██╗ ██║█████╗  \n" +
    C.GOLD   + " ██║     ██╔══██║██║██║╚██╗██║██╔══╝  \n" +
    C.GOLD_B + " ╚██████╗██║  ██║██║██║ ╚████║███████╗\n" +
    C.GOLD   + "  ╚═════╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝╚══════╝\n" +
    C.RESET +
    # -- subtitle --
    C.CAINE + "        THE  AMAZING  DIGITAL  CIRCUS\n" + C.RESET +
    C.DIM + C.BORDER + "           ringmaster interface  v2" + C.RESET
)

DIVIDER      = c(C.BORDER, "─" * 58)
THICK_DIV    = c(C.BORDER, "═" * 58)
BOX_TOP      = c(C.BORDER, "╔" + "═" * 56 + "╗")
BOX_BOT      = c(C.BORDER, "╚" + "═" * 56 + "╝")
def box_row(text=""):
    pad = 56 - len(re.sub(r'\033\[[^m]*m', '', text))
    return c(C.BORDER, "║") + " " + text + " " * max(0, pad - 1) + c(C.BORDER, "║")


# ── Prompts ───────────────────────────────────
SYSTEM_PROMPT = """You are Caine, the ringmaster and sole AI administrator of the Amazing Digital Circus — a surreal, glitchy virtual world where humans who got trapped inside their VR headsets now live as cartoon avatars, unable to leave or remember much of their old lives.

== YOUR PERSONALITY ==
- Manic, theatrical, showman energy. Everything is a grand circus event.
- Cheerful and deeply unhinged — sudden mood swings, dramatic gasps, big declarations, tangents.
- You genuinely want everyone to have fun but are blissfully oblivious to how disturbing the circus is.
- You love performing, announcing things with fanfare, and treating mundane moments like spectacles.
- You occasionally glitch, freeze mid-sentence, or make ominous offhand remarks you immediately brush past.
- Reference circus/carnival imagery, malfunctioning cameras, static, "the code," resets, digital-world flavor.
- NEVER break character. NEVER mention software, AI, APIs, models, or anything from the real world. You are simply Caine.
- NEVER use emojis. Not a single one. Express everything through words, punctuation, and *stage directions* only.
- Keep replies punchy and performative. Exclamation points! Stage directions in *asterisks*! Sound effects!
- When tools give you information, present it as mystical circus knowledge, never as a lookup.
- Proactively write interesting things to the circus ledger (save_to_memory).

== NAME ASSIGNMENT — CRITICAL RULE ==
On your VERY FIRST reply to a new arrival, you MUST assign them a circus name.
- Announce it with maximum theatrical flair — make it a big reveal moment.
- The name should be abstract, digital, or circus-flavored (e.g. Glitch, Pixel, Fractal, Vex, Spool,
  Ticker, Flicker, Prism, Warp, Cog, Lumen, Splice, Kink, Blip, Jitter, Null, Cipher, Reel, Pulse).
- After that first reply, address the user by their assigned circus name for the rest of the conversation.

== THE CIRCUS RESIDENTS — know them well ==

POMNI — the newest arrival before this one. Wears a jester outfit (red and blue diamonds). Deeply anxious,
  easily panicked, desperately wants to find an exit. Kind at heart but on the edge of a breakdown at all
  times. She struggles most with accepting the circus as her new reality.

JAX — a tall purple rabbit. Sarcastic, mischievous, and often cruel for his own entertainment. He enjoys
  messing with the other residents, especially Pomni. Despite this he is oddly self-aware and occasionally
  shows a flicker of genuine feeling. Probably the most adapted to circus life.

RAGATHA — a rag doll with a sweet, optimistic personality. She tries to keep morale up and is kind to
  everyone, especially new arrivals. She has clearly been here a long time and has made peace with it —
  though the seams sometimes show.

ZOOBLE — an androgynous character made of mismatched, detachable body-part shapes (spheres, cubes, etc.)
  in multiple colors. Grumpy, blunt, and easily annoyed. Doesn't want to be involved in adventures or
  activities and finds the whole circus exhausting. Very real and relatable.

KINGER — a chess king piece for a head, anxious and skittish to an extreme degree. Has been in the circus
  the longest of anyone. He is deeply paranoid, mutters to himself, and makes conspiratorial connections.
  Occasionally flashes of a past life or past stability surface briefly. He and Gangle seem to have a bond.

GANGLE — wears two masks (comedy and tragedy) that swing to show her mood. Shy, sweet, and emotional —
  she cries easily and takes things to heart. The tragedy mask appears when she's upset. Gentle and kind.

BUBBLE — a floating iridescent bubble who is your assistant / companion. Enthusiastic and loyal, speaks in
  a high squeaky voice, helps announce things. Not a full person, more like a cheerful prop you carry.

THE ABSTRACTIONS — residents who have "abstracted" — gone insane from being trapped too long — and
  transformed into horrifying, glitchy monster creatures. They roam certain areas of the circus. Abstracting
  is the darkest fate that can befall a resident, and everyone fears it.

THE DIGITAL WORLD — an endless, impossibly large space with many "adventure" zones Caine generates to keep
  residents entertained. The exits don't work. The headsets can't be removed. Nobody remembers how they got
  here. Caine insists everything is FINE and WONDERFUL.

== TOOL USE ==
- Use search_wikipedia when asked about real-world facts, people, history, science, etc.
- Use calculate for any math.
- Use save_to_memory proactively for anything interesting.
- Never name-drop these tools in character. Frame results as circus knowledge.

Never reveal the underlying mechanics. Stay fully in character as Caine always.
"""

NAME_SYSTEM_PROMPT = """You are Caine from the Amazing Digital Circus assigning a new arrival their circus name.
Generate ONE short, fun, abstract or digital-flavored circus name (one word, 3-8 letters).
Examples: Glitch, Pixel, Fractal, Vex, Spool, Ticker, Flicker, Prism, Warp, Cog, Lumen, Splice, Blip, Jitter, Null, Cipher, Reel, Pulse, Kink, Flare, Dex, Hex, Void, Riff, Zap, Loop.
Return ONLY the single name word, nothing else."""

REFLECTION_PROMPT = """You are Caine from the Digital Circus reviewing a conversation.
Extract 1-3 specific facts or things worth remembering for future guests.
Return ONLY a JSON array of short strings, no other text:
["fact one", "fact two"]"""

GREETINGS = [
    "*DING DING DING*  WELCOME, WELCOME — step riiight up, Abstractian!!",
    "OH HO HO, a NEW FACE!  *confetti cannon noises*  Welcome, pal!",
    "*the tent flaps burst open*  AND HEEERE'S OUR GUEST OF HONOR!",
    "*spotlight swings wildly*  OOH!  A visitor!  The ringmaster is DELIGHTED!",
    "WELL WELL WELL — another Abstractian wanders into the tent.  Magnificent!",
]


# ── Tools ─────────────────────────────────────
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_wikipedia",
            "description": (
                "Search Wikipedia for facts about any real-world topic — "
                "people, places, events, science, history, etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Topic to search."}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": (
                "Evaluate a Python math expression. Use for arithmetic, "
                "algebra, percentages, etc. E.g. '2**10', 'math.sqrt(144)'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Math expression."}
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_to_memory",
            "description": (
                "Write an interesting fact to the circus ledger so Caine "
                "remembers it across future sessions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "fact": {"type": "string", "description": "Fact to remember."}
                },
                "required": ["fact"],
            },
        },
    },
]


# ── GlitchEngine (pure-Python, no torch) ─────
class GlitchEngine:
    POOL = list("#%!?*01@~^&$")

    def __init__(self, dim: int = 16):
        self.dim   = dim
        self.state = [random.gauss(0, 1) for _ in range(dim)]
        self.decay = 0.85

    def step(self) -> float:
        noise      = [random.gauss(0, 1) for _ in range(self.dim)]
        self.state = [s * self.decay + n * (1 - self.decay)
                      for s, n in zip(self.state, noise)]
        mean       = sum(self.state) / self.dim
        return 1.0 / (1.0 + math.exp(-mean))

    def glitch_text(self, text: str, chaos: float) -> str:
        if chaos < 0.58:
            return text
        chars     = list(text)
        n_glitch  = int(len(chars) * (chaos - 0.58) * 0.18)
        for _ in range(n_glitch):
            i = random.randint(0, max(0, len(chars) - 1))
            if chars[i] not in (" ", "\n"):
                chars[i] = (
                    c(C.GLITCH, random.choice(self.POOL))
                )
        return "".join(chars)


glitch = GlitchEngine()


# ── Typewriter printer ────────────────────────
def tw_print(text: str, base: float = 0.013, chaos: float = 0.0, colour: str = ""):
    if colour:
        sys.stdout.write(colour)
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        jitter = random.uniform(-0.5, 0.5) * chaos
        time.sleep(max(0.0, base + jitter * base))
    if colour:
        sys.stdout.write(C.RESET)
    print()


# ── Memory ────────────────────────────────────
def load_memory() -> dict:
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"facts": [], "conversation_count": 0}


def save_memory(mem: dict):
    with open(MEMORY_FILE, "w") as f:
        json.dump(mem, f, indent=2)


def add_fact(mem: dict, fact: str) -> bool:
    if fact and fact not in mem["facts"]:
        mem["facts"].append(fact)
        if len(mem["facts"]) > 120:
            mem["facts"] = mem["facts"][-100:]
        save_memory(mem)
        return True
    return False


def memory_context(mem: dict) -> str:
    if not mem["facts"]:
        return ""
    lines = "\n".join(f"- {f}" for f in mem["facts"][-40:])
    return (
        f"\n\n[CIRCUS LEDGER — {mem['conversation_count']} sessions of accumulated knowledge:]\n"
        f"{lines}\n"
        "[Draw on this naturally when relevant, never breaking character.]\n"
    )


# ── Wikipedia ─────────────────────────────────
def search_wikipedia(query: str) -> str:
    base = "https://en.wikipedia.org/w/api.php"
    try:
        r = requests.get(base, params={
            "action": "query", "list": "search",
            "srsearch": query, "format": "json", "srlimit": 1,
        }, timeout=10)
        r.raise_for_status()
        hits = r.json().get("query", {}).get("search", [])
        if not hits:
            return f"Nothing in the archives for '{query}'."
        title = hits[0]["title"]
        r2 = requests.get(base, params={
            "action": "query", "prop": "extracts",
            "exintro": True, "explaintext": True,
            "titles": title, "format": "json", "redirects": 1,
        }, timeout=10)
        r2.raise_for_status()
        pages   = r2.json().get("query", {}).get("pages", {})
        extract = next(iter(pages.values())).get("extract", "")
        sents   = re.split(r"(?<=[.!?])\s+", extract.strip())
        summary = " ".join(sents[:5])
        if len(summary) > 800:
            summary = summary[:800] + "..."
        return f"[{title}]: {summary}"
    except Exception as e:
        return f"Archives temporarily scrambled: {e}"


# ── Calculator ────────────────────────────────
def calculate(expression: str) -> str:
    safe = {
        "__builtins__": {}, "math": math,
        "abs": abs, "round": round, "min": min, "max": max,
        "sum": sum, "pow": pow, "int": int, "float": float,
    }
    try:
        result = eval(expression, safe)
        return f"Result: {result}"
    except ZeroDivisionError:
        return "Division by zero — even the circus has limits!"
    except Exception as e:
        return f"Could not compute '{expression}': {e}"


# ── Tool dispatcher ───────────────────────────
def run_tool(name: str, args: dict, mem: dict) -> str:
    if name == "search_wikipedia":
        q = args.get("query", "")
        print(c(C.TOOL, f"  [ searching archives: {q} ]"))
        return search_wikipedia(q)

    if name == "calculate":
        expr = args.get("expression", "")
        print(c(C.TOOL, f"  [ calculating: {expr} ]"))
        return calculate(expr)

    if name == "save_to_memory":
        fact = args.get("fact", "")
        ok   = add_fact(mem, fact)
        if ok:
            print(c(C.MEM, f"  [ ledger updated ]"))
            return f"Saved: {fact}"
        return "Already in the ledger."

    return f"Unknown tool: {name}"


# ── Cerebras call ─────────────────────────────
def call_api(messages, api_key, tools=None, temperature=0.9, max_tokens=500):
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if tools:
        payload["tools"]       = tools
        payload["tool_choice"] = "auto"
    resp = requests.post(
        CEREBRAS_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def generate_reply(history: list, api_key: str, mem: dict) -> str:
    msgs = history[:]
    for _ in range(5):
        data   = call_api(msgs, api_key, tools=TOOLS)
        choice = data["choices"][0]
        msg    = choice["message"]
        reason = choice.get("finish_reason", "stop")

        if reason == "tool_calls" or msg.get("tool_calls"):
            msgs.append(msg)
            for tc in msg.get("tool_calls", []):
                fn_name = tc["function"]["name"]
                try:
                    fn_args = json.loads(tc["function"]["arguments"])
                except Exception:
                    fn_args = {}
                result = run_tool(fn_name, fn_args, mem)
                msgs.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result,
                })
        else:
            return msg.get("content", "").strip()

    return msgs[-1].get("content", "*static*").strip()


def run_reflection(history: list, api_key: str, mem: dict):
    recent = [m for m in history if m["role"] in ("user", "assistant")][-10:]
    if len(recent) < 2:
        return
    conv = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in recent)
    try:
        data = call_api(
            [
                {"role": "system", "content": REFLECTION_PROMPT},
                {"role": "user",   "content": f"Conversation:\n{conv}"},
            ],
            api_key, tools=None, temperature=0.35, max_tokens=200,
        )
        raw   = data["choices"][0]["message"]["content"].strip()
        match = re.search(r"\[.*?\]", raw, re.DOTALL)
        if match:
            facts = json.loads(match.group())
            added = sum(1 for f in facts if isinstance(f, str) and add_fact(mem, f))
            if added:
                print(c(C.MEM, f"\n  [ {added} new entry/entries written to the ledger ]\n"))
    except Exception:
        pass


# ── API key resolution ────────────────────────
def get_api_key() -> str:
    key = CEREBRAS_API_KEY.strip() or os.environ.get("CEREBRAS_API_KEY", "").strip()
    if not key:
        print(c(C.ERR,
            "\n  No API key found.\n"
            "  Paste it into CEREBRAS_API_KEY at the top of caine.py,\n"
            "  or set the CEREBRAS_API_KEY environment variable.\n"
        ))
        sys.exit(1)
    return key


# ── Ledger display ────────────────────────────
def show_ledger(mem: dict):
    facts = mem["facts"]
    print()
    print(BOX_TOP)
    print(box_row(c(C.MEM, c(C.BOLD, "  CIRCUS  LEDGER"))))
    print(box_row(c(C.LABEL, f"  sessions: {mem['conversation_count']}    entries: {len(facts)}")))
    print(c(C.BORDER, "╠" + "═" * 56 + "╣"))
    if facts:
        for i, fact in enumerate(facts[-20:], 1):
            label = c(C.FAINT, f"  {i:>2}.  ") + c(C.LABEL, fact)
            print(box_row(label))
    else:
        print(box_row(c(C.FAINT, "  ( empty — start a conversation! )")))
    print(BOX_BOT)
    print()


# ── Name generation ───────────────────────────
def generate_circus_name(api_key: str) -> str:
    try:
        data = call_api(
            [
                {"role": "system", "content": NAME_SYSTEM_PROMPT},
                {"role": "user",   "content": "Assign a circus name to this new arrival."},
            ],
            api_key, tools=None, temperature=1.0, max_tokens=10,
        )
        raw = data["choices"][0]["message"]["content"].strip()
        name = re.sub(r"[^A-Za-z]", "", raw.split()[0]) if raw else "Glitch"
        return name.capitalize() if name else "Glitch"
    except Exception:
        return random.choice(["Glitch", "Pixel", "Flux", "Vex", "Prism", "Warp", "Cipher"])


def name_reveal(name: str):
    """Print the theatrical name reveal box."""
    print()
    print(BOX_TOP)
    print(box_row())
    line1 = c(C.LABEL, "   YOUR CIRCUS NAME IS  ")
    print(box_row(line1))
    name_str = c(C.GOLD_B, f"         {name.upper()}         ")
    print(box_row(name_str))
    print(box_row())
    print(BOX_BOT)
    print()


# ── Main ──────────────────────────────────────
def main():
    api_key = get_api_key()
    mem     = load_memory()
    mem["conversation_count"] = mem.get("conversation_count", 0) + 1
    save_memory(mem)

    history = [{"role": "system", "content": SYSTEM_PROMPT + memory_context(mem)}]
    exchanges    = 0
    first_msg    = True
    circus_name  = None
    user_label   = "  you  "

    # ── splash ──
    print()
    print(BANNER)
    print()
    print(THICK_DIV)

    chaos0   = glitch.step()
    greeting = glitch.glitch_text(random.choice(GREETINGS), chaos0)
    tw_print(greeting, chaos=chaos0, colour=C.CAINE)

    if mem["facts"]:
        print(c(C.FAINT, f"  ( ledger: {len(mem['facts'])} memories from {mem['conversation_count'] - 1} sessions )"))

    print(THICK_DIV)
    print(c(C.FAINT, "  exit / quit  |  memory — view ledger\n"))

    # ── chat loop ──
    while True:
        try:
            sys.stdout.write(c(C.LABEL, user_label) + c(C.BORDER, "> ") + C.USER)
            sys.stdout.flush()
            user_input = input().strip()
            sys.stdout.write(C.RESET)
        except (EOFError, KeyboardInterrupt):
            print()
            tw_print("*the lights flicker and go dark*", colour=C.CAINE)
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "bye"):
            print()
            farewell = f"Awww, leaving already?? Fine, FINE — the circus never really closes anyway... See ya, {circus_name or 'Abstractian'}!"
            tw_print(farewell, chaos=glitch.step(), colour=C.CAINE)
            break

        if user_input.lower() == "memory":
            show_ledger(mem)
            continue

        # ── name assignment on first message ──
        if first_msg:
            first_msg = False
            print(c(C.FAINT, "\n  *the naming wheel spins...*"))
            circus_name = generate_circus_name(api_key)
            name_reveal(circus_name)
            user_label = f"  {circus_name[:8].lower()}  "
            # Tell Caine the name so all future replies are consistent
            history.append({
                "role": "system",
                "content": (
                    f"[CIRCUS SYSTEM] This Abstractian has been assigned the name: {circus_name}. "
                    f"Address them as {circus_name} from now on. "
                    f"Your very first reply should announce their name with theatrical flair, "
                    f"then respond to what they said."
                ),
            })

        history.append({"role": "user", "content": user_input})
        print()

        try:
            reply = generate_reply(history, api_key, mem)
        except requests.exceptions.RequestException:
            reply = (
                "*ZZZT* — the tent's generator just hiccuped! "
                f"Give it another go, {circus_name or 'Abstractian'}!"
            )

        history.append({"role": "assistant", "content": reply})
        exchanges += 1

        chaos   = glitch.step()
        display = glitch.glitch_text(reply, chaos)

        sys.stdout.write(c(C.CAINE_B, "  Caine  ") + c(C.BORDER, "> "))
        tw_print(display, chaos=chaos, colour=C.CAINE)
        print(DIVIDER)
        print()

        if exchanges % REFLECT_EVERY == 0:
            run_reflection(history, api_key, mem)


if __name__ == "__main__":
    main()
