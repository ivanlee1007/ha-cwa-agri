# CWA Agri - Home Assistant Integration

🌾 **CWA 農業報告整合** - 為 Home Assistant 提供 CWA 農業氣象設定介面，並將設定值暴露為 Entities，供 OpenClaw CWA Skill 讀取。

---

## 功能特色

- ✅ **友善的設定精靈 UI** - 在 Home Assistant 設定頁面直接輸入農場資訊
- ✅ **支援多種作物** - 藍莓、草莓、水稻、蔬菜、蘭花、茶葉等
- ✅ **生長階段設定** - 根據作物類型選擇對應的生長階段
- ✅ **位置資訊** - 自動抓取 HA 的位置，也可手動設定
- ✅ **設定同步** - OpenClaw CWA Skill 可直接讀取 HA Entities 取得設定

---

## 安裝方式

### 方法一：手動安裝

1. 下載此 repo
2. 將 `custom_components/cwa_agri` 資料夾複製到 Home Assistant 的 `config/custom_components/` 目錄
3. 重啟 Home Assistant

### 方法二：HACS（未來支援）

敬請期待...

---

## 設定方式

### Step 1: 基本資訊

```
農場名稱：呼密·藍莓農場
Home Assistant URL：http://homeassistant:8123
長期訪問令牌：eyJhbGc...
```

> 💡 **如何建立長期訪問令牌？**
> Home Assistant → 右上角大頭貼 → 個人 → 長期訪問令牌 → 建立

### Step 2: 作物設定

選擇種植的作物及其生長階段：

| 作物 | 生長階段選項 |
|------|-------------|
| 藍莓 | 休眠期、萌芽期、开花期、結果期、採收期 |
| 草莓 | 休眠期、營養生長期、开花期、結果期、採收期 |
| 水稻 | 育苗期、分糵期、抽穗期、乳熟期、成熟期 |
| 蔬菜 | 育苗期、營養期、开花期、結果期、採收期 |
| 蘭花 | 營養生長期、抽花梗期、开花期、花後養株期 |
| 茶葉 | 休眠期、萌芽期、頭水期、二水期、成熟期 |

### Step 3: 位置設定（選填）

系統會自動帶入 Home Assistant 的位置，也可自行修改。

---

## 與 OpenClaw CWA Skill 搭配使用

此整合會在 HA 中建立以下 Entities：

| Entity | 說明 |
|--------|------|
| `sensor.cwa_agri_*_settings` | 所有設定的 JSON（主要讀取來源） |

### OpenClaw CWA Skill 讀取方式

```javascript
// sync_ha_config.js - 從 HA 同步設定
const HA_URL = "http://homeassistant:8123";
const HA_TOKEN = process.env.HA_TOKEN;

// 讀取 HA Entities
const response = await fetch(`${HA_URL}/api/states`, {
  headers: {
    "Authorization": `Bearer ${HA_TOKEN}`,
    "Content-Type": "application/json"
  }
});

const states = await response.json();
const cwaSettings = states.find(s => s.entity_id.startsWith("sensor.cwa_agri") && s.entity_id.endsWith("_settings"));

if (cwaSettings) {
  const config = JSON.parse(cwaSettings.state);
  console.log("農場名稱:", config.farm_name);
  console.log("作物:", config.crops);
  // ... 寫入 cwa_config.json
}
```

---

## 資料格式

設定儲存格式：

```json
{
  "farm_name": "呼密·藍莓農場",
  "ha_url": "http://homeassistant:8123",
  "ha_token": "eyJhbGc...",
  "latitude": 23.123,
  "longitude": 120.456,
  "region": "台灣",
  "crops": [
    { "id": "blueberry", "name": "藍莓", "stage": "dormant" },
    { "id": "strawberry", "name": "草莓", "stage": "fruiting" }
  ]
}
```

---

## 檔案結構

```
custom_components/cwa_agri/
├── __init__.py          # 整合初始化
├── config_flow.py       # 設定精靈
├── const.py             # 常數定義
├── sensor.py            # Sensor 實體
├── manifest.json        # HACS 發布資訊
└── translations/
    ├── zh-Hant.json     # 繁體中文
    └── en.json          # 英文
```

---

## 需求

- Home Assistant 2024.1.0+
- OpenClaw CWA Skill（用於產生農業報告）

---

## License

MIT License
