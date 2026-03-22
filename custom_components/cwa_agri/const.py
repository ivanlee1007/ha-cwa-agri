"""Constants for CWA Agri integration."""

DOMAIN = "cwa_agri"

# Crop types
CROPS = [
    {"id": "blueberry", "name": "藍莓", "name_en": "Blueberry"},
    {"id": "strawberry", "name": "草莓", "name_en": "Strawberry"},
    {"id": "rice", "name": "水稻", "name_en": "Rice"},
    {"id": "vegetable", "name": "蔬菜", "name_en": "Vegetable"},
    {"id": "orchid", "name": "蘭花", "name_en": "Orchid"},
    {"id": "tea", "name": "茶葉", "name_en": "Tea"},
    {"id": "other", "name": "其他", "name_en": "Other"},
]

# Growth stages by crop
GROWTH_STAGES = {
    "blueberry": [
        {"id": "dormant", "name": "休眠期", "name_en": "Dormant"},
        {"id": "budding", "name": "萌芽期", "name_en": "Budding"},
        {"id": "flowering", "name": "开花期", "name_en": "Flowering"},
        {"id": "fruiting", "name": "結果期", "name_en": "Fruiting"},
        {"id": "harvest", "name": "採收期", "name_en": "Harvest"},
    ],
    "strawberry": [
        {"id": "dormant", "name": "休眠期", "name_en": "Dormant"},
        {"id": "vegetative", "name": "營養生長期", "name_en": "Vegetative"},
        {"id": "flowering", "name": "开花期", "name_en": "Flowering"},
        {"id": "fruiting", "name": "結果期", "name_en": "Fruiting"},
        {"id": "harvest", "name": "採收期", "name_en": "Harvest"},
    ],
    "rice": [
        {"id": "seedling", "name": "育苗期", "name_en": "Seedling"},
        {"id": "tillering", "name": "分糵期", "name_en": "Tillering"},
        {"id": "heading", "name": "抽穗期", "name_en": "Heading"},
        {"id": "grain_fill", "name": "乳熟期", "name_en": "Grain Fill"},
        {"id": "maturity", "name": "成熟期", "name_en": "Maturity"},
    ],
    "vegetable": [
        {"id": "seedling", "name": "育苗期", "name_en": "Seedling"},
        {"id": "vegetative", "name": "營養期", "name_en": "Vegetative"},
        {"id": "flowering", "name": "开花期", "name_en": "Flowering"},
        {"id": "fruiting", "name": "結果期", "name_en": "Fruiting"},
        {"id": "harvest", "name": "採收期", "name_en": "Harvest"},
    ],
    "orchid": [
        {"id": "vegetative", "name": "營養生長期", "name_en": "Vegetative"},
        {"id": "spike", "name": "抽花梗期", "name_en": "Spike"},
        {"id": "flowering", "name": "开花期", "name_en": "Flowering"},
        {"id": "post_harvest", "name": "花後養株期", "name_en": "Post-Harvest"},
    ],
    "tea": [
        {"id": "dormant", "name": "休眠期", "name_en": "Dormant"},
        {"id": "budding", "name": "萌芽期", "name_en": "Budding"},
        {"id": "first_flush", "name": "頭水期", "name_en": "First Flush"},
        {"id": "second_flush", "name": "二水期", "name_en": "Second Flush"},
        {"id": "maturity", "name": "成熟期", "name_en": "Maturity"},
    ],
    "other": [
        {"id": "active", "name": "生長期", "name_en": "Active"},
        {"id": "mature", "name": "成熟期", "name_en": "Mature"},
    ],
}

# Default stages for new crops
DEFAULT_STAGES = [
    {"id": "active", "name": "生長期", "name_en": "Active"},
    {"id": "mature", "name": "成熟期", "name_en": "Mature"},
]

# Config entry keys
CONF_FARM_NAME = "farm_name"
CONF_HA_URL = "ha_url"
CONF_HA_TOKEN = "ha_token"
CONF_CROPS = "crops"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_REGION = "region"

# Entity names
ENTITY_PREFIX = "cwa_agri"
