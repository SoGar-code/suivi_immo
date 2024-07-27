"""
Module containing the BNP RE parser
"""
import json
from bs4 import BeautifulSoup
import requests

from typing import List, Tuple, Optional

from commons import RentalItem

def get_rental_item(aux) -> Optional[RentalItem]:
    """
    Recover rental item contents
    """
    try:
        data_dict = json.loads(aux.attrs.get("data-marker-data"))
        internal_ref = aux.attrs.get("href")
    except TypeError as e:
        #print("TypeError when processing: ", aux)
        print("==> Moving on!")
        return None

    try:
        return RentalItem(
            address=next(aux.find("span", class_="card-subtitle huge").children),
            surface_m2=int(data_dict["surface"]),
            price_eur_per_year_per_m2=float(data_dict["price_loc"]),
            internal_ref=internal_ref
        )
    except Exception as e:
        print("Something went wrong when processing: ", aux)
        print(e)
        return None
    
def parser(url="https://www.bnppre.fr/a-louer/bureau/hauts-de-seine-92/montrouge-92120/"
          ) -> Tuple[int, List[Optional[RentalItem]]]:
    """
    Parser for BNP RE website
    """
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    
    try:
        count_tag = soup.find_all("h2", id="search-list-results-count")
        count_str = next(count_tag[0].children)
        nbr_items = int(count_str.split("bureaux")[0].strip())
    except:
        nbr_items = 0
        
    try:
        raw_items = list(soup.find("ul", id="sidenav-offers-results-list").children)
        basic_rental_items = [get_rental_item(aux) for aux in raw_items if aux != "\n" and aux]
        rental_items = [rental_item for rental_item in basic_rental_items if rental_item and rental_item.address.rsplit(",")[-1].strip() == '92120 Montrouge']
        
    except:
        rental_items = list()
        
    return nbr_items, rental_items
