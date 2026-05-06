#Final Project - Fenn Edmonds
#refrences: https://www.w3schools.com/python/ref_module_glob.asp
#https://www.w3schools.com/python/module_os.asp
#https://www.w3schools.com/python/pandas/pandas_csv.asp

import os
import glob
import pandas as pd
from kaggle.api.kaggle_api_extended import KaggleApi
from database import SessionLocal, engine
from classes import Base
from importer import ImportSpells 

#i'm using the legacy api keys for this
def DownloadKaggleData(download_path="./data"):
    api = KaggleApi()
    api.authenticate()
    api.dataset_download_files('mrpantherson/dndspells', path=download_path, unzip=True)

def RunData():
    data_dir = "./data"
    
    DownloadKaggleData(data_dir)
    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    if not csv_files:
        raise FileNotFoundError("No file :(")
    actual_csv_path = csv_files[0]
    df = pd.read_csv(actual_csv_path)

    #the people (me) named their material cost to match everything else so now i gotta fix it
    if "material cost" in df.columns:
        df.rename(columns={"material cost": "material_cost"}, inplace=True)
        df.to_csv(actual_csv_path, index=False)

    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        try:
            inserted_count = ImportSpells(session, actual_csv_path)
            print(f"Import finished!")
        except Exception as e:
            session.rollback()
            print(f"Bro something has gone WRONG")

if __name__ == "__main__":
    RunData()