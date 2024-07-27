"""
Module containing the JLL parser
"""
from bs4 import BeautifulSoup
import requests

from typing import List, Tuple, Optional

from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from commons import RentalItem

def parse_price(price_str) -> Optional[float]:
    """
    Parse price provided as string
    """
    try:
        return float(price_str.split("€")[0].strip())
    except ValueError:
        return 0
    
    
def parse_surface(surface_str) -> int:
    """
    Needs to support both format '1.203' and '1 203'!
    """
    return int(surface_str[:-2].replace(" ", "").replace(".", ""))


def get_rental_item(aux) -> Optional[RentalItem]:
    """
    Recover rental item contents
    """
    try:
        title = next(aux.find_all("span", class_="SRPPropertyCard__title")[0].children)
    except Exception as e:
        print("In JLL get get_rental_item, 'title' could not be found : ", aux)
        print(e)
        title = ""
        
    try:
        elts = [title] + [
            next(tag.children, "") for tag in aux.find_all("span", class_="SRPPropertyCard__address")]
        address = ", ".join([elt.upper() for elt in elts if elt])
    except StopIteration:
        address = title
        
    try:
        internal_ref = aux.find("a", href=True).get("href")
    except:
        print("No internal ref found for ", aux)
        internal_ref = ""
    
    try:
        for tag in aux.find_all("div", class_="PropertyMetric"):
            gen = tag.children
            reference = next(next(gen).children)
            metric_item = next(gen)
            if reference == "Loyer annuel":
                price_eur_per_year_per_m2 = parse_price(next(metric_item.children))
            if reference == "Surface":
                surface = parse_surface(next(metric_item.children))
            
        return RentalItem(
            address=address,
            surface_m2=surface,
            price_eur_per_year_per_m2=price_eur_per_year_per_m2,
            internal_ref=internal_ref,
        )
    except:
        print("Something went wrong when processing: ", aux)
        return None
    
def get_nbr_items(soup) -> int:
    """
    Get number of items
    """
    try:
        return int(next(soup.find_all("h3", class_="SRPOffersSearchSummary")[0].strong.children))
    except Exception as e:
        print("Something wrong in JLL.get_nbr_items: ")
        print(e)
        return 0

    
def get_rental_items(soup):
    """
    Get rental items from soup
    """
    try:
        return [get_rental_item(aux) for aux in soup.find_all(
            "div", {"class": "SRPPropertyCard SRPPropertyCard--default col-sm-6"})]
    except:
        return list()
    
    
def get_page_content(url = "https://immobilier.jll.fr/search?tenureType=rent&propertyType=office&city=MONTROUGE&postcode=92120") -> BeautifulSoup:
    """
    Recover page content in BeautifulSoup format
    """
    options = Options()
    options.add_argument("--headless")
    
    driver = webdriver.Firefox(options=options)
    driver.get(url)
    return BeautifulSoup(driver.page_source, 'html.parser')
    
    
def parser(soup: BeautifulSoup) -> Tuple[int, List[Optional[RentalItem]]]:
    """
    Parse data from JLL website
    
    NB: headers recovered from the initial request in my server (and added referrer). Cookies timing may need update!
    """
    nbr_items = get_nbr_items(soup) 
    rental_items = get_rental_items(soup)
        
    return nbr_items, rental_items


def full_parser() -> Tuple[int, List[Optional[RentalItem]]]:
    """
    Full processing of JLL page
    """
    return parser(get_page_content())