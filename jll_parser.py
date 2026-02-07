"""
Module containing the JLL parser
"""
import numpy as np
from bs4 import BeautifulSoup

from typing import List, Tuple, Optional

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import re
import traceback

from commons import RentalItem

#FIREFOX_SELENIUM_PROFILE_PATH = (
#    '/Users/OGabriel/Library/Application Support/Firefox/Profiles/fiy2r8a2.Selenium'
#)

FIREFOX_SELENIUM_PROFILE_PATH = (
    r"C:\Users\Personne\AppData\Local\Mozilla\Firefox\Profiles\utjbni1m.lenient_user"
)


def _extract_one_tag(tag):
    """
    Extract data (ref and value) from one tag
    """
    reference = ""
    value = "-"
    try:
        gen = tag.children
        reference = next(gen).span.get_text()
        value = re.sub(r"\s+", " ", next(gen).get_text())
    except Exception as e:
        print(f"Something wrong with {tag=}: {traceback.format_exc()}")

    return reference, value


def extract_ref_value_dict(item0) -> dict:
    """
    For given item, extract a dictionary with references and value

    Expected references:
    * Surface
    * Loyer par m2
    """
    ref_value_dict = dict()
    for tag in item0.find_all("div", {"class": "py-2.5 text-gray-500"})[0].find_all("p"):
        reference, value = _extract_one_tag(tag)
        ref_value_dict[reference] = value

    return ref_value_dict


def parse_price(price_str):# -> float | type(np.nan):
    """
    Parse price string to float.

    Accepts 'Nous consulter' -> np.nan.
    Accepts '204,76 € / m²' -> 204.76.
    Accepts '204.76 €' -> 204.76.
    Accepts '208,76 € / m2' -> 208.76.
    """
    if not price_str:
        return np.nan
    s = str(price_str).strip()
    s_low = s.lower()
    if "nous" in s_low:
        return np.nan
    m = re.search(r"(\d[\d\.,\s]*)", s)
    if not m:
        return np.nan
    num_str = m.group(1).strip()
    num_norm = num_str.replace(" ", "")
    if "." in num_norm and "," in num_norm:
        num_norm = num_norm.replace(".", "").replace(",", ".")
    else:
        if "," in num_norm:
            num_norm = num_norm.replace(",", ".")
    try:
        return float(num_norm)
    except Exception:
        print(f"{traceback.format_exc()}")
        return np.nan
    
    
def parse_surface(surface_str):# -> int:
    """
    Parse surface string into integer square meters.

    Supports '1.203', '1 203', '1 613 m² divisibles dès 598 m²'.
    Returns 0 on failure.
    """
    if not surface_str:
        return 0
    s = str(surface_str).strip()
    m = re.search(r'(\d[\d\.\s,]*)', s)
    if not m:
        return np.nan
    num_str = m.group(1).strip()
    s_norm = num_str.replace(' ', '')
    if ',' in s_norm and '.' in s_norm:
        s_norm = s_norm.replace('.', '').replace(',', '.')
    else:
        if ',' in s_norm:
            s_norm = s_norm.replace(',', '.')
        if '.' in s_norm:
            last_dot = s_norm.rfind('.')
            digits_after = len(s_norm) - last_dot - 1
            if digits_after == 3:
                s_norm = s_norm.replace('.', '')
    try:
        return int(float(s_norm))
    except Exception:
        return np.nan


def _extract_title(item0) -> str:
    """
    Extract title text from item or return '-' if not found.

    Try main span class first then alternate jll-red class. Raise on
    unexpected errors to let caller handle logging.
    """
    list_title = item0.find_all(
        "span",
        {"class": "font-helvetica block text-sm font-bold uppercase text-yellow-500"}
    )
    if len(list_title) > 0:
        return list_title[0].get_text()
    alt = item0.find_all(
        "span",
        {"class": "font-helvetica block text-sm font-bold uppercase text-jll-red"}
    )
    if len(alt) > 0:
        return alt[0].get_text()
    return "-"


def process_rental_item(item0) -> Optional[RentalItem]:
    """
    Recover rental item contents
    """
    title = "-"
    try:
        title = _extract_title(item0)
    except Exception as e:
        print("In JLL get get_rental_item, "
              "'title' could not be found : ", str(item0)[:15])
        print(f"{traceback.format_exc()}")

    try:
        elts = [title] + [
            elt.get_text()
            for elt in item0.find_all("span", {"class": "block text-base"})
        ]
        address = ", ".join([elt.upper() for elt in elts if elt])
    except StopIteration:
        address = title
        
    try:
        internal_ref = item0.find("a", href=True).get("href")
    except:
        print("No internal ref found for ", item0)
        internal_ref = ""
    
    try:
        ref_value_dict = extract_ref_value_dict(item0)
        price_eur_per_year_per_m2 = parse_price(ref_value_dict.get("Loyer annuel", "-"))
        surface = parse_surface(ref_value_dict.get("Surface", "-"))

        return RentalItem(
            address=address,
            surface_m2=int(surface),
            price_eur_per_year_per_m2=price_eur_per_year_per_m2,
            internal_ref=internal_ref,
        )
    except Exception:
        print(f"Something went wrong when processing: {str(item0)[:15]}, "
              f"{traceback.format_exc()}")
        return None
    
def get_nbr_items(soup) -> int:
    """
    Get number of items
    """
    try:
        return int(soup.find_all("h2", class_="text-2xl")[0].strong.get_text())
    except Exception as e:
        print(f"Something wrong in JLL.get_nbr_items: {traceback.format_exc()}")
        return 0

    
def get_rental_items(soup):
    """
    Get rental items from soup
    """
    try:
        return [process_rental_item(aux) for aux in soup.find_all(
            "div", {"class": "relative mx-auto shrink w-[268px]"})]
    except:
        return list()
    
    
def get_page_content(url = "https://immobilier.jll.fr/search?tenureType=rent&propertyType=office&city=MONTROUGE&postcode=92120") -> BeautifulSoup:
    """
    Recover page content in BeautifulSoup format
    """
    options = webdriver.FirefoxOptions()
    options.profile = webdriver.FirefoxProfile(FIREFOX_SELENIUM_PROFILE_PATH)
    driver = webdriver.Firefox(options)
    driver.get(
        "https://immobilier.jll.fr/search?tenureType=rent&propertyType=office&city=MONTROUGE&postcode=92120")

    WebDriverWait(driver, 120).until(EC.visibility_of_element_located(
        (By.XPATH, '/html/body/div[1]/div/div/div[2]/div/div[1]/div[1]/div/div[1]/div[1]/h2')))

    html_source = driver.page_source
    return BeautifulSoup(html_source, 'html.parser')
    
    
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