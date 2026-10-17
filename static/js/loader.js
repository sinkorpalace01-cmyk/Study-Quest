(() => {
  const overlay = document.getElementById('quest-loader');
  if (!overlay) return;
  const message = overlay.querySelector('[data-loader-message]');
  const captions = [
    'Gathering your next learning moment…',
    'Collecting bright ideas…',
    'Your next achievement is in sight…'
  ];
  let captionIndex = 0;
  let ticker;
  let fallback;
  const hide = () => {
    overlay.classList.add('is-hidden');
    window.clearInterval(ticker);
    window.clearTimeout(fallback);
    ticker = undefined;
  };
  const show = () => {
    overlay.classList.remove('is-hidden');
    captionIndex = 0;
    if (message) message.textContent = captions[0];
    window.clearInterval(ticker);
    ticker = window.setInterval(() => {
      captionIndex = (captionIndex + 1) % captions.length;
      if (message) message.textContent = captions[captionIndex];
    }, 1000);
    window.clearTimeout(fallback);
    fallback = window.setTimeout(hide, 8000);
  };
  show();
  if (document.readyState === 'complete') hide();
  else window.addEventListener('load', hide, {once: true});
  window.addEventListener('pageshow', hide);
  document.addEventListener('click', event => {
    const link = event.target.closest('a[href]');
    if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || link.target === '_blank' || link.hasAttribute('download')) return;
    const url = new URL(link.href, location.href);
    if (url.origin !== location.origin || (url.pathname === location.pathname && url.search === location.search && url.hash)) return;
    window.setTimeout(() => { if (!event.defaultPrevented) show(); }, 0);
  });
  document.addEventListener('submit', event => {
    window.setTimeout(() => { if (!event.defaultPrevented) show(); }, 0);
  });
})();
