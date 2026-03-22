# CWA Agri - Home Assistant Integration

這個整合的角色很單純：

- 在 Home Assistant 提供 **CWA 農場設定 UI**
- 讓使用者用較省力的方式維護 **作物清單 / 生長階段**
- 把設定以 Entity 形式暴露給 **OpenClaw CWA Skill** 讀取

> 這個 repo **不包含** Lovelace dashboard 卡片。Dashboard 請搭配另一個 repo：`cwa-agri-dashboard`

---

## 目前設計（v2 / v2.1）

### v2：簡化安裝流程
安裝精靈只做兩件事：
1. 基本連線資料
2. 位置 + 初始作物清單（可留空）

作物不再用「新增一筆 / 刪除一筆 / 下一步」那種卡住人的 flow。

### v2.1：半自動 stage assistant
每個作物會自動產生：
- `select.cwa_agri_<crop>_stage`：目前階段
- `select.cwa_agri_<crop>_stage_mode`：`手動 / 半自動`
- `sensor.cwa_agri_<crop>_stage_assistant`：系統建議、信心、原因
- `button.cwa_agri_<crop>_apply_stage_suggestion`：套用建議
- `button.cwa_agri_<crop>_keep_current_stage`：維持目前階段

理念是：
- 平常系統先推估
- 使用者只在要調整時按一下
- 不要每次都回設定精靈裡維護

---

## 安裝方式

### HACS Custom Repository
1. Home Assistant → **HACS**
2. **Custom repositories**
3. 加入：
   - Repository: `https://github.com/ivanlee1007/ha-cwa-agri`
   - Category: `Integration`
4. 安裝 **CWA Agri**
5. 重啟 Home Assistant
6. 到 **設定 → 裝置與服務** 新增整合

---

## 使用方式

### 第一次安裝
填：
- 農場名稱
- HA URL
- 長期訪問令牌
- 經緯度 / 區域
- 初始作物名稱（每行一個，可先空著）

### 後續維護
到整合的 **選項** 頁面，直接用一個多行欄位管理作物名稱：

```text
藍莓
草莓
番茄
```

然後每個作物的 stage 可以直接在 HA 裡用 select entity 改，不必再回安裝 flow。

---

## 與 OpenClaw 搭配

OpenClaw 端用 `sync_ha_config.js` 把整合設定拉回去：

```bash
export HA_URL="http://your-home-assistant:8123"
export HA_TOKEN="your_long_lived_access_token"
node scripts/sync_ha_config.js
```

同步流程：

1. HA Integration 暴露設定 Entity
2. OpenClaw 讀取設定
3. 合併進 `cwa_config.json`
4. `cwa_agri_report.js` 產生報告
5. 推送到 `sensor.cwa_agri_report`
6. Dashboard 顯示

---

## 注意

- `cwa_api_key` 仍保留在 OpenClaw 端，不放在這個整合裡
- 這個整合目前的 stage assistant 是 **季節節奏推估**，不是作物學等級的精準生理模型
- 如果要更準，下一步應該是加：
  - GDD
  - 區域季節模板
  - 作物模板
  - 事件觸發提醒

---

## 相關 repo

- HA Integration：`ha-cwa-agri`
- Dashboard Card：`cwa-agri-dashboard`
- OpenClaw Skill：`openclaw-cwa-skill`
