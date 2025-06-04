// app/static/js/workflow/structure_stage.js

// Example static data (replace with real data fetch later)
const sections = [
  { id: 1, title: 'Introduction', ideas: ['Idea 1'], facts: ['Fact A'] },
  { id: 2, title: 'Background', ideas: ['Idea 2'], facts: ['Fact B'] },
  { id: 3, title: 'Main Argument', ideas: ['Idea 3'], facts: ['Fact C'] },
  { id: 4, title: 'Conclusion', ideas: ['Idea 4'], facts: ['Fact D'] },
];

function renderSections(list, sections) {
  list.innerHTML = '';
  sections.forEach((section, idx) => {
    const li = document.createElement('li');
    li.className = 'bg-gray-700 rounded p-4 flex items-center justify-between cursor-move';
    li.setAttribute('data-id', section.id);
    li.innerHTML = `
      <div>
        <span class="font-bold text-gray-100">${idx + 1}. ${section.title}</span>
        <span class="ml-4 text-xs text-gray-300">Ideas: ${section.ideas.join(', ')}</span>
        <span class="ml-4 text-xs text-gray-300">Facts: ${section.facts.join(', ')}</span>
      </div>
      <span class="text-gray-400">&#x2630;</span>
    `;
    list.appendChild(li);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  const list = document.getElementById('sections-list');
  if (!list) return;
  renderSections(list, sections);
  // Initialize SortableJS
  new window.Sortable(list, {
    animation: 150,
    handle: '.cursor-move',
    onEnd: function (evt) {
      // Update sections array to reflect new order
      const newOrder = Array.from(list.children).map(li => parseInt(li.getAttribute('data-id')));
      sections.sort((a, b) => newOrder.indexOf(a.id) - newOrder.indexOf(b.id));
      renderSections(list, sections); // Re-render to update indices
    }
  });
}); 