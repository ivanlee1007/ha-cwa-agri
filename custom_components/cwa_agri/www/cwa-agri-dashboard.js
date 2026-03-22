class CwaAgriReportCard extends HTMLElement {
  setConfig(config) {
    this.config = {
      entity: 'sensor.cwa_agri_report',
      title: '農業氣象報告 v5.1',
      days: 7,
      ...config,
    };
    if (!this.config.entity) throw new Error('entity is required');
  }

  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  getCardSize() {
    return 10;
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
    const currentSummary = [fs.headline, fs.weather].filter(Boolean).join('｜');

    const styles = `
      <style>
        ha-card { display:block; }
        .card { padding: 18px; font-size: 15px; line-height: 1.65; }
        .pad { padding: 16px; }
        .muted { color: var(--secondary-text-color); }
        .hero-card {
          display: grid;
          grid-template-columns: 1.6fr 0.9fr;
          gap: 12px;
          padding: 16px;
          border-radius: 18px;
          background: linear-gradient(135deg, rgba(33,150,243,.10), rgba(76,175,80,.08));
          border: 1px solid rgba(33,150,243,.16);
        }
        .hero-title-row {
          display:flex;
          align-items:center;
          justify-content:space-between;
          gap:12px;
        }
        .hero-title { font-size: 1.28rem; font-weight: 800; line-height: 1.35; }
        .hero-sub, .hero-issued { color: var(--secondary-text-color); margin-top: 8px; font-size: .95rem; }
        .hero-side {
          padding: 12px;
          border-radius: 14px;
          background: rgba(255,255,255,.42);
          text-align: right;
        }
        .hero-temp { font-size: 1.35rem; font-weight: 800; line-height: 1.3; }
        .hero-weather { margin-top: 8px; font-weight: 600; font-size: 1rem; }
        .build-tag {
          display:inline-block;
          padding:4px 10px;
          border-radius:999px;
          background: rgba(33, 150, 243, 0.16);
          color: var(--primary-color);
          font-size: .78rem;
          font-weight: 700;
          white-space: nowrap;
        }
        .chip-row {
          display:flex;
          flex-wrap:wrap;
          gap:8px;
          margin-top:12px;
        }
        .chip {
          display:inline-flex;
          gap:6px;
          align-items:center;
          padding:6px 10px;
          border-radius:999px;
          background: var(--secondary-background-color);
          font-size: .82rem;
        }
        .chip-label { color: var(--secondary-text-color); }
        .chip-value { font-weight: 700; }
        .alert-banner {
          margin-top: 14px;
          padding: 14px 16px;
          border-radius: 16px;
          border-left: 5px solid transparent;
        }
        .alert-banner.warn {
          background: rgba(245, 124, 0, 0.12);
          border-left-color: rgba(245, 124, 0, 0.9);
        }
        .alert-banner.ok {
          background: rgba(56, 142, 60, 0.10);
          border-left-color: rgba(56, 142, 60, 0.9);
        }
        .alert-title { font-weight: 800; margin-bottom: 4px; }
        .alert-text { font-weight: 600; }
        .alert-sub { margin-top: 6px; color: var(--secondary-text-color); }
        .grid {
          display:grid;
          gap: 12px;
          margin-top: 14px;
        }
        .grid.two {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        .section-card {
          padding: 14px;
          border-radius: 16px;
          background: var(--ha-card-background, var(--card-background-color));
          box-shadow: inset 0 0 0 1px rgba(127,127,127,0.12);
        }
        .section-title {
          font-size: 1.02rem;
          font-weight: 800;
          margin-bottom: 12px;
        }
        .bullet-list {
          margin: 0;
          padding-left: 18px;
        }
        .bullet-list li { margin: 8px 0; }
        .info-row {
          display:grid;
          grid-template-columns: 88px 1fr;
          gap: 12px;
          padding: 10px 0;
          border-bottom: 1px solid rgba(127,127,127,0.12);
        }
        .info-row:last-child { border-bottom: none; padding-bottom: 0; }
        .info-label { color: var(--secondary-text-color); font-weight: 700; }
        .info-value { line-height: 1.75; word-break: break-word; }
        .forecast-summary {
          color: var(--secondary-text-color);
          margin-bottom: 10px;
        }
        .forecast-cards {
          display:grid;
          grid-template-columns: repeat(auto-fit, minmax(118px, 1fr));
          gap: 10px;
        }
        .forecast-card {
          padding: 14px 12px;
          border-radius: 14px;
          background: var(--secondary-background-color);
          text-align:center;
        }
        .forecast-date { font-weight: 800; }
        .forecast-icon { font-size: 1.5rem; margin-top: 8px; }
        .forecast-weather { margin-top: 6px; font-weight: 600; }
        .forecast-temp { margin-top: 6px; }
        .forecast-meta { margin-top: 4px; color: var(--secondary-text-color); font-size: .82rem; }
        .note-card { color: var(--secondary-text-color); }
        .note-line + .note-line { margin-top: 6px; }
        @media (max-width: 800px) {
          .hero-card,
          .grid.two {
            grid-template-columns: 1fr;
          }
          .hero-side {
            text-align:left;
          }
          .card { padding: 16px; font-size: 15px; }
          .info-row { grid-template-columns: 80px 1fr; gap: 10px; }
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
                <div class="build-tag">v5.1 · build type-tune</div>
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

          <div class="alert-banner ${hasWarning ? 'warn' : 'ok'}">
            <div class="alert-title">${hasWarning ? '⚠️ 目前提醒' : '✅ 今日狀態'}</div>
            <div class="alert-text">${this._esc(hasWarning ? bannerText : '目前沒有額外即時警報，可照排程作業')}</div>
            ${fs.tonight_warning_note ? `<div class="alert-sub">${this._esc(fs.tonight_warning_note)}</div>` : ''}
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
  }
}

customElements.define('cwa-agri-report-card', CwaAgriReportCard);
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'cwa-agri-report-card',
  name: 'CWA Agri Report Card',
  description: 'OpenClaw CWA agri report dashboard card',
});
