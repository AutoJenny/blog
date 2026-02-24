/**
 * W2-GOV-8: Homepage Governance Panel.
 * Fetches /api/home/governance-summary and renders slots table with deep-links only.
 * No framework; no global pollution; fail gracefully on error.
 */
(function () {
  'use strict';

  var API_URL = '/api/home/governance-summary';
  var START_AUTOMATION_URL = '/launchpad/one-click-publication/api/start-automation';

  function escapeHtml(str) {
    if (str == null) return '';
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function formatBool(value) {
    if (value === null || value === undefined) return '—';
    return value ? 'Yes' : 'No';
  }

  function formatDate(isoDate) {
    if (!isoDate) return '—';
    try {
      var d = new Date(isoDate + 'T00:00:00');
      return isNaN(d.getTime()) ? isoDate : d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
    } catch (_) {
      return isoDate;
    }
  }

  function roleLabel(itemType) {
    if (!itemType) return '—';
    return String(itemType).charAt(0).toUpperCase() + String(itemType).slice(1);
  }

  function renderError(message) {
    var panel = document.getElementById('governance-panel');
    if (!panel) return;
    panel.innerHTML = '<p class="text-slate-400 text-sm">' + escapeHtml(message) + '</p>';
  }

  function renderPanel(data) {
    var panel = document.getElementById('governance-panel');
    if (!panel) return;

    var week = data.current_week;
    var year = data.year;
    var slots = data.slots || [];
    var summary = data.automation_summary || {};

    var headerHtml = '<h2 class="text-lg font-semibold text-white mb-4">Week ' + escapeHtml(String(week)) + ' (' + escapeHtml(String(year)) + ')</h2>';

    var tableHtml = '';
    if (slots.length === 0) {
      tableHtml = '<p class="text-slate-400 text-sm">No slots for this week.</p>';
    } else {
      tableHtml =
        '<div class="overflow-x-auto rounded-lg border border-slate-600">' +
        '<table class="min-w-full text-left text-sm">' +
        '<thead class="bg-slate-800 text-slate-300 uppercase tracking-wide">' +
        '<tr>' +
        '<th class="px-4 py-2 font-medium">Role</th>' +
        '<th class="px-4 py-2 font-medium">Scheduled Date</th>' +
        '<th class="px-4 py-2 font-medium">Post Status</th>' +
        '<th class="px-4 py-2 font-medium">Workflow Stage</th>' +
        '<th class="px-4 py-2 font-medium">Automation Enabled</th>' +
        '<th class="px-4 py-2 font-medium">Output Ready</th>' +
        '<th class="px-4 py-2 font-medium">Actions</th>' +
        '</tr></thead><tbody class="bg-slate-900/50 text-slate-200">';

      for (var i = 0; i < slots.length; i++) {
        var s = slots[i];
        var role = roleLabel(s.item_type);
        var scheduledDate = formatDate(s.scheduled_date);
        var postStatus = s.post_status != null ? escapeHtml(String(s.post_status)) : '—';
        var workflowStage = s.workflow_stage != null ? escapeHtml(String(s.workflow_stage)) : '—';
        var automationEnabled = formatBool(s.automation_enabled);
        var outputReady = formatBool(s.output_ready);

        var actions = [];
        if (s.post_id != null) {
          actions.push('<a href="/planning/posts/' + s.post_id + '/calendar" class="text-blue-400 hover:text-blue-300">Open Post</a>');
          if (s.automation_enabled === true && s.output_ready === true && s.automation_blocked_reason == null) {
            actions.push('<button type="button" class="gov-run-automation text-emerald-400 hover:text-emerald-300" data-post-id="' + escapeHtml(String(s.post_id)) + '">Run Automation</button>');
          }
        } else {
          actions.push('<a href="/launchpad/one-click-publication?slot_id=' + escapeHtml(String(s.slot_id)) + '" class="text-blue-400 hover:text-blue-300">Create From Slot</a>');
        }
        var actionsHtml = actions.length ? actions.join(' · ') : '—';

        tableHtml +=
          '<tr class="border-t border-slate-700">' +
          '<td class="px-4 py-2">' + escapeHtml(role) + '</td>' +
          '<td class="px-4 py-2">' + escapeHtml(scheduledDate) + '</td>' +
          '<td class="px-4 py-2">' + postStatus + '</td>' +
          '<td class="px-4 py-2">' + workflowStage + '</td>' +
          '<td class="px-4 py-2">' + escapeHtml(automationEnabled) + '</td>' +
          '<td class="px-4 py-2">' + escapeHtml(outputReady) + '</td>' +
          '<td class="px-4 py-2">' + actionsHtml + '</td>' +
          '</tr>';
      }
      tableHtml += '</tbody></table></div>';
    }

    var summaryHtml = '<p class="text-slate-400 text-xs mt-2">Ready: ' + (summary.ready_count || 0) + ' · Blocked: ' + (summary.blocked_count || 0) + ' · No post: ' + (summary.no_post_count || 0) + '</p>';

    panel.innerHTML = '<div class="card-dark rounded-xl p-6 border border-slate-700">' + headerHtml + tableHtml + summaryHtml + '</div>';

    // Bind Run Automation buttons
    panel.querySelectorAll('.gov-run-automation').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var postId = this.getAttribute('data-post-id');
        if (!postId) return;
        runAutomation(parseInt(postId, 10));
      });
    });
  }

  function runAutomation(postId) {
    var panel = document.getElementById('governance-panel');
    if (!panel) return;
    var btn = panel.querySelector('.gov-run-automation[data-post-id="' + postId + '"]');
    if (btn) {
      btn.disabled = true;
      btn.textContent = 'Running…';
    }
    fetch(START_AUTOMATION_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ post_id: postId })
    })
      .then(function (res) { return res.json().then(function (data) { return { ok: res.ok, data: data }; }); })
      .then(function (result) {
        if (result.ok && result.data && result.data.success) {
          loadGovernancePanel();
        } else {
          if (btn) {
            btn.disabled = false;
            btn.textContent = 'Run Automation';
          }
          alert(result.data && result.data.error ? result.data.error : 'Automation request failed.');
        }
      })
      .catch(function () {
        if (btn) {
          btn.disabled = false;
          btn.textContent = 'Run Automation';
        }
        alert('Request failed.');
      });
  }

  function loadGovernancePanel() {
    fetch(API_URL)
      .then(function (res) {
        if (!res.ok) throw new Error('Endpoint error');
        return res.json();
      })
      .then(function (data) {
        if (data && typeof data.current_week !== 'undefined' && typeof data.year !== 'undefined') {
          renderPanel(data);
        } else {
          renderError('Governance panel unavailable.');
        }
      })
      .catch(function () {
        renderError('Governance panel unavailable.');
      });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadGovernancePanel);
  } else {
    loadGovernancePanel();
  }
})();
