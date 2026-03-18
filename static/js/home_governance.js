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

  function roleLabel(itemType, role) {
    if (role === 'blog') return 'Blog';
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

  function createGovModalWrapper(id) {
    var wrapper = document.createElement('div');
    wrapper.id = id;
    wrapper.className = 'gov-modal-wrapper';
    var backdrop = document.createElement('div');
    backdrop.className = 'modal-backdrop';
    var panel = document.createElement('div');
    panel.className = 'modal modal-dark';
    wrapper.appendChild(backdrop);
    wrapper.appendChild(panel);
    return { wrapper: wrapper, backdrop: backdrop, panel: panel };
  }

  function openNewIdeaModal() {
    var existing = document.getElementById('gov-new-idea-modal');
    if (existing) existing.remove();
    var struct = createGovModalWrapper('gov-new-idea-modal');
    struct.panel.innerHTML =
      '<div class="gov-modal-panel-inner w-full max-w-md rounded-lg border border-slate-600 p-4">' +
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
    struct.backdrop.addEventListener('click', function () { struct.wrapper.remove(); });
    document.body.appendChild(struct.wrapper);

    document.getElementById('gov-new-idea-cancel').addEventListener('click', function () {
      struct.wrapper.remove();
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
          struct.wrapper.remove();
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
    var struct = createGovModalWrapper('gov-edit-modal');
    struct.panel.innerHTML =
      '<div class="gov-modal-panel-inner w-full max-w-md rounded-lg border border-slate-600 p-4">' +
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
    struct.backdrop.addEventListener('click', function () { struct.wrapper.remove(); });
    document.body.appendChild(struct.wrapper);

    document.getElementById('gov-edit-cancel').addEventListener('click', function () {
      struct.wrapper.remove();
    });
    document.getElementById('gov-edit-save').addEventListener('click', function () {
      var title = (document.getElementById('gov-edit-title').value || '').trim();
      var summary = (document.getElementById('gov-edit-summary').value || '').trim();
      patchJson(IDEA_API_PREFIX + candidate.item_id, {
        idea_title: title,
        idea_description: summary
      }).then(function (result) {
        if (result.ok && result.data && result.data.success) {
          struct.wrapper.remove();
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
    var struct = createGovModalWrapper('gov-move-modal');
    struct.panel.innerHTML =
      '<div class="gov-modal-panel-inner w-full max-w-sm rounded-lg border border-slate-600 p-4">' +
      '<h3 class="text-lg font-semibold text-white mb-3">Move Blog Candidate</h3>' +
      '<label class="block text-sm text-slate-300 mb-2">Scheduled date</label>' +
      '<input id="gov-move-date" type="date" class="w-full mb-4 rounded border border-slate-600 bg-slate-800 text-slate-100 px-3 py-2">' +
      '<div class="flex justify-end gap-2">' +
      '<button type="button" id="gov-move-cancel" class="px-3 py-2 rounded bg-slate-700 hover:bg-slate-600 text-slate-100 text-sm">Cancel</button>' +
      '<button type="button" id="gov-move-save" class="px-3 py-2 rounded bg-blue-600 hover:bg-blue-500 text-white text-sm">Save</button>' +
      '</div>' +
      '</div>';
    struct.backdrop.addEventListener('click', function () { struct.wrapper.remove(); });
    document.body.appendChild(struct.wrapper);

    document.getElementById('gov-move-cancel').addEventListener('click', function () {
      struct.wrapper.remove();
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
          struct.wrapper.remove();
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
        patchJson(WEEK_ITEM_API_PREFIX + weekItemId, { is_selected: true }).then(function (result) {
          if (!(result.ok && result.data && result.data.success)) {
            alert((result.data && result.data.error) ? result.data.error : 'Could not set selected candidate.');
            loadGovernancePanel();
          } else {
            loadGovernancePanel();
          }
        }).catch(function () {
          alert('Could not set selected candidate.');
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
          var createPayload = {
            category: 'idea',
            item_id: selected.item_id,
            week_item_id: selected.week_item_id,
            year: panelYear,
            week: panelWeek
          };
          postJson(CONVERT_URL, createPayload).then(function (result) {
            if (!result.ok || !result.data || !result.data.success) {
              var msg = (result.data && (result.data.error || result.data.message)) || 'Convert failed.';
              alert(msg);
              return;
            }
            var postId = result.data.post_id;
            if (postId == null) return;
            patchJson(WEEK_ITEM_API_PREFIX + selected.week_item_id, {
              metadata: { converted: true, post_id: postId },
              is_selected: true,
              is_active: true
            }).then(function (patchResult) {
              if (patchResult.ok && patchResult.data && patchResult.data.success) {
                loadGovernancePanel();
              } else {
                loadGovernancePanel();
              }
            }).catch(function () {
              loadGovernancePanel();
            });
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

  function formatWindowDate(isoDate) {
    if (!isoDate) return '';
    try {
      var d = new Date(isoDate + 'T00:00:00');
      return isNaN(d.getTime()) ? isoDate : d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
    } catch (_) {
      return isoDate;
    }
  }

  function isoWeekFromDateStr(isoDateStr) {
    if (!isoDateStr) return { year: null, week: null };
    try {
      var d = new Date(isoDateStr + 'T12:00:00');
      if (isNaN(d.getTime())) return { year: null, week: null };
      d.setHours(0, 0, 0, 0);
      d.setDate(d.getDate() + 4 - (d.getDay() || 7));
      var y = d.getFullYear();
      var start = new Date(y, 0, 1);
      var week = Math.ceil((((d - start) / 86400000) + 1) / 7);
      return { year: y, week: week };
    } catch (_) {
      return { year: null, week: null };
    }
  }

  function renderPanel(data) {
    var panel = document.getElementById('governance-panel');
    if (!panel) return;

    try {
      var windowStart = data.window_start || '';
      var windowEnd = data.window_end || '';
      var iso = isoWeekFromDateStr(windowStart);
      panelYear = iso.year;
      panelWeek = iso.week;
      var slots = Array.isArray(data.scheduled_slots) ? data.scheduled_slots : [];
      var candidates = Array.isArray(data.blog_candidates) ? data.blog_candidates : [];
      var summary = data.automation_summary || {};
      var headingLabel = windowStart && windowEnd
        ? 'Next 7 days (' + formatWindowDate(windowStart) + ' – ' + formatWindowDate(windowEnd) + ')'
        : 'Next 7 days';

      var html = '';
      html += '<div class="flex flex-wrap items-center justify-between gap-2 mb-4">';
      html += '<div>';
      html += '<h2 class="text-lg font-semibold text-white">' + escapeHtml(headingLabel) + '</h2>';
      html += '</div>';
      html += '<a href="/planning/calendar" class="text-sm text-slate-400 hover:text-slate-200">View full calendar →</a>';
      html += '</div>';
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

      if (slots.length === 0) {
        html += '<tr class="border-t border-slate-700"><td colspan="9" class="px-4 py-4 text-slate-400">No scheduled content in the next 7 days.</td></tr>';
      }
      for (var i = 0; i < slots.length; i++) {
        var slot = slots[i];
        var actions = [];
        if (slot.post_id != null) {
          actions.push('<a href="/planning/posts/' + slot.post_id + '/calendar" class="text-blue-400 hover:text-blue-300">Open Post</a>');
          if (slot.automation_enabled === true && slot.output_ready === true && slot.automation_blocked_reason == null) {
            actions.push('<button type="button" class="gov-run-automation text-emerald-400 hover:text-emerald-300" data-post-id="' + escapeHtml(String(slot.post_id)) + '">Run Automation</button>');
          }
        } else {
          if (slot.role === 'blog' || slot.item_type === 'blog') {
            actions.push('<span class="text-slate-500" title="Start from ideas below">—</span>');
          } else {
            actions.push('<a href="/launchpad/one-click-publication?slot_id=' + escapeHtml(String(slot.slot_id)) + '" class="text-blue-400 hover:text-blue-300">Create From Slot</a>');
          }
        }
        html += '<tr class="border-t border-slate-700">';
        html += '<td class="px-4 py-2">' + escapeHtml(roleLabel(slot.item_type, slot.role)) + '</td>';
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

      html += '<details class="blog-candidates gov-accordion mt-4">';
      html += '<summary class="gov-accordion-toggle cursor-pointer text-slate-300 hover:text-white font-medium">Blog ideas (' + escapeHtml(String(candidates.length)) + ' available)</summary>';
      html += '<div class="gov-accordion-body mt-2">';
      html += '<div class="blog-candidate-controls"><button id="addNewIdeaBtn">+ New Idea</button></div>';
      html += '<div id="blogCandidatesList">';
      candidateByWeekItemId = {};
      for (var j = 0; j < candidates.length; j++) {
        var c = candidates[j];
        candidateByWeekItemId[String(c.week_item_id)] = c;
        var meta = c.metadata || {};
        var converted = meta.converted === true && (meta.post_id != null || c.post_id != null);
        var postId = c.post_id != null ? c.post_id : (meta.post_id != null ? meta.post_id : null);
        var isSelected = c.is_selected === true;
        html += '<div class="blog-candidate-card">';
        html += '<label>';
        html += '<input type="radio" name="blogCandidate" value="' + escapeHtml(String(c.week_item_id)) + '"' + (c.is_selected === true ? ' checked' : '') + '>';
        html += '<strong>' + escapeHtml(c.title || ('Idea #' + c.item_id)) + '</strong>';
        if (isSelected) html += ' <span class="gov-candidate-active-tag">Active</span>';
        html += '</label>';
        html += '<div class="candidate-summary">' + escapeHtml(c.summary || '') + '</div>';
        html += '<div class="candidate-actions">';
        if (converted && postId) {
          html += '<a href="/planning/posts/' + escapeHtml(String(postId)) + '/calendar" class="candidate-btn primary">Open Post</a>';
          html += '<button class="candidate-btn" data-action="edit" data-id="' + escapeHtml(String(c.week_item_id)) + '">Edit</button>';
          html += '<button class="candidate-btn" data-action="move" data-id="' + escapeHtml(String(c.week_item_id)) + '">Move</button>';
          html += '<button class="candidate-btn danger" data-action="delete" data-id="' + escapeHtml(String(c.week_item_id)) + '" disabled title="Converted item">Delete</button>';
        } else {
          html += '<button class="candidate-btn primary" data-action="convert" data-id="' + escapeHtml(String(c.week_item_id)) + '" title="Creates a draft blog post from this idea and sets it as this week\'s active blog.">Start Blog Post</button>';
          html += '<button class="candidate-btn" data-action="edit" data-id="' + escapeHtml(String(c.week_item_id)) + '">Edit</button>';
          html += '<button class="candidate-btn" data-action="move" data-id="' + escapeHtml(String(c.week_item_id)) + '">Move</button>';
          html += '<button class="candidate-btn danger" data-action="delete" data-id="' + escapeHtml(String(c.week_item_id)) + '">Delete</button>';
        }
        html += '</div>';
        html += '</div>';
      }
      html += '</div></div></details>';

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
    } catch (err) {
      panel.innerHTML = '<div class="card-dark rounded-xl p-6 border border-slate-700"><p class="text-red-400 text-sm">Render error: ' + escapeHtml((err && (err.message || String(err))) ? String(err.message || err).slice(0, 80) : 'Unknown error') + '</p></div>';
    }
  }

  function loadGovernancePanel() {
    fetch(API_URL)
      .then(function (res) {
        if (!res.ok) throw new Error('Endpoint error');
        return res.json();
      })
      .then(function (data) {
        if (!data || data.window_start === undefined) {
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
