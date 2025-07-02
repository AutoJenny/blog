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

function renderSectionFields(section) {
    // Render all fields, pretty-printing objects/JSON
    return Object.entries(section).map(([key, value]) => {
        let displayValue;
        if (value === null || value === undefined || value === '') {
            displayValue = '<span style="color:#888">(empty)</span>';
        } else if (typeof value === 'object') {
            displayValue = `<pre style="background:#1a232a;color:#b9e0ff;padding:0.5em 1em;border-radius:0.3em;overflow-x:auto;">${JSON.stringify(value, null, 2)}</pre>`;
        } else {
            displayValue = `<span style="color:#e0e6ed;">${value}</span>`;
        }
        return `<div style="margin-bottom:0.5em;"><span style="font-weight:bold;color:#7dd3fc;">${key.replace(/_/g, ' ')}:</span> ${displayValue}</div>`;
    }).join('');
}

function renderStructure(structure) {
    // Generate a unique ID for each accordion to avoid conflicts
    function sectionId(i) { return `section-accordion-${i}`; }
    // Add container ID for drag-and-drop
    const containerId = 'sections-sortable-container';
    return `
        <div id="${containerId}" class="sections" style="display:flex;flex-direction:column;gap:2rem;">
            ${structure.sections.map((s, i) => {
                const number = (typeof s.orderIndex === 'number' ? s.orderIndex : i) + 1;
                const heading = s.title || '(No heading)';
                const desc = s.description || '';
                const accId = sectionId(i);
                return `
                    <div class="section" data-section-id="${s.id}" style="background:#14342b;border-radius:1rem;box-shadow:0 2px 12px #0004;">
                        <div style="display:flex;align-items:center;cursor:pointer;padding:1.5rem 2rem;" onclick="const c=document.getElementById('${accId}');c.style.display=c.style.display==='none'?'block':'none';">
                            <span class="section-drag-handle" style="cursor:grab;margin-right:1rem;color:#b9e0ff;font-size:1.5rem;user-select:none;">&#x2630;</span>
                            <h2 style="color:#7dd3fc;font-size:1.5rem;font-weight:bold;flex:1;">${number}. ${heading}</h2>
                            <span style="color:#b9e0ff;font-size:1.5rem;user-select:none;">&#x25BC;</span>
                        </div>
                        <div style="padding:0 2rem 1.5rem 2rem;" onclick="event.stopPropagation();">
                            <div style="color:#b9e0ff;font-size:1.1rem;margin-bottom:0.5rem;">${desc}</div>
                        </div>
                        <div id="${accId}" style="display:none;padding:0 2rem 2rem 2rem;">
                            ${renderSectionFields(s)}
                            <button class="btn btn-secondary" style="margin-top:1rem;" onclick="goToEdit(${structure.post.id}, '${encodeURIComponent(heading)}')">Edit</button>
                        </div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

export default {
    renderStructure,
    goToTemplate,
    goToPreview,
    goToEdit
}; 