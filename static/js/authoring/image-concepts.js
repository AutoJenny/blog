import { SectionsPanel } from './sections-panel.js';
import { OutputPanel } from './output-panel.js';

function initTabs() {
  const tabButtons = document.querySelectorAll('.tab-btn');
  const tabPanels  = document.querySelectorAll('.tab-panel');
  tabButtons.forEach(btn => btn.addEventListener('click', () => {
    const t = btn.getAttribute('data-tab');
    tabButtons.forEach(b => b.classList.remove('active'));
    tabPanels.forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(`${t}-tab`)?.classList.add('active');
    localStorage.setItem('planning-active-tab', t);
  }));
  const saved = localStorage.getItem('planning-active-tab');
  if (saved) document.querySelector(`.tab-btn[data-tab="${saved}"]`)?.click();
}

document.addEventListener('DOMContentLoaded', () => {
  initTabs();

  const postId = window.postId;
  const output = new OutputPanel({ postId });

  new SectionsPanel({
    postId,
    onSelect: (section) => output.show(section)
  });
});
