# CWA Agri - Home Assistant Integration

🌾 **CWA 農業報告整合** - 為 Home Assistant 提供 CWA 農業氣象設定介面，並一站式包含 Lovelace 顯示卡片。

---

## 功能特色

- ✅ **友善的設定精靈 UI** - 在 Home Assistant 設定頁面直接輸入農場資訊
- ✅ **支援多種作物** - 藍莓、草莓、水稻、蔬菜、蘭花、茶葉等
- ✅ **生長階段設定** - 根據作物類型選擇對應的生長階段
- ✅ **位置資訊** - 自動抓取 HA 的位置，也可手動設定
- ✅ **內建 Dashboard 卡片** - 無需另外安裝，UI 直接可選 `CWA Agri Report Card`
- ✅ **設定同步** - OpenClaw CWA Skill 可直接讀取 HA Entities 取得設定

---

## 安裝方式

### 方法 1：透過 HACS 安裝（推薦）

1. 在 Home Assistant 開啟 **HACS**
2. 進入 **設定** → **Custom repositories**
3. 填入：
   ```
   Repository: https://github.com/ivanlee1007/ha-cwa-agri
   Category: Integration
   ```
4. 按 **新增**
5. 回到 HACS 首頁，搜尋 **CWA Agri**
6. 點進去 → **下載 / Download**

### 方法 2：手動安裝

1. 下載此 repo
2. 將 `custom_components/cwa_agri` 資料夾複製到 Home Assistant 的 `config/custom_components/` 目錄
3. 重啟 Home Assistant

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
| 蔬菜 | 育苗期、營養期、开花期、结果期、採收期 |
| 蘭花 | 營養生長期、抽花梗期、开花期、花後養株期 |
| 茶葉 | 休眠期、萌芽期、頭水期、二水期、成熟期 |

### Step 3: 位置設定（選填）

系統會自動帶入 Home Assistant 的位置，也可自行修改。

---

## 新增 Dashboard 卡片

安裝完成並設定後，在 HA Dashboard 新增卡片：

1. 進入 Dashboard → 編輯 → 新增卡片
2. 搜尋 **CWA Agri Report Card** 或找到 **CWA Agri**
3. 選擇並新增

卡片會自動讀取 `sensor.cwa_agri_report`（由 OpenClaw CWA Skill 產生）

---

## 與 OpenClaw CWA Skill 搭配使用

### 安裝 OpenClaw CWA Skill

```bash
# 在 OpenClaw 主機
cp -r skills/openclaw-cwa-skill ~/.openclaw/skills/
```

### 同步 HA 設定到 OpenClaw

此整合會在 HA 中建立設定 Entities，OpenClaw 可自動同步：

```bash
cd ~/.openclaw/skills/openclaw-cwa-skill

# 設定環境變數
export HA_TOKEN="your_long_lived_access_token"
export HA_URL="http://homeassistant:8123"

# 同步設定
node scripts/sync_ha_config.js
```

**特點**：
- ✅ 自動從 HA 讀取所有設定
- ✅ 合併到現有 `cwa_config.json`
- ✅ **保留原有的 CWA API Key**（不從 HA 讀取）
- ✅ 支援 `--dry-run` 測試模式

### OpenClaw 產出報告到 HA

```
設定同步 → OpenClaw CWA Skill 產生報告 → 推送 sensor.cwa_agri_report → Dashboard 顯示
```

OpenClaw 需要處理的 Entity：

| Entity | 用途 |
|--------|------|
| `sensor.cwa_agri_report` | OpenClaw 產生的農業報告（需手動建立或由整合建立） |

> 📝 **注意**：`sensor.cwa_agri_report` 由 OpenClaw CWA Skill 產生並推送，HA Integration 本身不建立此 Entity。

---

## 資料格式

HA Integration 產生的設定 Entity：

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
├── manifest.json        # 整合發布資訊（含前端插件設定）
├── translations/
│   ├── zh-Hant.json     # 繁體中文
│   └── en.json          # 英文
└── www/
    └── cwa-agri-dashboard.js  # Lovelace 卡片 ⭐內建
```

---

## 需求

- Home Assistant 2024.1.0+
- OpenClaw CWA Skill（用於產生農業報告並推送到 HA）

---

## License

MIT License
