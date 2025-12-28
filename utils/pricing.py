from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class CardPackage:
    code: str
    diamonds: int
    price_rub: int


@dataclass(frozen=True)
class StarsPackage:
    code: str
    diamonds: int
    stars: int


_CARD_PACKAGES: List[CardPackage] = [
    CardPackage(code="card_40", diamonds=40, price_rub=200),
    CardPackage(code="card_100", diamonds=100, price_rub=500),
    CardPackage(code="card_200", diamonds=200, price_rub=900),
    CardPackage(code="card_300", diamonds=300, price_rub=1499),
    CardPackage(code="card_600", diamonds=600, price_rub=2999),
]

_STARS_PACKAGES: List[StarsPackage] = [
    StarsPackage(code="stars_40", diamonds=40, stars=140),
    StarsPackage(code="stars_100", diamonds=100, stars=340),
    StarsPackage(code="stars_200", diamonds=200, stars=650),
]

CARD_PACKAGES_MAP: Dict[str, CardPackage] = {pkg.code: pkg for pkg in _CARD_PACKAGES}
STARS_PACKAGES_MAP: Dict[str, StarsPackage] = {pkg.code: pkg for pkg in _STARS_PACKAGES}


def list_card_packages() -> List[CardPackage]:
    return list(_CARD_PACKAGES)


def list_stars_packages() -> List[StarsPackage]:
    return list(_STARS_PACKAGES)


def get_card_package(code: str) -> Optional[CardPackage]:
    return CARD_PACKAGES_MAP.get(code)


def get_stars_package(code: str) -> Optional[StarsPackage]:
    return STARS_PACKAGES_MAP.get(code)
