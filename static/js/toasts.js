(() => {
  const stack = document.getElementById('feedback-stack');
  if (!stack) return;

  const labels = {
    success: ['Success', '✓'],
    error: ['Something went wrong', '!'],
    warning: ['Please note', '!'],
    info: ['Update', 'i'],
    debug: ['Update', 'i']
  };

  // Form-level errors use the same presentation as Django's message framework.
  document.querySelectorAll('.message').forEach(source => {
    const kind = Object.keys(labels).find(name => source.classList.contains(name)) || 'info';
    const [heading, icon] = labels[kind];
    const toast = document.createElement('div');
    toast.className = `feedback-toast ${kind}`;
    toast.dataset.feedbackToast = '';
    toast.setAttribute('role', kind === 'error' ? 'alert' : 'status');
    const mark = document.createElement('span');
    mark.className = 'feedback-icon';
    mark.setAttribute('aria-hidden', 'true');
    mark.textContent = icon;
    const copy = document.createElement('div');
    copy.className = 'feedback-copy';
    const title = document.createElement('strong');
    title.textContent = heading;
    const body = document.createElement('span');
    body.textContent = source.textContent.trim();
    copy.append(title, body);
    const close = document.createElement('button');
    close.className = 'feedback-close';
    close.type = 'button';
    close.dataset.feedbackClose = '';
    close.setAttribute('aria-label', 'Dismiss notification');
    close.textContent = '×';
    const progress = document.createElement('span');
    progress.className = 'feedback-progress';
    progress.setAttribute('aria-hidden', 'true');
    toast.append(mark, copy, close, progress);
    stack.append(toast);
    source.remove();
  });

  stack.querySelectorAll('[data-feedback-toast]').forEach(toast => {
    const duration = toast.classList.contains('error') || toast.classList.contains('warning') ? 12000 : 8000;
    toast.style.setProperty('--feedback-duration', `${duration}ms`);
    let remaining = duration;
    let started = 0;
    let timeout;
    let leaving = false;

    const dismiss = () => {
      if (leaving) return;
      leaving = true;
      clearTimeout(timeout);
      toast.classList.add('is-leaving');
      window.setTimeout(() => toast.remove(), 220);
    };
    const resume = () => {
      if (leaving || timeout || document.hidden || toast.matches(':hover') || toast.contains(document.activeElement)) return;
      started = performance.now();
      toast.classList.remove('is-paused');
      timeout = window.setTimeout(dismiss, remaining);
    };
    const pause = () => {
      if (!timeout) return;
      clearTimeout(timeout);
      timeout = undefined;
      remaining -= performance.now() - started;
      toast.classList.add('is-paused');
    };
    toast.querySelector('[data-feedback-close]').addEventListener('click', dismiss);
    toast.addEventListener('mouseenter', pause);
    toast.addEventListener('mouseleave', resume);
    toast.addEventListener('focusin', pause);
    toast.addEventListener('focusout', resume);
    document.addEventListener('visibilitychange', () => document.hidden ? pause() : resume());
    resume();
  });
})();
