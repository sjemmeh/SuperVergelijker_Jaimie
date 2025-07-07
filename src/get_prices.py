import os
import sys
import io
import requests
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
from colorama import Fore, Style, init
    
def run_get():

    init(autoreset=True)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    dotenv_path = os.path.join(script_dir, ".env")
    load_dotenv(dotenv_path)

    api_key = os.getenv("BUDGETGAMING_API_KEY")
    store_id = os.getenv("BUDGETGAMING_STORE_ID")
    store_url = os.getenv("BUDGETGAMING_STORE_URL")
    user_agent = os.getenv("HEADERS_USER_AGENT", "Mozilla/5.0")
    content_type = os.getenv("HEADERS_CONTENT_TYPE", "text/html")

    if not all([api_key, store_id, store_url]):
        print("❌ .env mist vereiste variabelen (API_KEY, STORE_ID of STORE_URL).")
        sys.exit(1)

    all_systems = load_consoles(script_dir)
    if not all_systems:
        print("❌ Geen consoles gevonden.")
        sys.exit(1)

    selected_systems = choose_consoles(all_systems)
    if not selected_systems:
        print("❌ Geen consoles geselecteerd. Programma wordt afgesloten.")
        sys.exit(0)

    results = fetch_all_data(selected_systems, api_key, store_id, store_url, user_agent, content_type)
    save_results(results, selected_systems, script_dir)


def load_consoles(script_dir):
    path = os.path.join(script_dir, "consoles.txt")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("❌ Bestand 'consoles.txt' niet gevonden.")
        return []


def clear_console():
    import os
    os.system('cls' if os.name == 'nt' else 'clear')


def print_console_menu(all_systems, selected):
    from colorama import Fore, Style
    print("✅ Selecteer de consoles (typ het nummer om te selecteren, 'a' = alles selecteren, 'n' = niets, Enter om door te gaan):\n")
    for idx, systeem in enumerate(all_systems, 1):
        kleur = Fore.GREEN if systeem in selected else Fore.RED
        print(f"{idx:2d}. {kleur}{systeem}{Style.RESET_ALL}")
    print()


def choose_consoles(all_systems):
    selected = set()
    while True:
        clear_console()
        print_console_menu(all_systems, selected)
        choice = input("Jouw keuze: ").strip().lower()
        if choice == "":
            break
        elif choice == "a":
            selected = set(all_systems)
        elif choice == "n":
            selected = set()
        elif choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(all_systems):
                systeem = all_systems[index]
                if systeem in selected:
                    selected.remove(systeem)
                else:
                    selected.add(systeem)
            else:
                print("❌ Ongeldig nummer.")
                input("Druk op Enter om verder te gaan...")
        else:
            print("❌ Ongeldige invoer. Typ een nummer, 'a', 'n' of druk Enter om door te gaan.")
            input("Druk op Enter om verder te gaan...")
    return list(selected)


def fetch_all_data(systems, api_key, store_id, store_url, user_agent, content_type):
    import io
    import requests
    import pandas as pd
    from tqdm import tqdm

    base_url = f"{store_url}?page=budgetgamingfeed&winkel={store_id}&code={api_key}&console="
    headers = {
        "User-Agent": user_agent,
        "Content-Type": content_type
    }

    all_data = []

    for system in tqdm(systems, desc="📡 Consoles ophalen", unit="console"):
        url = base_url + system
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            if "<html" in response.text.lower():
                print(f"\n⚠️  {system} overgeslagen: HTML ontvangen i.p.v. CSV.")
                continue

            text = response.text.replace("&nbsp", "").replace("<br>", "\n")
            csv_data = io.StringIO(text)

            try:
                df = pd.read_csv(csv_data, sep=";", dtype=str, engine="python")
                df["console"] = system
                all_data.append(df)
            except Exception as e:
                print(f"\n❌ Fout bij inlezen CSV voor {system}: {e}")

        except Exception as e:
            print(f"\n❌ Fout bij ophalen van {system}: {e}")

    return all_data


def save_results(all_data, systems, script_dir):
    import os
    import pandas as pd
    from datetime import datetime

    if not all_data:
        print("⚠️ Geen gegevens verzameld.")
        return

    df = pd.concat(all_data, ignore_index=True)
    columns = ["titel", "console", "ean", "laagsteprijs", "laagsteprijstweedehands"]
    df = df[columns]

    df = df[~(df["titel"].isna() & df["ean"].isna())]

    consolenaam = "_".join(systems).replace(" ", "_").lower()
    datum = datetime.now().strftime("%d-%m-%Y")

    output_dir = os.path.abspath(os.path.join(script_dir, "..", "resultaat"))
    os.makedirs(output_dir, exist_ok=True)

    filename = os.path.join(output_dir, f"{consolenaam}_{datum}.csv")
    df.to_csv(filename, sep=";", index=False)
    print(f"\n✅ Bestand opgeslagen als: {filename}")
