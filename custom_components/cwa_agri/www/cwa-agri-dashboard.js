class CwaAgriReportCard extends HTMLElement {
  setConfig(config) {
    this.config = {
      entity: 'sensor.cwa_agri_report',
      title: '農業氣象報告 v5.5',
      days: 7,
      ...config,
    };
    if (!this.config.entity) throw new Error('entity is required');
    // 延遲啟動輪詢，等 hass 設定
    setTimeout(() => this._pollForEntity(), 500);
  }

  set hass(hass) {
    this._hass = hass;
    this.render();
    // Entity 出現後清除輪詢
    if (this._pollTimer) {
      const stateObj = hass.states[this.config?.entity];
      if (stateObj) {
        clearTimeout(this._pollTimer);
        this._pollTimer = null;
      }
    }
  }

  _pollForEntity(retries = 0) {
    if (!this._hass || !this.config) return;
    const stateObj = this._hass.states[this.config.entity];
    if (stateObj) {
      this.render();
      return;
    }
    if (retries < 10) {
      this._pollTimer = setTimeout(() => this._pollForEntity(retries + 1), 2000);
    }
  }

  getCardSize() {
    return 10;
  }

  async _onRefresh() {
    if (!this._hass) return;
    try {
      await this._hass.callService('button', 'press', { entity_id: 'button.cwa_agri_refresh' });
    } catch (e) {
      console.error('[CWA Agri] refresh failed:', e);
    }
  }

  _esc(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  _arr(value) {
    return Array.isArray(value) ? value.filter(Boolean) : [];
  }

  _fmtDate(value) {
    if (!value || typeof value !== 'string' || value.length < 10) return '-';
    return `${Number(value.slice(5, 7))}/${Number(value.slice(8, 10))}`;
  }

  _fmtIssued(value) {
    if (!value || typeof value !== 'string') return '-';
    return value.replace('T', ' ').replace(/:\d{2}(?:\.\d+)?([+-]\d{2}:?\d{2}|Z)?$/, '');
  }

  _weatherIcon(text) {
    const s = String(text || '');
    if (s.includes('雷')) return '⛈️';
    if (s.includes('雨')) return '🌧️';
    if (s.includes('晴')) return '☀️';
    if (s.includes('陰')) return '☁️';
    if (s.includes('雲')) return '⛅';
    return '🌤️';
  }

  _tag(label, value, cls = '') {
    if (value === undefined || value === null || value === '') return '';
    return `<div class="chip ${cls}"><span class="chip-label">${this._esc(label)}</span><span class="chip-value">${this._esc(value)}</span></div>`;
  }

  _sectionCard(title, body) {
    if (!body) return '';
    return `
      <section class="section-card">
        <div class="section-title">${this._esc(title)}</div>
        ${body}
      </section>
    `;
  }

  _renderBulletList(items, empty = '—') {
    const arr = this._arr(items);
    if (!arr.length) return `<div class="muted">${this._esc(empty)}</div>`;
    return `<ul class="bullet-list">${arr.map((x) => `<li>${this._esc(x)}</li>`).join('')}</ul>`;
  }

  _renderInfoRows(rows) {
    const html = rows.filter(Boolean).map((row) => `
      <div class="info-row">
        <div class="info-label">${this._esc(row.label)}</div>
        <div class="info-value">${this._esc(row.value)}</div>
      </div>
    `).join('');
    return html || '<div class="muted">—</div>';
  }

  _renderForecastCards(weekly) {
    if (!weekly.length) return '<div class="muted">暫無 7 天預報</div>';
    return `
      <div class="forecast-cards">
        ${weekly.map((d) => `
          <div class="forecast-card">
            <div class="forecast-date">${this._esc(this._fmtDate(d.date))}</div>
            <div class="forecast-icon">${this._weatherIcon(d.weather)}</div>
            <div class="forecast-weather">${this._esc(d.weather || '-')}</div>
            <div class="forecast-temp">${this._esc(d.minT ?? '-')} ~ ${this._esc(d.maxT ?? '-')}°C</div>
            ${d.rain_prob !== undefined ? `<div class="forecast-meta">降雨 ${this._esc(d.rain_prob)}%</div>` : ''}
          </div>
        `).join('')}
      </div>
    `;
  }

  render() {
    if (!this._hass || !this.config) return;
    const stateObj = this._hass.states[this.config.entity];
    if (!stateObj) {
      this.innerHTML = `<ha-card><div class="pad">找不到 entity：${this._esc(this.config.entity)}</div></ha-card>`;
      return;
    }

    const a = stateObj.attributes || {};
    const fs = a.farmer_summary || {};
    const note = fs.note_section || a.note_section || {};
    const weekly = this._arr(a.weekly_forecast || []).slice(0, this.config.days || 7);
    const warningActions = this._arr(fs.warning_priority_actions).slice(0, 5);
    const liveAlertActions = this._arr(fs.live_alert_actions).slice(0, 5);
    const next3 = this._arr(fs.next_3_day_action_window).slice(0, 3);
    const stageAdvice = this._arr(fs.stage_based_advice).slice(0, 4);
    const riskDrivers = this._arr(fs.risk_drivers).slice(0, 4);
    const weeklyActionFocus = this._arr(a.weekly_action_focus || fs.weekly_action_focus).slice(0, 4);
    const weeklyManagementAdvice = this._arr(a.weekly_management_advice || fs.weekly_management_advice).slice(0, 4);
    const highestRiskDay = a.highest_risk_day || fs.highest_risk_day || null;

    const dayTemps = weekly.map((d) => Number(d.maxT)).filter((n) => Number.isFinite(n));
    const nightTemps = weekly.map((d) => Number(d.minT)).filter((n) => Number.isFinite(n));
    const trend = weekly.length
      ? `白天 ${Math.min(...dayTemps)}~${Math.max(...dayTemps)}°C，夜間 ${Math.min(...nightTemps)}~${Math.max(...nightTemps)}°C`
      : '暫無 7 天預報';

    const statusChips = [
      this._tag('風險', a.risk_level || stateObj.state || '-'),
      this._tag('作物', a.crop_name || '-'),
      this._tag('生長期', a.growth_stage || '-'),
      this._tag('預警來源', a.warning_source || '-')
    ].join('');

    const bannerText = fs.warning_headline || a.warning_headline || '';
    const hasWarning = Boolean(bannerText);
    const isDemo = stateObj.state === 'demo';
    const currentSummary = [fs.headline, fs.weather].filter(Boolean).join('｜');

    const styles = `
      <style>
        ha-card { display:block; }
        .card { padding: 12px; font-size: 14px; line-height: 1.55; }
        .pad { padding: 12px; }
        .muted { color: var(--secondary-text-color); }
        .hero-card {
          display: grid;
          grid-template-columns: 1.6fr 0.9fr;
          gap: 8px;
          padding: 10px 12px;
          border-radius: 14px;
          background: linear-gradient(135deg, rgba(33,150,243,.10), rgba(76,175,80,.08));
          border: 1px solid rgba(33,150,243,.16);
        }
        .hero-title-row {
          display:flex;
          align-items:center;
          justify-content:space-between;
          gap:8px;
        }
        .hero-title { font-size: 1.15rem; font-weight: 800; line-height: 1.3; }
        .hero-sub, .hero-issued { color: var(--secondary-text-color); margin-top: 4px; font-size: .88rem; }
        .hero-side {
          padding: 8px 10px;
          border-radius: 10px;
          background: rgba(255,255,255,.42);
          text-align: right;
        }
        .hero-temp { font-size: 1.2rem; font-weight: 800; line-height: 1.3; }
        .hero-weather { margin-top: 4px; font-weight: 600; font-size: .92rem; }
        .build-tag {
          display:inline-flex;
          align-items:center;
          gap:4px;
          padding:3px 8px;
          border-radius:999px;
          background: rgba(33, 150, 243, 0.16);
          color: var(--primary-color);
          font-size: .72rem;
          font-weight: 700;
          white-space: nowrap;
        }
        .refresh-btn {
          background:none;border:none;cursor:pointer;font-size:.85rem;padding:0 2px;
          transition:transform .3s;
        }
        .refresh-btn:hover { transform:rotate(90deg); }
        .chip-row {
          display:flex;
          flex-wrap:wrap;
          gap:6px;
          margin-top:8px;
        }
        .chip {
          display:inline-flex;
          gap:4px;
          align-items:center;
          padding:4px 8px;
          border-radius:999px;
          background: var(--secondary-background-color);
          font-size: .78rem;
        }
        .chip-label { color: var(--secondary-text-color); }
        .chip-value { font-weight: 700; }
        .alert-banner {
          margin-top: 10px;
          padding: 10px 12px;
          border-radius: 12px;
          border-left: 4px solid transparent;
        }
        .alert-banner.warn {
          background: rgba(245, 124, 0, 0.12);
          border-left-color: rgba(245, 124, 0, 0.9);
        }
        .alert-banner.ok {
          background: rgba(56, 142, 60, 0.10);
          border-left-color: rgba(56, 142, 60, 0.9);
        }
        .alert-banner.demo {
          background: rgba(33, 150, 243, 0.10);
          border-left-color: rgba(33, 150, 243, 0.9);
        }
        .alert-title { font-weight: 800; margin-bottom: 2px; }
        .alert-text { font-weight: 600; }
        .alert-sub { margin-top: 4px; color: var(--secondary-text-color); font-size: .88rem; }
        .grid {
          display:grid;
          gap: 8px;
          margin-top: 10px;
        }
        .grid.two {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        .section-card {
          padding: 10px 12px;
          border-radius: 12px;
          background: var(--ha-card-background, var(--card-background-color));
          box-shadow: inset 0 0 0 1px rgba(127,127,127,0.12);
        }
        .section-title {
          font-size: .95rem;
          font-weight: 800;
          margin-bottom: 8px;
        }
        .bullet-list {
          margin: 0;
          padding-left: 16px;
        }
        .bullet-list li { margin: 4px 0; }
        .info-row {
          display:grid;
          grid-template-columns: 72px 1fr;
          gap: 8px;
          padding: 6px 0;
          border-bottom: 1px solid rgba(127,127,127,0.12);
        }
        .info-row:last-child { border-bottom: none; padding-bottom: 0; }
        .info-label { color: var(--secondary-text-color); font-weight: 700; font-size: .88rem; }
        .info-value { line-height: 1.6; word-break: break-word; font-size: .9rem; }
        .forecast-summary {
          color: var(--secondary-text-color);
          margin-bottom: 6px;
          font-size: .88rem;
        }
        .forecast-cards {
          display:grid;
          grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
          gap: 6px;
          max-height: 220px;
          overflow-y: auto;
        }
        .forecast-card {
          padding: 8px 6px;
          border-radius: 10px;
          background: var(--secondary-background-color);
          text-align:center;
        }
        .forecast-date { font-weight: 800; font-size: .85rem; }
        .forecast-icon { font-size: 1.2rem; margin-top: 4px; }
        .forecast-weather { margin-top: 2px; font-weight: 600; font-size: .8rem; }
        .forecast-temp { margin-top: 2px; font-size: .85rem; }
        .forecast-meta { margin-top: 2px; color: var(--secondary-text-color); font-size: .75rem; }
        .note-card { color: var(--secondary-text-color); }
        .note-line + .note-line { margin-top: 4px; }
        .note-card { max-height: 120px; overflow-y: auto; }
        @media (max-width: 800px) {
          .hero-card,
          .grid.two {
            grid-template-columns: 1fr;
          }
          .hero-side {
            text-align:left;
          }
          .card { padding: 12px; font-size: 14px; }
          .info-row { grid-template-columns: 68px 1fr; gap: 6px; }
        }
      </style>
    `;

    this.innerHTML = `
      ${styles}
      <ha-card header="${this._esc(this.config.title)}">
        <div class="card">
          <div class="hero-card">
            <div class="hero-main">
              <div class="hero-title-row">
                <div class="hero-title">${this._esc(a.risk_icon || '🌱')} ${this._esc(a.farm_name || '農場')}</div>
                <div class="build-tag">
                  <button class="refresh-btn" id="cwa-refresh-btn" title="重新整理氣象報告">🔄</button>
                  v5.5
                </div>
              </div>
              <div class="hero-sub">${this._esc(a.crop_name || '-')}｜${this._esc(a.date || '-')}</div>
              <div class="chip-row">${statusChips}</div>
            </div>
            <div class="hero-side">
              <div class="hero-temp">${this._esc(a.temp_min ?? '-')}° ~ ${this._esc(a.temp_max ?? '-')}°</div>
              <div class="hero-weather">${this._esc(a.current_weather || '-')}</div>
              <div class="hero-issued">更新：${this._esc(this._fmtIssued(a.issued_at || '-'))}</div>
            </div>
          </div>

          <div class="alert-banner ${isDemo ? 'demo' : hasWarning ? 'warn' : 'ok'}">
            ${isDemo ? `
              <div class="alert-title">📋 示範報表</div>
              <div class="alert-text">這是安裝後的預覽資料，請執行 OpenClaw sync_and_report.js 推送真實報表</div>
            ` : `
              <div class="alert-title">${hasWarning ? '⚠️ 目前提醒' : '✅ 今日狀態'}</div>
              <div class="alert-text">${this._esc(hasWarning ? bannerText : '目前沒有額外即時警報，可照排程作業')}</div>
              ${fs.tonight_warning_note ? `<div class="alert-sub">${this._esc(fs.tonight_warning_note)}</div>` : ''}
            `}
          </div>

          <div class="grid two">
            ${this._sectionCard('今日判讀', this._renderInfoRows([
              currentSummary ? { label: '整體', value: currentSummary } : null,
              { label: '天氣', value: `${a.current_weather || '-'}｜${a.temp_min ?? '-'}°C ~ ${a.temp_max ?? '-'}°C` },
              fs.risk_interpretation ? { label: '判讀', value: fs.risk_interpretation } : (a.risk_interpretation ? { label: '判讀', value: a.risk_interpretation } : null),
            ]))}

            ${this._sectionCard('今日作業', this._renderInfoRows([
              fs.work_window ? { label: '巡田', value: fs.work_window } : null,
              fs.fertilizing_advice ? { label: '施肥', value: fs.fertilizing_advice } : null,
              fs.spraying_advice ? { label: '噴藥', value: fs.spraying_advice } : null,
              fs.irrigation_advice ? { label: '灌溉', value: fs.irrigation_advice } : null,
            ]))}
          </div>

          <div class="grid two">
            ${this._sectionCard('優先動作', this._renderBulletList(warningActions, '今日無特別優先處置'))}
            ${this._sectionCard('近 3 天窗口', this._renderBulletList(next3, '暫無資料'))}
          </div>

          <div class="grid two">
            ${this._sectionCard('生長狀態', this._renderInfoRows([
              a.risk_text ? { label: '風險說明', value: a.risk_text } : null,
              a.gdd_today !== undefined ? { label: '本日度日', value: `${a.gdd_today} GDD` } : null,
              a.gdd_accumulated !== undefined ? { label: '累計積溫', value: `${a.gdd_accumulated} GDD` } : null,
              a.gdd_progress ? { label: '進度', value: a.gdd_progress } : null,
            ]))}
            ${this._sectionCard('生長期建議', this._renderBulletList(stageAdvice, '暫無額外建議'))}
          </div>

          <div class="grid two">
            ${this._sectionCard('本週重點', this._renderInfoRows([
              highestRiskDay ? { label: '最高風險日', value: highestRiskDay.summary || highestRiskDay.reason || highestRiskDay } : null,
              weeklyActionFocus.length ? { label: '作業焦點', value: weeklyActionFocus.join('；') } : null,
              weeklyManagementAdvice.length ? { label: '管理建議', value: weeklyManagementAdvice.join('；') } : null,
            ]))}
            ${this._sectionCard('風險來源', this._renderBulletList(riskDrivers, '暫無顯著風險來源'))}
          </div>

          ${liveAlertActions.length ? this._sectionCard('即時警報動作', this._renderBulletList(liveAlertActions)) : ''}

          ${this._sectionCard('7 天預報', `
            <div class="forecast-summary">${this._esc(trend)}</div>
            ${this._renderForecastCards(weekly)}
          `)}

          ${note.monitoring_items_text || note.monitoring_risks_text ? `
            <section class="section-card note-card">
              <div class="section-title">附註說明</div>
              ${note.monitoring_risks_text ? `<div class="note-line">${this._esc(note.monitoring_risks_text)}</div>` : ''}
              ${note.monitoring_items_text ? `<div class="note-line">${this._esc(note.monitoring_items_text)}</div>` : ''}
            </section>
          ` : ''}
        </div>
      </ha-card>
    `;

    // 綁定刷新按鈕（直接在 render 後綁定，不依賴 connectedCallback）
    const btn = this.querySelector('#cwa-refresh-btn');
    if (btn && !btn.onclick) {
      btn.onclick = () => this._onRefresh();
    }
  }

  connectedCallback() {
    // fallback: 若 render 後才 connect，也綁一次
    const btn = this.querySelector('#cwa-refresh-btn');
    if (btn && !btn.onclick) {
      btn.onclick = () => this._onRefresh();
    }
  }
}

if (!customElements.get('cwa-agri-report-card')) {
  customElements.define('cwa-agri-report-card', CwaAgriReportCard);
}
window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === 'cwa-agri-report-card')) {
  window.customCards.push({
    type: 'cwa-agri-report-card',
    name: 'UNiNUS CWA Agri Report Card',
    description: 'OpenClaw CWA agri report dashboard card (bundled with ha-cwa-agri)',
  });
}
