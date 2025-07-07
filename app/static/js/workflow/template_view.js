import { navigateToWorkflow } from '../workflow_nav.js';

function goToTemplate(postId) {
    navigateToWorkflow(postId, 'template');
}

function goToPreview(postId) {
    navigateToWorkflow(postId, 'preview');
}

function goToEdit(postId, section) {
    navigateToWorkflow(postId, 'edit', null, section);
}

// Utility: pretty-print JSON or arrays
function prettyValue(value) {
    if (value === null || value === undefined || value === '') {
        return '<span style="color:#888">(empty)</span>';
    } else if (Array.isArray(value)) {
        if (value.length === 0) return '<span style="color:#888">(empty)</span>';
        return '<ul style="margin:0.5em 0 0 1.5em;">' + value.map(v => `<li>${v}</li>`).join('') + '</ul>';
    } else if (typeof value === 'object') {
        return `<pre style="background:#1a232a;color:#b9e0ff;padding:0.5em 1em;border-radius:0.3em;overflow-x:auto;">${JSON.stringify(value, null, 2)}</pre>`;
    } else {
        return `<span style="color:#e0e6ed;">${value}</span>`;
    }
}

// Group field definitions - showing actual database field names from post_section table
// API field names (key) map to database field names (label) for clarity
const GROUPS = [
    {
        name: 'Content',
        fields: [
            { key: 'title', label: 'section_heading (DB)' },
            { key: 'description', label: 'section_description (DB)' },
            { key: 'content', label: 'first_draft (DB)' },
            { key: 'facts_to_include', label: 'facts_to_include (DB)' },
            { key: 'ideas_to_include', label: 'ideas_to_include (DB)' },
            { key: 'highlighting', label: 'highlighting (DB)' },
            { key: 'uk_british', label: 'uk_british (DB)' },
        ]
    },
    {
        name: 'Image Generation',
        fields: [
            { key: 'image_concepts', label: 'image_concepts (DB)' },
            { key: 'image_prompts', label: 'image_prompts (DB)' },
            { key: 'generation', label: 'generation (DB)' },
            { key: 'optimization', label: 'optimization (DB)' },
            { key: 'watermarking', label: 'watermarking (DB)' },
        ]
    },
    {
        name: 'Images',
        fields: [
            { key: 'image_id', label: 'image_id (DB)' },
            { key: 'image_captions', label: 'image_captions (DB)' },
            { key: 'image_meta_descriptions', label: 'image_meta_descriptions (DB)' },
            { key: 'generated_image_url', label: 'generated_image_url (DB)' },
            { key: 'image_generation_metadata', label: 'image_generation_metadata (DB)' },
        ]
    },
    {
        name: 'System',
        fields: [
            { key: 'position', label: 'section_order (DB)' },
            { key: 'status', label: 'status (DB)' },
        ]
    }
];

// Helper to get nested field values (e.g., 'elements.facts')
function getField(section, key) {
    return key.split('.').reduce((obj, k) => (obj && obj[k] !== undefined ? obj[k] : undefined), section);
}

function renderSectionGroups(section, sectionIndex) {
    // Render all groups as headings with their fields, no internal accordions
    return `
      <div class="section-groups">
        ${GROUPS.map((group, gi) => {
            const fieldsHtml = group.fields.map(f => {
                const val = getField(section, f.key);
                const isEmpty = val === null || val === undefined || val === '' || (Array.isArray(val) && val.length === 0);
                const fieldStyle = isEmpty
                  ? 'margin-bottom:0.5em;border:2px solid #374151;background:#23272e;padding:0.5em 1em;border-radius:0.4em;opacity:0.6;'
                  : 'margin-bottom:0.5em;border:2px solid #4ade80;background:#1e293b;padding:0.5em 1em;border-radius:0.4em;';
                const labelStyle = isEmpty
                  ? 'color:#a3a3a3;font-weight:500;margin-right:0.5em;'
                  : 'color:#aaffaa;font-weight:500;margin-right:0.5em;';
                const valueStyle = isEmpty
                  ? 'color:#6b7280;font-style:italic;'
                  : 'color:#fff;';
                return `<div class="field" style="${fieldStyle}">
                  <span class="label" style="${labelStyle}">[FIELD] ${f.label}:</span> 
                  <span class="value" style="${valueStyle}">${prettyValue(val)}</span>
                </div>`;
            }).join('');
            return `
              <div class="group-block" style="margin-bottom:1.5em;">
                <div class="group-heading" style="color:#7dd3fc;font-size:1.2rem;font-weight:bold;margin-bottom:0.5em;">${group.name}</div>
                ${fieldsHtml}
              </div>
            `;
        }).join('')}
      </div>
    `;
}

function renderStructure(structure) {
    console.log('[DEBUG] renderStructure called with structure:', structure);
    function sectionId(i) { return `section-accordion-${i}`; }
    const containerId = 'sections-sortable-container';
    // Add Select All checkbox and selection count
    let selectAllHtml = `
        <div style="display:flex;align-items:center;gap:1em;margin-bottom:1.5em;">
            <input type="checkbox" id="select-all-sections" checked style="width:1.2em;height:1.2em;">
            <label for="select-all-sections" style="color:#7dd3fc;font-size:1.1rem;font-weight:bold;cursor:pointer;">Select All Sections</label>
            <span id="selected-section-count" style="color:#b9e0ff;font-size:1rem;margin-left:1em;">All selected</span>
        </div>
    `;
    return `
        ${selectAllHtml}
        <div id="${containerId}" class="sections" style="display:flex;flex-direction:column;gap:2rem;">
            ${structure.sections.map((s, i) => {
                const number = i + 1;
                const heading = s.title || '(No heading)';
                const desc = s.description || '';
                const accId = sectionId(i);
                return `
                    <div class="section" data-section-id="${s.id}" style="background:#14342b;border-radius:1rem;box-shadow:0 2px 12px #0004;">
                        <div style="display:flex;align-items:center;gap:1em;padding:1.2rem 2rem 0 2rem;">
                            <input type="checkbox" class="section-select-checkbox" data-section-id="${s.id}" checked style="width:1.2em;height:1.2em;">
                            <button class="section-accordion-trigger" type="button" aria-expanded="false" aria-controls="${accId}" style="display:flex;align-items:center;width:100%;background:none;border:none;cursor:pointer;padding:0;text-align:left;">
                                <span class="section-drag-handle" style="cursor:grab;margin-right:1rem;color:#b9e0ff;font-size:1.5rem;user-select:none;">&#x2630;</span>
                                <h2 style="color:#7dd3fc;font-size:1.5rem;font-weight:bold;flex:1;margin:0;">${number}. ${heading}</h2>
                                <span class="section-arrow" style="color:#b9e0ff;font-size:1.5rem;user-select:none;transition:transform 0.2s;">&#x25BC;</span>
                            </button>
                        </div>
                        <div style="padding:0 2rem 1.5rem 2rem;" onclick="event.stopPropagation();">
                            <div style="color:#b9e0ff;font-size:1.1rem;margin-bottom:0.5rem;">${desc}</div>
                        </div>
                        <div id="${accId}" style="display:none;padding:0 2rem 2rem 2rem;">
                            ${renderSectionGroups(s, i)}
                        </div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

// Call this after rendering to attach accordion event listeners
function initAccordions() {
    console.log('[DEBUG] initAccordions called');
    // Section accordions
    document.querySelectorAll('.section-accordion-trigger').forEach(btn => {
        btn.addEventListener('click', function() {
            const section = btn.closest('.section');
            const accId = btn.getAttribute('aria-controls');
            const content = document.getElementById(accId);
            const arrow = btn.querySelector('.section-arrow');
            const expanded = btn.getAttribute('aria-expanded') === 'true';
            btn.setAttribute('aria-expanded', !expanded);
            if (content) {
                content.style.display = expanded ? 'none' : 'block';
            }
            if (arrow) {
                arrow.innerHTML = expanded ? '&#x25BC;' : '&#x25B2;'; // ▼/▲
            }
        });
    });
    // No more group accordions
    const triggers = document.querySelectorAll('.accordion-trigger');
    console.log('[DEBUG] Found triggers:', triggers.length);
}

// UI-only: Section selection logic for checkboxes
function initSectionSelectionUI() {
    const selectAll = document.getElementById('select-all-sections');
    const checkboxes = Array.from(document.querySelectorAll('.section-select-checkbox'));
    const countSpan = document.getElementById('selected-section-count');
    function updateCount() {
        const selected = checkboxes.filter(cb => cb.checked).length;
        if (selected === checkboxes.length) {
            countSpan.textContent = 'All selected';
        } else if (selected === 0) {
            countSpan.textContent = 'None selected';
        } else {
            countSpan.textContent = `${selected} selected`;
        }
    }
    if (selectAll) {
        selectAll.addEventListener('change', function() {
            checkboxes.forEach(cb => { cb.checked = selectAll.checked; });
            updateCount();
        });
    }
    checkboxes.forEach(cb => {
        cb.addEventListener('change', function() {
            if (!cb.checked) selectAll.checked = false;
            else if (checkboxes.every(c => c.checked)) selectAll.checked = true;
            updateCount();
        });
    });
    updateCount();
}

export default {
    renderStructure,
    goToTemplate,
    goToPreview,
    goToEdit,
    initAccordions, // <-- Call this after rendering
    initSectionSelectionUI // <-- New: call after rendering for selection logic
}; 