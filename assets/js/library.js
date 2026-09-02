/*
 * Library filtering.
 *
 * Everything is already in the page as real HTML, which is what search engines
 * and anyone with JavaScript disabled will see. This script only hides and
 * shows what is already there, so the page works fine without it.
 *
 * It reads ?type= and ?topic= from the address bar on load, and writes the
 * active filters back, so a filtered view can be bookmarked or shared.
 */
(function () {
  'use strict';

  var grid = document.getElementById('lib-grid');
  var rows = document.getElementById('lib-rows');
  if (!grid && !rows) return;

  var items   = document.querySelectorAll('#lib-grid .pub, #lib-rows .row');
  var count   = document.getElementById('count');
  var heading = document.getElementById('rows-heading');
  var empty   = document.getElementById('lib-empty');
  var search  = document.querySelector('.search');
  var state   = { type: 'all', topic: 'all', q: '' };

  function apply() {
    var shown = 0, gridShown = 0, rowsShown = 0;

    items.forEach(function (el) {
      // data-topic holds one or more topics, space separated, so an item can
      // sit under several filters at once.
      var okType  = state.type  === 'all' || el.dataset.type === state.type;
      var okTopic = state.topic === 'all' ||
                    (el.dataset.topic || '').split(' ').indexOf(state.topic) > -1;
      var okQuery = !state.q || el.textContent.toLowerCase().indexOf(state.q) > -1;
      var ok = okType && okTopic && okQuery;

      el.classList.toggle('is-hidden', !ok);
      if (ok) {
        shown++;
        if (el.classList.contains('pub')) { gridShown++; } else { rowsShown++; }
      }
    });

    if (count) {
      count.textContent = shown;
      count.parentNode.setAttribute('aria-live', 'polite');
    }

    // Never leave a heading sitting above nothing.
    if (grid)    grid.classList.toggle('is-hidden', gridShown === 0);
    if (heading) heading.classList.toggle('is-hidden', rowsShown === 0);
    if (rows)    rows.classList.toggle('is-hidden', rowsShown === 0);
    if (empty)   empty.classList.toggle('is-on', shown === 0);
  }

  function setChip(group, value) {
    var chip = document.querySelector(
      '.chip[data-filter="' + group + '"][data-value="' + value + '"]');
    if (!chip) return false;
    document.querySelectorAll('.chip[data-filter="' + group + '"]').forEach(function (c) {
      c.classList.remove('is-on');
      c.setAttribute('aria-pressed', 'false');
    });
    chip.classList.add('is-on');
    chip.setAttribute('aria-pressed', 'true');
    state[group] = value;
    return true;
  }

  function updateUrl() {
    if (!window.history || !window.history.replaceState) return;
    var p = new URLSearchParams();
    if (state.type  !== 'all') p.set('type',  state.type);
    if (state.topic !== 'all') p.set('topic', state.topic);
    var qs = p.toString();
    window.history.replaceState({}, '', window.location.pathname + (qs ? '?' + qs : ''));
  }

  document.querySelectorAll('.chip').forEach(function (chip) {
    chip.addEventListener('click', function () {
      setChip(chip.dataset.filter, chip.dataset.value);
      apply();
      updateUrl();
    });
  });

  if (search) {
    search.addEventListener('input', function () {
      state.q = search.value.toLowerCase().trim();
      apply();
    });
  }

  var params = new URLSearchParams(window.location.search);
  ['type', 'topic'].forEach(function (group) {
    var val = params.get(group);
    if (val) setChip(group, val);
  });

  apply();
})();
