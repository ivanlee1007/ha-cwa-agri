# 故障排除 - UNiNUS CWA Agri

## 目錄

1. [Dashboard 卡片顯示「設定錯誤」](#1-dashboard-卡片顯示設定錯誤)
2. [硬刷新後卡片偶爾消失](#2-硬刷新後卡片偶爾消失)
3. [刷新按鈕無效](#3-刷新按鈕無效)
4. [Bridge 連線問題](#4-bridge-連線問題)
5. [JS 檔案載入相關知識](#5-js-檔案載入相關知識)

---

## 1. Dashboard 卡片顯示「設定錯誤」

### 症狀

- 卡片位置顯示「設定錯誤」或「Custom element doesn't exist」
- DevTools Console 看到錯誤，但 `[CWA Agri] card registered` 有出現

### 原因

這是 Lovelace 前端的 race condition：Dashboard HTML 解析時 JS 模組尚未完全載入，導致 custom element 無法正確初始化。

### 解決方案

1. **確保使用最新版**（v1.4.3+）— 已實作 stub-first 註冊機制，大幅降低 race condition
2. **硬刷新瀏覽器**：`Ctrl+Shift+R`（Windows/Linux）或 `Cmd+Shift+R`（Mac）
3. **清除瀏覽器快取**：
   - F12 開 DevTools → Application → Clear storage → Clear site data
   - 或設定 → 隱私權與安全性 → 清除瀏覽資料（勾選快取的圖片和檔案）

### 技術背景

v1.4.3 採用 stub-first 註冊模式：
- JS 載入時先註冊一個輕量 stub element（顯示「載入中...」）
- 當完整 class 載入後，透過 `setPrototypeOf` 將 stub 的方法指向完整實作
- 避免 Lovelace 解析 YAML 時 JS 還沒載入導致的「設定錯誤」

---

## 2. 硬刷新後卡片偶爾消失

### 症狀

- 按 `Ctrl+Shift+R` 後卡片有時候出現，有時候「設定錯誤」
- 重複測試：約 80-90% 成功，10-20% 失敗

### 原因

JS 檔案載入路徑的穩定性問題。

### 架構說明

HA 中 JS 卡片有兩種載入路徑：

| 路徑 | 註冊方式 | 穩定性 |
|------|----------|--------|
| `/cwa_agri_static/` | Integration `async_setup()` → `frontend.add_extra_js_url()` | ❌ Runtime-only，重啟後可能未寫入 resources |
| `/local/cwa_agri/` | 直接寫入 `.storage/lovelace_resources` | ✅ HA 原生 serve，持久化 |

**v1.4.3 起使用 `/local/` 路徑**，JS 檔案安裝在 HA 的 `/config/www/cwa_agri/` 目錄。

### 解決方案

1. 確認已更新到 v1.4.3+
2. 執行 `ha core restart`（非 reload）
3. 等待 HA 完全啟動（約 30-60 秒）
4. 硬刷新瀏覽器

若仍有問題，手動檢查：
```bash
# 確認 JS 檔案存在
curl -s -o /dev/null -w "%{http_code}" http://<HA_IP>:8123/local/cwa_agri/cwa-agri-dashboard.js
# 應回傳 200

# 確認 lovelace_resources 已註冊
curl -s -H "Authorization: Bearer <TOKEN>" http://<HA_IP>:8123/api/lovelace/resources | grep "cwa_agri"
# 應看到 /local/cwa_agri/ 路徑
```

---

## 3. 刷新按鈕無效

### 症狀

- 點擊卡片右上角 🔄 按鈕沒有反應
- Bridge log 沒有收到請求

### 原因

v1.4.3 之前，按鈕 click handler 綁定有問題（LitElement `@click` 語法不適用於 HTMLElement Light DOM）。

### 解決方案

1. 確認已更新到 v1.4.3+
2. 點擊按鈕後打開 DevTools Console，應看到 `[CWA Agri] refresh button clicked`
3. 確認 Bridge 服務正在運行：`curl http://<BRIDGE_IP>:18801/health`

### 技術背景

v1.4.3 修復：`btn.onclick = () => this._onRefresh()` 在 `render()` 中 after `innerHTML` 設定。

---

## 4. Bridge 連線問題

### Bridge 健康檢查

```bash
curl http://<BRIDGE_IP>:18801/health
# 預期回應：{"status":"ok","script":"..."}
```

### Bridge 重啟

```bash
# systemd service
sudo systemctl restart cwa-refresh-bridge
sudo systemctl status cwa-refresh-bridge

# 查看 log
journalctl -u cwa-refresh-bridge -f
```

### Bridge 不回應

1. 確認 port 18801 未被占用：`ss -tlnp | grep 18801`
2. 確認 `openclaw-cwa-skill` repo 路徑正確
3. 確認 `cwa_config.json` 中的 HA URL 和 Token 正確

---

## 5. JS 檔案載入相關知識

### HA 中 custom card 的載入順序

```
1. HA 啟動 → 載入所有 custom_components
2. Integration async_setup() 執行
3. Frontend 載入 lovelace_resources 中的所有 JS
4. Lovelace 解析 dashboard YAML
5. 對每個 custom:xxx-card → 呼叫 customElements.get() 確認是否已註冊
6. 若已註冊 → new element → setConfig() → hass setter → render()
7. 若未註冊 → 顯示「Custom element doesn't exist」
```

### `/local/` 路徑原理

- HA 的 `www/` 目錄對應 URL 的 `/local/` 前綴
- 檔案放在 `/config/www/xxx.js` → 可透過 `http://HA_IP:8123/local/xxx.js` 存取
- 這是 HA 原生機制，不依賴任何 integration
- 寫入 `.storage/lovelace_resources` 後，HA 每次啟動都會自動載入

### 為什麼不用 `frontend.add_extra_js_url()`

`frontend.add_extra_js_url()` 是 runtime-only 的註冊方式：
- 優點：程式碼簡單，integration 內就能完成
- 缺點：不寫入 `.storage/lovelace_resources`，依賴 integration 的 static path 註冊時序
- 實際表現：有時候 integration 先註冊，有時候 Lovelace 先請求 → 間歇性 404

v1.4.3 起改用 `/local/` + `lovelace_resources` 持久化方案。

---

## 開發者筆記

### 檔案結構

```
custom_components/cwa_agri/
├── __init__.py          # Integration 入口，設定 UI
├── manifest.json        # Integration metadata
├── config_flow.py       # 設定精靈
├── sensor.py            # Sensor entity
├── button.py            # Refresh button
├── www/                 # JS 原始碼（開發用，已不作為載入路徑）
│   └── cwa-agri-dashboard.js
└── ...

HA 端（實際載入路徑）:
/config/www/cwa_agri/
└── cwa-agri-dashboard.js  # 實際被 Lovelace 載入的 JS

/config/.storage/lovelace_resources  # 註冊 /local/ 路徑
```

### 為什麼 www/ 目錄下還有 JS 檔案

`custom_components/cwa_agri/www/` 下的 JS 是開發/備份用途。實際載入路徑是 `/config/www/cwa_agri/`（HA 原生 `/local/` 路徑）。兩者內容應保持同步。

### 如何更新卡片 JS

1. 編輯 `custom_components/cwa_agri/www/cwa-agri-dashboard.js`
2. 複製到 HA：`scp ... /config/www/cwa_agri/cwa-agri-dashboard.js`
3. 重啟 HA 或硬刷新瀏覽器
