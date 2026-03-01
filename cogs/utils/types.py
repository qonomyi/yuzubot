from typing import TypedDict


class HoYoUserData(TypedDict):
    user_id: int
    zzz_uid: int | str
    cookies: str


class DiscProperty(TypedDict):
    property_name: str
    property_id: int
    base: str
    level: int
    valid: bool
    system_id: int
    add: int


class DiscEquipSuit(TypedDict):
    suit_id: int
    name: str
    own: int
    desc1: str
    desc2: str
    icon: str
    cnt: int
    rarity: str


class Disc(TypedDict):
    id: int
    level: int
    name: str
    icon: str
    rarity: str
    properties: list[DiscProperty]
    main_properties: list[DiscProperty]
    equip_suit: DiscEquipSuit
    equipment_type: int
    invalid_property_cnt: int
    all_hit: bool
