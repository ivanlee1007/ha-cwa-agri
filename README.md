# UNiNUS CWA Agri - Home Assistant Integration

台灣中央氣象署 (CWA) 農業氣象報告整合，搭配 OpenClaw CWA Skill 使用。

## 功能

- **設定 UI**：安裝精靈配置農場、作物、位置
- **半自動 Stage Assistant**：系統推估生長階段，一鍵套用
- **內建 Dashboard 卡片**：`custom:cwa-agri-report-card` 自動註冊，不需另外安裝
- **手動刷新按鈕**：`button.cwa_agri_refresh` 觸發 OpenClaw 重新產生報告
- **安全憑證管理**：`ha_token` 不暴露在 entity 屬性中，寫入私有檔案
- **Demo Sensor**：首次安裝自動建立示範報表，推送真實報表後自動覆蓋
- **多值作物輸入**：選單式新增/刪除作物，不卡住流程

---

## 安裝方式（HACS Custom Repository）

1. Home Assistant → **HACS** → **Custom repositories**
2. 加入：`https://github.com/ivanlee1007/ha-cwa-agri`，Category：`Integration`
3. 安裝 **UNiNUS CWA Agri**
4. **重啟 Home Assistant**
5. 設定 → 裝置與服務 → 新增整合 → 搜尋「CWA Agri」

### Bridge 自動啟動（一鍵設定）

在 OpenClaw 機器上已設定 crontab @reboot 自動啟動 bridge：
```bash
# 確認 bridge 運作中
curl http://192.168.1.226:18801/health
```

---

## 設定精靈

1. **基本資訊**：農場名稱、HA URL、HA Token
2. **作物設定**：多值選單輸入作物名稱（輸入一個按一次 Enter）
3. **位置**：經緯度、區域（可選）

安裝後可隨時到整合的**選項**頁面修改作物清單。

---

## Entities 一覽

### Settings
| Entity | 說明 |
|--------|------|
| `sensor.cwa_agri_*_settings` | JSON 格式設定，供 OpenClaw sync 讀取 |

### Per-Crop（每種作物自動產生）
| Entity | 說明 |
|--------|------|
| `sensor.cwa_agri_<name>` | 作物狀態（目前階段） |
| `select.cwa_agri_<name>_stage` | 生長階段下拉選單 |
| `select.cwa_agri_<name>_stage_mode` | 手動 / 半自動模式 |
| `sensor.cwa_agri_<name>_stage_assistant` | 系統建議階段、信心度、原因 |
| `button.cwa_agri_<name>_apply_stage_suggestion` | 套用系統建議 |
| `button.cwa_agri_<name>_keep_current_stage` | 維持目前階段 |

### 全域
| Entity | 說明 |
|--------|------|
| `sensor.cwa_agri_report` | 農業氣象報告（由 OpenClaw 推送） |
| `button.cwa_agri_refresh` | 手動刷新按鈕（觸發 OpenClaw 重新產生報告） |

---

## Dashboard 卡片

直接在 Lovelace 使用：

```yaml
type: custom:cwa-agri-report-card
entity: sensor.cwa_agri_report
title: 農業氣象報告
```

- 內建於 integration，不需另外裝 repo
- 右上角 🔄 按鈕可手動刷新
- 卡片 v5.4+ 支援 compact layout

若出現 `Custom element doesn't exist`：
1. 確認 `ha-cwa-agri` 已更新到最新版
2. 重啟 Home Assistant
3. 移除舊的 `cwa-agri-dashboard` HACS repo / Resource（避免衝突）
4. 瀏覽器硬重新整理（Ctrl+Shift+R）

---

## 與 OpenClaw 搭配

```bash
cd ~/.openclaw/workspace/openclaw-cwa-skill
HA_TOKEN="<token>" node scripts/sync_and_report.js --all-sites
```

### 自動排程（已在 OpenClaw cron 設定）

| 排程 | 時間 |
|------|------|
| 日報 | 每天 07:00 Asia/Taipei |
| 週報 | 每週一 08:00 Asia/Taipei |

### 手動刷新流程

```
Dashboard 🔄 → button.cwa_agri_refresh → HA service
    → Bridge :18801 → OpenClaw WebSocket → Agent wakes
    → sync_and_report.js → sensor.cwa_agri_report → Card auto-refresh
```

---

## 版本紀錄

| 版本 | 重點 |
|------|------|
| v1.2.0 | Dashboard card 內建進 integration |
| v1.2.1 | 多站台 sync 支援 |
| v1.3.0 | sync_and_report.js wrapper、作物 object 格式 |
| v1.3.1 | Demo sensor（首次安裝預覽） |
| v1.3.2 | 憑證安全（ha_token 私有化，不暴露在 entity 屬性） |
| v1.3.3 | 手動刷新按鈕 + bridge HTTP→WS |

---

## 安全說明

- `ha_token` **不會**暴露在 entity 屬性中
- 憑證寫入 HA 端私有檔案 `/config/cwa_credentials.json`（只有 integration 能讀）
- `cwa_api_key` 保留在 OpenClaw 端

---

## 相關 Repo

- **HA Integration + Card**：[ha-cwa-agri](https://github.com/ivanlee1007/ha-cwa-agri)
- **OpenClaw Skill**：[openclaw-cwa-skill](https://github.com/ivanlee1007/openclaw-cwa-skill)
