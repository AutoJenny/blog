(function(){
  const postId = window.postId;
  async function fetchJSON(url, opts){
    const res = await fetch(url, Object.assign({ headers: { 'Content-Type': 'application/json' }}, opts||{}));
    if(!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  }

  async function renderPreview(sectionId, modelKey){
    const payload = { post_id: postId, section_id: sectionId, model_key: modelKey };
    const data = await fetchJSON(`/authoring/api/render-prompt-preview`, { method: 'POST', body: JSON.stringify(payload) });
    document.dispatchEvent(new CustomEvent('authoring:prompt:preview', { detail: data }));
    return data;
  }

  window.PromptPreview = { renderPreview };
})();


