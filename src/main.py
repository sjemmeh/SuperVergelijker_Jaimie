import os
import sys

def prijzen_ophalen():
    from get_prices import run_get
    run_get()

def vergelijken():
    from compare import run_vergelijken
    run_vergelijken()

def main_menu():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("🎮 BudgetGaming Vergelijker")
        print("==========================\n")
        print("1. Prijzen ophalen")
        print("2. Prijzen vergelijken")
        print("0. Afsluiten\n")

        keuze = input("Maak een keuze: ").strip()

        if keuze == "1":
            prijzen_ophalen()
        elif keuze == "2":
            vergelijken()
        elif keuze == "0":
            print("\n👋 Tot ziens!")
            break
        else:
            print("\n❌ Ongeldige keuze.")
            input("Druk op Enter om opnieuw te proberen.")

if __name__ == "__main__":
    main_menu()
