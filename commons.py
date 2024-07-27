"""
Commons objects
"""
from pydantic import BaseModel, Field


class RentalItem(BaseModel):
    address: str
    surface_m2: int
    price_eur_per_year_per_m2: float
    internal_ref: str = Field(default="")
