"""
Functions for the scraping module
"""
from bs4 import BeautifulSoup
import requests
import pandas as pd
import datetime as dt

from pydantic import BaseModel
from typing import List, Tuple, Optional
from sqlalchemy import create_engine, text

from bnp_re_parser import parser as bnp_parser
from jll_parser import full_parser as jll_parser

BUREAUX_TABLE = "location_bureaux"

def get_engine():
    """
    Create engine with suitable config
    """
    user_name = "postgres"
    password = "hLlq3FhZ9MRGzLeQZfeD"
    host = "localhost"
    db_name = "postgres"

    return create_engine(f"postgresql+psycopg2://{user_name}:{password}@{host}/{db_name}", echo=False)


def save_data(df):
    """
    Save provided dataframe to database
    """
    df.to_sql(name=BUREAUX_TABLE, con=get_engine(), if_exists="append", index=False)
    

def scrape_save():
    """
    Scrape data from multiple sources and save the result
    """
    parser_dict = {
        "JLL": jll_parser,
        "BNP": bnp_parser
    }
    today_dt = dt.date.today()
    df = pd.DataFrame()
    
    for source_str, parser in parser_dict.items():
        nbr_items, list_items = parser()

        if nbr_items != len(list_items):
            print(f"Something wrong for {source_str}! (multiple pages?)")
            print(f"{nbr_items=} and {len(list_items)=}")
        else:
            print(f"Fetched {nbr_items} items from {source_str}.")

        aux_df = pd.DataFrame.from_records([item.__dict__ for item in list_items])
        aux_df["date"] = today_dt
        aux_df["source"] = source_str
        
        df=df.append(aux_df)
    
    save_data(df)

    
def load_data() -> pd.DataFrame:
    """
    Load data from database
    """
    with get_engine().begin() as conn:
        query = text(f"SELECT * FROM {BUREAUX_TABLE};")
        return pd.read_sql_query(query, conn)
