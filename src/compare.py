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

    Args:
        caption: The prompt message for the user.
        files: A list of Path objects representing the files to choose from.

    Returns:
        The selected Path object, or None if no valid selection is made.
    """
    if not files:
        print("❌ Geen bestanden gevonden.") # No files found.
        return None

    print(f"\n{caption}")
    for i, f in enumerate(files, 1):
        print(f"{i}. {f.name}")

    choice = input("\nSelecteer bestand (nummer): ").strip() # Select file (number):
    if not choice.isdigit() or not (1 <= int(choice) <= len(files)):
        print("❌ Ongeldige keuze.") # Invalid choice.
        return None

    return files[int(choice) - 1]


def _load_prices(path: Path) -> pd.DataFrame:
    """
    Loads price data from a CSV file into a Pandas DataFrame.

    Args:
        path: The path to the CSV file.

    Returns:
        A Pandas DataFrame containing the price data.
    """
    prijzen = pd.read_csv(path, sep=";", dtype=str)
    prijzen["ean"] = prijzen["ean"].str.strip()
    return prijzen

def _parse_magento_export(path: Path) -> pd.DataFrame:
    """
    Parses a Magento export CSV file and extracts SKU, price, EAN, and type.

    Args:
        path: The path to the Magento export CSV file.

    Returns:
        A Pandas DataFrame with parsed Magento product data.
    """
    skus, prijzen_magento = [], []
    with open(path, encoding="utf-8") as f:
        next(f) # Skip header row
        for line in f:
            parts = line.strip().split(",")
            if not parts:
                continue
            raw_sku = parts[0].strip().strip('"')
            if not raw_sku or raw_sku.lower() == "catalog_product_attribute.sku":
                continue
            skus.append(raw_sku)
            try:
                prijs_raw = parts[2].strip().strip('"')
                prijs_mag = float(prijs_raw.replace(",", "."))
            except (IndexError, ValueError):
                prijs_mag = None
            prijzen_magento.append(prijs_mag)

    df = pd.DataFrame({
        "catalog_product_attribute.sku": skus,
        "huidige_prijs_magento": prijzen_magento
    })
    df["ean"] = df["catalog_product_attribute.sku"].str[:-1].str.strip()
    df["type"] = df["catalog_product_attribute.sku"].str[-1].str.upper()
    return df

def _compare_prices(magento: pd.DataFrame, prijzen: pd.DataFrame) -> pd.DataFrame:
    """
    Compares Magento prices with the lowest prices from the price file.

    Args:
        magento: DataFrame containing Magento product data.
        prijzen: DataFrame containing price data from BudgetGaming.

    Returns:
        A DataFrame with products that have a price difference (Magento price > lowest price).
    """
    merged = magento.merge(prijzen, on="ean", how="left")
    # Convert price columns to numeric, coercing errors to NaN
    for col in ("laagsteprijs", "laagsteprijstweedehands"):
        merged[col] = pd.to_numeric(merged[col], errors="coerce")
    # Calculate the minimum of the lowest new and second-hand prices
    merged["min_laagste"] = merged.apply(
    lambda row: row["laagsteprijs"] if row["type"] == "N"
    else row["laagsteprijstweedehands"] if row["type"] == "G"
    else None,
    axis=1
)
    # Calculate the price difference
    merged["prijsverschil"] = merged["huidige_prijs_magento"] - merged["min_laagste"]
    # Filter for valid lowest prices and positive price differences
    return merged[(~merged["min_laagste"].isna()) & (merged["prijsverschil"] > 0)].copy()

def _export_aanbiedingen(df: pd.DataFrame, naam_basis: str) -> None:
    """
    Exports identified deals (price drops) to a CSV file.

    Args:
        df: DataFrame containing the deals.
        naam_basis: Base name for the export file.
    """
    # Define the export directory
    export_dir = Path(__file__).resolve().parent.parent / "prijsdalingen"
    export_dir.mkdir(exist_ok=True) # Create directory if it doesn't exist
    datum = datetime.now().strftime("%d-%m-%Y") # Get current date for filename
    export_path = export_dir / f"prijsdalingen_{datum}.csv"

    # Define columns to export
    kolommen = [
        "catalog_product_attribute.sku",
        "titel",
        "min_laagste",
        "console",
        "huidige_prijs_magento"
    ]
    df[kolommen].to_csv(export_path, sep=";", index=False) # Save to CSV
    print(f"\n📂 Aanbiedingen opgeslagen in: {export_path}") # Deals saved in:

def run_compare() -> None:
    """
    Main function to run the price comparison process.
    It guides the user through selecting files, performs the comparison,
    and displays/exports the results.
    """
    _print_titel("📊 Vergelijk Magento-export met prijsbestand") # Compare Magento export with price file
    project_root = Path(__file__).resolve().parent.parent
    # Select the result file (containing BudgetGaming prices)
    result_path = _select_file("📄 Kies resultaatbestand:", sorted((project_root / "resultaat").glob("*.csv"))) # Choose result file:
    if not result_path:
        input("Druk op Enter om terug te keren...") # Press Enter to return...
        return

    # Select the Magento export file
    magento_path = _select_file("📁 Kies Magento-exportbestand:", sorted(project_root.glob("*.csv"))) # Choose Magento export file:
    if not magento_path:
        input("Druk op Enter om terug te keren...") # Press Enter to return...
        return

    try:
        # Load and parse dataframes
        prijzen_df = _load_prices(result_path)
        magento_df = _parse_magento_export(magento_path)
        # Perform price comparison
        price_drop_offers_df = _compare_prices(magento_df, prijzen_df)
    except Exception as exc:
        print(f"❌ Fout tijdens verwerking: {exc}") # Error during processing:
        input("Druk op Enter om terug te keren...") # Press Enter to return...
        return

    if price_drop_offers_df.empty:
        print("\nℹ️ Geen prijsdalingen gevonden.") # No price drops found.
    else:
        _print_titel(f"📋 {len(price_drop_offers_df)} prijsdalingen gevonden:") # offers found:
        # Export the deals to a CSV file
        _export_aanbiedingen(price_drop_offers_df, result_path.stem)

    input("\n📅 Vergelijking voltooid. Druk op Enter om terug te keren...") # Comparison completed. Press Enter to return...