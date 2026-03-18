(function () {
  'use strict';

  var API = '/chat-history/api';
  var conversations = [];
  var openConvId = null;

  function escHtml(s) {
    if (!s) return '';
    var d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
  }

  function shortTs(iso) {
    if (!iso) return '';
    try {
      var d = new Date(iso);
      return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }) +
        ' ' + d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
    } catch (_) { return iso; }
  }

  function fetchJson(url, opts) {
    return fetch(url, opts).then(function (r) {
      return r.json().then(function (d) { return { ok: r.ok, data: d }; });
    });
  }

  function loadConversations() {
    fetchJson(API + '/conversations').then(function (r) {
      if (r.ok) {
        conversations = r.data.conversations || [];
        render();
        loadUnassignedCount();
      }
    });
  }

  function loadUnassignedCount() {
    fetchJson(API + '/unassigned-count').then(function (r) {
      var badge = document.getElementById('import-badge');
      if (badge && r.ok && r.data.count > 0) {
        badge.textContent = r.data.count;
        badge.style.display = 'inline';
      } else if (badge) {
        badge.style.display = 'none';
      }
    });
  }

  function render() {
    var container = document.getElementById('accordion-container');
    var empty = document.getElementById('empty-state');
    if (!container) return;

    if (conversations.length === 0) {
      container.innerHTML = '';
      container.appendChild(empty || createEmpty());
      if (empty) empty.style.display = '';
      return;
    }
    if (empty) empty.style.display = 'none';

    var html = '';
    for (var i = 0; i < conversations.length; i++) {
      var c = conversations[i];
      var isOpen = c.id === openConvId;
      var msgCount = (c.messages || []).length;
      html += '<div class="conv-accordion" data-id="' + escHtml(c.id) + '">';
      html += '<div class="conv-header" data-id="' + escHtml(c.id) + '">';
      html += '<div class="conv-header-left">';
      html += '<i class="fa-solid fa-chevron-right conv-chevron' + (isOpen ? ' open' : '') + '"></i>';
      html += '<span class="conv-name">' + escHtml(c.name) + '</span>';
      html += '<span style="color:#64748b;font-size:0.75rem;">(' + msgCount + ')</span>';
      html += '</div>';
      html += '<div class="conv-header-right">';
      html += '<span class="conv-timestamp">' + escHtml(shortTs(c.updated_at)) + '</span>';
      html += '<i class="fa-solid fa-pen conv-edit" data-id="' + escHtml(c.id) + '" title="Rename"></i>';
      html += '<i class="fa-solid fa-trash conv-delete" data-id="' + escHtml(c.id) + '" title="Delete conversation"></i>';
      html += '</div>';
      html += '</div>';
      html += '<div class="conv-body' + (isOpen ? ' open' : '') + '" data-id="' + escHtml(c.id) + '">';
      html += renderMessages(c);
      html += '</div>';
      html += '</div>';
    }
    container.innerHTML = html;
    bindAccordionEvents();
  }

  function renderMessages(conv) {
    var msgs = conv.messages || [];
    if (msgs.length === 0) {
      return '<div style="color:#64748b;font-size:0.875rem;text-align:center;padding:1rem;">No messages yet. Import chats to populate.</div>';
    }
    var html = '';
    for (var j = 0; j < msgs.length; j++) {
      var m = msgs[j];
      html += '<div class="msg-item">';
      html += '<div class="msg-header">';
      html += '<span class="msg-role ' + escHtml(m.role || '') + '">' + escHtml(m.role || 'unknown') + '</span>';
      html += '<div class="msg-header-right">';
      html += '<span class="msg-timestamp">' + escHtml(shortTs(m.timestamp)) + '</span>';
      html += '<i class="fa-solid fa-trash msg-delete" data-conv="' + escHtml(conv.id) + '" data-idx="' + j + '" title="Delete message"></i>';
      html += '</div>';
      html += '</div>';
      html += '<div class="msg-content">' + escHtml(m.content || '') + '</div>';
      html += '</div>';
    }
    return html;
  }

  function bindAccordionEvents() {
    document.querySelectorAll('.conv-header').forEach(function (hdr) {
      hdr.addEventListener('click', function (e) {
        if (e.target.closest('.conv-delete') || e.target.closest('.conv-edit')) return;
        var id = this.getAttribute('data-id');
        openConvId = (openConvId === id) ? null : id;
        render();
      });
    });

    document.querySelectorAll('.conv-delete').forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.stopPropagation();
        var id = this.getAttribute('data-id');
        if (!confirm('Delete this conversation and all its messages?')) return;
        fetchJson(API + '/conversations/' + id, { method: 'DELETE' }).then(function (r) {
          if (r.ok) {
            if (openConvId === id) openConvId = null;
            loadConversations();
          } else {
            alert(r.data.error || 'Delete failed');
          }
        });
      });
    });

    document.querySelectorAll('.conv-edit').forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.stopPropagation();
        var id = this.getAttribute('data-id');
        var conv = conversations.find(function (c) { return c.id === id; });
        if (!conv) return;
        var newName = prompt('Rename conversation:', conv.name);
        if (newName === null || !newName.trim()) return;
        fetchJson(API + '/conversations/' + id, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: newName.trim() })
        }).then(function (r) {
          if (r.ok) loadConversations();
          else alert(r.data.error || 'Rename failed');
        });
      });
    });

    document.querySelectorAll('.msg-delete').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var convId = this.getAttribute('data-conv');
        var idx = parseInt(this.getAttribute('data-idx'), 10);
        if (!confirm('Delete this message?')) return;
        fetchJson(API + '/conversations/' + convId + '/messages/' + idx, { method: 'DELETE' }).then(function (r) {
          if (r.ok) loadConversations();
          else alert(r.data.error || 'Delete failed');
        });
      });
    });
  }

  function createEmpty() {
    var div = document.createElement('div');
    div.className = 'empty-state';
    div.id = 'empty-state';
    div.innerHTML = '<i class="fa-solid fa-comments"></i><p>No conversations yet. Create one to get started.</p>';
    return div;
  }

  // New conversation modal
  function openModal() {
    var bg = document.getElementById('new-conv-modal-bg');
    var input = document.getElementById('new-conv-name');
    if (bg) bg.classList.add('open');
    if (input) { input.value = ''; input.focus(); }
  }

  function closeModal() {
    var bg = document.getElementById('new-conv-modal-bg');
    if (bg) bg.classList.remove('open');
  }

  function createConversation() {
    var input = document.getElementById('new-conv-name');
    var name = (input ? input.value : '').trim();
    if (!name) { alert('Name is required.'); return; }
    fetchJson(API + '/conversations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: name })
    }).then(function (r) {
      if (r.ok && r.data.success) {
        closeModal();
        openConvId = r.data.conversation.id;
        loadConversations();
      } else {
        alert(r.data.error || 'Create failed');
      }
    });
  }

  function importTranscripts() {
    fetchJson(API + '/import-transcripts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    }).then(function (r) {
      if (r.ok && r.data.success) {
        loadConversations();
      } else {
        alert(r.data.error || 'Import failed');
      }
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('btn-new-conv').addEventListener('click', openModal);
    document.getElementById('btn-modal-cancel').addEventListener('click', closeModal);
    document.getElementById('btn-modal-create').addEventListener('click', createConversation);
    document.getElementById('btn-import').addEventListener('click', importTranscripts);

    document.getElementById('new-conv-modal-bg').addEventListener('click', function (e) {
      if (e.target === this) closeModal();
    });

    document.getElementById('new-conv-name').addEventListener('keydown', function (e) {
      if (e.key === 'Enter') createConversation();
    });

    loadConversations();
  });
})();
