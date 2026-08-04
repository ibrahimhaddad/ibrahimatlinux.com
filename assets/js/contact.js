/*
 * Contact form submission.
 *
 * WHAT THIS DOES
 *   Intercepts the submit, posts the form to Web3Forms in the background, and
 *   writes the result into the status line under the button. The visitor never
 *   leaves the page.
 *
 * WHAT HAPPENS IF THIS SCRIPT NEVER RUNS
 *   Nothing breaks. The <form> has a real action and a real method, and a
 *   hidden redirect field pointing at /contact/thanks/. With JavaScript off the
 *   browser does an ordinary POST and lands on the thank-you page. Slightly
 *   less pleasant, still works. Do not remove that hidden field.
 *
 * WHERE THE EMAIL ADDRESS IS
 *   Not here. Not in the HTML either. Web3Forms holds it against the access
 *   key, and the key is a random string that reveals nothing. Anyone reading
 *   the page source or watching the network tab sees the key and no address,
 *   which is the whole reason the form exists instead of a mailto: link.
 */
(function () {
  'use strict';

  var form = document.getElementById('contact-form');
  if (!form) return;

  var status = document.getElementById('form-status');
  var button = form.querySelector('button[type="submit"]');
  var label = button ? button.textContent : '';

  function say(state, message) {
    if (!status) return;
    status.setAttribute('data-state', state);
    status.textContent = message;
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();

    var data = new FormData(form);

    // Give the notification email a useful subject line rather than the
    // service's generic one, so the inbox is sortable at a glance.
    var reason = data.get('What this is about') || 'Website enquiry';
    var who = data.get('name') || 'someone';
    data.set('subject', reason + ' from ' + who + ' (ibrahimatlinux.com)');

    if (button) { button.disabled = true; button.textContent = 'Sending'; }
    say('sending', 'Sending your message.');

    fetch('https://api.web3forms.com/submit', {
      method: 'POST',
      body: data
    })
      .then(function (r) { return r.json(); })
      .then(function (result) {
        if (result.success) {
          form.reset();
          say('ok', 'Message sent. I read everything and usually reply within two business days.');
          if (button) button.textContent = 'Sent';
          return;
        }
        // The service answered but refused it. Almost always a bad or missing
        // access key, so point at the other routes rather than saying "error".
        say('error', 'That did not go through. Please reach me on LinkedIn instead.');
        if (button) { button.disabled = false; button.textContent = label; }
      })
      .catch(function () {
        say('error', 'That did not go through, which usually means a network problem. '
                   + 'Try again, or reach me on LinkedIn.');
        if (button) { button.disabled = false; button.textContent = label; }
      });
  });
})();
