// Modular LLM Workflow logic for Input, Actions, Output, and Post Development Fields panels
// This script is designed to be reusable for all workflow stages

(async function() {
  // Utility: fetch field mappings from /api/settings/field-mapping
  async function fetchFieldMappings() {
    const resp = await fetch('/api/settings/field-mapping');
    return resp.ok ? await resp.json() : [];
  }

  // Utility: group fields by stage/substage
  function groupFieldsByStage(mappings) {
    const grouped = {};
    for (const m of mappings) {
      if (!grouped[m.stage_name]) grouped[m.stage_name] = {};
      if (!grouped[m.stage_name][m.substage_name]) grouped[m.stage_name][m.substage_name] = [];
      grouped[m.stage_name][m.substage_name].push(m.field_name);
    }
    return grouped;
  }

  // Utility: fetch post_development for a post
  async function fetchPostDevelopment(postId) {
    const resp = await fetch(`/api/v1/post_development/${postId}`);
    return resp.ok ? await resp.json() : {};
  }

  // Utility: update a post_development field
  async function updatePostDevelopmentField(postId, field, value) {
    const resp = await fetch(`/api/v1/post_development/${postId}/update_field`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ field, value })
    });
    return resp.ok ? await resp.json() : { status: 'error' };
  }

  // Utility: fetch LLM actions
  async function fetchLLMActions() {
    const resp = await fetch('/api/v1/llm/actions');
    return resp.ok ? await resp.json() : [];
  }

  // Utility: fetch LLM action details
  async function fetchLLMActionDetails(actionId) {
    const resp = await fetch(`/api/v1/llm/actions/${actionId}`);
    return resp.ok ? await resp.json() : {};
  }

  // Utility: run LLM action
  async function runLLMAction(actionId, input) {
    const resp = await fetch(`/api/v1/llm/actions/${actionId}/test`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input })
    });
    return resp.ok ? await resp.json() : { error: 'Failed to run action' };
  }

  // Get postId from URL
  const urlParams = new URLSearchParams(window.location.search);
  const postId = urlParams.get('post_id');
  if (!postId) return;

  // DOM elements
  const inputFieldSelect = document.getElementById('inputFieldSelect');
  const inputFieldValue = document.getElementById('inputFieldValue');
  const actionSelect = document.getElementById('actionSelect');
  const actionPromptPanel = document.getElementById('actionPromptPanel');
  const runActionBtn = document.getElementById('runActionBtn');
  const outputFieldSelect = document.getElementById('outputFieldSelect');
  const outputFieldValue = document.getElementById('outputFieldValue');
  const actionOutputPanel = document.getElementById('actionOutputPanel');
  const saveOutputBtn = document.getElementById('saveOutputBtn');
  const postDevFieldsPanel = document.getElementById('postDevFieldsPanel');

  // State
  let fieldMappings = [];
  let groupedFields = {};
  let postDev = {};
  let llmActions = [];
  let actionDetails = {};
  let lastActionOutput = '';

  // Fetch all data
  async function init() {
    fieldMappings = await fetchFieldMappings();
    groupedFields = groupFieldsByStage(fieldMappings);
    postDev = await fetchPostDevelopment(postId);
    llmActions = await fetchLLMActions();
    renderFieldDropdown(inputFieldSelect, groupedFields);
    renderFieldDropdown(outputFieldSelect, groupedFields);
    renderActionDropdown(actionSelect, llmActions);
    renderPostDevFields(postDevFieldsPanel, fieldMappings, postDev);
  }

  // Render dropdown for fields
  function renderFieldDropdown(select, grouped) {
    select.innerHTML = '';
    for (const stage in grouped) {
      const stageOptGroup = document.createElement('optgroup');
      stageOptGroup.label = stage;
      for (const substage in grouped[stage]) {
        const substageOptGroup = document.createElement('optgroup');
        substageOptGroup.label = `  ${substage}`;
        for (const field of grouped[stage][substage]) {
          const opt = document.createElement('option');
          opt.value = field;
          opt.textContent = field.replace(/_/g, ' ');
          substageOptGroup.appendChild(opt);
        }
        stageOptGroup.appendChild(substageOptGroup);
      }
      select.appendChild(stageOptGroup);
    }
  }

  // Render action dropdown
  function renderActionDropdown(select, actions) {
    select.innerHTML = '<option value="">Select Action...</option>';
    for (const action of actions) {
      const opt = document.createElement('option');
      opt.value = action.id;
      opt.textContent = action.field_name;
      select.appendChild(opt);
    }
  }

  // Render post development fields table
  function renderPostDevFields(panel, mappings, postDev) {
    // Only show fields mapped to this substage (e.g., idea)
    const substageId = 1; // For Idea stage; make dynamic for other stages
    const fields = mappings.filter(m => m.substage_id == substageId).map(m => m.field_name);
    let html = '<table class="min-w-full bg-dark-card border border-gray-700 rounded-lg text-sm"><thead><tr>';
    for (const field of fields) {
      html += `<th class="px-3 py-2">${field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</th>`;
    }
    html += '</tr></thead><tbody><tr>';
    for (const field of fields) {
      html += `<td class="px-3 py-2">${postDev[field] || ''}</td>`;
    }
    html += '</tr></tbody></table>';
    panel.innerHTML = html;
  }

  // Field dropdown change handlers
  inputFieldSelect.addEventListener('change', () => {
    const field = inputFieldSelect.value;
    inputFieldValue.textContent = postDev[field] || '(No value)';
  });
  outputFieldSelect.addEventListener('change', () => {
    const field = outputFieldSelect.value;
    outputFieldValue.textContent = postDev[field] || '(No value)';
  });

  // Action dropdown change handler
  actionSelect.addEventListener('change', async () => {
    const actionId = actionSelect.value;
    if (!actionId) {
      actionPromptPanel.textContent = 'Select an action to view its prompt/template.';
      return;
    }
    actionDetails = await fetchLLMActionDetails(actionId);
    actionPromptPanel.textContent = actionDetails.prompt_template || '(No prompt template)';
  });

  // Run Action button handler
  runActionBtn.addEventListener('click', async () => {
    const actionId = actionSelect.value;
    const inputField = inputFieldSelect.value;
    if (!actionId || !inputField) {
      actionOutputPanel.textContent = 'Please select both an action and an input field.';
      return;
    }
    const inputValue = postDev[inputField] || '';
    actionOutputPanel.textContent = 'Running action...';
    const result = await runLLMAction(actionId, inputValue);
    if (result && result.result && result.result.output) {
      lastActionOutput = result.result.output;
      actionOutputPanel.textContent = lastActionOutput;
    } else if (result.response) {
      lastActionOutput = result.response;
      actionOutputPanel.textContent = lastActionOutput;
    } else {
      actionOutputPanel.textContent = result.error || 'No output.';
    }
  });

  // Save Output button handler
  saveOutputBtn.addEventListener('click', async () => {
    const outputField = outputFieldSelect.value;
    if (!outputField) {
      actionOutputPanel.textContent = 'Please select an output field.';
      return;
    }
    if (!lastActionOutput) {
      actionOutputPanel.textContent = 'No output to save.';
      return;
    }
    const resp = await updatePostDevelopmentField(postId, outputField, lastActionOutput);
    if (resp.status === 'success') {
      actionOutputPanel.textContent = 'Output saved!';
      // Refresh postDev and output panel
      postDev = await fetchPostDevelopment(postId);
      outputFieldValue.textContent = postDev[outputField] || '(No value)';
      renderPostDevFields(postDevFieldsPanel, fieldMappings, postDev);
    } else {
      actionOutputPanel.textContent = 'Failed to save output.';
    }
  });

  // Initial load
  await init();
})(); 