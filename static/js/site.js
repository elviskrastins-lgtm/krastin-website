/* Krastin CFO Partners — small progressive enhancements. Every page works without this file. */
(function () {
  'use strict';
  var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var store = {
    get: function (k) { try { return JSON.parse(sessionStorage.getItem(k)); } catch (e) { return null; } },
    set: function (k, v) { try { sessionStorage.setItem(k, JSON.stringify(v)); } catch (e) {} },
    del: function (k) { try { sessionStorage.removeItem(k); } catch (e) {} }
  };

  /* ---------- Header: scrolled state + mobile menu ---------- */
  var header = $('.k-header');
  if (header) {
    var onScroll = function () { header.classList.toggle('is-scrolled', window.scrollY > 8); };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    var btn = $('.k-menu-btn', header);
    var setOpen = function (open) {
      header.classList.toggle('is-open', open);
      document.documentElement.classList.toggle('k-menu-open', open);
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      btn.setAttribute('aria-label', open ? btn.dataset.close : btn.dataset.open);
    };
    if (btn) {
      btn.addEventListener('click', function () { setOpen(!header.classList.contains('is-open')); });
      document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && header.classList.contains('is-open')) { setOpen(false); btn.focus(); } });
      var mq = window.matchMedia('(max-width: 1120px)');
      var onMq = function () { if (!mq.matches) setOpen(false); };
      mq.addEventListener ? mq.addEventListener('change', onMq) : mq.addListener(onMq);
    }
  }

  /* ---------- Home: typed word ---------- */
  var typed = $('.k-typed');
  if (typed && !reduced) {
    var words = JSON.parse(typed.dataset.words);
    var text = $('.k-typed__text', typed);
    var caret = document.createElement('span');
    caret.className = 'k-caret';
    caret.setAttribute('aria-hidden', 'true');
    typed.appendChild(caret);
    var idx = 0, len = words[0].length, deleting = false;
    var tick = function () {
      var w = words[idx], delay;
      if (!deleting) {
        if (len < w.length) { len++; delay = len < w.length ? 78 : 1600; }
        else { deleting = true; delay = 45; }
      } else if (len > 0) { len--; delay = len > 0 ? 45 : 360; }
      else { deleting = false; idx = (idx + 1) % words.length; delay = 78; }
      text.textContent = words[idx].slice(0, len);
      setTimeout(tick, delay);
    };
    setTimeout(tick, 1600);
  }

  /* ---------- Home: smooth scroll to problems ---------- */
  $$('[data-scroll-to]').forEach(function (a) {
    a.addEventListener('click', function (e) {
      var el = document.getElementById(a.dataset.scrollTo);
      if (!el) return;
      e.preventDefault();
      var y = el.getBoundingClientRect().top + window.scrollY - 76;
      window.scrollTo({ top: y, behavior: reduced ? 'auto' : 'smooth' });
    });
  });

  /* ---------- Home: problem chips ---------- */
  var picker = $('.k-problems');
  if (picker) {
    var helper = $('.k-helper', picker);
    var chips = $$('.k-chip', picker);
    var saved = store.get('k-problems') || [];
    var update = function () {
      var picked = chips.filter(function (c) { return c.getAttribute('aria-pressed') === 'true'; }).map(function (c) { return c.textContent.trim(); });
      var n = picked.length;
      helper.textContent = n === 0 ? helper.dataset.none : (n === 1 ? helper.dataset.one : helper.dataset.many).replace('{n}', n);
      if (n) store.set('k-problems', picked); else store.del('k-problems');
    };
    chips.forEach(function (c) {
      if (saved.indexOf(c.textContent.trim()) !== -1) c.setAttribute('aria-pressed', 'true');
      c.addEventListener('click', function () {
        c.setAttribute('aria-pressed', c.getAttribute('aria-pressed') === 'true' ? 'false' : 'true');
        update();
      });
    });
    if (saved.length) update();
  }

  /* ---------- Insight line art: replay on hover ---------- */
  $$('.k-art').forEach(function (art) {
    art.addEventListener('mouseenter', function () {
      if (reduced) return;
      var svg = $('svg', art);
      var copy = svg.cloneNode(true);
      svg.parentNode.replaceChild(copy, svg);
    });
  });

  /* ---------- Services: tiles, task panel, task detail ---------- */
  var tilesWrap = $('.k-tiles');
  if (tilesWrap) {
    var narrowMq = window.matchMedia('(max-width: 640px)');
    var tiles = $$('.k-tile', tilesWrap);
    var panelHome = $('.k-panels');
    var panels = {};
    $$('.k-tile-panel', panelHome).forEach(function (p) { panels[p.dataset.area] = p; });
    var current = null;

    var place = function () {
      var narrow = narrowMq.matches;
      Object.keys(panels).forEach(function (id) {
        var p = panels[id];
        var tile = tilesWrap.querySelector('.k-tile[data-area="' + id + '"]');
        if (narrow) { tile.insertAdjacentElement('afterend', p); p.classList.add('k-tile-panel--inline'); }
        else { panelHome.appendChild(p); p.classList.remove('k-tile-panel--inline'); }
        // task detail boxes
        $$('.k-task', p).forEach(function (t) {
          var d = document.getElementById(t.getAttribute('aria-controls'));
          if (narrow) { t.insertAdjacentElement('afterend', d); d.classList.add('k-task-detail'); }
          else { $('.k-details', p).appendChild(d); d.classList.remove('k-task-detail'); }
        });
      });
    };
    var openArea = function (id) {
      current = current === id ? null : id;
      tiles.forEach(function (t) { t.setAttribute('aria-expanded', t.dataset.area === current ? 'true' : 'false'); });
      Object.keys(panels).forEach(function (k) {
        panels[k].hidden = k !== current;
        closeTasks(panels[k]);
      });
    };
    var closeTasks = function (p) {
      $$('.k-task', p).forEach(function (t) { t.setAttribute('aria-pressed', 'false'); document.getElementById(t.getAttribute('aria-controls')).hidden = true; });
    };
    tiles.forEach(function (t) { t.addEventListener('click', function () { openArea(t.dataset.area); }); });
    Object.keys(panels).forEach(function (k) {
      var p = panels[k];
      $$('.k-task', p).forEach(function (t, i) {
        t.style.animationDelay = (i * 45) + 'ms';
        t.addEventListener('click', function () {
          var on = t.getAttribute('aria-pressed') === 'true';
          closeTasks(p);
          if (!on) { t.setAttribute('aria-pressed', 'true'); document.getElementById(t.getAttribute('aria-controls')).hidden = false; }
        });
      });
      $$('.k-detail__close', p).forEach(function (b) { b.addEventListener('click', function () { closeTasks(p); }); });
    });
    narrowMq.addEventListener ? narrowMq.addEventListener('change', place) : narrowMq.addListener(place);
    place();
    var fromHash = location.hash.slice(1);
    if (fromHash && panels[fromHash]) {
      openArea(fromHash);
      var tile = tilesWrap.querySelector('.k-tile[data-area="' + fromHash + '"]');
      setTimeout(function () { tile.scrollIntoView({ block: 'start' }); }, 0);
    } else {
      openArea(tiles[0].dataset.area);
    }
  }

  /* ---------- FAQ accordion (one open at a time) ---------- */
  var faqBtns = $$('.k-faq-q');
  faqBtns.forEach(function (b) {
    b.addEventListener('click', function () {
      var open = b.getAttribute('aria-expanded') === 'true';
      faqBtns.forEach(function (o) { o.setAttribute('aria-expanded', 'false'); document.getElementById(o.getAttribute('aria-controls')).hidden = true; });
      if (!open) { b.setAttribute('aria-expanded', 'true'); document.getElementById(b.getAttribute('aria-controls')).hidden = false; }
    });
  });

  /* ---------- Contact form ---------- */
  var form = $('.k-form');
  if (form) {
    var card = form.parentNode;
    var success = $('.k-success', card);
    var errorEl = $('.k-form__error', form);
    var submit = $('button[type="submit"]', form);
    var msg = $('textarea', form);
    var problems = store.get('k-problems');
    if (problems && problems.length && !msg.value) {
      msg.value = form.dataset.prefill + '\n' + problems.map(function (p) { return '- ' + p; }).join('\n') + '\n\n';
    }
    if (/[?&]sent=1/.test(location.search)) { form.hidden = true; success.hidden = false; }
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      errorEl.hidden = true;
      if (!form.reportValidity()) return;
      var label = submit.innerHTML;
      submit.disabled = true;
      submit.textContent = form.dataset.sending;
      var data = {};
      new FormData(form).forEach(function (v, k) { data[k] = v; });
      fetch(form.action, { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' }, body: JSON.stringify(data) })
        .then(function (r) { return r.json().then(function (j) { if (!r.ok || !j.success) throw new Error(j.message || 'failed'); }); })
        .then(function () {
          form.reset();
          store.del('k-problems');
          form.hidden = true;
          success.hidden = false;
          $('h2', success).focus();
        })
        .catch(function () { errorEl.hidden = false; })
        .then(function () { submit.disabled = false; submit.innerHTML = label; });
    });
    $('.k-success .k-btn', card).addEventListener('click', function () {
      success.hidden = true;
      form.hidden = false;
      if (history.replaceState) history.replaceState(null, '', location.pathname);
      $('input:not([type=hidden]):not(.k-hp)', form).focus();
    });
  }
})();
