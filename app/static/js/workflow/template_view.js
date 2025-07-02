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
    return `
        <div class="template-view" style="background:#0f2222;padding:2rem;min-height:100vh;">
            <div class="actions" style="margin-bottom:2rem;">
                <button class="btn btn-outline" onclick="goToTemplate(${structure.post.id})">Template</button>
                <button class="btn btn-secondary" onclick="goToPreview(${structure.post.id})">Preview</button>
            </div>
            <div class="sections" style="display:flex;flex-direction:column;gap:2rem;">
                ${structure.sections.map((s, i) => `
                    <div class="section" style="background:#14342b;border-radius:1rem;box-shadow:0 2px 12px #0004;padding:2rem 1.5rem;">
                        <h2 style="color:#7dd3fc;font-size:1.5rem;font-weight:bold;margin-bottom:1rem;">Section ${i + 1}: ${s.section_heading || '(No heading)'}</h2>
                        ${renderSectionFields(s)}
                        <button class="btn btn-secondary" style="margin-top:1rem;" onclick="goToEdit(${structure.post.id}, '${encodeURIComponent(s.section_heading || 'Section ' + (i+1))}')">Edit</button>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

export default {
    renderStructure,
    goToTemplate,
    goToPreview,
    goToEdit
}; 