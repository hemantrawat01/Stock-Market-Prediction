/**
 * Cursor Interaction Engine
 * Features:
 * 1. Ambient cursor follower with physics interpolation (lerp)
 * 2. Per-button cursor-tracking spotlight (radial glow following cursor coordinates)
 * 3. Magnetic pull towards cursor on hover
 * 4. Coordinate-based ripple wave effect on click
 * 5. Audio-tactile feedback using Web Audio API
 * 6. MutationObserver ensuring all dynamically injected buttons are reactive
 */

(function () {
  'use strict';

  let mouseX = -100;
  let mouseY = -100;
  let auraX = -100;
  let auraY = -100;
  let isSoundEnabled = false;

  // Web Audio Context for tactile micro-feedback
  let audioCtx = null;
  function playClickHaptic() {
    if (!isSoundEnabled) return;
    try {
      if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      }
      if (audioCtx.state === 'suspended') {
        audioCtx.resume();
      }
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(800, audioCtx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(350, audioCtx.currentTime + 0.04);
      gain.gain.setValueAtTime(0.08, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.04);
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.05);
    } catch (e) {
      // AudioContext policy fallback
    }
  }

  // Create ambient cursor aura element
  function createCursorAura() {
    if (document.getElementById('cursor-aura')) return;
    const aura = document.createElement('div');
    aura.id = 'cursor-aura';
    document.body.appendChild(aura);

    // Track mouse coordinates
    window.addEventListener('mousemove', (e) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
      if (e.target && e.target.closest('input, textarea, select, .input-box, .modal-content')) {
        aura.style.opacity = '0';
      } else {
        aura.style.opacity = '1';
      }
    }, { passive: true });

    document.documentElement.addEventListener('mouseleave', () => {
      aura.style.opacity = '0';
    });

    window.addEventListener('mousedown', () => {
      aura.classList.add('clicking');
    });

    window.addEventListener('mouseup', () => {
      aura.classList.remove('clicking');
    });

    // Smooth lerp animation loop
    function animateAura() {
      // Linear interpolation factor
      const ease = 0.18;
      auraX += (mouseX - auraX) * ease;
      auraY += (mouseY - auraY) * ease;

      aura.style.transform = `translate(${auraX}px, ${auraY}px) translate(-50%, -50%)`;
      requestAnimationFrame(animateAura);
    }
    requestAnimationFrame(animateAura);
  }

  // Bind cursor reactivity to an element (buttons, pills, interactive cards)
  function attachCursorReactivity(elem) {
    if (elem.__cursorReactiveAttached) return;
    if (elem.classList.contains('no-reactive') || elem.classList.contains('input-btn-eye')) return;
    elem.__cursorReactiveAttached = true;

    // Mouse move: update spotlight position & magnetic pull
    elem.addEventListener('mousemove', (e) => {
      const rect = elem.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      elem.style.setProperty('--cursor-x', `${x}px`);
      elem.style.setProperty('--cursor-y', `${y}px`);

      // Calculate magnetic displacement from center (capped to subtle offset)
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;
      const deltaX = (x - centerX) * 0.12;
      const deltaY = (y - centerY) * 0.12;

      elem.style.setProperty('--mag-x', `${deltaX}px`);
      elem.style.setProperty('--mag-y', `${deltaY}px`);

      const aura = document.getElementById('cursor-aura');
      if (aura) aura.classList.add('hovering-button');
    });

    // Mouse leave: reset magnetic displacement smoothly
    elem.addEventListener('mouseleave', () => {
      elem.style.setProperty('--mag-x', '0px');
      elem.style.setProperty('--mag-y', '0px');

      const aura = document.getElementById('cursor-aura');
      if (aura) aura.classList.remove('hovering-button');
    });

    // Click: spawn ripple effect from exact click coordinates
    elem.addEventListener('click', (e) => {
      playClickHaptic();

      const rect = elem.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const clickY = e.clientY - rect.top;

      const ripple = document.createElement('span');
      ripple.className = 'btn-ripple';

      // Size of ripple based on button max dimension
      const size = Math.max(rect.width, rect.height) * 2;
      ripple.style.width = `${size}px`;
      ripple.style.height = `${size}px`;
      ripple.style.left = `${clickX - size / 2}px`;
      ripple.style.top = `${clickY - size / 2}px`;

      elem.appendChild(ripple);

      // Clean up after animation finishes
      setTimeout(() => {
        if (ripple && ripple.parentNode) {
          ripple.parentNode.removeChild(ripple);
        }
      }, 700);
    });
  }

  // Scan and attach reactivity to all buttons & interactive elements
  function initAllButtons() {
    const selector = 'button:not(.no-reactive):not(.input-btn-eye), .btn-reactive, .btn-pill, .interactive-card, a.btn-action';
    const elements = document.querySelectorAll(selector);
    elements.forEach(attachCursorReactivity);
  }

  // Observe DOM additions to make future dynamically injected buttons reactive
  function observeDOM() {
    const observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        if (mutation.addedNodes.length) {
          mutation.addedNodes.forEach((node) => {
            if (node.nodeType === 1) {
              if (node.matches && node.matches('button:not(.no-reactive):not(.input-btn-eye), .btn-reactive, .btn-pill, .interactive-card')) {
                attachCursorReactivity(node);
              }
              const childButtons = node.querySelectorAll ? node.querySelectorAll('button:not(.no-reactive):not(.input-btn-eye), .btn-reactive, .btn-pill, .interactive-card') : [];
              childButtons.forEach(attachCursorReactivity);
            }
          });
        }
      }
    });

    observer.observe(document.body, { childList: true, subtree: true });
  }

  // Public sound toggle function
  window.toggleAudioFeedback = function () {
    isSoundEnabled = !isSoundEnabled;
    return isSoundEnabled;
  };

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      createCursorAura();
      initAllButtons();
      observeDOM();
    });
  } else {
    createCursorAura();
    initAllButtons();
    observeDOM();
  }
})();
