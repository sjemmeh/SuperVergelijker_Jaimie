import pandas as pd
from pathlib import Path
from typing import List, Optional
from datetime import datetime


def _print_titel(titel: str) -> None:
    print(f"\n{titel}\n" + "─" * len(titel))

def _select_file(caption: str, files: List[Path]) -> Optional[Path]:
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


def _load_prijzen(path: Path) -> pd.DataFrame:
    prijzen = pd.read_csv(path, sep=";", dtype=str)
    prijzen["ean"] = prijzen["ean"].str.strip()
    return prijzen

def _parse_magento_export(path: Path) -> pd.DataFrame:
    skus, prijzen_magento = [], []
    with open(path, encoding="utf-8") as f:
        next(f)
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
        "prijs_magento": prijzen_magento
    })
    df["ean"] = df["catalog_product_attribute.sku"].str[:-1].str.strip()
    df["type"] = df["catalog_product_attribute.sku"].str[-1].str.upper()
    return df

def _vergelijk_prijzen(magento: pd.DataFrame, prijzen: pd.DataFrame) -> pd.DataFrame:
    merged = magento.merge(prijzen, on="ean", how="left")
    for col in ("laagsteprijs", "laagsteprijstweedehands"):
        merged[col] = pd.to_numeric(merged[col], errors="coerce")
    merged["min_laagste"] = merged[["laagsteprijs", "laagsteprijstweedehands"]].min(axis=1)
    merged["prijsverschil"] = merged["prijs_magento"] - merged["min_laagste"]
    return merged[(~merged["min_laagste"].isna()) & (merged["prijsverschil"] > 0)].copy()

def _export_aanbiedingen(df: pd.DataFrame, naam_basis: str) -> None:
    export_dir = Path(__file__).resolve().parent.parent / "prijsdalingen"
    export_dir.mkdir(exist_ok=True)
    datum = datetime.now().strftime("%d-%m-%Y")
    export_path = export_dir / f"prijsdalingen_{datum}.csv"
    
    kolommen = [
        "catalog_product_attribute.sku",
        "titel",
        "min_laagste",
        "console",
        "prijs_magento"
    ]
    df[kolommen].to_csv(export_path, sep=";", index=False)
    print(f"\n📂 Aanbiedingen opgeslagen in: {export_path}")

def run_vergelijken() -> None:
    _print_titel("📊 Vergelijk Magento-export met prijsbestand")
    project_root = Path(__file__).resolve().parent.parent
    resultaat_path = _select_file("📄 Kies resultaatbestand:", sorted((project_root / "resultaat").glob("*.csv")))
    if not resultaat_path:
        input("Druk op Enter om terug te keren...")
        return

    magento_path = _select_file("📁 Kies Magento-exportbestand:", sorted(project_root.glob("*.csv")))
    if not magento_path:
        input("Druk op Enter om terug te keren...")
        return

    try:
        prijzen_df = _load_prijzen(resultaat_path)
        magento_df = _parse_magento_export(magento_path)
        aanbiedingen_df = _vergelijk_prijzen(magento_df, prijzen_df)
    except Exception as exc:
        print(f"❌ Fout tijdens verwerking: {exc}")
        input("Druk op Enter om terug te keren...")
        return

    if aanbiedingen_df.empty:
        print("\nℹ️ Geen prijsdalingen gevonden.")
    else:
        _print_titel(f"📋 {len(aanbiedingen_df)} aanbiedingen gevonden:")
        print(aanbiedingen_df[[
            "catalog_product_attribute.sku",
            "titel",
            "min_laagste",
            "console",
            "prijs_magento"
        ]].to_string(index=False))
        _export_aanbiedingen(aanbiedingen_df, resultaat_path.stem)

    input("\n📅 Vergelijking voltooid. Druk op Enter om terug te keren...")
