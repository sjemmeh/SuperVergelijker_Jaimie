# 🎮 BudgetGaming Vergelijker

Een script om automatisch prijzen op te halen van BudgetGaming.nl en deze te vergelijken met je eigen Magento-export.

---

## ✅ Functies

* Haalt prijzen op per console van BudgetGaming.nl
* Vergelijkt deze met een Magento-exportbestand
* Detecteert prijsdalingen
* Exporteert resultaten naar CSV-bestanden

---

## 📁 Structuur

```
SuperVergelijker_Jaimie/
├── resultaat/ # Hier komen je CSV-bestanden
├── src/
│ ├── get_prices.py # Ophalen van prijzen
│ ├── compare.py # Vergelijken van prijzen
│ ├── main.py # Hoofdmenu
│ ├── consoles.txt # Lijst met consoles
│ ├── .env # API instellingen
│ ├── requirements.txt
│ └── vergelijker_env/ # Virtuele omgeving (automatisch aangemaakt)
├── start.bat # Start het programma (Windows)
```

---

## ▶️ Gebruik

### 1. Vereisten

* Windows
* Python 3.13+

### 2. Starten

Dubbelklik op `start.bat`.

De eerste keer wordt automatisch een virtuele omgeving aangemaakt en de benodigde modules geïnstalleerd.

---

## ⚙️ .env voorbeeld

Zorg dat er in `src/.env` een bestand staat met de volgende inhoud:

BUDGETGAMING_API_KEY=JouwAPIKey
BUDGETGAMING_STORE_ID=JouwStoreID
STORE_URL=https://www.budgetgaming.nl/budgetgamingfeed.php
HEADERS_USER_AGENT=Mozilla/5.0
HEADERS_CONTENT_TYPE=text/html


---

## 📌 consoles.txt voorbeeld

Lijst met consoles (één per regel), bijvoorbeeld:

ps5
switch
xboxone
ps4