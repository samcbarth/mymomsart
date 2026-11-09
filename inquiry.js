// Inquiry form: posts to the "Basil Inquiry" HubSpot form (portal 20693956).
// Any <form class="inquiry-form"> on the page is wired up; data-inquiry-type and
// data-artwork prefill the HubSpot fields so Lisa sees what the visitor came for.
(function () {
  var PORTAL = '20693956';
  var FORM = '7032fed2-210a-4173-a316-453668c8e322';
  var UTM = ['utm_source', 'utm_medium', 'utm_campaign'];

  function store(get, key, val) {
    try { return get ? sessionStorage.getItem(key) : sessionStorage.setItem(key, val); } catch (e) { return null; }
  }

  // Keep first-touch UTMs for the session so they survive navigation to a painting page.
  var params = new URLSearchParams(window.location.search);
  UTM.forEach(function (k) {
    var v = params.get(k);
    if (v) store(false, 'basil_' + k, v);
  });

  function cookie(name) {
    var m = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
    return m ? decodeURIComponent(m[1]) : '';
  }

  function field(name, value) {
    return { objectTypeId: '0-1', name: name, value: value };
  }

  function wire(form) {
    var note = form.querySelector('.iq-note');
    var type = form.getAttribute('data-inquiry-type');
    if (type && form.elements.type) form.elements.type.value = type;

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (form.elements.website && form.elements.website.value) return; // honeypot
      if (!form.checkValidity()) { form.reportValidity(); return; }

      var f = form.elements;
      var parts = f.name.value.trim().split(/\s+/);
      var first = parts.shift();
      var last = parts.join(' ');
      var fields = [
        field('firstname', first),
        field('email', f.email.value.trim()),
        field('basil_inquiry_type', f.type.value),
        field('basil_artwork_interest', form.getAttribute('data-artwork') || '')
      ];
      if (last) fields.push(field('lastname', last));
      if (f.phone.value.trim()) fields.push(field('phone', f.phone.value.trim()));
      if (f.budget.value) fields.push(field('basil_budget_range', f.budget.value));
      if (f.timeline.value.trim()) fields.push(field('basil_timeline', f.timeline.value.trim()));
      if (f.location.value.trim()) fields.push(field('basil_location', f.location.value.trim()));
      if (f.details.value.trim()) fields.push(field('basil_project_details', f.details.value.trim()));
      UTM.forEach(function (k) {
        var v = store(true, 'basil_' + k);
        if (v) fields.push(field('basil_' + k, v));
      });

      var btn = form.querySelector('button[type=submit]');
      btn.disabled = true;
      note.textContent = 'Sending...';

      var ctx = { pageUri: window.location.href, pageName: document.title };
      var hutk = cookie('hubspotutk');
      if (hutk) ctx.hutk = hutk;

      fetch('https://api.hsforms.com/submissions/v3/integration/submit/' + PORTAL + '/' + FORM, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fields: fields, context: ctx })
      }).then(function (res) {
        if (!res.ok) throw new Error(res.status);
        form.reset();
        if (type && f.type) f.type.value = type;
        note.textContent = 'Thank you. Lisa will reply to you by email.';
        if (window._hsq) window._hsq.push(['trackCustomBehavioralEvent', { name: 'basil_inquiry_submitted' }]);
      }).catch(function () {
        note.textContent = 'That did not go through. Please email pljbarth@gmail.com instead.';
      }).then(function () { btn.disabled = false; });
    });
  }

  document.querySelectorAll('.inquiry-form').forEach(wire);
})();
