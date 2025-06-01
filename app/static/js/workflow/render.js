// UI rendering functions for workflow LLM modular UI

/**
 * Render the field dropdown.
 */
export function renderFieldDropdown(select, mappings, selected, substage) {
  select.innerHTML = '';
  // Group by stage and substage for optgroups
  let lastStage = null;
  let lastSubstage = null;
  let stageOptGroup = null;
  let allFieldNames = new Set();
  for (const m of mappings) {
    // New stage: create a new optgroup
    if (m.stage_name !== lastStage) {
      stageOptGroup = document.createElement('optgroup');
      stageOptGroup.label = m.stage_name;
      select.appendChild(stageOptGroup);
      lastStage = m.stage_name;
      lastSubstage = null;
    }
    // New substage: add a disabled label option
    if (m.substage_name !== lastSubstage) {
      const substageLabel = document.createElement('option');
      substageLabel.textContent = m.substage_name;
      substageLabel.disabled = true;
      stageOptGroup.appendChild(substageLabel);
      lastSubstage = m.substage_name;
    }
    // Add the field option
    const opt = document.createElement('option');
    opt.value = m.field_name;
    opt.textContent = m.display_name || m.field_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    stageOptGroup.appendChild(opt);
    allFieldNames.add(m.field_name);
  }
  // Add dark theme classes
  select.classList.add('bg-gray-900', 'text-gray-100', 'border', 'border-gray-700');
  // Find all valid (non-disabled) options
  const validOptions = Array.from(select.options).filter(o => !o.disabled).map(o => o.value);
  // Find the first field for the current substage
  const substageField = mappings.find(m => m.substage_name === substage);
  const substageDefault = substageField ? substageField.field_name : validOptions[0];
  // If selected is not in validOptions and is not empty/null, add it as a special option
  if (selected && !validOptions.includes(selected)) {
    const specialOpt = document.createElement('option');
    specialOpt.value = selected;
    specialOpt.textContent = `Other: ${selected}`;
    specialOpt.selected = true;
    select.insertBefore(specialOpt, select.firstChild);
  }
  // Set value if present, else default to substage field or first valid
  if (selected) {
    select.value = selected;
  } else {
    select.value = substageDefault;
  }
}

/**
 * Render the action dropdown.
 */
export function renderActionDropdown(select, actions, selected) {
  select.innerHTML = '<option value="">Select Action...</option>';
  for (const action of actions) {
    const opt = document.createElement('option');
    opt.value = action.id;
    opt.textContent = action.field_name;
    if (selected && String(selected) === String(action.id)) opt.selected = true;
    select.appendChild(opt);
  }
  // Dark theme classes
  select.classList.add('bg-gray-900', 'text-gray-100', 'border', 'border-gray-700');
  // Explicitly set value to ensure sync
  if (selected) select.value = String(selected);
}

/**
 * Render post development fields for the current substage.
 */
export function renderPostDevFields(panel, mappings, postDev, substage) {
  // Find substage_id for the current substage name
  const substageEntry = mappings.find(m => m.substage_name === substage);
  const substageId = substageEntry ? substageEntry.substage_id : null;
  const fields = substageId ? mappings.filter(m => m.substage_id == substageId).map(m => m.field_name) : [];
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

/**
 * Show action details (prompt/template, model, etc).
 */
export async function showActionDetails(actionId, actionPromptPanel, fetchLLMActionDetails) {
  if (!actionId) {
    actionPromptPanel.innerHTML = '(No action selected)';
    return;
  }
  const details = await fetchLLMActionDetails(actionId);
  // Robust: support both {action: {...}} and flat
  const action = details.action || details;
  let html = '';
  if (action.prompt_template) {
    html += `<div><b>Prompt Template:</b><pre class='bg-gray-800 text-gray-100 rounded p-2 mt-1 mb-2'>${action.prompt_template}</pre></div>`;
  }
  if (action.llm_model) {
    html += `<div><b>LLM Model:</b> <span class='text-green-300'>${action.llm_model}</span></div>`;
  }
  if (!html) html = '(No details)';
  actionPromptPanel.innerHTML = html;
}

/**
 * Show/hide input/output panels based on action selection.
 */
export function updatePanelVisibility(actionSelect, inputPanel, outputPanel) {
  if (actionSelect.value) {
    inputPanel.classList.remove('hidden');
    outputPanel.classList.remove('hidden');
  } else {
    inputPanel.classList.add('hidden');
    outputPanel.classList.add('hidden');
  }
} 