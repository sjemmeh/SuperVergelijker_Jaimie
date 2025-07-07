import os
import sys
import io
import requests
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
from colorama import Fore, Style, init

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
    Fetches price data for selected console systems from BudgetGaming.nl API.

    Args:
        systems: A list of console systems to fetch data for.
        api_key: The API key for BudgetGaming.
        store_id: The store ID for BudgetGaming.
        store_url: The base URL of the BudgetGaming API.
        user_agent: User-Agent header for the request.
        content_type: Content-Type header for the request.

    Returns:
        A list of Pandas DataFrames, each containing data for a specific console.
    """
    import io
    import requests
    import pandas as pd
    from tqdm import tqdm # For progress bar

    base_url = f"{store_url}?page=budgetgamingfeed&winkel={store_id}&code={api_key}&console="
    headers = {
        "User-Agent": user_agent,
        "Content-Type": content_type
    }

    all_data = []

    for system in tqdm(systems, desc="📡 Consoles ophalen", unit="console"): # Fetching consoles
        url = base_url + system
        try:
            response = requests.get(url, headers=headers, timeout=10) # Make GET request
            response.raise_for_status() # Raise an exception for HTTP errors

            if "<html" in response.text.lower():
                print(f"\n⚠️  {system} overgeslagen: HTML ontvangen i.p.v. CSV.") # {system} skipped: HTML received instead of CSV.
                continue

            # Clean up response text and read as CSV
            text = response.text.replace("&nbsp", "").replace("<br>", "\n")
            csv_data = io.StringIO(text)

            try:
                df = pd.read_csv(csv_data, sep=";", dtype=str, engine="python")
                df["console"] = system # Add console name as a column
                all_data.append(df)
            except Exception as e:
                print(f"\n❌ Fout bij inlezen CSV voor {system}: {e}") # Error reading CSV for {system}:

        except Exception as e:
            print(f"\n❌ Fout bij ophalen van {system}: {e}") # Error fetching {system}:

    return all_data


def save_results(all_data, systems, script_dir):
    """
    Saves the fetched data to a CSV file in the 'resultaat' directory.

    Args:
        all_data: A list of DataFrames containing the fetched data.
        systems: A list of console systems for which data was fetched.
        script_dir: The directory where the script is located.
    """
    import os
    import pandas as pd
    from datetime import datetime

    if not all_data:
        print("⚠️ Geen gegevens verzameld.") # No data collected.
        return

    df = pd.concat(all_data, ignore_index=True) # Concatenate all dataframes
    # Select and reorder relevant columns
    columns = ["titel", "console", "ean", "laagsteprijs", "laagsteprijstweedehands"]
    df = df[columns]

    # Remove rows where both 'titel' and 'ean' are missing
    df = df[~(df["titel"].isna() & df["ean"].isna())]

    # Create filename based on selected consoles and current date
    consolenaam = "_".join(systems).replace(" ", "_").lower()
    datum = datetime.now().strftime("%d-%m-%Y")

    # Define output directory and create if it doesn't exist
    output_dir = os.path.abspath(os.path.join(script_dir, "..", "resultaat"))
    os.makedirs(output_dir, exist_ok=True)

    filename = os.path.join(output_dir, f"{consolenaam}_{datum}.csv")
    df.to_csv(filename, sep=";", index=False) # Save dataframe to CSV
    print(f"\n✅ Bestand opgeslagen als: {filename}") # File saved as: