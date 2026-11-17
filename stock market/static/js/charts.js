/**
 * Interactive Time Series & Financial Charting Engine
 * Powered by Chart.js with dynamic theme styling and confidence bands
 */

window.chartInstances = {
  price: null,
  volume: null,
  rsi: null,
  macd: null
};

// Helper for Indian Rupee currency formatting
function formatINR(val) {
  if (val === null || val === undefined || isNaN(val)) return '₹0.00';
  return '₹' + Number(val).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// Retrieve theme-adaptive colors
function getChartThemeColors() {
  const isDark = document.documentElement.getAttribute('data-theme') !== 'light';
  return {
    gridColor: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(15, 23, 42, 0.06)',
    textColor: isDark ? '#94a3b8' : '#64748b',
    tooltipBg: isDark ? 'rgba(17, 24, 39, 0.95)' : 'rgba(255, 255, 255, 0.95)',
    tooltipText: isDark ? '#f8fafc' : '#0f172a',
    tooltipBorder: isDark ? 'rgba(255, 255, 255, 0.15)' : 'rgba(15, 23, 42, 0.15)',
    primaryLine: isDark ? '#06b6d4' : '#0891b2',
    primaryGradient: isDark ? ['rgba(6, 182, 212, 0.28)', 'rgba(6, 182, 212, 0.01)'] : ['rgba(8, 145, 178, 0.2)', 'rgba(8, 145, 178, 0.01)'],
    forecastLine: '#8b5cf6',
    forecastBandFill: isDark ? 'rgba(139, 92, 246, 0.12)' : 'rgba(139, 92, 246, 0.08)'
  };
}

// Render or Update the Main Stock & Prediction Chart
window.renderMainPriceChart = function (candles, prediction = null, indicators = null, chartType = 'area') {
  const ctx = document.getElementById('main-price-chart');
  if (!ctx) return;

  const theme = getChartThemeColors();
  const histDates = candles.map(c => c.date);
  const histCloses = candles.map(c => c.close);

  let allDates = [...histDates];
  let forecastData = new Array(histDates.length - 1).fill(null);
  // Bridge the last historical point with the forecast
  forecastData.push(histCloses[histCloses.length - 1]);

  let upperBandData = new Array(histDates.length - 1).fill(null);
  upperBandData.push(histCloses[histCloses.length - 1]);

  let lowerBandData = new Array(histDates.length - 1).fill(null);
  lowerBandData.push(histCloses[histCloses.length - 1]);

  if (prediction && prediction.future_dates) {
    allDates = allDates.concat(prediction.future_dates);
    forecastData = forecastData.concat(prediction.forecast_prices);
    upperBandData = upperBandData.concat(prediction.upper_bounds);
    lowerBandData = lowerBandData.concat(prediction.lower_bounds);
  }

  // Build datasets
  const datasets = [
    {
      label: 'Historical Close (₹)',
      data: histCloses,
      borderColor: theme.primaryLine,
      borderWidth: 2.2,
      backgroundColor: (context) => {
        const chart = context.chart;
        const { ctx, chartArea } = chart;
        if (!chartArea) return null;
        const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
        gradient.addColorStop(0, theme.primaryGradient[0]);
        gradient.addColorStop(1, theme.primaryGradient[1]);
        return gradient;
      },
      fill: chartType === 'area',
      tension: 0.25,
      pointRadius: 0,
      pointHoverRadius: 5,
      pointHoverBackgroundColor: theme.primaryLine,
      pointHoverBorderColor: '#ffffff',
      pointHoverBorderWidth: 2,
      order: 3
    }
  ];

  // Optional Overlays (SMA 20, SMA 50, Bollinger Bands)
  if (indicators) {
    if (window.activeOverlays?.sma20 && indicators.sma_20) {
      datasets.push({
        label: 'SMA 20',
        data: indicators.sma_20,
        borderColor: '#f59e0b',
        borderWidth: 1.5,
        borderDash: [4, 4],
        pointRadius: 0,
        fill: false,
        order: 4
      });
    }
    if (window.activeOverlays?.sma50 && indicators.sma_50) {
      datasets.push({
        label: 'SMA 50',
        data: indicators.sma_50,
        borderColor: '#3b82f6',
        borderWidth: 1.5,
        borderDash: [4, 4],
        pointRadius: 0,
        fill: false,
        order: 5
      });
    }
    if (window.activeOverlays?.bb && indicators.bb_upper && indicators.bb_lower) {
      datasets.push({
        label: 'BB Upper',
        data: indicators.bb_upper,
        borderColor: 'rgba(99, 102, 241, 0.4)',
        borderWidth: 1,
        pointRadius: 0,
        fill: false,
        order: 6
      });
      datasets.push({
        label: 'BB Lower',
        data: indicators.bb_lower,
        borderColor: 'rgba(99, 102, 241, 0.4)',
        borderWidth: 1,
        pointRadius: 0,
        fill: false,
        order: 7
      });
    }
  }

  // Time Series Prediction & Confidence Interval Bands
  if (prediction && prediction.forecast_prices) {
    // Upper Bound
    datasets.push({
      label: 'Confidence Upper (95% CI)',
      data: upperBandData,
      borderColor: 'transparent',
      pointRadius: 0,
      fill: false,
      order: 1
    });

    // Lower Bound with area fill up to Upper Bound
    datasets.push({
      label: 'Confidence Lower (95% CI)',
      data: lowerBandData,
      borderColor: 'transparent',
      backgroundColor: theme.forecastBandFill,
      fill: '-1', // Fills between Upper and Lower
      pointRadius: 0,
      order: 2
    });

    // Predicted Forecast Trajectory Line
    datasets.push({
      label: `Forecast (${prediction.model_display || 'Prediction'})`,
      data: forecastData,
      borderColor: theme.forecastLine,
      borderWidth: 2.8,
      borderDash: [6, 4],
      pointRadius: (ctx) => (ctx.dataIndex === forecastData.length - 1 ? 5 : 0),
      pointBackgroundColor: theme.forecastLine,
      pointBorderColor: '#ffffff',
      pointBorderWidth: 2,
      fill: false,
      tension: 0.2,
      order: 0
    });

    // Monte Carlo individual sample paths
    if (prediction.sample_paths && prediction.sample_paths.length > 0) {
      prediction.sample_paths.forEach((path, idx) => {
        let pathData = new Array(histDates.length - 1).fill(null);
        pathData.push(histCloses[histCloses.length - 1]);
        pathData = pathData.concat(path);

        datasets.push({
          label: `Sim Path #${idx + 1}`,
          data: pathData,
          borderColor: 'rgba(168, 85, 247, 0.22)',
          borderWidth: 1,
          pointRadius: 0,
          fill: false,
          tension: 0.15,
          order: 8
        });
      });
    }
  }

  if (window.chartInstances.price) {
    window.chartInstances.price.destroy();
  }

  window.chartInstances.price = new Chart(ctx, {
    type: 'line',
    data: {
      labels: allDates,
      datasets: datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false
      },
      plugins: {
        legend: {
          display: true,
          position: 'top',
          labels: {
            color: theme.textColor,
            font: { size: 11, family: 'Inter' },
            boxWidth: 12,
            filter: (item) => !item.text.includes('Sim Path') && !item.text.includes('Confidence')
          }
        },
        tooltip: {
          backgroundColor: theme.tooltipBg,
          titleColor: theme.tooltipText,
          bodyColor: theme.tooltipText,
          borderColor: theme.tooltipBorder,
          borderWidth: 1,
          padding: 12,
          boxPadding: 4,
          cornerRadius: 10,
          callbacks: {
            label: function (context) {
              if (context.raw === null || context.raw === undefined) return null;
              return `${context.dataset.label}: ${formatINR(context.raw)}`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: { color: theme.gridColor, drawBorder: false },
          ticks: {
            color: theme.textColor,
            maxTicksLimit: 12,
            font: { size: 10 }
          }
        },
        y: {
          grid: { color: theme.gridColor, drawBorder: false },
          ticks: {
            color: theme.textColor,
            font: { size: 10 },
            callback: (val) => {
              if (val >= 10000000) return `₹${(val / 10000000).toFixed(1)}Cr`;
              if (val >= 100000) return `₹${(val / 100000).toFixed(1)}L`;
              if (val >= 1000) return `₹${(val / 1000).toFixed(0)}k`;
              return `₹${val}`;
            }
          }
        }
      }
    }
  });
};

// ==========================================
// Ultra-Smooth Live Chart Tick & Prediction Update (60 FPS)
// ==========================================
window.updateLivePriceChart = function (newPrice, prediction = null) {
  const chart = window.chartInstances.price;
  if (!chart || !chart.data || !chart.data.datasets || chart.data.datasets.length === 0) return;

  const histDataset = chart.data.datasets.find(d => d.label && d.label.includes('Historical Close'));
  if (histDataset && histDataset.data.length > 0) {
    histDataset.data[histDataset.data.length - 1] = newPrice;
  }

  // If a live prediction was recalculated on this tick, update the forecast line and confidence bands!
  if (prediction && prediction.forecast_prices) {
    const histLen = histDataset ? histDataset.data.length : 0;
    
    // Forecast Line
    const forecastDataset = chart.data.datasets.find(d => d.label && d.label.includes('Forecast'));
    if (forecastDataset) {
      let fData = new Array(Math.max(0, histLen - 1)).fill(null);
      fData.push(newPrice);
      fData = fData.concat(prediction.forecast_prices);
      forecastDataset.data = fData;
    }

    // Upper Band
    const upperDataset = chart.data.datasets.find(d => d.label && d.label.includes('Confidence Upper'));
    if (upperDataset && prediction.upper_bounds) {
      let uData = new Array(Math.max(0, histLen - 1)).fill(null);
      uData.push(newPrice);
      uData = uData.concat(prediction.upper_bounds);
      upperDataset.data = uData;
    }

    // Lower Band
    const lowerDataset = chart.data.datasets.find(d => d.label && d.label.includes('Confidence Lower'));
    if (lowerDataset && prediction.lower_bounds) {
      let lData = new Array(Math.max(0, histLen - 1)).fill(null);
      lData.push(newPrice);
      lData = lData.concat(prediction.lower_bounds);
      lowerDataset.data = lData;
    }
  }

  // Update chart smoothly without full re-render
  chart.update('none');
};

// Render Synchronized Volume Sub-chart
window.renderVolumeChart = function (candles) {
  const ctx = document.getElementById('volume-chart');
  if (!ctx) return;

  const theme = getChartThemeColors();
  const dates = candles.map(c => c.date);
  const volumes = candles.map(c => c.volume);
  const bgColors = candles.map(c => (c.close >= c.open ? 'rgba(16, 185, 129, 0.45)' : 'rgba(244, 63, 94, 0.45)'));

  if (window.chartInstances.volume) {
    window.chartInstances.volume.destroy();
  }

  window.chartInstances.volume = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: dates,
      datasets: [{
        label: 'Volume',
        data: volumes,
        backgroundColor: bgColors,
        borderWidth: 0,
        borderRadius: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => `Vol: ${(ctx.raw).toLocaleString()}`
          }
        }
      },
      scales: {
        x: { display: false },
        y: {
          grid: { color: theme.gridColor, drawBorder: false },
          ticks: {
            color: theme.textColor,
            maxTicksLimit: 3,
            callback: (v) => `${(v / 1e6).toFixed(1)}M`
          }
        }
      }
    }
  });
};

// Render RSI (Relative Strength Index) Chart
window.renderRSIChart = function (dates, rsiValues) {
  const ctx = document.getElementById('rsi-chart');
  if (!ctx) return;

  const theme = getChartThemeColors();

  if (window.chartInstances.rsi) {
    window.chartInstances.rsi.destroy();
  }

  window.chartInstances.rsi = new Chart(ctx, {
    type: 'line',
    data: {
      labels: dates,
      datasets: [
        {
          label: 'RSI (14)',
          data: rsiValues,
          borderColor: '#8b5cf6',
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.2,
          fill: false
        },
        {
          label: 'Overbought (70)',
          data: new Array(dates.length).fill(70),
          borderColor: 'rgba(239, 68, 68, 0.6)',
          borderWidth: 1.2,
          borderDash: [5, 5],
          pointRadius: 0,
          fill: false
        },
        {
          label: 'Oversold (30)',
          data: new Array(dates.length).fill(30),
          borderColor: 'rgba(16, 185, 129, 0.6)',
          borderWidth: 1.2,
          borderDash: [5, 5],
          pointRadius: 0,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: { display: false },
        y: {
          min: 0,
          max: 100,
          grid: { color: theme.gridColor },
          ticks: {
            color: theme.textColor,
            stepSize: 20,
            font: { size: 9 }
          }
        }
      }
    }
  });
};

// Render MACD Sub-chart
window.renderMACDChart = function (dates, macdPack) {
  const ctx = document.getElementById('macd-chart');
  if (!ctx) return;

  const theme = getChartThemeColors();

  if (window.chartInstances.macd) {
    window.chartInstances.macd.destroy();
  }

  const histColors = macdPack.macd_hist.map(v => (v >= 0 ? 'rgba(16, 185, 129, 0.7)' : 'rgba(244, 63, 94, 0.7)'));

  window.chartInstances.macd = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: dates,
      datasets: [
        {
          type: 'line',
          label: 'MACD (12,26)',
          data: macdPack.macd,
          borderColor: '#06b6d4',
          borderWidth: 1.8,
          pointRadius: 0,
          fill: false,
          tension: 0.2
        },
        {
          type: 'line',
          label: 'Signal (9)',
          data: macdPack.macd_signal,
          borderColor: '#f59e0b',
          borderWidth: 1.8,
          pointRadius: 0,
          fill: false,
          tension: 0.2
        },
        {
          type: 'bar',
          label: 'Histogram',
          data: macdPack.macd_hist,
          backgroundColor: histColors,
          borderWidth: 0
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: 'top',
          labels: { color: theme.textColor, font: { size: 10 }, boxWidth: 10 }
        }
      },
      scales: {
        x: { display: false },
        y: {
          grid: { color: theme.gridColor },
          ticks: { color: theme.textColor, font: { size: 9 } }
        }
      }
    }
  });
};

// Refresh All Active Charts when switching Dark / Light theme
window.refreshAllChartsTheme = function () {
  if (window.lastStockData) {
    window.renderMainPriceChart(
      window.lastStockData.candles,
      window.lastPredictionData,
      window.lastIndicatorsData
    );
    window.renderVolumeChart(window.lastStockData.candles);
    if (window.lastIndicatorsData) {
      window.renderRSIChart(window.lastIndicatorsData.dates, window.lastIndicatorsData.rsi_14);
      window.renderMACDChart(window.lastIndicatorsData.dates, window.lastIndicatorsData);
    }
  }
};
