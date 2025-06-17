// Minimal JS for standalone sections panel
let sections = [];

function fetchSections() {
    fetch('/api/sections/')
        .then(r => r.json())
        .then(data => {
            sections = data;
            renderSections();
        });
}

function renderSections() {
    const list = document.getElementById('sections-list');
    list.innerHTML = '';
    sections.forEach(section => {
        const card = document.createElement('div');
        card.className = 'section-card';
        card.setAttribute('draggable', 'true');
        card.setAttribute('data-id', section.id);
        card.innerHTML = `
            <div class="section-header">${section.section_heading}</div>
            <div class="section-desc">${section.section_description}</div>
            <div class="section-ideas"><em>${section.ideas_to_include}</em></div>
            <div class="section-actions">
                <button onclick="editSection(${section.id})">Edit</button>
                <button onclick="deleteSection(${section.id})">Delete</button>
            </div>
        `;
        // Drag events
        card.addEventListener('dragstart', dragStart);
        card.addEventListener('dragover', dragOver);
        card.addEventListener('drop', drop);
        card.addEventListener('dragend', dragEnd);
        list.appendChild(card);
    });
}

let dragSrcEl = null;
function dragStart(e) {
    dragSrcEl = this;
    this.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
}
function dragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
}
function drop(e) {
    e.stopPropagation();
    if (dragSrcEl !== this) {
        const list = this.parentNode;
        list.insertBefore(dragSrcEl, this);
        // Update order in sections array
        const ids = Array.from(list.children).map(card => parseInt(card.getAttribute('data-id')));
        sections.sort((a, b) => ids.indexOf(a.id) - ids.indexOf(b.id));
        saveSections();
    }
    return false;
}
function dragEnd() {
    this.classList.remove('dragging');
}

function addSection() {
    const newId = Math.max(0, ...sections.map(s => s.id)) + 1;
    sections.push({
        id: newId,
        post_id: 22,
        section_heading: 'New Section',
        section_description: '',
        ideas_to_include: '',
        status: 'draft',
        section_order: sections.length + 1
    });
    saveSections();
}

function editSection(id) {
    const section = sections.find(s => s.id === id);
    if (!section) return;
    document.getElementById('edit-id').value = section.id;
    document.getElementById('edit-heading').value = section.section_heading;
    document.getElementById('edit-desc').value = section.section_description;
    document.getElementById('edit-ideas').value = section.ideas_to_include;
    document.getElementById('edit-modal').style.display = 'block';
}

function saveEdit() {
    const id = parseInt(document.getElementById('edit-id').value);
    const section = sections.find(s => s.id === id);
    if (!section) return;
    section.section_heading = document.getElementById('edit-heading').value;
    section.section_description = document.getElementById('edit-desc').value;
    section.ideas_to_include = document.getElementById('edit-ideas').value;
    document.getElementById('edit-modal').style.display = 'none';
    saveSections();
}

function closeEdit() {
    document.getElementById('edit-modal').style.display = 'none';
}

function deleteSection(id) {
    sections = sections.filter(s => s.id !== id);
    saveSections();
}

function saveSections() {
    // Re-number section_order
    sections.forEach((s, i) => s.section_order = i + 1);
    fetch('/api/sections/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sections })
    }).then(() => fetchSections());
}

document.addEventListener('DOMContentLoaded', fetchSections); 