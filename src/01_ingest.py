from pathlib import Path
import time

import requests


DATA_URL = "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip"

RAW_DIR = Path("data/raw")
ZIP_FILE = RAW_DIR / "online_retail_ii.zip"

CHUNK_SIZE = 1024 * 1024
MAX_RETRIES = 5


def download_file():
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if ZIP_FILE.exists():
        print(f"Raw archive already exists: {ZIP_FILE}")
        return

    headers = {
        "User-Agent": "Retail-Commercial-Intelligence/1.0"
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"\nDownload attempt {attempt}/{MAX_RETRIES}")

            with requests.get(
                DATA_URL,
                headers=headers,
                stream=True,
                timeout=(30, 120),
            ) as response:

                response.raise_for_status()

                total_size = int(response.headers.get("content-length", 0))
                downloaded = 0

                temp_file = ZIP_FILE.with_suffix(".part")

                with open(temp_file, "wb") as file:
                    for chunk in response.iter_content(
                        chunk_size=CHUNK_SIZE
                    ):
                        if chunk:
                            file.write(chunk)
                            downloaded += len(chunk)

                            if total_size:
                                percent = downloaded / total_size * 100
                                print(
                                    f"\rDownloaded: {percent:6.2f}%",
                                    end="",
                                )

                print()

                temp_file.replace(ZIP_FILE)

                print("\nDownload completed successfully.")
                print(f"Saved to: {ZIP_FILE}")

                if total_size:
                    print(f"File size: {downloaded / 1024 / 1024:.2f} MB")

                return

        except requests.RequestException as error:
            print(f"\nDownload failed: {error}")

            temp_file = ZIP_FILE.with_suffix(".part")

            if temp_file.exists():
                temp_file.unlink()

            if attempt < MAX_RETRIES:
                wait_time = 2 ** attempt
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise RuntimeError(
                    "Dataset download failed after all retry attempts."
                ) from error


def main():
    print("=" * 60)
    print("ONLINE RETAIL II — RAW DATA INGESTION")
    print("=" * 60)

    print("\nSource: UCI Machine Learning Repository")
    print("Dataset: Online Retail II")
    print(f"Destination: {ZIP_FILE}")

    download_file()


if __name__ == "__main__":
    main()