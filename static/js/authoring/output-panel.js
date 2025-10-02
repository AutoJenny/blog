import { postJSON, getJSON } from './api.js';

export class OutputPanel {
  constructor({ postId }) {
    this.postId = postId;
    this.current = null;
    this.cache = new Map();
    this.postData = null;
    this.bind();
    this.loadPostData();
  }

  async loadPostData() {
    try {
      const data = await getJSON(`/planning/api/posts/${this.postId}`);
      this.postData = data;
      this.updatePostContext();
    } catch (error) {
      console.error('Error loading post data:', error);
    }
  }

  updatePostContext() {
    if (!this.postData || !this.postData.post) return;
    
    const ideaSeedEl = document.getElementById('selected-idea-display');
    const expandedIdeaEl = document.getElementById('expanded-idea-display');
    
    if (ideaSeedEl) {
      ideaSeedEl.textContent = this.postData.post.idea_seed || '-';
    }
    
    if (expandedIdeaEl) {
      expandedIdeaEl.textContent = this.postData.post.expanded_idea || '-';
    }
  }

  bind() {
    const editor = document.getElementById('content-editor');
    editor?.addEventListener('input', () => this.updateWordCount());

    document.getElementById('save-btn')?.addEventListener('click', () => this.save());
    document.getElementById('regenerate-btn')?.addEventListener('click', () => this.regenerate());

    window.addEventListener('sections:batch-generate', async (e) => {
      const ids = e.detail?.ids || [];
      for (const id of ids) { await this.regenerate(id); }
    });
  }

  show(section) {
    this.current = section || null;
    if (!section) return;

    document.getElementById('current-section-title').textContent = section.title || 'Untitled';
    document.getElementById('section-title-display').textContent = section.title || '';
    document.getElementById('section-subtitle-display').textContent = section.subtitle || '';
    document.getElementById('section-topics-display').innerHTML = (section.topics||[]).map(t=>`<span class="topic-tag">${t}</span>`).join('');

    const editor = document.getElementById('content-editor');
    editor.disabled = false;
    document.getElementById('preview-btn').disabled = false;
    document.getElementById('save-btn').disabled = false;
    document.getElementById('regenerate-btn').disabled = false;

    editor.value = section.draft_content || '';
    this.updateWordCount();
  }

  updateWordCount() {
    const text = (document.getElementById('content-editor')?.value || '').trim();
    const n = text ? text.split(/\s+/).filter(Boolean).length : 0;
    const wc = document.getElementById('word-count');
    if (wc) wc.textContent = `${n} words`;
  }

  async save() {
    if (!this.current) return;
    const content = document.getElementById('content-editor').value;
    await postJSON(`/authoring/api/posts/${this.postId}/sections/${this.current.id}/save`, { draft_content: content });
    document.getElementById('last-saved').textContent = `Saved ${new Date().toLocaleTimeString()}`;
  }

  async regenerate(sectionId = null) {
    const id = sectionId || (this.current?.id);
    if (!id) return;
    const editor = document.getElementById('content-editor');
    editor.value = 'Regenerating content…';
    editor.disabled = true;

    try {
      const res = await postJSON(`/authoring/api/posts/${this.postId}/sections/${id}/regenerate`, {});
      editor.value = res.draft_content || '(no content)';
    } catch (err) {
      editor.value = 'Error generating content';
      console.error(err);
    } finally {
      editor.disabled = false;
      this.updateWordCount();
    }
  }
}
