import os
import json
import uuid
import glob
from datetime import datetime
from flask import Blueprint, render_template, jsonify, request
import logging

bp = Blueprint('chat_history', __name__, url_prefix='/chat-history')
logger = logging.getLogger(__name__)

TRANSCRIPTS_DIR = os.path.expanduser(
    '~/.cursor/projects/Users-autojenny-Documents-projects-blog/agent-transcripts'
)
CONVERSATIONS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 'data', 'chat_conversations.json'
)
PROJECT_NAME = 'blog'


def _load_conversations():
    if os.path.isfile(CONVERSATIONS_FILE):
        try:
            with open(CONVERSATIONS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"conversations": []}


def _save_conversations(data):
    os.makedirs(os.path.dirname(CONVERSATIONS_FILE), exist_ok=True)
    with open(CONVERSATIONS_FILE, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def _parse_transcript(filepath):
    """Parse a JSONL transcript file into a list of messages."""
    messages = []
    try:
        mtime = os.path.getmtime(filepath)
        file_ts = datetime.fromtimestamp(mtime).isoformat()
        with open(filepath, 'r') as f:
            for line_num, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    role = entry.get('role', 'unknown')
                    msg = entry.get('message', {})
                    content_parts = msg.get('content', [])
                    text = ''
                    for part in content_parts:
                        if isinstance(part, dict) and part.get('type') == 'text':
                            text += part.get('text', '')
                    # Strip system context / user_query wrapper for cleaner display
                    if '<user_query>' in text:
                        start = text.find('<user_query>')
                        end = text.find('</user_query>')
                        if start >= 0 and end > start:
                            inner = text[start + len('<user_query>'):end].strip()
                            # If there's a USER: line in the inner content, use only that
                            if '\nUSER:\n' in inner:
                                inner = inner.split('\nUSER:\n')[-1].strip()
                            text = inner
                    if not text.strip():
                        continue
                    messages.append({
                        'role': role,
                        'content': text.strip()[:2000],
                        'line': line_num,
                        'source_file': os.path.basename(filepath),
                        'timestamp': file_ts,
                    })
                except json.JSONDecodeError:
                    continue
    except (IOError, OSError) as e:
        logger.warning(f"Could not read transcript {filepath}: {e}")
    return messages


def _get_unassigned_transcripts(conversations_data):
    """Return transcript files not yet assigned to any conversation."""
    assigned_files = set()
    for conv in conversations_data.get('conversations', []):
        for msg in conv.get('messages', []):
            sf = msg.get('source_file')
            if sf:
                assigned_files.add(sf)

    all_files = []
    if os.path.isdir(TRANSCRIPTS_DIR):
        all_files = glob.glob(os.path.join(TRANSCRIPTS_DIR, '*.jsonl'))

    unassigned = []
    for fpath in sorted(all_files, key=os.path.getmtime, reverse=True):
        if os.path.basename(fpath) not in assigned_files:
            unassigned.append(fpath)
    return unassigned


@bp.route('/')
def index():
    return render_template('chat_history/index.html', project_name=PROJECT_NAME)


@bp.route('/api/conversations', methods=['GET'])
def api_list_conversations():
    data = _load_conversations()
    convs = sorted(
        data.get('conversations', []),
        key=lambda c: c.get('updated_at', ''),
        reverse=True,
    )
    return jsonify({'conversations': convs, 'project_name': PROJECT_NAME})


@bp.route('/api/conversations', methods=['POST'])
def api_create_conversation():
    body = request.get_json(silent=True) or {}
    name = (body.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'error': 'Name is required'}), 400

    now = datetime.now().isoformat()
    conv = {
        'id': str(uuid.uuid4()),
        'name': name,
        'created_at': now,
        'updated_at': now,
        'messages': [],
    }
    data = _load_conversations()
    data['conversations'].append(conv)
    _save_conversations(data)
    return jsonify({'success': True, 'conversation': conv})


@bp.route('/api/conversations/<conv_id>', methods=['PATCH'])
def api_update_conversation(conv_id):
    body = request.get_json(silent=True) or {}
    data = _load_conversations()
    for conv in data['conversations']:
        if conv['id'] == conv_id:
            if 'name' in body:
                new_name = (body['name'] or '').strip()
                if not new_name:
                    return jsonify({'success': False, 'error': 'Name cannot be empty'}), 400
                conv['name'] = new_name
                conv['updated_at'] = datetime.now().isoformat()
            _save_conversations(data)
            return jsonify({'success': True, 'conversation': conv})
    return jsonify({'success': False, 'error': 'Not found'}), 404


@bp.route('/api/conversations/<conv_id>', methods=['DELETE'])
def api_delete_conversation(conv_id):
    data = _load_conversations()
    original_len = len(data['conversations'])
    data['conversations'] = [c for c in data['conversations'] if c['id'] != conv_id]
    if len(data['conversations']) == original_len:
        return jsonify({'success': False, 'error': 'Not found'}), 404
    _save_conversations(data)
    return jsonify({'success': True})


@bp.route('/api/conversations/<conv_id>/messages/<int:msg_index>', methods=['DELETE'])
def api_delete_message(conv_id, msg_index):
    data = _load_conversations()
    for conv in data['conversations']:
        if conv['id'] == conv_id:
            if 0 <= msg_index < len(conv['messages']):
                conv['messages'].pop(msg_index)
                conv['updated_at'] = datetime.now().isoformat()
                _save_conversations(data)
                return jsonify({'success': True})
            return jsonify({'success': False, 'error': 'Message index out of range'}), 400
    return jsonify({'success': False, 'error': 'Conversation not found'}), 404


@bp.route('/api/import-transcripts', methods=['POST'])
def api_import_transcripts():
    """Import unassigned transcript files into the most recent conversation."""
    data = _load_conversations()
    if not data['conversations']:
        return jsonify({'success': False, 'error': 'Create a conversation first'}), 400

    body = request.get_json(silent=True) or {}
    target_id = body.get('conversation_id')

    target = None
    if target_id:
        for conv in data['conversations']:
            if conv['id'] == target_id:
                target = conv
                break
    if not target:
        # Default to most recently updated
        target = max(data['conversations'], key=lambda c: c.get('updated_at', ''))

    unassigned = _get_unassigned_transcripts(data)
    imported_count = 0
    for fpath in unassigned:
        messages = _parse_transcript(fpath)
        for msg in messages:
            target['messages'].append(msg)
            imported_count += 1

    if imported_count > 0:
        target['updated_at'] = datetime.now().isoformat()
        _save_conversations(data)

    return jsonify({
        'success': True,
        'imported_count': imported_count,
        'files_processed': len(unassigned),
    })


@bp.route('/api/unassigned-count', methods=['GET'])
def api_unassigned_count():
    data = _load_conversations()
    unassigned = _get_unassigned_transcripts(data)
    return jsonify({'count': len(unassigned)})
