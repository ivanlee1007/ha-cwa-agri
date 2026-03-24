"""Constants for CWA Agri integration."""

DOMAIN = "cwa_agri"
ENTITY_PREFIX = "cwa_agri"

CARD_JS_FILENAME = "cwa-agri-dashboard.js"
CARD_STATIC_URL = f"/{DOMAIN}_static/{CARD_JS_FILENAME}"
CARD_RESOURCE_VERSION = "1.3.3"
CARD_RESOURCE_URL = f"{CARD_STATIC_URL}?v={CARD_RESOURCE_VERSION}"

CONF_FARM_NAME = "farm_name"
CONF_HA_URL = "ha_url"
CONF_HA_TOKEN = "ha_token"
CONF_CROPS = "crops"
CONF_REGION = "region"

CONF_STAGE_MODE = "stage_mode"
CONF_LAST_ACK_STAGE = "last_ack_stage"
CONF_LAST_ACK_MONTH = "last_ack_month"
CONF_PROFILE = "profile"

DEFAULT_REPORT_SENSOR_ENTITY = "sensor.cwa_agri_report"

STAGE_MODE_MANUAL = "manual"
STAGE_MODE_ASSIST = "assist"
DEFAULT_STAGE_MODE = STAGE_MODE_ASSIST

PROFILE_GENERIC = "generic"

# Generic stages used for custom crop names and fallback behavior.
DEFAULT_STAGES = [
    {"id": "dormant", "name": "休眠期", "name_en": "Dormant"},
    {"id": "vegetative", "name": "營養生長期", "name_en": "Vegetative"},
    {"id": "flowering", "name": "開花期", "name_en": "Flowering"},
    {"id": "fruiting", "name": "結果期", "name_en": "Fruiting"},
    {"id": "harvest", "name": "採收期", "name_en": "Harvest"},
]

GROWTH_STAGES = {
    "blueberry": [
        {"id": "dormant", "name": "休眠期", "name_en": "Dormant"},
        {"id": "budding", "name": "萌芽期", "name_en": "Budding"},
        {"id": "flowering", "name": "開花期", "name_en": "Flowering"},
        {"id": "fruiting", "name": "結果期", "name_en": "Fruiting"},
        {"id": "harvest", "name": "採收期", "name_en": "Harvest"},
    ],
    "strawberry": [
        {"id": "dormant", "name": "休眠期", "name_en": "Dormant"},
        {"id": "vegetative", "name": "營養生長期", "name_en": "Vegetative"},
        {"id": "flowering", "name": "開花期", "name_en": "Flowering"},
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
        {"id": "vegetative", "name": "營養生長期", "name_en": "Vegetative"},
        {"id": "flowering", "name": "開花期", "name_en": "Flowering"},
        {"id": "fruiting", "name": "結果期", "name_en": "Fruiting"},
        {"id": "harvest", "name": "採收期", "name_en": "Harvest"},
    ],
    "orchid": [
        {"id": "vegetative", "name": "營養生長期", "name_en": "Vegetative"},
        {"id": "spike", "name": "抽花梗期", "name_en": "Spike"},
        {"id": "flowering", "name": "開花期", "name_en": "Flowering"},
        {"id": "post_harvest", "name": "花後養株期", "name_en": "Post-Harvest"},
    ],
    "tea": [
        {"id": "dormant", "name": "休眠期", "name_en": "Dormant"},
        {"id": "budding", "name": "萌芽期", "name_en": "Budding"},
        {"id": "first_flush", "name": "頭水期", "name_en": "First Flush"},
        {"id": "second_flush", "name": "二水期", "name_en": "Second Flush"},
        {"id": "maturity", "name": "成熟期", "name_en": "Maturity"},
    ],
    PROFILE_GENERIC: DEFAULT_STAGES,
}

PROFILE_LABELS = {
    "blueberry": "藍莓",
    "strawberry": "草莓",
    "rice": "水稻",
    "vegetable": "蔬菜",
    "orchid": "蘭花",
    "tea": "茶葉",
    PROFILE_GENERIC: "通用作物",
}

PROFILE_KEYWORDS = {
    "blueberry": ["藍莓", "blueberry"],
    "strawberry": ["草莓", "strawberry"],
    "rice": ["水稻", "rice", "稻"],
    "vegetable": ["蔬菜", "番茄", "tomato", "辣椒", "黃瓜", "小黃瓜", "葉菜", "vegetable"],
    "orchid": ["蘭花", "orchid"],
    "tea": ["茶", "tea"],
}

ASSIST_MONTH_MAP = {
    "blueberry": {
        1: "dormant", 2: "dormant", 3: "budding", 4: "flowering",
        5: "fruiting", 6: "fruiting", 7: "harvest", 8: "harvest",
        9: "budding", 10: "budding", 11: "dormant", 12: "dormant",
    },
    "strawberry": {
        1: "fruiting", 2: "fruiting", 3: "harvest", 4: "harvest",
        5: "vegetative", 6: "vegetative", 7: "vegetative", 8: "vegetative",
        9: "vegetative", 10: "flowering", 11: "flowering", 12: "fruiting",
    },
    "rice": {
        1: "maturity", 2: "maturity", 3: "seedling", 4: "seedling",
        5: "tillering", 6: "heading", 7: "grain_fill", 8: "maturity",
        9: "maturity", 10: "seedling", 11: "tillering", 12: "maturity",
    },
    "vegetable": {
        1: "vegetative", 2: "vegetative", 3: "flowering", 4: "flowering",
        5: "fruiting", 6: "fruiting", 7: "harvest", 8: "harvest",
        9: "vegetative", 10: "vegetative", 11: "flowering", 12: "fruiting",
    },
    "orchid": {
        1: "flowering", 2: "flowering", 3: "post_harvest", 4: "vegetative",
        5: "vegetative", 6: "vegetative", 7: "vegetative", 8: "spike",
        9: "spike", 10: "flowering", 11: "flowering", 12: "flowering",
    },
    "tea": {
        1: "dormant", 2: "budding", 3: "first_flush", 4: "first_flush",
        5: "second_flush", 6: "second_flush", 7: "maturity", 8: "maturity",
        9: "budding", 10: "first_flush", 11: "maturity", 12: "dormant",
    },
    PROFILE_GENERIC: {
        1: "dormant", 2: "dormant", 3: "vegetative", 4: "vegetative",
        5: "flowering", 6: "flowering", 7: "fruiting", 8: "fruiting",
        9: "harvest", 10: "harvest", 11: "vegetative", 12: "dormant",
    },
}

# ── CWA F-A0010-001 農業氣象 縣市→地區 映射表 ──
# 使用者選縣市，系統自動對應到 F-A0010-001 的 6 個地區
CWA_COUNTY_TO_REGION = {
    "基隆市": "北部地區",
    "臺北市": "北部地區",
    "新北市": "北部地區",
    "桃園市": "北部地區",
    "新竹市": "北部地區",
    "新竹縣": "北部地區",
    "苗栗縣": "中部地區",
    "臺中市": "中部地區",
    "彰化縣": "中部地區",
    "南投縣": "中部地區",
    "雲林縣": "中部地區",
    "嘉義縣": "南部地區",
    "嘉義市": "南部地區",
    "臺南市": "南部地區",
    "高雄市": "南部地區",
    "屏東縣": "南部地區",
    "宜蘭縣": "東北部地區",
    "花蓮縣": "東部地區",
    "臺東縣": "東南部地區",
    "澎湖縣": "南部地區",
    "金門縣": "中部地區",
    "連江縣": "北部地區",
}

# 下拉選單用的 22 縣市列表（F-C0032-001 官定）
CWA_COUNTIES = list(CWA_COUNTY_TO_REGION.keys())
