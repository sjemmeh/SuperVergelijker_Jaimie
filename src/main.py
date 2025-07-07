import os
import sys

def prijzen_ophalen():
    """
    Calls the run_get function from the get_prices module to fetch prices.
    """
    from get_prices import run_get
    run_get()

def vergelijken():
    """
    Calls the run_vergelijken function from the compare module to compare prices.
    """
    from compare import run_vergelijken
    run_vergelijken()

def main_menu():
    """
    Displays the main menu of the BudgetGaming Comparer application.
    Allows the user to choose between fetching prices, comparing prices, or exiting.
    """
    while True:
        os.system('cls' if os.name == 'nt' else 'clear') # Clear console screen
        print("🎮 BudgetGaming Vergelijker") # BudgetGaming Comparer
        print("==========================\n")
        print("1. Prijzen ophalen") # Fetch Prices
        print("2. Prijzen vergelijken") # Compare Prices
        print("0. Afsluiten\n") # Exit

        keuze = input("Maak een keuze: ").strip() # Make a choice:

        if keuze == "1":
            prijzen_ophalen()
        elif keuze == "2":
            vergelijken()
        elif keuze == "0":
            print("\n👋 Tot ziens!") # Goodbye!
            break
        else:
            print("\n❌ Ongeldige keuze.") # Invalid choice.
            input("Druk op Enter om opnieuw te proberen.") # Press Enter to try again.

if __name__ == "__main__":
    main_menu() # Run the main menu when the script is executed