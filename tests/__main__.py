"""Dev file for temporary testing"""

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from dsutils.ai.clustering import create_mapping_cluster
from dsutils.io.json import save_json

load_dotenv(override=True)

fp = Path(os.getenv("temp_file_path"))


def main():
    model_name = "BAAI/bge-large-en-v1.5"
    local_model_path = "Models/bge-large-en-v1.5"
    target_sectors = [
        "Information and communication",
        "Electricity, gas, steam and air conditioning supply",
        "Professional, scientific and technical activities",
        "Real estate activities",
        "Water supply; sewerage, waste management and remediation activities",
        "Manufacturing",
        "Administrative and support service activities",
        "Wholesale and retail trade; repair of motor vehicles and motorcycles",
        "Construction",
        "Manufacture of textiles, wearing apparel, leather and related products",
        "Transportation and storage",
        "Accommodation and food service activities",
        "Agriculture, forestry and fishing",
    ]

    df = pd.read_excel(fp, sheet_name="Edge Contacts")

    data_entries = (
        df["Primary code in national industry classification - description"]
        .dropna()
        .astype(str)
        .tolist()
    )

    map = create_mapping_cluster(
        target_sectors, data_entries, model_name, local_model_path
    )

    save_json("test.json", map)

    print(map)


if __name__ == "__main__":
    main()
