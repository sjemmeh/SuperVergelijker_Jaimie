import os
import sys
import io
import requests
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
from colorama import Fore, Style, init

from main import set_console_title

def run_get():
    """
    Main function to fetch price data from BudgetGaming.nl.
    Initializes colorama, loads environment variables,
    loads and selects consoles, fetches data, and saves results.
    """
    init(autoreset=True) # Initialize colorama for auto-resetting styles

    script_dir = os.path.dirname(os.path.abspath(__file__))
    dotenv_path = os.path.join(script_dir, ".env")
    load_dotenv(dotenv_path) # Load environment variables from .env file

    # Retrieve API credentials and headers from environment variables
    api_key = os.getenv("BUDGETGAMING_API_KEY")
    store_id = os.getenv("BUDGETGAMING_STORE_ID")
    store_url = os.getenv("BUDGETGAMING_STORE_URL")
    user_agent = os.getenv("HEADERS_USER_AGENT", "Mozilla/5.0")
    content_type = os.getenv("HEADERS_CONTENT_TYPE", "text/html")

    # Check if all required environment variables are set
    if not all([api_key, store_id, store_url]):
        print("❌ .env mist vereiste variabelen (API_KEY, STORE_ID of STORE_URL).") # .env is missing required variables (API_KEY, STORE_ID or STORE_URL).
        sys.exit(1)

    all_systems = load_consoles(script_dir) # Load available consoles from consoles.txt
    if not all_systems:
        print("❌ Geen consoles gevonden.") # No consoles found.
        sys.exit(1)

    selected_systems = choose_consoles(all_systems) # Allow user to select consoles
    if not selected_systems:
        print("❌ Geen consoles geselecteerd. Programma wordt afgesloten.") # No consoles selected. Program will exit.
        sys.exit(0)

    # Fetch data for selected consoles
    results = fetch_all_data(selected_systems, api_key, store_id, store_url, user_agent, content_type)
    save_results(results, selected_systems, script_dir) # Save the fetched data to a CSV file


def load_consoles(script_dir):
    """
    Loads a list of console names from 'consoles.txt'.

    Args:
        script_dir: The directory where the script is located.

    Returns:
        A list of console names, or an empty list if the file is not found.
    """
    path = os.path.join(script_dir, "consoles.txt")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("❌ Bestand 'consoles.txt' niet gevonden.") # File 'consoles.txt' not found.
        return []


def clear_console():
    """
    Clears the console screen. Works on both Windows ('cls') and Unix-like ('clear') systems.
    """
    import os
    os.system('cls' if os.name == 'nt' else 'clear')


def print_console_menu(all_systems, selected):
    """
    Prints the interactive menu for console selection.

    Args:
        all_systems: A list of all available console systems.
        selected: A set of currently selected console systems.
    """
    from colorama import Fore, Style
    print("✅ Selecteer de consoles (typ het nummer om te selecteren, 'a' = alles selecteren, 'n' = niets, Enter om door te gaan):\n") # Select the consoles (type the number to select, 'a' = select all, 'n' = none, Enter to continue):
    for idx, systeem in enumerate(all_systems, 1):
        kleur = Fore.GREEN if systeem in selected else Fore.RED # Green for selected, Red for unselected
        print(f"{idx:2d}. {kleur}{systeem}{Style.RESET_ALL}")
    print()


def choose_consoles(all_systems):
    """
    Allows the user to interactively select consoles from a list.

    Args:
        all_systems: A list of all available console systems.

    Returns:
        A list of selected console systems.
    """
    selected = set()
    while True:
        clear_console()
        print_console_menu(all_systems, selected)
        choice = input("Jouw keuze: ").strip().lower() # Your choice:
        if choice == "": # If user presses Enter, exit selection
            break
        elif choice == "a": # Select all
            selected = set(all_systems)
        elif choice == "n": # Select none
            selected = set()
        elif choice.isdigit(): # If a number is entered
            index = int(choice) - 1
            if 0 <= index < len(all_systems):
                systeem = all_systems[index]
                if systeem in selected:
                    selected.remove(systeem) # Deselect if already selected
                else:
                    selected.add(systeem) # Select if not selected
            else:
                print("❌ Ongeldig nummer.") # Invalid number.
                input("Druk op Enter om verder te gaan...") # Press Enter to continue...
        else:
            print("❌ Ongeldige invoer. Typ een nummer, 'a', 'n' of druk Enter om door te gaan.") # Invalid input. Type a number, 'a', 'n' or press Enter to continue.
            input("Druk op Enter om verder te gaan...") # Press Enter to continue...
    return list(selected)

def fetch_all_data(systems, api_key, store_id, store_url, user_agent, content_type):
    """
    Fetches and cleans price data for selected console systems from the BudgetGaming.nl API.
    It now correctly handles the HTML-like response and structures the data.
    """
    import requests
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
            set_console_title(f"Ophalen van prijzen voor {system}")
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            body_content = response.text
            if '<body>' in body_content.lower():
                body_start_index = body_content.lower().find('<body>') + len('<body>')
                body_end_index = body_content.lower().find('</body>', body_start_index)
                if body_end_index == -1:
                    body_end_index = len(body_content)
                body_content = body_content[body_start_index:body_end_index]

            lines = body_content.replace("&nbsp;", "").strip().split("<br>")
            
            # Skip empty lines and get header
            lines = [line.strip() for line in lines if line.strip()]
            if not lines:
                print(f"\n⚠️  Geen data gevonden voor {system}.")
                continue

            header = [h.strip().strip('"') for h in lines[0].split(';')]
            
            for line in lines[1:]:
                fields = [field.strip().strip('"') for field in line.split(';')]
                if len(fields) == len(header):
                    row_data = dict(zip(header, fields))
                    row_data['console'] = system
                    all_data.append(row_data)

        except Exception as e:
            print(f"\n❌ Fout bij ophalen van {system}: {e}")

    return all_data

def save_results(all_data, systems, script_dir):
    """
    Saves the fetched and cleaned data to a CSV file in the 'budgetgaming' directory.
    This version now intelligently deduplicates by keeping the entry with the lowest price.
    """
    import os
    import pandas as pd
    import numpy as np
    from datetime import datetime

    if not all_data:
        print("⚠️ Geen gegevens verzameld.")
        return

    df = pd.DataFrame(all_data)

    # --- Price Cleaning ---
    prijs_kolommen = ['laagsteprijs', 'verzendkostennieuw', 'laagsteprijstweedehands', 'verzendkostentweedehands']
    for col in prijs_kolommen:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.')
            df[col] = pd.to_numeric(df[col], errors='coerce')
        else:
            df[col] = 0.0
    df[prijs_kolommen] = df[prijs_kolommen].fillna(0.0)

    # --- EAN Cleaning ---
    df['ean'] = df['ean'].astype(str).str.replace(r'\D', '', regex=True).str.lstrip('0')
    df.dropna(subset=['ean'], inplace=True)
    df = df[df['ean'] != '']

    # --- Deduplication ---
    # Create a temporary column with the lowest price for sorting.
    df['temp_min_price'] = df[['laagsteprijs', 'laagsteprijstweedehands']].min(axis=1)
    # Sort by EAN and then by the lowest price, so the best price is first.
    df.sort_values('temp_min_price', ascending=True, inplace=True)
    # Drop duplicates, keeping the first entry (which now has the lowest price).
    df.drop_duplicates(subset=['ean'], keep='first', inplace=True)
    df.drop(columns=['temp_min_price'], inplace=True)

    # --- Final Processing ---
    df['laagsteprijs'] = (df['laagsteprijs'] - df['verzendkostennieuw']).round(2)
    df['laagsteprijstweedehands'] = (df['laagsteprijstweedehands'] - df['verzendkostentweedehands']).round(2)

    columns = ["titel", "console", "ean", "laagsteprijs", "laagsteprijstweedehands", "link"]
    for col in columns:
        if col not in df.columns:
            df[col] = '' if col in ['titel', 'console', 'ean', 'link'] else 0.0

    df = df[columns]
    df = df[~(df["titel"].isna() & df["ean"].isna())]

    consolenaam = "_".join(systems).replace(" ", "_").lower()
    datum = datetime.now().strftime("%d-%m-%Y")

    output_dir = os.path.abspath(os.path.join(script_dir, "..", "budgetgaming"))
    os.makedirs(output_dir, exist_ok=True)

    filename = os.path.join(output_dir, f"{consolenaam}_{datum}.csv")
    df.to_csv(filename, sep=";", index=False, decimal=',')
    print(f"\n✅ Bestand opgeslagen als: {filename}")
