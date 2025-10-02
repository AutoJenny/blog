import { getJSON } from './api.js';

export class SectionsPanel {
  constructor({ postId, onSelect }) {
    this.postId = postId;
    this.onSelect = onSelect;
    this.sections = [];
    this.selected = new Set();
    this.bindStaticControls();
    this.load();
  }

  async load() {
    const data = await getJSON(`/authoring/api/posts/${this.postId}/sections`);
    this.sections = data.success ? (data.sections || []) : [];
    this.render();
  }

  bindStaticControls() {
    const list = document.getElementById('sections-list');
    list?.addEventListener('click', (e) => {
      const row = e.target.closest('.section-item');
      if (row && e.target.type !== 'checkbox') this.select(row.dataset.sectionId);
    });

    document.querySelector('.section-filters')?.addEventListener('click', (e) => {
      const btn = e.target.closest('.filter-btn'); if (!btn) return;
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      this.applyFilter(btn.dataset.filter);
    });

    document.getElementById('select-all-btn')?.addEventListener('click', () => {
      this.selected = new Set(this.sections.map(s => String(s.id)));
      this.syncSelectionUI();
    });

    document.getElementById('batch-generate-btn')?.addEventListener('click', () => {
      const ids = Array.from(this.selected);
      const evt = new CustomEvent('sections:batch-generate', { detail: { ids }});
      window.dispatchEvent(evt);
    });
  }

  render() {
    const list = document.getElementById('sections-list');
    if (!list) return;
    list.innerHTML = '';
    if (this.sections.length === 0) {
      list.innerHTML = '<div class="loading">No sections found</div>';
      return;
    }
    this.sections.forEach(s => {
      const div = document.createElement('div');
      div.className = 'section-item';
      div.dataset.sectionId = s.id;
      div.dataset.status = s.status || 'draft';
      div.innerHTML = `
        <div class="section-header">
          <input type="checkbox" class="section-checkbox" data-section-id="${s.id}">
          <span class="section-number">${s.order}</span>
          <span class="section-title">${s.title}</span>
          <span class="section-status ${s.status || 'draft'}">${(s.status || 'draft').replace(/^./, c=>c.toUpperCase())}</span>
        </div>
        ${s.subtitle ? `<div class="section-subtitle">${s.subtitle}</div>` : ''}
        <div class="section-topics">${(s.topics||[]).map(t=>`<span class="topic-tag">${t}</span>`).join('')}</div>
        <div class="section-progress">
          <div class="progress-bar"><div class="progress-fill" style="width:${s.progress||0}%"></div></div>
          <span class="progress-text">${s.progress||0}% complete</span>
        </div>`;
      list.appendChild(div);
    });
    this.syncSelectionUI();
  }

  select(id) {
    this.selected = new Set([String(id)]);
    this.syncSelectionUI();
    const s = this.sections.find(x => String(x.id) === String(id));
    this.onSelect?.(s);
  }

  syncSelectionUI() {
    document.querySelectorAll('.section-item').forEach(el => {
      const id = el.dataset.sectionId;
      el.classList.toggle('selected', this.selected.has(id));
      const cb = el.querySelector('.section-checkbox');
      if (cb) cb.checked = this.selected.has(id);
      cb?.addEventListener('change', () => {
        if (cb.checked) this.selected.add(id); else this.selected.delete(id);
      });
    });
  }

  applyFilter(kind) {
    document.querySelectorAll('.section-item').forEach(el => {
      const status = el.dataset.status || 'draft';
      el.style.display = (kind === 'all' || status === kind) ? '' : 'none';
    });
  }
}