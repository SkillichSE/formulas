import os
import json
import random
import requests

TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
GUILD_ID = os.environ.get("DISCORD_GUILD_ID")
API_BASE = "https://discord.com/api/v10"

FORMULAS_URL = "https://raw.githubusercontent.com/<user>/<repo>/main/formulas.json"

HISTORY_FILE = "used_formulas.json"

BACKUP_LAWS = [
    "Mean value theorem: (f(b) - f(a)) / (b - a) = f'(c)",
    "Law of universal gravitation: F = G * (m1 * m2) / r^2",
    "Ideal gas law: PV = nRT",
    "Ohm's law: I = U / R",
    "Mass-energy equivalence: E = mc^2",
    "Newton's second law: F = ma",
    "Pythagorean theorem: a^2 + b^2 = c^2",
    "Fundamental theorem of calculus: int[a,b] f(x)dx = F(b) - F(a)",
]


def load_history() -> set:
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def save_history(history: set) -> None:
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(history), f, ensure_ascii=False)


def fetch_all_formulas() -> list:
    response = requests.get(FORMULAS_URL, timeout=10)
    response.raise_for_status()
    laws_list = response.json()
    return [f"{item['name']}: {item['formula']}" for item in laws_list]


def pick_new_formula():
    try:
        all_formulas = fetch_all_formulas()
    except Exception as e:
        print(f"Could not fetch formulas.json ({e}). Using backup list.")
        all_formulas = BACKUP_LAWS

    history = load_history()
    remaining = [f for f in all_formulas if f not in history]

    if not remaining:
        return None, history

    selected = random.choice(remaining)
    history.add(selected)
    return selected, history


def run():
    if not TOKEN:
        print("Error: DISCORD_BOT_TOKEN not found in secrets!")
        exit(1)
    if not GUILD_ID:
        print("Error: DISCORD_GUILD_ID not found in secrets!")
        exit(1)

    law_text, history = pick_new_formula()

    if law_text is None:
        print("No unused formulas left. Skipping update.")
        return

    if len(law_text) > 190:
        law_text = law_text[:187] + "..."

    headers = {
        "Authorization": f"Bot {TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {"bio": law_text}
    url = f"{API_BASE}/guilds/{GUILD_ID}/members/@me"
    response = requests.patch(url, json=payload, headers=headers)

    if response.status_code == 200:
        save_history(history)
        print(f"Bio successfully set: {law_text}")
    else:
        print(f"Error {response.status_code}: {response.text}")
        exit(1)


if __name__ == "__main__":
    run()
