/**
 * Phase H-4/H-5: Unified Channel Workbench — prompt inspector, editor, run history, comparison, regeneration.
 * H-5: engine selector, current-output selection, "Use this output", ✓ Current in History.
 * All API calls use content_ref, platform, channel_type from pageData (no platform-specific branching).
 */
(function() {
    const pd = window.pageData || {};
    const platform = (pd.platform && pd.platform.name) ? pd.platform.name : 'facebook';
    const channelType = (pd.channel_type && pd.channel_type.name) ? pd.channel_type.name : 'blog_post';
    const SLOT_PRIMARY = 'primary';

    let contentRef = null;
    let currentPrompt = null;
    let runs = [];
    let engines = [];
    let selectedRunId = null;
    let currentRunId = null;
    let comparisonRunIds = [null, null];

    function params() {
        return { content_ref: contentRef, platform, channel_type: channelType };
    }

    function showSurfaces(show) {
        const el = document.getElementById('workbench-surfaces');
        if (el) el.classList.toggle('d-none', !show);
    }

    function setInspector(text, isHistorical, isCurrentOutput) {
        const pre = document.getElementById('prompt-inspector-text');
        const label = document.getElementById('prompt-inspector-label');
        if (pre) pre.textContent = text || 'No prompt to display.';
        if (label) {
            if (isCurrentOutput) label.textContent = 'Prompt for current output';
            else if (isHistorical) label.textContent = 'Prompt used for this run';
            else label.textContent = 'Current prompt';
        }
    }

    async function loadEngines() {
        try {
            const r = await fetch('/launchpad/api/workbench/engines');
            const list = await r.json();
            engines = Array.isArray(list) ? list : [];
            const sel = document.getElementById('workbench-engine-select');
            if (sel) {
                sel.innerHTML = engines.length ? engines.map(eng => `<option value="${eng.engine_id || ''}">${eng.label || eng.engine_id}</option>`).join('') : '<option value="text/ollama-mistral">Default (Ollama Mistral)</option>';
            }
        } catch (e) { console.error('Workbench load engines:', e); }
    }

    async function loadCurrentOutput() {
        if (!contentRef) return;
        try {
            const q = new URLSearchParams({ ...params(), slot_identifier: SLOT_PRIMARY });
            const r = await fetch('/launchpad/api/workbench/current-output?' + q.toString());
            const data = await r.json();
            if (data.success && data.run_id) {
                currentRunId = data.run_id;
            } else {
                currentRunId = null;
            }
            renderHistory();
        } catch (e) { console.error('Workbench load current output:', e); }
    }

    async function setCurrentOutput(runId) {
        if (!contentRef || !runId) return;
        try {
            const r = await fetch('/launchpad/api/workbench/current-output', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ...params(), content_ref: contentRef, slot_identifier: SLOT_PRIMARY, run_id: runId })
            });
            const data = await r.json();
            if (data.success) {
                currentRunId = runId;
                renderHistory();
                loadComparisonOutputs();
            } else alert('Failed to set current output: ' + (data.error || 'Unknown'));
        } catch (e) { alert('Error: ' + e.message); }
    }

    async function loadCurrentPrompt() {
        if (!contentRef) return;
        try {
            const q = new URLSearchParams(params());
            const r = await fetch('/launchpad/api/workbench/prompt?' + q.toString());
            const data = await r.json();
            if (data.success) {
                currentPrompt = data.text_prompt || '';
                if (!selectedRunId) setInspector(currentPrompt || '(No current prompt set)', false, false);
                const ta = document.getElementById('prompt-editor-text');
                if (ta) ta.value = currentPrompt || '';
            }
        } catch (e) { console.error('Workbench load prompt:', e); }
    }

    async function loadRuns() {
        if (!contentRef) return;
        try {
            const q = new URLSearchParams(params());
            const r = await fetch('/launchpad/api/workbench/runs?' + q.toString());
            const data = await r.json();
            if (data.success) {
                runs = data.runs || [];
                renderHistory();
            }
        } catch (e) { console.error('Workbench load runs:', e); }
    }

    function engineLabel(engineId) {
        const eng = engines.find(e => (e.engine_id || '') === (engineId || ''));
        return (eng && eng.label) ? eng.label : (engineId || '-');
    }

    function renderHistory() {
        const list = document.getElementById('generation-history-list');
        if (!list) return;
        if (runs.length === 0) {
            list.innerHTML = '<div class="text-muted small">No runs yet. Use Run with engine to create one.</div>';
            return;
        }
        list.innerHTML = runs.map(r => {
            const ts = r.started_at ? new Date(r.started_at).toLocaleString() : '-';
            const sel = r.id === selectedRunId ? ' list-group-item-primary' : '';
            const currentMark = r.id === currentRunId ? ' ✓ Current' : '';
            return `<a href="#" class="list-group-item list-group-item-action list-group-item-dark${sel}" data-run-id="${r.id}" data-run-json="${encodeURIComponent(JSON.stringify(r))}">Run ${r.id} · ${engineLabel(r.engine_id)} · ${ts} · ${r.status || '-'} · ${r.trigger || '-'}${currentMark}</a>`;
        }).join('');
        list.querySelectorAll('[data-run-id]').forEach(el => {
            el.addEventListener('click', function(e) {
                e.preventDefault();
                const id = parseInt(this.getAttribute('data-run-id'), 10);
                const runJson = this.getAttribute('data-run-json');
                const run = runJson ? JSON.parse(decodeURIComponent(runJson)) : runs.find(rr => rr.id === id);
                selectedRunId = id;
                if (run && run.prompt_snapshot) {
                    const t = run.prompt_snapshot.text_prompt || '(no text prompt)';
                    setInspector(t, true, run.id === currentRunId);
                }
                renderHistory();
                updateComparisonSelection(id);
            });
        });
    }

    function updateComparisonSelection(runId) {
        if (comparisonRunIds[0] === null) comparisonRunIds[0] = runId;
        else if (comparisonRunIds[1] === null) comparisonRunIds[1] = runId;
        else { comparisonRunIds[0] = comparisonRunIds[1]; comparisonRunIds[1] = runId; }
        loadComparisonOutputs();
    }

    async function loadComparisonOutputs() {
        const left = document.getElementById('comparison-left');
        const right = document.getElementById('comparison-right');
        if (!left || !right) return;
        const ids = [comparisonRunIds[0], comparisonRunIds[1]];
        const runMap = {};
        runs.forEach(r => { runMap[r.id] = r; });

        function renderCard(runId, sideLabel) {
            if (!runId || !runMap[runId]) return `<div class="text-muted small">Select a run (${sideLabel})</div>`;
            const r = runMap[runId];
            const ts = r.started_at ? new Date(r.started_at).toLocaleString() : '-';
            const label = engineLabel(r.engine_id);
            const isCurrent = r.id === currentRunId;
            const contentPlaceholder = '(loading content…)';
            return `<div class="mb-2" data-run-id="${r.id}"><div class="small text-info mb-1">${label} · ${ts}${isCurrent ? ' · ✓ Current' : ''}</div><div class="comparison-content border rounded p-2 bg-dark small text-break mb-2" data-run-id="${r.id}">${contentPlaceholder}</div><button type="button" class="btn btn-sm btn-outline-primary workbench-use-output" data-run-id="${r.id}">Use this output</button></div>`;
        }

        left.innerHTML = renderCard(ids[0], 'left');
        right.innerHTML = renderCard(ids[1], 'right');

        const queueIds = ids.map(id => runMap[id] && runMap[id].output_refs && runMap[id].output_refs.posting_queue_id).filter(Boolean);
        if (queueIds.length === 0) {
            left.querySelectorAll('.comparison-content').forEach(el => { el.textContent = runMap[el.getAttribute('data-run-id')] ? '(no output ref)' : '(no run)'; });
            right.querySelectorAll('.comparison-content').forEach(el => { el.textContent = runMap[el.getAttribute('data-run-id')] ? '(no output ref)' : '(no run)'; });
        } else {
            try {
                const q = new URLSearchParams({ platform, channel_type: channelType });
                const r = await fetch('/launchpad/api/queue?' + q.toString());
                const data = await r.json();
                const items = (data.items || data.timeline || []).filter(item => queueIds.includes(item.id));
                const byId = {};
                items.forEach(item => { byId[item.id] = item.generated_content || '(no content)'; });
                [left, right].forEach(container => {
                    container.querySelectorAll('.comparison-content').forEach(el => {
                        const runId = parseInt(el.getAttribute('data-run-id'), 10);
                        const run = runMap[runId];
                        const qid = run && run.output_refs && run.output_refs.posting_queue_id;
                        el.textContent = qid != null ? (byId[qid] || '(no content)') : '(no output ref)';
                    });
                });
            } catch (e) {
                left.querySelectorAll('.comparison-content').forEach(el => { el.textContent = 'Error loading'; });
                right.querySelectorAll('.comparison-content').forEach(el => { el.textContent = 'Error loading'; });
            }
        }

        left.querySelectorAll('.workbench-use-output').forEach(btn => {
            btn.addEventListener('click', function() { setCurrentOutput(parseInt(this.getAttribute('data-run-id'), 10)); });
        });
        right.querySelectorAll('.workbench-use-output').forEach(btn => {
            btn.addEventListener('click', function() { setCurrentOutput(parseInt(this.getAttribute('data-run-id'), 10)); });
        });
    }

    document.addEventListener('postSelected', function(event) {
        const detail = event.detail || {};
        contentRef = detail.postId != null ? detail.postId : (detail.post && detail.post.id);
        if (!contentRef) {
            showSurfaces(false);
            return;
        }
        showSurfaces(true);
        selectedRunId = null;
        currentRunId = null;
        comparisonRunIds = [null, null];
        loadCurrentPrompt();
        loadRuns();
        loadCurrentOutput();
        setInspector('Loading…', false, false);
    });

    const saveBtn = document.getElementById('prompt-editor-save');
    if (saveBtn) {
        saveBtn.addEventListener('click', async function() {
            if (!contentRef) return;
            const ta = document.getElementById('prompt-editor-text');
            const text = ta ? ta.value : '';
            try {
                const r = await fetch('/launchpad/api/workbench/prompt', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ...params(), content_ref: contentRef, text_prompt: text })
                });
                const data = await r.json();
                if (data.success) {
                    currentPrompt = data.text_prompt || text;
                    if (!selectedRunId) setInspector(currentPrompt, false, false);
                } else alert('Failed to save prompt: ' + (data.error || 'Unknown'));
            } catch (e) { alert('Error: ' + e.message); }
        });
    }

    const regenBtn = document.getElementById('workbench-regenerate-btn');
    const regenStatus = document.getElementById('regeneration-status');
    if (regenBtn) {
        regenBtn.addEventListener('click', async function() {
            if (!contentRef) return;
            const engineSelect = document.getElementById('workbench-engine-select');
            const engineId = (engineSelect && engineSelect.value) ? engineSelect.value : 'text/ollama-mistral';
            regenBtn.disabled = true;
            if (regenStatus) regenStatus.textContent = 'Running…';
            try {
                const r = await fetch('/launchpad/api/workbench/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ...params(), content_ref: contentRef, engine_id: engineId, slot_identifier: SLOT_PRIMARY, trigger: 'user' })
                });
                const data = await r.json();
                if (regenStatus) regenStatus.textContent = data.success ? 'Run created.' : (data.error || 'Failed');
                if (data.success) {
                    loadRuns();
                    loadCurrentOutput();
                }
            } catch (e) {
                if (regenStatus) regenStatus.textContent = 'Error: ' + e.message;
            }
            regenBtn.disabled = false;
        });
    }

    loadEngines();
})();
