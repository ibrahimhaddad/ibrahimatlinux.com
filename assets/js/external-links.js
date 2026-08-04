/*
 * Outbound links open in a new tab.
 *
 * WHY THIS EXISTS
 *   Every link that leaves ibrahimatlinux.com should open in a new tab, so a
 *   visitor reading a paper on LinkedIn or downloading a report still has this
 *   site sitting in the tab behind it. Losing the reader to a one-way click is
 *   the single easiest thing to get wrong on a site whose whole job is to keep
 *   someone reading.
 *
 * WHY IT IS SCRIPTED RATHER THAN WRITTEN INTO THE HTML
 *   Most of it *is* written into the HTML. tools/build.py already stamps
 *   target and rel onto every publication link flagged external in
 *   data/publications.json, and the header and footer links are marked up by
 *   hand. This script is the safety net for the cases that slip through: a
 *   link pasted into a page later, an entry in the JSON that was never flagged,
 *   anything added by someone who has not read the build script.
 *
 *   So if JavaScript is off, the important links still behave correctly. This
 *   only closes the gaps.
 *
 * WHAT COUNTS AS EXTERNAL
 *   A different hostname. Same-host PDFs are included too, deliberately: a PDF
 *   that replaces the page is functionally the same problem as an outbound
 *   link, because the reader has to press Back to return to the site.
 *
 * rel="noopener"
 *   Without it, the page being opened gets a handle on this one through
 *   window.opener and can navigate it somewhere else. Modern browsers imply
 *   noopener for target="_blank", but older ones do not, and it costs nothing.
 */
(function () {
  'use strict';

  var host = window.location.hostname;

  function isExternal(a) {
    // href="#thing", "mailto:", "tel:" and javascript: all report the current
    // host or an empty one. Only http(s) links can be external.
    if (a.protocol !== 'http:' && a.protocol !== 'https:') return false;
    return a.hostname !== host;
  }

  function isDocument(a) {
    return /\.(pdf|epub|zip)$/i.test(a.pathname);
  }

  document.querySelectorAll('a[href]').forEach(function (a) {
    var external = isExternal(a);
    if (!external && !isDocument(a)) return;

    a.setAttribute('target', '_blank');

    // Preserve any rel already on the element, such as rel="me" on the social
    // links, which is what tells other services these profiles are his.
    var rel = (a.getAttribute('rel') || '').split(/\s+/).filter(Boolean);
    ['noopener', 'noreferrer'].forEach(function (token) {
      if (rel.indexOf(token) === -1) rel.push(token);
    });
    a.setAttribute('rel', rel.join(' '));

    // Screen readers otherwise give no warning that the tab is about to change.
    if (!a.querySelector('.u-visually-hidden') && a.textContent.trim()) {
      var note = document.createElement('span');
      note.className = 'u-visually-hidden';
      note.textContent = ' (opens in a new tab)';
      a.appendChild(note);
    }

    // The arrow glyph, but only on links inside running text. Navigation,
    // footers, buttons and anything wrapping an image stay clean.
    if (external &&
        !a.closest('.nav, .site-footer, .logobar, .strip') &&
        !a.classList.contains('btn') &&
        !a.classList.contains('pub') &&
        !a.querySelector('img')) {
      a.classList.add('u-ext');
    }
  });
})();
