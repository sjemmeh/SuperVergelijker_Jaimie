import os
import sys

def set_console_title(title):
    """
    Sets the title of the console window.
    Works for CMD, PowerShell, and most Unix-like terminals.
    """
    if sys.platform.startswith('win'):
        # For Windows (CMD, PowerShell)
        os.system(f'title {title}')
    elif sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
        # For Linux/macOS (most terminals that support ANSI escape codes)
        sys.stdout.write(f'\x1b]2;{title}\x07')
        sys.stdout.flush()
    else:
        print(f"Warning: Unable to set console title on unsupported platform: {sys.platform}")

def get_prices():
    """
    Calls the run_get function from the get_prices module to fetch prices.
    """
    from get_prices import run_get
    run_get()

def compare():
    """
    Calls the run_vergelijken function from the compare module to compare prices.
    """
    from compare import run_compare
    run_compare()

def main_menu():
    app_title = "BudgetGaming Vergelijker"  # BudgetGaming Comparer
    """
    Displays the main menu of the BudgetGaming Comparer application.
    Allows the user to choose between fetching prices, comparing prices, or exiting.
    """
    while True:
        set_console_title(app_title)
        os.system('cls' if os.name == 'nt' else 'clear') # Clear console screen
        print("🎮 BudgetGaming Vergelijker") # BudgetGaming Comparer
        print("==========================\n")
        print("1. Prijzen ophalen") # Fetch Prices
        print("2. Prijzen vergelijken") # Compare Prices
        print("0. Afsluiten\n") # Exit

        keuze = input("Maak een keuze: ").strip() # Make a choice:

        if keuze == "1":
            set_console_title("Prijzen ophalen") # Fetching Prices
            get_prices()
        elif keuze == "2":
            set_console_title("Prijzen vergelijken") # Comparing Prices
            compare()
        elif keuze == "0":
            print("\n👋 Tot ziens!") # Goodbye!
            break
        else:
            print("\n❌ Ongeldige keuze.") # Invalid choice.
            input("Druk op Enter om opnieuw te proberen.") # Press Enter to try again.

if __name__ == "__main__":
    main_menu() # Run the main menu when the script is executed