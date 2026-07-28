const menuButton = document.getElementById('menuButton');
const mobileMenu = document.getElementById('mobileMenu');
const themeToggle = document.getElementById('themeToggle');
const copyEmailButton = document.getElementById('copyEmail');
const yearElement = document.getElementById('year');
const tabButtons = Array.from(document.querySelectorAll('.tab-btn'));
const tabPanels = Array.from(document.querySelectorAll('.tab-panel'));

if (yearElement) {
  yearElement.textContent = new Date().getFullYear();
}

if (menuButton && mobileMenu) {
  menuButton.addEventListener('click', () => {
    mobileMenu.classList.toggle('hidden');
  });
}

const applyTheme = (theme) => {
  document.documentElement.classList.toggle('dark', theme === 'dark');
  document.body.classList.toggle('bg-slate-950', theme === 'dark');
  document.body.classList.toggle('bg-slate-50', theme === 'light');
  document.body.classList.toggle('text-slate-100', theme === 'dark');
  document.body.classList.toggle('text-slate-900', theme === 'light');
};

const savedTheme = localStorage.getItem('cv-theme');
const initialTheme = savedTheme || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
applyTheme(initialTheme);

if (themeToggle) {
  themeToggle.addEventListener('click', () => {
    const nextTheme = document.documentElement.classList.contains('dark') ? 'light' : 'dark';
    localStorage.setItem('cv-theme', nextTheme);
    applyTheme(nextTheme);
  });
}

if (copyEmailButton) {
  copyEmailButton.addEventListener('click', async () => {
    const email = 'gareth.thomas@example.com';
    try {
      await navigator.clipboard.writeText(email);
      copyEmailButton.textContent = 'Copied!';
      setTimeout(() => {
        copyEmailButton.textContent = 'Copy email';
      }, 1500);
    } catch (error) {
      copyEmailButton.textContent = 'Copy failed';
      setTimeout(() => {
        copyEmailButton.textContent = 'Copy email';
      }, 1500);
    }
  });
}

if (tabButtons.length && tabPanels.length) {
  const switchTab = (targetId) => {
    tabButtons.forEach((button) => {
      const isActive = button.dataset.target === targetId;
      button.classList.toggle('bg-brand-600', isActive);
      button.classList.toggle('text-white', isActive);
      button.classList.toggle('bg-white/5', !isActive);
      button.classList.toggle('text-slate-200', !isActive);
      button.setAttribute('aria-selected', String(isActive));
    });

    tabPanels.forEach((panel) => {
      panel.classList.toggle('hidden', panel.id !== targetId);
    });
  };

  tabButtons.forEach((button) => {
    button.addEventListener('click', () => switchTab(button.dataset.target));
  });

  switchTab('professional');
}
