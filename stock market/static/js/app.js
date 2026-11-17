/**
 * Stock Market Prediction & Dashboard Controller
 * Fully localized in Indian Rupees (₹ / INR)
 * Supports the 10 core trades across Indian Indices, Commodities, Crypto, Forex, and Global Indices
 */

window.currentTicker = 'NIFTY50';
window.currentRange = '1y';
window.currentModel = 'ensemble';
window.currentHorizon = 14;

window.lastStockData = null;
window.lastPredictionData = null;
window.lastIndicatorsData = null;
window.featuredTradesData = [];

window.activeOverlays = {
  sma20: true,
  sma50: false,
  bb: true
};

// Indian Rupee currency formatting helper
window.formatINR = function(val, includeDecimals = true) {
  if (val === null || val === undefined || isNaN(val)) return '₹0.00';
  const num = Number(val);
  return '₹' + num.toLocaleString('en-IN', {
    minimumFractionDigits: includeDecimals ? 2 : 0,
    maximumFractionDigits: includeDecimals ? 2 : 0
  });
};

// ==========================================
// 1. Theme Management (Dark & Light Mode)
// ==========================================

function initTheme() {
  const savedTheme = localStorage.getItem('stock_market_theme') || 'dark';
  setTheme(savedTheme);

  const toggleBtn = document.getElementById('theme-toggle-btn');
  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme') || 'dark';
      const newTheme = current === 'dark' ? 'light' : 'dark';
      setTheme(newTheme);
    });
  }
}

function setTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('stock_market_theme', theme);

  const knob = document.getElementById('theme-toggle-knob');
  if (knob) {
    knob.innerHTML = theme === 'dark' ? '<i class="fas fa-moon"></i>' : '<i class="fas fa-sun"></i>';
  }

  if (window.refreshAllChartsTheme) {
    window.refreshAllChartsTheme();
  }
}

// ==========================================
// 2. Featured 10 Trades Rendering
// ==========================================

async function loadFeaturedTrades() {
  try {
    const res = await fetch('/api/trades/featured');
    if (!res.ok) throw new Error('Failed to load featured trades');
    const trades = await res.json();
    window.featuredTradesData = trades;
    renderFeaturedTrades(trades);
  } catch (err) {
    console.error('Error fetching featured trades:', err);
  }
}

function renderFeaturedTrades(trades, categoryFilter = 'ALL') {
  const container = document.getElementById('featured-trades-container');
  if (!container) return;

  const filtered = categoryFilter === 'ALL' 
    ? trades 
    : trades.filter(t => t.category.toLowerCase() === categoryFilter.toLowerCase());

  container.innerHTML = filtered.map(t => {
    const isPos = t.change >= 0;
    const isSelected = t.id === window.currentTicker;
    return `
      <button onclick="loadStockData('${t.id}')" id="ft-card-${t.id}" class="btn-reactive flex-shrink-0 flex items-center justify-between gap-3 px-3.5 py-2 rounded-2xl border transition-all text-left ${
        isSelected 
          ? 'border-cyan-500/80 bg-cyan-500/15 shadow-lg shadow-cyan-500/20' 
          : 'border-white/10 bg-white/5 hover:bg-white/10'
      }">
        <div class="flex items-center gap-2">
          <span class="text-xs font-bold text-cyan-400 font-mono">#${t.rank}</span>
          <div>
            <div class="font-bold text-xs theme-text-primary">
              ${t.name}
            </div>
            <div class="text-[10px] text-slate-400 flex items-center gap-1 mt-0.5">
              <span class="text-[9px] text-cyan-400 font-medium">${t.category}</span>
            </div>
          </div>
        </div>

        <div class="text-right pl-2 border-l border-white/5">
          <div id="ft-price-${t.id}" data-price="${t.price}" class="font-mono font-bold text-xs theme-text-primary transition-all">${formatINR(t.price)}</div>
          <div id="ft-change-${t.id}" class="text-[10px] font-bold ${isPos ? 'text-emerald-400' : 'text-rose-400'}">
            ${isPos ? '+' : ''}${t.change_pct.toFixed(2)}%
          </div>
        </div>
      </button>
    `;
  }).join('');
}

window.filterTradeCategory = function(cat) {
  document.querySelectorAll('.cat-pill').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-cat') === cat);
  });
  renderFeaturedTrades(window.featuredTradesData, cat);
};

// ==========================================
// 3. Stock Data Fetching & Display (INR)
// ==========================================

async function loadStockData(ticker = window.currentTicker, range = window.currentRange) {
  window.currentTicker = ticker.toUpperCase().trim();
  window.currentRange = range;

  setLoadingState(true);

  try {
    const res = await fetch(`/api/stock/${window.currentTicker}?range=${window.currentRange}`);
    if (!res.ok) throw new Error('Failed to fetch market data');
    const data = await res.json();
    window.lastStockData = data;

    const indRes = await fetch(`/api/stock/${window.currentTicker}/indicators?range=${window.currentRange}`);
    const indicators = indRes.ok ? await indRes.json() : null;
    window.lastIndicatorsData = indicators;

    updateStockHeader(data);
    updateTechnicalPanel(indicators);

    await runPrediction();
    updateWatchlistStarButton();

    // Re-highlight active trade button
    if (window.featuredTradesData.length > 0) {
      renderFeaturedTrades(window.featuredTradesData);
    }

    // Schedule continuous live streaming on this asset
    if (window.isLiveStreaming) {
      scheduleNextTick();
    }

  } catch (error) {
    console.error('Error loading trade:', error);
    showToast(`Error loading ${ticker}: ${error.message}`, 'error');
  } finally {
    setLoadingState(false);
  }
}

// ==========================================
// 3.1 Real-Time Live Market & Live Prediction Engine
// ==========================================

window.isLiveStreaming = true; // Auto-active by default!
window.liveIntervalMs = 3000;  // 3s interval
window.isLivePredictEnabled = true; // Auto-predict on every live tick!
window.liveTickTimer = null;
window.liveCountdownTimer = null;
window.liveCountdown = 3;
window.liveTickCount = 0;
window.isTickInProgress = false;

window.toggleLiveStreaming = function() {
  window.isLiveStreaming = !window.isLiveStreaming;
  updateLiveUIState();
  if (window.isLiveStreaming) {
    showToast('🟢 Real-Time Live Market: ACTIVE', 'success');
    executeLiveTick();
    scheduleNextTick();
  } else {
    showToast('⏸️ Real-Time Live Market: PAUSED', 'info');
    clearTimeout(window.liveTickTimer);
    clearInterval(window.liveCountdownTimer);
  }
};

window.setLiveInterval = function(ms) {
  window.liveIntervalMs = ms;
  document.querySelectorAll('.live-pill-speed').forEach(pill => {
    pill.classList.toggle('active', parseInt(pill.getAttribute('data-speed')) === ms);
  });
  window.liveCountdown = Math.round(ms / 1000);
  const countdownEl = document.getElementById('live-tick-countdown');
  if (countdownEl) countdownEl.innerText = `${window.liveCountdown}s`;
  if (window.isLiveStreaming) {
    clearTimeout(window.liveTickTimer);
    scheduleNextTick();
  }
  showToast(`Live update interval: ${ms / 1000}s`, 'info');
};

window.toggleLivePredict = function(checked) {
  window.isLivePredictEnabled = checked;
  showToast(checked ? '⚡ Auto-prediction on live ticks: ACTIVE' : 'Auto-prediction on live ticks: OFF', 'info');
};

window.triggerManualTick = function() {
  const manualBtn = document.getElementById('manual-tick-btn');
  if (manualBtn) {
    manualBtn.classList.add('scale-95');
    setTimeout(() => manualBtn.classList.remove('scale-95'), 150);
  }
  executeLiveTick(true);
};

function updateLiveUIState() {
  const btn = document.getElementById('live-toggle-btn');
  const beacon = document.getElementById('live-beacon-indicator');
  const text = document.getElementById('live-toggle-text');
  if (!btn || !beacon || !text) return;

  if (window.isLiveStreaming) {
    beacon.classList.remove('paused');
    text.innerText = 'LIVE STREAMING';
    btn.className = 'btn-reactive px-3 py-1.5 rounded-xl text-xs font-bold flex items-center gap-2 bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-sm';
  } else {
    beacon.classList.add('paused');
    text.innerText = 'STREAM PAUSED';
    btn.className = 'btn-reactive px-3 py-1.5 rounded-xl text-xs font-bold flex items-center gap-2 bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-sm';
  }
}

function scheduleNextTick() {
  clearTimeout(window.liveTickTimer);
  clearInterval(window.liveCountdownTimer);

  if (!window.isLiveStreaming) return;

  window.liveCountdown = Math.round(window.liveIntervalMs / 1000);
  const countdownEl = document.getElementById('live-tick-countdown');
  if (countdownEl) countdownEl.innerText = `${window.liveCountdown}s`;

  window.liveCountdownTimer = setInterval(() => {
    if (!window.isLiveStreaming) {
      clearInterval(window.liveCountdownTimer);
      return;
    }
    window.liveCountdown--;
    if (window.liveCountdown < 0) {
      window.liveCountdown = Math.round(window.liveIntervalMs / 1000);
    }
    if (countdownEl) countdownEl.innerText = `${window.liveCountdown}s`;
  }, 1000);

  window.liveTickTimer = setTimeout(async () => {
    if (window.isLiveStreaming) {
      await executeLiveTick();
      scheduleNextTick();
    }
  }, window.liveIntervalMs);
}

async function executeLiveTick(isManual = false) {
  if (window.isTickInProgress && !isManual) return;
  window.isTickInProgress = true;

  try {
    const predictParam = window.isLivePredictEnabled ? '1' : '0';
    const ticker = window.currentTicker;

    // Concurrently trigger live tick for active asset and all 10 featured trades
    const [tickRes, featuredRes] = await Promise.allSettled([
      fetch(`/api/stock/${ticker}/live-tick?predict=${predictParam}&model=${window.currentModel}&horizon=${window.currentHorizon}&range=${window.currentRange}`),
      fetch('/api/trades/live-featured')
    ]);

    if (tickRes.status === 'fulfilled' && tickRes.value.ok) {
      const tickData = await tickRes.value.json();
      applyLiveTickData(tickData);
    }

    if (featuredRes.status === 'fulfilled' && featuredRes.value.ok) {
      const trades = await featuredRes.value.json();
      window.featuredTradesData = trades;
      updateFeaturedTradesLive(trades);
    }
  } catch (err) {
    console.warn('Live tick error:', err);
  } finally {
    window.isTickInProgress = false;
  }
}

function applyLiveTickData(tickData) {
  window.liveTickCount++;
  const tickCountEl = document.getElementById('live-tick-count');
  if (tickCountEl) tickCountEl.innerText = `${window.liveTickCount} ticks`;

  // 1. Current Price in Indian Rupees (₹) with smooth visual flash
  const priceEl = document.getElementById('metric-current-price');
  if (priceEl) {
    priceEl.innerText = formatINR(tickData.current_price);
    priceEl.classList.remove('tick-flash-up', 'tick-flash-down');
    void priceEl.offsetWidth; // Reflow trigger
    if (tickData.tick_direction === 'up') {
      priceEl.classList.add('tick-flash-up');
    } else if (tickData.tick_direction === 'down') {
      priceEl.classList.add('tick-flash-down');
    }
  }

  // 2. Price Change Badge
  const changeEl = document.getElementById('metric-price-change');
  if (changeEl) {
    const isPositive = tickData.change >= 0;
    changeEl.className = `inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold ${
      isPositive ? 'badge-bullish' : 'badge-bearish'
    }`;
    changeEl.innerHTML = `
      <i class="fas fa-arrow-${isPositive ? 'up' : 'down'}"></i>
      <span>${isPositive ? '+' : ''}${formatINR(tickData.change)} (${isPositive ? '+' : ''}${tickData.change_pct.toFixed(2)}%)</span>
    `;
  }

  // 3. 52W High / Low
  if (tickData.high_52) {
    const elH = document.getElementById('metric-high-52');
    if (elH) elH.innerText = formatINR(tickData.high_52);
  }
  if (tickData.low_52) {
    const elL = document.getElementById('metric-low-52');
    if (elL) elL.innerText = formatINR(tickData.low_52);
  }

  // 4. Update in-memory candle
  if (window.lastStockData && window.lastStockData.candles && tickData.candle) {
    const candles = window.lastStockData.candles;
    const lastIdx = candles.length - 1;
    candles[lastIdx] = tickData.candle;
    window.lastStockData.current_price = tickData.current_price;
    window.lastStockData.change = tickData.change;
    window.lastStockData.change_pct = tickData.change_pct;
  }

  // 5. Live Technical Analysis updates
  if (tickData.indicators) {
    window.lastIndicatorsData = tickData.indicators;
    updateTechnicalPanel(tickData.indicators);
  }

  // 6. Live Time Series Prediction updates
  if (tickData.prediction) {
    window.lastPredictionData = tickData.prediction;
    renderPredictionResults(tickData.prediction);
  }

  // 7. Update Chart smoothly (60 FPS without destroying canvas)
  if (window.updateLivePriceChart) {
    window.updateLivePriceChart(tickData.current_price, tickData.prediction);
  }
}

function updateFeaturedTradesLive(trades) {
  trades.forEach(t => {
    const priceEl = document.getElementById(`ft-price-${t.id}`);
    const changeEl = document.getElementById(`ft-change-${t.id}`);
    if (priceEl) {
      priceEl.innerText = formatINR(t.price);
      if (t.tick_direction === 'up') {
        priceEl.classList.remove('tick-flash-up', 'tick-flash-down');
        void priceEl.offsetWidth;
        priceEl.classList.add('tick-flash-up');
      } else if (t.tick_direction === 'down') {
        priceEl.classList.remove('tick-flash-up', 'tick-flash-down');
        void priceEl.offsetWidth;
        priceEl.classList.add('tick-flash-down');
      }
    }
    if (changeEl) {
      const isPos = t.change >= 0;
      changeEl.className = `text-[10px] font-bold ${isPos ? 'text-emerald-400' : 'text-rose-400'}`;
      changeEl.innerText = `${isPos ? '+' : ''}${t.change_pct.toFixed(2)}%`;
    }
  });
}

function updateStockHeader(data) {
  const nameEl = document.getElementById('header-name');
  if (nameEl) nameEl.innerText = data.name || data.symbol;

  const catBadge = document.getElementById('header-category-badge');
  if (catBadge) catBadge.innerText = data.category || 'Trading Market';

  const unitEl = document.getElementById('header-unit');
  if (unitEl) unitEl.innerText = data.unit || 'Points (₹)';

  const srcEl = document.getElementById('header-source');
  if (srcEl) srcEl.innerText = data.data_source || 'Live Market Feed (INR)';

  const priceEl = document.getElementById('metric-current-price');
  if (priceEl) priceEl.innerText = formatINR(data.current_price);

  const changeEl = document.getElementById('metric-price-change');
  const isPositive = data.change >= 0;
  changeEl.className = `inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold ${
    isPositive ? 'badge-bullish' : 'badge-bearish'
  }`;
  changeEl.innerHTML = `
    <i class="fas fa-arrow-${isPositive ? 'up' : 'down'}"></i>
    <span>${isPositive ? '+' : ''}${formatINR(data.change)} (${isPositive ? '+' : ''}${data.change_pct.toFixed(2)}%)</span>
  `;

  document.getElementById('metric-high-52').innerText = formatINR(data.high_52);
  document.getElementById('metric-low-52').innerText = formatINR(data.low_52);
  document.getElementById('metric-volatility').innerText = `${data.volatility_30d}%`;
  document.getElementById('metric-volume').innerText = (data.avg_volume / 1e6).toFixed(1) + 'M';
}

function updateTechnicalPanel(indicators) {
  if (!indicators) return;

  // Support / Resistance Pivot levels in Indian Rupees (₹)
  document.getElementById('pivot-val').innerText = formatINR(indicators.levels.pivot);
  document.getElementById('r1-val').innerText = formatINR(indicators.levels.r1);
  document.getElementById('r2-val').innerText = formatINR(indicators.levels.r2);
  document.getElementById('s1-val').innerText = formatINR(indicators.levels.s1);
  document.getElementById('s2-val').innerText = formatINR(indicators.levels.s2);

  // Quantitative Technical Score
  const score = indicators.technical_score;
  const scorePercent = ((score + 100) / 200) * 100;
  const scoreBar = document.getElementById('tech-score-bar');
  if (scoreBar) {
    scoreBar.style.width = `${scorePercent}%`;
    scoreBar.style.backgroundColor = indicators.verdict_color;
  }
  document.getElementById('tech-score-num').innerText = `${score > 0 ? '+' : ''}${score}`;

  const verdictEl = document.getElementById('tech-verdict-badge');
  if (verdictEl) {
    verdictEl.innerText = indicators.verdict;
    verdictEl.style.color = indicators.verdict_color;
    verdictEl.style.borderColor = indicators.verdict_color;
    verdictEl.style.backgroundColor = `${indicators.verdict_color}22`;
  }

  // Key Technical Signals
  const signalsList = document.getElementById('technical-signals-list');
  if (signalsList) {
    signalsList.innerHTML = indicators.signals.map(sig => `
      <li class="flex items-start gap-2 text-xs text-slate-300 py-1 border-b border-white/5 last:border-0">
        <i class="fas fa-check-circle text-cyan-400 mt-0.5 text-[11px]"></i>
        <span>${sig}</span>
      </li>
    `).join('');
  }

  if (window.renderRSIChart) {
    window.renderRSIChart(indicators.dates, indicators.rsi_14);
  }
  if (window.renderMACDChart) {
    window.renderMACDChart(indicators.dates, indicators);
  }
}

// ==========================================
// 4. Time Series Forecasting (INR)
// ==========================================

async function runPrediction() {
  const predictBtn = document.getElementById('run-prediction-btn');
  if (predictBtn) {
    predictBtn.disabled = true;
    predictBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Analyzing Time Series...';
  }

  try {
    const res = await fetch(`/api/stock/${window.currentTicker}/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: window.currentModel,
        horizon: window.currentHorizon,
        range: window.currentRange
      })
    });

    if (!res.ok) throw new Error('Prediction analysis failed');
    const predData = await res.json();
    window.lastPredictionData = predData;

    renderPredictionResults(predData);

    if (window.renderMainPriceChart && window.lastStockData) {
      window.renderMainPriceChart(
        window.lastStockData.candles,
        predData,
        window.lastIndicatorsData
      );
      window.renderVolumeChart(window.lastStockData.candles);
    }

    if (window.currentUser && window.loadPredictionHistory) {
      window.loadPredictionHistory();
    }
  } catch (err) {
    console.error('Prediction failed:', err);
    showToast('Failed to compute time series prediction.', 'error');
  } finally {
    if (predictBtn) {
      predictBtn.disabled = false;
      predictBtn.innerHTML = '<i class="fas fa-bolt mr-2 text-cyan-400"></i> Run Time Series Prediction';
    }
  }
}

function renderPredictionResults(pred) {
  document.getElementById('pred-target-price').innerText = formatINR(pred.target_price);
  const changeEl = document.getElementById('pred-change-pct');
  const isPos = pred.expected_change >= 0;
  changeEl.className = `text-sm font-semibold ${isPos ? 'text-emerald-400' : 'text-rose-400'}`;
  changeEl.innerText = `${isPos ? '+' : ''}${formatINR(pred.expected_change)} (${isPos ? '+' : ''}${pred.expected_change_pct.toFixed(2)}%)`;

  const trendEl = document.getElementById('pred-trend-call');
  trendEl.innerText = pred.trend_call;
  trendEl.style.color = pred.trend_call_color;

  document.getElementById('pred-model-display').innerText = pred.model_display;
  document.getElementById('pred-model-desc').innerText = pred.model_description;

  // Evaluation Metrics in INR
  const m = pred.metrics;
  document.getElementById('metric-rmse').innerText = formatINR(m.rmse);
  document.getElementById('metric-mae').innerText = formatINR(m.mae);
  document.getElementById('metric-mape').innerText = `${m.mape.toFixed(2)}%`;
  document.getElementById('metric-r2').innerText = m.r2.toFixed(3);
  document.getElementById('metric-dir-acc').innerText = `${m.directional_accuracy.toFixed(1)}%`;
}

// ==========================================
// 5. Watchlist & Search Handling
// ==========================================

async function loadWatchlist() {
  try {
    const res = await fetch('/api/watchlist');
    const data = await res.json();
    const list = data.watchlist || [];

    const container = document.getElementById('watchlist-container');
    if (!container) return;

    if (list.length === 0) {
      container.innerHTML = '<div class="text-xs text-slate-400 p-3 text-center">Watchlist is empty. Click star to add trades!</div>';
      return;
    }

    container.innerHTML = list.map(sym => {
      const match = window.featuredTradesData.find(t => t.id === sym || t.symbol === sym);
      const name = match ? match.name : sym;
      const category = match ? match.category : 'Market';
      return `
        <button onclick="loadStockData('${sym}')" class="btn-reactive w-full flex items-center justify-between p-2.5 rounded-xl border border-white/5 bg-white/5 hover:bg-white/10 transition-all text-left mb-1.5 ${
          sym === window.currentTicker ? 'border-cyan-500/50 bg-cyan-500/10' : ''
        }">
          <div>
            <span class="font-bold text-xs theme-text-primary block">${name}</span>
            <span class="text-[9px] text-cyan-400">${category}</span>
          </div>
          <span class="text-[10px] text-cyan-400 font-mono">View <i class="fas fa-chevron-right text-[8px] ml-0.5"></i></span>
        </button>
      `;
    }).join('');

    updateWatchlistStarButton();
  } catch (err) {
    console.error('Failed to load watchlist:', err);
  }
}

async function toggleWatchlist() {
  if (!window.currentUser) {
    showToast('Please sign in to save trades to your watchlist.', 'warning');
    openAuthModal('login');
    return;
  }

  try {
    const res = await fetch('/api/watchlist/toggle', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ticker: window.currentTicker })
    });
    const data = await res.json();
    if (data.success) {
      showToast(data.message, 'success');
      loadWatchlist();
    }
  } catch (err) {
    showToast('Failed to update watchlist.', 'error');
  }
}

async function updateWatchlistStarButton() {
  const starIcon = document.getElementById('watchlist-star-icon');
  if (!starIcon) return;

  try {
    const res = await fetch('/api/watchlist');
    const data = await res.json();
    const list = data.watchlist || [];
    const isWatched = list.includes(window.currentTicker);

    if (isWatched) {
      starIcon.classList.remove('far');
      starIcon.classList.add('fas', 'text-amber-400');
    } else {
      starIcon.classList.remove('fas', 'text-amber-400');
      starIcon.classList.add('far');
    }
  } catch (err) {
    // ignore
  }
}

// Load Recent Prediction History
async function loadPredictionHistory() {
  const container = document.getElementById('history-container');
  if (!container) return;

  try {
    const res = await fetch('/api/predictions/history');
    const data = await res.json();
    const history = data.history || [];

    if (history.length === 0) {
      container.innerHTML = '<div class="text-xs text-slate-400 p-2 text-center">No predictions saved yet.</div>';
      return;
    }

    container.innerHTML = history.map(h => {
      const isPos = h.change_pct >= 0;
      return `
        <div class="flex items-center justify-between p-2 rounded-xl border border-white/5 bg-white/5 text-xs mb-1">
          <div>
            <span class="font-bold theme-text-primary mr-1.5">${h.ticker}</span>
            <span class="text-[10px] text-slate-400">${h.model} (${h.horizon}d)</span>
          </div>
          <div class="text-right">
            <span class="font-semibold theme-text-primary">${formatINR(h.predicted_price)}</span>
            <span class="text-[10px] ml-1.5 font-bold ${isPos ? 'text-emerald-400' : 'text-rose-400'}">${isPos ? '+' : ''}${h.change_pct.toFixed(1)}%</span>
          </div>
        </div>
      `;
    }).join('');
  } catch (err) {
    // ignore
  }
}

// Export Prediction Report as JSON or CSV
window.exportPredictionReport = function (format = 'json') {
  if (!window.lastPredictionData || !window.lastStockData) {
    showToast('No active prediction to export.', 'warning');
    return;
  }

  const ticker = window.currentTicker;
  const pred = window.lastPredictionData;
  const stock = window.lastStockData;

  if (format === 'json') {
    const report = {
      market: ticker,
      currency: 'INR (₹)',
      stock_summary: stock,
      prediction: pred,
      exported_at: new Date().toISOString()
    };
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    downloadBlob(blob, `${ticker}_TimeSeries_Forecast_INR.json`);
  } else {
    let csv = 'Date,Forecast_Price_INR,Lower_95_CI_INR,Upper_95_CI_INR\n';
    pred.future_dates.forEach((dt, i) => {
      csv += `${dt},${pred.forecast_prices[i]},${pred.lower_bounds[i]},${pred.upper_bounds[i]}\n`;
    });
    const blob = new Blob([csv], { type: 'text/csv' });
    downloadBlob(blob, `${ticker}_TimeSeries_Forecast_INR.csv`);
  }
  showToast(`Exported ${ticker} prediction report in INR (${format.toUpperCase()})!`, 'success');
};

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function setLoadingState(loading) {
  const chartWrapper = document.getElementById('chart-wrapper');
  if (chartWrapper) {
    chartWrapper.classList.toggle('opacity-50', loading);
  }
}

// ==========================================
// 6. DOM Initialization & Event Listeners
// ==========================================

document.addEventListener('DOMContentLoaded', async () => {
  initTheme();
  updateLiveUIState();
  await loadFeaturedTrades();
  loadWatchlist();
  loadStockData('NIFTY50', '1y');

  const searchInput = document.getElementById('stock-search-input');
  const searchBtn = document.getElementById('stock-search-btn');

  function triggerSearch() {
    const val = searchInput.value.trim();
    if (val) {
      loadStockData(val);
      searchInput.value = '';
    }
  }

  if (searchInput) {
    searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') triggerSearch();
    });
  }
  if (searchBtn) {
    searchBtn.addEventListener('click', triggerSearch);
  }

  const mobileSearch = document.getElementById('stock-search-input-mobile');
  if (mobileSearch) {
    mobileSearch.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        const val = mobileSearch.value.trim();
        if (val) {
          loadStockData(val);
          mobileSearch.value = '';
        }
      }
    });
  }

  // Model Selector Pills
  const modelPills = document.querySelectorAll('.model-pill');
  modelPills.forEach(pill => {
    pill.addEventListener('click', () => {
      modelPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      window.currentModel = pill.getAttribute('data-model');
      runPrediction();
    });
  });

  // Horizon Selector Pills
  const horizonPills = document.querySelectorAll('.horizon-pill');
  horizonPills.forEach(pill => {
    pill.addEventListener('click', () => {
      horizonPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      window.currentHorizon = parseInt(pill.getAttribute('data-horizon'));
      runPrediction();
    });
  });

  // Range Selector Pills
  const rangePills = document.querySelectorAll('.range-pill');
  rangePills.forEach(pill => {
    pill.addEventListener('click', () => {
      rangePills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      const newRange = pill.getAttribute('data-range');
      loadStockData(window.currentTicker, newRange);
    });
  });

  // Overlay Toggles
  document.querySelectorAll('.overlay-toggle').forEach(chk => {
    chk.addEventListener('change', (e) => {
      const type = e.target.getAttribute('data-overlay');
      window.activeOverlays[type] = e.target.checked;
      if (window.renderMainPriceChart && window.lastStockData) {
        window.renderMainPriceChart(
          window.lastStockData.candles,
          window.lastPredictionData,
          window.lastIndicatorsData
        );
      }
    });
  });

  // Sound Toggle Button
  const soundBtn = document.getElementById('sound-toggle-btn');
  if (soundBtn) {
    soundBtn.addEventListener('click', () => {
      const active = window.toggleAudioFeedback();
      soundBtn.innerHTML = active
        ? '<i class="fas fa-volume-up text-cyan-400"></i>'
        : '<i class="fas fa-volume-mute text-slate-400"></i>';
      showToast(active ? 'Tactile Audio Feedback: ON' : 'Tactile Audio Feedback: OFF', 'info');
    });
  }
});
