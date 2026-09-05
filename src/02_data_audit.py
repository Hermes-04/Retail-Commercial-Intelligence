from pathlib import Path

import pandas as pd


INPUT_FILE = Path("data/raw/online_retail_II.xlsx")


def main():
    print("=" * 70)
    print("ONLINE RETAIL II — DATA QUALITY AUDIT")
    print("=" * 70)

    print(f"\nFile: {INPUT_FILE}")

    # Inspect workbook
    excel_file = pd.ExcelFile(INPUT_FILE)

    print("\nSheets:")
    for sheet in excel_file.sheet_names:
        print(f"  - {sheet}")

    # Load all sheets
    sheets = pd.read_excel(INPUT_FILE, sheet_name=None)

    for sheet_name, df in sheets.items():

        print("\n" + "=" * 70)
        print(f"SHEET: {sheet_name}")
        print("=" * 70)

        print(f"\nRows: {len(df):,}")
        print(f"Columns: {len(df.columns)}")

        print("\nColumns:")
        for column in df.columns:
            print(f"  - {column}")

        print("\nData types:")
        print(df.dtypes)

        print("\nMissing values:")
        missing = df.isna().sum()
        missing_pct = (missing / len(df) * 100).round(2)

        missing_report = pd.DataFrame({
            "missing_count": missing,
            "missing_pct": missing_pct
        })

        print(missing_report[missing_report["missing_count"] > 0])

        print("\nDuplicate rows:")
        print(df.duplicated().sum())

        print("\nSample records:")
        print(df.head(5).to_string())

        print("\nNumeric summary:")
        print(df.describe().to_string())

    print("\n" + "=" * 70)
    print("AUDIT COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()