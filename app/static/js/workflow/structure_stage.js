// app/static/js/workflow/structure_stage.js

// Example static data (replace with real data fetch later)
let sections = [
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

async function planSectionsLLM(inputs) {
  const resp = await fetch('/api/v1/structure/plan', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(inputs)
  });
  if (!resp.ok) throw new Error('Failed to plan sections');
  return await resp.json();
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

  // Wire up Plan Sections (LLM) button
  const planBtn = document.querySelector('.btn-primary');
  if (planBtn) {
    planBtn.addEventListener('click', async () => {
      planBtn.disabled = true;
      planBtn.textContent = 'Planning...';
      try {
        // Get input values
        const title = document.querySelector('input[type="text"]')?.value || '';
        const idea = document.querySelectorAll('textarea')[0]?.value || '';
        const facts = document.querySelectorAll('textarea')[1]?.value.split('\n').map(f => f.trim()).filter(f => f) || [];
        const inputs = { title, idea, facts };
        const result = await planSectionsLLM(inputs);
        // Expect result.sections as array
        if (Array.isArray(result.sections)) {
          sections = result.sections;
          renderSections(list, sections);
        } else {
          alert('LLM did not return a valid section plan.');
        }
      } catch (e) {
        alert('Error planning sections: ' + e.message);
      } finally {
        planBtn.disabled = false;
        planBtn.textContent = 'Plan Sections (LLM)';
      }
    });
  }
}); 