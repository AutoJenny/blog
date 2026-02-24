/**
 * Governance panel renderer.
 */
(function () {
  'use strict';

  var API_URL = '/api/home/governance-summary';
  var CONVERT_URL = '/launchpad/one-click-publication/api/create-post-from-item';
  var START_AUTOMATION_URL = '/launchpad/one-click-publication/api/start-automation';
  var IDEA_API_PREFIX = '/planning/api/calendar/ideas/';
  var WEEK_ITEM_API_PREFIX = '/planning/api/calendar/week-items/';
  var candidateByWeekItemId = {};
  var panelYear = null;
  var panelWeek = null;

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
    if (itemType === 'idea') return 'Blog Candidate';
    return String(itemType).charAt(0).toUpperCase() + String(itemType).slice(1);
  }

  function renderError(message) {
    var panel = document.getElementById('governance-panel');
    if (!panel) return;
    panel.innerHTML = '<p class="text-slate-400 text-sm">' + escapeHtml(message) + '</p>';
  }

  function channelIcon(channel) {
    var key = String(channel || '').toLowerCase();
    if (key === 'blog') return '📝';
    if (key === 'facebook') return 'f';
    if (key === 'instagram') return '📷';
    if (key === 'twitter' || key === 'x') return 'X';
    if (key === 'newsletter') return '✉️';
    return '•';
  }

  function renderChannels(channels) {
    if (!Array.isArray(channels) || channels.length === 0) return '—';
    var html = [];
    for (var i = 0; i < channels.length; i++) {
      var ch = channels[i] || {};
      var channel = String(ch.channel || '');
      html.push('<span title="' + escapeHtml(channel) + '">' + escapeHtml(channelIcon(channel)) + '</span>');
    }
    return html.join(' ');
  }

  function summaryText(summary) {
    if (!summary) return '—';
    var s = String(summary);
    if (s.length > 140) s = s.slice(0, 137) + '...';
    return s;
  }

  function patchJson(url, payload) {
    return fetch(url, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload || {})
    }).then(function (res) {
      return res.json().catch(function () { return {}; }).then(function (data) {
        return { ok: res.ok, data: data };
      });
    });
  }

  function postJson(url, payload) {
    return fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload || {})
    }).then(function (res) {
      return res.json().catch(function () { return {}; }).then(function (data) {
        return { ok: res.ok, data: data };
      });
    });
  }

  function openNewIdeaModal() {
    var existing = document.getElementById('gov-new-idea-modal');
    if (existing) existing.remove();
    var modal = document.createElement('div');
    modal.id = 'gov-new-idea-modal';
    modal.className = 'modal modal-dark fixed inset-0 z-50 flex items-center justify-center bg-black/60';
    modal.innerHTML =
      '<div class="w-full max-w-md rounded-lg border border-slate-600 bg-slate-900 p-4">' +
      '<h3 class="text-lg font-semibold text-white mb-3">New Idea</h3>' +
      '<label class="block text-sm text-slate-300 mb-2">Title</label>' +
      '<input id="gov-new-idea-title" type="text" class="w-full mb-3 rounded border border-slate-600 bg-slate-800 text-slate-100 px-3 py-2">' +
      '<label class="block text-sm text-slate-300 mb-2">Summary</label>' +
      '<textarea id="gov-new-idea-summary" class="w-full mb-4 rounded border border-slate-600 bg-slate-800 text-slate-100 px-3 py-2" rows="4"></textarea>' +
      '<div class="flex justify-end gap-2">' +
      '<button type="button" id="gov-new-idea-cancel" class="px-3 py-2 rounded bg-slate-700 hover:bg-slate-600 text-slate-100 text-sm">Cancel</button>' +
      '<button type="button" id="gov-new-idea-save" class="px-3 py-2 rounded bg-blue-600 hover:bg-blue-500 text-white text-sm">Save</button>' +
      '</div>' +
      '</div>';
    document.body.appendChild(modal);

    document.getElementById('gov-new-idea-cancel').addEventListener('click', function () {
      modal.remove();
    });
    document.getElementById('gov-new-idea-save').addEventListener('click', function () {
      var title = (document.getElementById('gov-new-idea-title').value || '').trim();
      var summary = (document.getElementById('gov-new-idea-summary').value || '').trim();
      if (!title) {
        alert('Title is required.');
        return;
      }
      postJson('/planning/api/calendar/ideas', {
        title: title,
        summary: summary || null,
        year: panelYear,
        week_number: panelWeek
      }).then(function (result) {
        if (result.ok && result.data && result.data.success) {
          modal.remove();
          loadGovernancePanel();
        } else {
          alert((result.data && result.data.error) ? result.data.error : 'Create failed.');
        }
      }).catch(function () {
        alert('Request failed.');
      });
    });
  }

  function openEditModal(candidate) {
    var existing = document.getElementById('gov-edit-modal');
    if (existing) existing.remove();
    var modal = document.createElement('div');
    modal.id = 'gov-edit-modal';
    modal.className = 'modal modal-dark fixed inset-0 z-50 flex items-center justify-center bg-black/60';
    modal.innerHTML =
      '<div class="w-full max-w-md rounded-lg border border-slate-600 bg-slate-900 p-4">' +
      '<h3 class="text-lg font-semibold text-white mb-3">Edit Blog Candidate</h3>' +
      '<label class="block text-sm text-slate-300 mb-2">Title</label>' +
      '<input id="gov-edit-title" type="text" value="' + escapeHtml(candidate.title || '') + '" class="w-full mb-3 rounded border border-slate-600 bg-slate-800 text-slate-100 px-3 py-2">' +
      '<label class="block text-sm text-slate-300 mb-2">Description</label>' +
      '<textarea id="gov-edit-summary" class="w-full mb-4 rounded border border-slate-600 bg-slate-800 text-slate-100 px-3 py-2" rows="4">' + escapeHtml(candidate.summary || '') + '</textarea>' +
      '<div class="flex justify-end gap-2">' +
      '<button type="button" id="gov-edit-cancel" class="px-3 py-2 rounded bg-slate-700 hover:bg-slate-600 text-slate-100 text-sm">Cancel</button>' +
      '<button type="button" id="gov-edit-save" class="px-3 py-2 rounded bg-blue-600 hover:bg-blue-500 text-white text-sm">Save</button>' +
      '</div>' +
      '</div>';
    document.body.appendChild(modal);

    document.getElementById('gov-edit-cancel').addEventListener('click', function () {
      modal.remove();
    });
    document.getElementById('gov-edit-save').addEventListener('click', function () {
      var title = (document.getElementById('gov-edit-title').value || '').trim();
      var summary = (document.getElementById('gov-edit-summary').value || '').trim();
      patchJson(IDEA_API_PREFIX + candidate.item_id, {
        idea_title: title,
        idea_description: summary
      }).then(function (result) {
        if (result.ok && result.data && result.data.success) {
          modal.remove();
          loadGovernancePanel();
        } else {
          alert((result.data && result.data.error) ? result.data.error : 'Edit failed.');
        }
      }).catch(function () {
        alert('Request failed.');
      });
    });
  }

  function openMoveModal(candidate) {
    var existing = document.getElementById('gov-move-modal');
    if (existing) existing.remove();
    var modal = document.createElement('div');
    modal.id = 'gov-move-modal';
    modal.className = 'modal modal-dark fixed inset-0 z-50 flex items-center justify-center bg-black/60';
    modal.innerHTML =
      '<div class="w-full max-w-sm rounded-lg border border-slate-600 bg-slate-900 p-4">' +
      '<h3 class="text-lg font-semibold text-white mb-3">Move Blog Candidate</h3>' +
      '<label class="block text-sm text-slate-300 mb-2">Scheduled date</label>' +
      '<input id="gov-move-date" type="date" class="w-full mb-4 rounded border border-slate-600 bg-slate-800 text-slate-100 px-3 py-2">' +
      '<div class="flex justify-end gap-2">' +
      '<button type="button" id="gov-move-cancel" class="px-3 py-2 rounded bg-slate-700 hover:bg-slate-600 text-slate-100 text-sm">Cancel</button>' +
      '<button type="button" id="gov-move-save" class="px-3 py-2 rounded bg-blue-600 hover:bg-blue-500 text-white text-sm">Save</button>' +
      '</div>' +
      '</div>';
    document.body.appendChild(modal);

    document.getElementById('gov-move-cancel').addEventListener('click', function () {
      modal.remove();
    });
    document.getElementById('gov-move-save').addEventListener('click', function () {
      var dateValue = (document.getElementById('gov-move-date').value || '').trim();
      if (!dateValue) {
        alert('Select a date.');
        return;
      }
      patchJson(WEEK_ITEM_API_PREFIX + candidate.week_item_id, {
        year: panelYear,
        week_number: panelWeek,
        scheduled_date: dateValue
      }).then(function (result) {
        if (result.ok && result.data && result.data.success) {
          modal.remove();
          loadGovernancePanel();
        } else {
          alert((result.data && result.data.error) ? result.data.error : 'Move failed.');
        }
      }).catch(function () {
        alert('Request failed.');
      });
    });
  }

  function bindCandidateEvents() {
    var addNewIdeaBtn = document.getElementById('addNewIdeaBtn');
    if (addNewIdeaBtn) {
      addNewIdeaBtn.addEventListener('click', function () {
        openNewIdeaModal();
      });
    }

    document.querySelectorAll('input[name="blogCandidate"]').forEach(function (radio) {
      radio.addEventListener('change', function () {
        if (!this.checked) return;
        var weekItemId = parseInt(this.value, 10);
        if (!weekItemId) return;
        patchJson(WEEK_ITEM_API_PREFIX + weekItemId + '/primary', {}).then(function (result) {
          if (!(result.ok && result.data && result.data.success)) {
            alert((result.data && result.data.error) ? result.data.error : 'Could not set primary candidate.');
            loadGovernancePanel();
          }
        }).catch(function () {
          alert('Could not set primary candidate.');
          loadGovernancePanel();
        });
      });
    });

    document.querySelectorAll('.candidate-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var action = String(this.getAttribute('data-action') || '').toLowerCase();
        var weekItemId = String(this.getAttribute('data-id') || '');
        var candidate = candidateByWeekItemId[weekItemId];
        if (!candidate) return;

        if (action === 'convert') {
          var selectedRadio = document.querySelector('input[name="blogCandidate"]:checked');
          if (!selectedRadio) {
            alert('Select a candidate first.');
            return;
          }
          var selectedWeekItemId = parseInt(selectedRadio.value, 10);
          var selected = candidateByWeekItemId[String(selectedWeekItemId)];
          if (!selected) {
            alert('Candidate not found.');
            return;
          }
          var convertPayload = {
            category: 'idea',
            item_id: selected.item_id,
            week_item_id: selected.week_item_id,
            year: panelYear,
            week: panelWeek
          };
          console.log('[blog-candidate] convert request', convertPayload);
          postJson(CONVERT_URL, {
            category: 'idea',
            item_id: selected.item_id,
            week_item_id: selected.week_item_id,
            year: panelYear,
            week: panelWeek
          }).then(function (result) {
            console.log('[blog-candidate] convert response', { ok: result.ok, status: result.data && result.data.status, data: result.data });
            if (result.ok && result.data && result.data.success) {
              loadGovernancePanel();
            } else {
              alert((result.data && result.data.error) ? result.data.error : 'Convert failed.');
            }
          }).catch(function () {
            alert('Request failed.');
          });
          return;
        }

        if (action === 'edit') {
          openEditModal(candidate);
          return;
        }

        if (action === 'move') {
          openMoveModal(candidate);
          return;
        }

        if (action === 'delete') {
          if (!window.confirm('Delete this blog candidate?')) return;
          patchJson(WEEK_ITEM_API_PREFIX + candidate.week_item_id, {
            is_active: false
          }).then(function (result) {
            if (result.ok && result.data && result.data.success) {
              loadGovernancePanel();
            } else {
              alert((result.data && result.data.error) ? result.data.error : 'Delete failed.');
            }
          }).catch(function () {
            alert('Request failed.');
          });
          return;
        }

        if (action === 'noop') {
          return;
        }

        alert('Unknown action.');
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

  function renderPanel(data) {
    var panel = document.getElementById('governance-panel');
    if (!panel) return;

    panelYear = data.year;
    panelWeek = data.current_week;
    var slots = Array.isArray(data.scheduled_slots) ? data.scheduled_slots : [];
    var candidates = Array.isArray(data.blog_candidates) ? data.blog_candidates : [];
    var summary = data.automation_summary || {};

    var html = '';
    html += '<h2 class="text-lg font-semibold text-white mb-4">Week ' + escapeHtml(String(panelWeek)) + ' (' + escapeHtml(String(panelYear)) + ')</h2>';
    html += '<div class="overflow-x-auto rounded-lg border border-slate-600">';
    html += '<table class="min-w-full text-left text-sm">';
    html += '<thead class="bg-slate-800 text-slate-300 uppercase tracking-wide"><tr>';
    html += '<th class="px-4 py-2 font-medium">Role</th>';
    html += '<th class="px-4 py-2 font-medium">Scheduled Date</th>';
    html += '<th class="px-4 py-2 font-medium">Channels</th>';
    html += '<th class="px-4 py-2 font-medium">Summary</th>';
    html += '<th class="px-4 py-2 font-medium">Post Status</th>';
    html += '<th class="px-4 py-2 font-medium">Workflow Stage</th>';
    html += '<th class="px-4 py-2 font-medium">Automation Enabled</th>';
    html += '<th class="px-4 py-2 font-medium">Output Ready</th>';
    html += '<th class="px-4 py-2 font-medium">Actions</th>';
    html += '</tr></thead><tbody class="bg-slate-900/50 text-slate-200">';

    for (var i = 0; i < slots.length; i++) {
      var slot = slots[i];
      if (slot.item_type === 'idea') continue;
      var actions = [];
      if (slot.post_id != null) {
        actions.push('<a href="/planning/posts/' + slot.post_id + '/calendar" class="text-blue-400 hover:text-blue-300">Open Post</a>');
        if (slot.automation_enabled === true && slot.output_ready === true && slot.automation_blocked_reason == null) {
          actions.push('<button type="button" class="gov-run-automation text-emerald-400 hover:text-emerald-300" data-post-id="' + escapeHtml(String(slot.post_id)) + '">Run Automation</button>');
        }
      } else {
        actions.push('<a href="/launchpad/one-click-publication?slot_id=' + escapeHtml(String(slot.slot_id)) + '" class="text-blue-400 hover:text-blue-300">Create From Slot</a>');
      }
      html += '<tr class="border-t border-slate-700">';
      html += '<td class="px-4 py-2">' + escapeHtml(roleLabel(slot.item_type)) + '</td>';
      html += '<td class="px-4 py-2">' + escapeHtml(formatDate(slot.scheduled_date)) + '</td>';
      html += '<td class="px-4 py-2">' + renderChannels(slot.channels) + '</td>';
      html += '<td class="px-4 py-2 max-w-md">' + escapeHtml(summaryText(slot.summary)) + '</td>';
      html += '<td class="px-4 py-2">' + escapeHtml(slot.post_status != null ? String(slot.post_status) : '—') + '</td>';
      html += '<td class="px-4 py-2">' + escapeHtml(slot.workflow_stage != null ? String(slot.workflow_stage) : '—') + '</td>';
      html += '<td class="px-4 py-2">' + escapeHtml(formatBool(slot.automation_enabled)) + '</td>';
      html += '<td class="px-4 py-2">' + escapeHtml(formatBool(slot.output_ready)) + '</td>';
      html += '<td class="px-4 py-2">' + actions.join(' · ') + '</td>';
      html += '</tr>';
    }
    html += '</tbody></table></div>';

    html += '<div class="blog-candidates">';
    html += '<h3>Ideas Available for Week ' + escapeHtml(String(panelWeek)) + ' (' + escapeHtml(String(candidates.length)) + ')</h3>';
    html += '<div class="blog-candidate-controls"><button id="addNewIdeaBtn">+ New Idea</button></div>';
    html += '<div id="blogCandidatesList">';
    candidateByWeekItemId = {};
    for (var j = 0; j < candidates.length; j++) {
      var c = candidates[j];
      candidateByWeekItemId[String(c.week_item_id)] = c;
      html += '<div class="blog-candidate-card">';
      html += '<label>';
      html += '<input type="radio" name="blogCandidate" value="' + escapeHtml(String(c.week_item_id)) + '"' + (c.is_primary === true ? ' checked' : '') + '>';
      html += '<strong>' + escapeHtml(c.title || ('Idea #' + c.item_id)) + '</strong>';
      html += '</label>';
      html += '<div class="candidate-summary">' + escapeHtml(c.summary || '') + '</div>';
      html += '<div class="candidate-actions">';
      html += '<button class="candidate-btn primary" data-action="convert" data-id="' + escapeHtml(String(c.week_item_id)) + '">Convert</button>';
      html += '<button class="candidate-btn" data-action="edit" data-id="' + escapeHtml(String(c.week_item_id)) + '">Edit</button>';
      html += '<button class="candidate-btn" data-action="move" data-id="' + escapeHtml(String(c.week_item_id)) + '">Move</button>';
      html += '<button class="candidate-btn danger" data-action="delete" data-id="' + escapeHtml(String(c.week_item_id)) + '">Delete</button>';
      html += '</div>';
      html += '</div>';
    }
    html += '</div></div>';

    html += '<p class="text-slate-400 text-xs mt-2">Ready: ' + (summary.ready_count || 0) + ' · Blocked: ' + (summary.blocked_count || 0) + ' · No post: ' + (summary.no_post_count || 0) + '</p>';

    panel.innerHTML = '<div class="card-dark rounded-xl p-6 border border-slate-700">' + html + '</div>';

    panel.querySelectorAll('.gov-run-automation').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var postId = this.getAttribute('data-post-id');
        if (!postId) return;
        runAutomation(parseInt(postId, 10));
      });
    });
    bindCandidateEvents();
  }

  function loadGovernancePanel() {
    fetch(API_URL)
      .then(function (res) {
        if (!res.ok) throw new Error('Endpoint error');
        return res.json();
      })
      .then(function (data) {
        if (!data || typeof data.current_week === 'undefined' || typeof data.year === 'undefined') {
          renderError('Governance panel unavailable.');
          return;
        }
        renderPanel(data);
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
