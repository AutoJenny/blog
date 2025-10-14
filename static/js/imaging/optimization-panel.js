// Optimization Panel JS
(function(){
  function onReady(fn){ if(document.readyState!=='loading'){ fn(); } else { document.addEventListener('DOMContentLoaded', fn); } }

  function getSelectedSections(){
    const checked = Array.from(document.querySelectorAll('.section-checkbox:checked'));
    return checked.map(cb => cb.dataset.sectionId);
  }

  async function optimizeSection(postId, sectionId, params){
    // Use existing optimize-one endpoint; extend later for params if needed
    const resp = await fetch(`/imaging/api/optimize/posts/${postId}/sections/${sectionId}/optimize-image`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(params||{}) });
    return await resp.json();
  }

  async function optimizeBatch(postId, sectionIds, params){
    const results = [];
    for (let i=0;i<sectionIds.length;i++){
      const id = sectionIds[i];
      try {
        const res = await optimizeSection(postId, id, params);
        results.push({ id, success: !!res.success, data: res });
        
        // Update output panel if this section is currently selected
        if (window.optimizedOutputPanel && window.optimizedOutputPanel.currentSectionId === id && res.success) {
          window.optimizedOutputPanel.onImageOptimized(res.optimized_path);
        }
      } catch (e) {
        results.push({ id, success: false, error: String(e) });
      }
    }
    return results;
  }

  function collectParams(){
    return {
      preset: document.getElementById('opt-preset')?.value || 'blog',
      quality: Number(document.getElementById('opt-quality')?.value || 50),
      overlay_text: document.getElementById('opt-overlay-text')?.value || 'AI-generated image',
      text_position: document.getElementById('opt-text-position')?.value || 'bottom-left',
      text_size: Number(document.getElementById('opt-text-size')?.value || 16),
      watermark: !!document.getElementById('opt-watermark')?.checked,
      text_overlay: !!document.getElementById('opt-text-overlay')?.checked,
      watermark_size: document.getElementById('opt-watermark-size')?.value || 'auto',
      watermark_margin: Number(document.getElementById('opt-watermark-margin')?.value || 10),
      bg_opacity: Number(document.getElementById('opt-bg-opacity')?.value || 20)
    };
  }

  function setStatus(text){
    const el = document.getElementById('optimization-status');
    if (el) el.textContent = text;
  }

  const ACCORDION_STATE_KEY = 'imaging-optimization-accordion-state';

  window.toggleOptimizationAccordion = function(){
    const content = document.getElementById('optimization-accordion-content');
    const icon = document.getElementById('optimization-accordion-icon');
    if (!content || !icon) return;
    const open = (content.style.display === 'block');
    const nextOpen = !open;
    content.style.display = nextOpen ? 'block' : 'none';
    icon.className = nextOpen ? 'fas fa-chevron-down' : 'fas fa-chevron-up';
    try { localStorage.setItem(ACCORDION_STATE_KEY, nextOpen ? 'open' : 'closed'); } catch(_){}
  };

  onReady(function(){
    const postId = window.postId;
    const btnSel = document.getElementById('optimize-selected-btn');
    const btnAll = document.getElementById('optimize-all-btn');

    // Restore accordion state
    try {
      const st = localStorage.getItem(ACCORDION_STATE_KEY);
      const content = document.getElementById('optimization-accordion-content');
      const icon = document.getElementById('optimization-accordion-icon');
      if (content && icon) {
        if (st === 'open') {
          content.style.display = 'block';
          icon.className = 'fas fa-chevron-down';
        } else {
          content.style.display = 'none';
          icon.className = 'fas fa-chevron-up';
        }
      }
    } catch(_) {}

    // Range slider value display
    const bgOpacityRange = document.getElementById('opt-bg-opacity');
    const bgOpacityValue = document.getElementById('opt-bg-opacity-value');
    if (bgOpacityRange && bgOpacityValue) {
      bgOpacityRange.addEventListener('input', function() {
        bgOpacityValue.textContent = this.value + '%';
      });
    }

    btnSel?.addEventListener('click', async function(){
      const ids = getSelectedSections();
      if (ids.length === 0){ alert('Select one or more sections in the left panel.'); return; }
      const params = collectParams();
      setStatus('Optimizing selected...');
      const res = await optimizeBatch(postId, ids, params);
      setStatus('Ready');
      console.log('[Optimization] Selected results:', res);
    });

    btnAll?.addEventListener('click', async function(){
      // If we later want server-side optimize-all, call that; for now iterate locally for consistency
      const all = Array.from(document.querySelectorAll('.section-item')).map(el => el.dataset.sectionId);
      if (all.length === 0){ alert('No sections found.'); return; }
      const params = collectParams();
      setStatus('Optimizing all...');
      const res = await optimizeBatch(postId, all, params);
      setStatus('Ready');
      console.log('[Optimization] All results:', res);
    });
  });
})();


