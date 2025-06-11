// app/static/js/workflow/template_view.js

// Utility: get post_id from URL or data attribute
function getPostId() {
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.has('post_id')) return urlParams.get('post_id');
  // Try data attribute on root
  const root = document.getElementById('template-root');
  if (root && root.dataset.postId) return root.dataset.postId;
  return null;
}

// Fetch structure from API
async function fetchStructure(postId) {
  const resp = await fetch(`/api/v1/post/${postId}/structure`);
  if (!resp.ok) throw new Error('Failed to fetch article structure');
  return await resp.json();
}

// Status color map
const statusColor = {
  'complete': 'bg-green-100 text-green-800',
  'draft': 'bg-yellow-100 text-yellow-800',
  'needs work': 'bg-red-100 text-red-800',
  'in_progress': 'bg-yellow-100 text-yellow-800',
  '': 'bg-gray-200 text-gray-700',
  null: 'bg-gray-200 text-gray-700',
  undefined: 'bg-gray-200 text-gray-700',
};

// Render Template View
function renderTemplate(structure) {
  const root = document.getElementById('template-root');
  if (!root) return;
  // Header
  let html = `
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-4">
        <h1 class="text-2xl font-bold">${structure.post.title || '(Untitled Post)'}</h1>
        <span class="px-2 py-1 rounded ${statusColor[structure.post.status] || 'bg-gray-200 text-gray-700'} text-xs">${structure.post.status || 'Draft'}</span>
      </div>
      <div class="flex items-center gap-2">
        <button class="btn btn-outline" onclick="window.location.href='/workflow/template/?post_id=${structure.post.id}'">Template</button>
        <button class="btn btn-secondary" onclick="window.location.href='/workflow/preview/?post_id=${structure.post.id}'">Preview</button>
      </div>
    </div>
    <div class="mb-8">
      <!-- TODO: Render process indicator if needed -->
    </div>
    <div class="space-y-6">
  `;
  // Intro
  html += `
    <div class="panel bg-gray-50 dark:bg-gray-800 rounded-lg p-6 flex justify-between items-center">
      <div><strong>Intro:</strong> <span class="text-gray-800 dark:text-gray-200">${structure.intro.intro || '(No intro yet)'}</span></div>
      <div>
        <button class="btn btn-secondary" onclick="window.location.href='/workflow/edit/?section=Intro&post_id=${structure.post.id}'">Edit</button>
        <span class="ml-2 px-2 py-1 rounded ${statusColor[structure.status.intro]} text-xs">${structure.status.intro || 'Draft'}</span>
      </div>
    </div>
  `;
  // Sections
  for (let i = 0; i < structure.sections.length; i++) {
    const s = structure.sections[i];
    html += `
      <div class="panel bg-gray-50 dark:bg-gray-800 rounded-lg p-6 flex justify-between items-center">
        <div>
          <strong>Section ${i + 1}:</strong> <span class="font-semibold text-gray-800 dark:text-gray-200">${s.section_heading || '(No heading)'}</span> <span class="italic text-gray-500 dark:text-gray-400">${s.theme || ''}</span>
          <div class="text-gray-800 dark:text-gray-200 mt-1">${s.snippet || ''}</div>
        </div>
        <div>
          <button class="btn btn-secondary" onclick="window.location.href='/workflow/edit/?section=${encodeURIComponent(s.section_heading || 'Section ' + (i+1))}&post_id=${structure.post.id}'">Edit</button>
          <span class="ml-2 px-2 py-1 rounded ${statusColor[structure.status.sections[i]]} text-xs">${structure.status.sections[i] || 'Draft'}</span>
        </div>
      </div>
    `;
  }
  // Conclusion
  html += `
    <div class="panel bg-gray-50 dark:bg-gray-800 rounded-lg p-6 flex justify-between items-center">
      <div><strong>Conclusion:</strong> <span class="text-gray-800 dark:text-gray-200">${structure.conclusion.conclusion || '(No conclusion yet)'}</span></div>
      <div>
        <button class="btn btn-secondary" onclick="window.location.href='/workflow/edit/?section=Conclusion&post_id=${structure.post.id}'">Edit</button>
        <span class="ml-2 px-2 py-1 rounded ${statusColor[structure.status.conclusion]} text-xs">${structure.status.conclusion || 'Draft'}</span>
      </div>
    </div>
  `;
  // Metadata
  html += `
    <div class="panel bg-gray-50 dark:bg-gray-800 rounded-lg p-6 flex justify-between items-center">
      <div><strong>Metadata:</strong> <span class="text-gray-800 dark:text-gray-200">${Object.entries(structure.metadata).map(([k, v]) => `<span class='mr-2'><b>${k.replace(/_/g, ' ')}:</b> ${v || ''}</span>`).join(' ')}</span></div>
      <div>
        <button class="btn btn-secondary" onclick="window.location.href='/workflow/edit/?section=Metadata&post_id=${structure.post.id}'">Edit</button>
        <span class="ml-2 px-2 py-1 rounded ${statusColor[structure.status.metadata]} text-xs">${structure.status.metadata || 'Draft'}</span>
      </div>
    </div>
  `;
  // Controls
  html += `
    <div class="flex gap-2 mt-4">
      <button class="btn btn-success">Add Section</button>
      <button class="btn btn-outline">Reorder Sections</button>
    </div>
  `;
  html += '</div>';
  root.innerHTML = html;
}

// Main
(async function() {
  const postId = getPostId();
  const root = document.getElementById('template-root');
  if (!postId) {
    if (root) root.innerHTML = '<div class="text-red-600">No post_id specified.</div>';
    return;
  }
  try {
    const structure = await fetchStructure(postId);
    renderTemplate(structure);
  } catch (e) {
    if (root) root.innerHTML = `<div class='text-red-600'>Error loading article structure: ${e.message}</div>`;
  }
})(); 