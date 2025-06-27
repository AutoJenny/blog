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

function renderStructure(structure) {
    return `
        <div class="template-view">
            <div class="actions">
                <button class="btn btn-outline" onclick="goToTemplate(${structure.post.id})">Template</button>
                <button class="btn btn-secondary" onclick="goToPreview(${structure.post.id})">Preview</button>
            </div>
            
            <div class="intro">
                <h2>Introduction</h2>
                <p>${structure.intro || 'No introduction yet'}</p>
                <button class="btn btn-secondary" onclick="goToEdit(${structure.post.id}, 'Intro')">Edit</button>
            </div>
            
            <div class="sections">
                ${structure.sections.map((s, i) => `
                    <div class="section">
                        <h2>${s.section_heading || 'Section ' + (i+1)}</h2>
                        <p>${s.content || 'No content yet'}</p>
                        <button class="btn btn-secondary" onclick="goToEdit(${structure.post.id}, '${encodeURIComponent(s.section_heading || 'Section ' + (i+1))}')">Edit</button>
                    </div>
                `).join('')}
            </div>
            
            <div class="conclusion">
                <h2>Conclusion</h2>
                <p>${structure.conclusion || 'No conclusion yet'}</p>
                <button class="btn btn-secondary" onclick="goToEdit(${structure.post.id}, 'Conclusion')">Edit</button>
            </div>
            
            <div class="metadata">
                <h2>Metadata</h2>
                <p>${structure.metadata || 'No metadata yet'}</p>
                <button class="btn btn-secondary" onclick="goToEdit(${structure.post.id}, 'Metadata')">Edit</button>
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