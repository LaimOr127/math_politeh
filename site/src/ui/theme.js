import { PreferencesStore } from '../storage/ProgressStore.js';

export const preferences = new PreferencesStore(() => window.localStorage);
const systemTheme = window.matchMedia('(prefers-color-scheme: dark)');

/** @returns {string} Effective theme; updates the document and toggle labels. */
export function applyTheme() {
  const saved = preferences.load().theme;
  const theme = saved === 'system' ? (systemTheme.matches ? 'dark' : 'light') : saved;
  document.documentElement.dataset.theme = theme;
  for (const button of document.querySelectorAll('[data-action="theme"]')) {
    button.textContent = theme === 'dark' ? '☀ Светлая' : '☾ Тёмная';
    button.setAttribute('aria-label',theme === 'dark' ? 'Включить светлую тему' : 'Включить тёмную тему');
  }
  return theme;
}
document.addEventListener('click', event => {
  if (!event.target.closest('[data-action="theme"]')) return;
  preferences.setTheme(applyTheme() === 'dark' ? 'light' : 'dark');
  applyTheme();
});
systemTheme.addEventListener('change',applyTheme);
applyTheme();
