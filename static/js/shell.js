(() => {
  const sidebar = document.getElementById('sidebar');
  const toggle = document.getElementById('sidebar-toggle');
  const close = document.getElementById('sidebar-close');
  const backdrop = document.getElementById('sidebar-backdrop');
  if (!sidebar || !toggle || !backdrop) return;

  const mobile = () => window.matchMedia('(max-width: 760px)').matches;
  if (!mobile() && localStorage.getItem('studyquest-sidebar') === 'closed') {
    document.body.classList.add('sidebar-collapsed');
  }
  const sync = () => {
    const open = mobile() ? sidebar.classList.contains('open') : !document.body.classList.contains('sidebar-collapsed');
    sidebar.inert = !open;
    sidebar.setAttribute('aria-hidden', String(!open));
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
  };
  const closeMenu = () => {
    if (mobile()) {
      sidebar.classList.remove('open');
      backdrop.classList.remove('visible');
      document.body.classList.remove('navigation-open');
    } else {
      document.body.classList.add('sidebar-collapsed');
      localStorage.setItem('studyquest-sidebar', 'closed');
    }
    sync();
  };
  const openMenu = () => {
    if (mobile()) {
      sidebar.classList.add('open');
      backdrop.classList.add('visible');
      document.body.classList.add('navigation-open');
    } else {
      document.body.classList.remove('sidebar-collapsed');
      localStorage.setItem('studyquest-sidebar', 'open');
    }
    sync();
  };

  toggle.addEventListener('click', () => {
    const open = mobile() ? sidebar.classList.contains('open') : !document.body.classList.contains('sidebar-collapsed');
    open ? closeMenu() : openMenu();
  });
  close?.addEventListener('click', closeMenu);
  backdrop.addEventListener('click', closeMenu);
  sidebar.querySelectorAll('a').forEach(link => link.addEventListener('click', () => { if (mobile()) closeMenu(); }));
  document.addEventListener('keydown', event => { if (event.key === 'Escape') closeMenu(); });
  window.addEventListener('resize', () => { if (!mobile()) { sidebar.classList.remove('open'); backdrop.classList.remove('visible'); document.body.classList.remove('navigation-open'); } sync(); });
  sync();
})();
