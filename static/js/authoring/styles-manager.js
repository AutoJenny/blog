// Post-wide styles manager for authoring Image Prompts page
(function(){
  const postId = window.postId;
  async function fetchJSON(url, opts){
    const res = await fetch(url, Object.assign({ headers: { 'Content-Type': 'application/json' }}, opts||{}));
    if(!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  }

  async function loadStyles(){
    try {
      console.log('[Styles Manager] Loading styles for post:', postId);
      const data = await fetchJSON(`/authoring/api/posts/${postId}/styles`);
      console.log('[Styles Manager] Styles loaded:', data);
      window.authoringStyles = data;
      console.log('[Styles Manager] Dispatching authoring:styles:loaded event');
      document.dispatchEvent(new CustomEvent('authoring:styles:loaded', { detail: data }));
    } catch(err){ console.error('Failed to load styles', err); }
  }

  async function createStyle(name, style_json, activate=true){
    try {
      const data = await fetchJSON(`/authoring/api/posts/${postId}/styles`, {
        method: 'POST', body: JSON.stringify({ name, style_json, activate })
      });
      await loadStyles();
      return data;
    } catch(err){ console.error('Failed to create style', err); }
  }

  async function activateStyle(index){
    try {
      const data = await fetchJSON(`/authoring/api/posts/${postId}/styles/${index}/activate`, { method: 'POST' });
      await loadStyles();
      return data;
    } catch(err){ console.error('Failed to activate style', err); }
  }

  // Expose helpers
  window.AuthoringStyles = { loadStyles, createStyle, activateStyle };

  // Auto-load on page ready
  document.addEventListener('DOMContentLoaded', loadStyles);
})();


