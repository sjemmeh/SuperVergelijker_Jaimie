import pandas as pd
from pathlib import Path
from typing import List, Optional
from datetime import datetime

def _print_titel(titel: str) -> None:
    """
    Prints a formatted title with an underline.
    """
    print(f"\n{titel}\n" + "─" * len(titel))

def _select_file(caption: str, files: List[Path]) -> Optional[Path]:
    """
    Allows the user to select a file from a list of files.
    """
    if not files:
        print("❌ Geen bestanden gevonden.")
        return None
    print(f"\n{caption}")
    for i, f in enumerate(files, 1):
        print(f"{i}. {f.name}")
    choice = input("\nSelecteer bestand (nummer): ").strip()
    if not choice.isdigit() or not (1 <= int(choice) <= len(files)):
        print("❌ Ongeldige keuze.")
        return None
    return files[int(choice) - 1]

def _clean_ean(ean_series: pd.Series) -> pd.Series:
    """
    Cleans EANs by removing non-digit characters and ensuring they are treated as strings.
    """
    return ean_series.astype(str).str.strip().str.replace(r'\D', '', regex=True).replace('', pd.NA)

def _clean_price(price_series: pd.Series) -> pd.Series:
    """
    Cleans price strings and converts to numeric.
    """
    cleaned_prices = price_series.astype(str).fillna('').str.replace(',', '.', regex=False).str.replace(r'[^\d.]', '', regex=True)
    cleaned_prices = cleaned_prices.apply(lambda x: x.split('.', 1)[0] + ('.' + x.split('.', 1)[1] if '.' in x else ''))
    return pd.to_numeric(cleaned_prices, errors='coerce')

def _load_prices(path: Path) -> pd.DataFrame:
    """
    Loads price data from a CSV, cleans it, and converts prices from cents.
    """
    prijzen = pd.read_csv(path, sep=";", dtype=str)
    prijzen['ean'] = _clean_ean(prijzen['ean'])
    prijzen.dropna(subset=['ean'], inplace=True)
    price_cols = ['laagsteprijs', 'laagsteprijstweedehands']
    for col in price_cols:
        if col in prijzen.columns:
            prijzen[col] = _clean_price(prijzen[col])
            prijzen[col] = prijzen[col] / 100.0
    prijzen['temp_min_price'] = prijzen[price_cols].min(axis=1)
    prijzen.sort_values('temp_min_price', ascending=True, inplace=True)
    prijzen.drop_duplicates(subset=['ean'], keep='first', inplace=True)
    prijzen.drop(columns=['temp_min_price'], inplace=True)
    return prijzen

def _parse_magento_export(path: Path) -> pd.DataFrame:
    """
    Parses a Magento export XLSX file and standardizes the EAN column.
    """
    df = pd.read_excel(path, sheet_name=0, dtype=str)
    df.rename(columns={
        'catalog_product_attribute.name': 'Title (magento)',
        'inventory_stock_status.qty': 'Current quantity (magento)',
        'catalog_product_attribute.price': 'Gsprijs (magento)'
    }, inplace=True)
    df['catalog_product_attribute.sku'] = df['catalog_product_attribute.sku'].astype(str).str.strip()
    df["ean"] = df["catalog_product_attribute.sku"].str[:-1]
    df["type"] = df["catalog_product_attribute.sku"].str[-1].str.upper()
    df['ean'] = _clean_ean(df['ean'])
    df.dropna(subset=['ean'], inplace=True)
    if 'Gsprijs (magento)' in df.columns:
        df['Gsprijs (magento)'] = _clean_price(df['Gsprijs (magento)'].astype(str))
    return df

def _compare_prices(magento: pd.DataFrame, prijzen: pd.DataFrame) -> pd.DataFrame:
    """
    Compares Magento prices with the lowest prices from the price file.
    """
    merged = magento.merge(prijzen, on="ean", how="inner")
    merged["Cheapest price (budgetgaming)"] = merged.apply(
        lambda row: row["laagsteprijs"] if row["type"] == "N"
        else row["laagsteprijstweedehands"] if row["type"] == "G"
        else None,
        axis=1
    )
    merged["Cheapest price (budgetgaming)"] = pd.to_numeric(merged["Cheapest price (budgetgaming)"], errors='coerce')
    merged["Price difference"] = (merged["Gsprijs (magento)"] - merged["Cheapest price (budgetgaming)"]).round(2)
    return merged

def _export_to_csv(df: pd.DataFrame, project_root: Path, result_path: Path) -> None:
    """
    Exports the DataFrame to a CSV file in the 'vergelijkingen' directory.
    """
    try:
        today_str = datetime.now().strftime("%d-%m-%Y")
        output_dir = project_root / "vergelijkingen"
        filename = f"vergelijking-{today_str}.csv"
        output_path = output_dir / filename

        # Prepare dataframe for export
        df_export = df.copy()
        df_export.rename(columns={
            "link": "BGLink", "ean": "BGEAN", "Title (magento)": "Titel",
            "Current quantity (magento)": "GSVoorraad", "Gsprijs (magento)": "GSPrijs",
            "Cheapest price (budgetgaming)": "Goedkoopste Prijs", "Price difference": "Verschil",
            "catalog_product_attribute.sku": "GST EAN"
        }, inplace=True)

        df_export['GSVoorraad'] = pd.to_numeric(df_export['GSVoorraad'], errors='coerce').fillna(0).astype(int)

        def is_lowest(row):
            return 'Y' if pd.isna(row['Goedkoopste Prijs']) or row['GSPrijs'] <= row['Goedkoopste Prijs'] else 'N'
        df_export['Laagste?'] = df_export.apply(is_lowest, axis=1)

        # Add new empty columns
        df_export["Gecheckt door"] = ""
        df_export["Is OK?"] = ""
        df_export["Datum"] = ""
        df_export["Opmerking"] = ""

        export_columns = [
            "BGLink", "BGEAN", "Titel", "GSVoorraad", "GSPrijs",
            "Goedkoopste Prijs", "Verschil", "Laagste?", "Gecheckt door", "Is OK?", "Datum", "Opmerking", "GST EAN"
        ]
        # Ensure all columns exist, fill with empty string if not
        for col in export_columns:
            if col not in df_export.columns:
                df_export[col] = ''
        
        df_export = df_export[export_columns] # Reorder and select columns
        
        df_export.to_csv(output_path, sep=";", index=False, decimal=',')
        
        print(f"\n✅ Gegevens succesvol geëxporteerd naar CSV: {output_path}")

    except Exception as e:
        print(f"❌ Er is een fout opgetreden bij het exporteren naar CSV: {e}")


def run_compare() -> None:
    """
    Main function to run the price comparison process.
    """
    _print_titel("📊 Vergelijk Magento-export met prijsbestand")
    project_root = Path(__file__).resolve().parent.parent
    
    result_path = _select_file("📄 Kies budgetgaming bestand:", sorted((project_root / "budgetgaming").glob("*.csv")))
    if not result_path:
        input("Druk op Enter om terug te keren...")
        return

    magento_path = _select_file("📁 Kies Magento-exportbestand:", sorted(project_root.glob("*.xlsx")))
    if not magento_path:
        input("Druk op Enter om terug te keren...")
        return

    try:
        prijzen_df = _load_prices(result_path)
        magento_df = _parse_magento_export(magento_path)
        comparison_df = _compare_prices(magento_df, prijzen_df)
    except Exception as exc:
        print(f"❌ Fout tijdens verwerking: {exc}")
        input("Druk op Enter om terug te keren...")
        return

    if comparison_df.empty:
        print("\nℹ️ Geen producten gevonden om te vergelijken.")
    else:
        _print_titel(f"📋 {len(comparison_df)} producten vergeleken:")
        _export_to_csv(comparison_df, project_root, result_path)

    input("\n📅 Vergelijking voltooid. Druk op Enter om terug te keren...")