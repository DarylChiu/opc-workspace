#!/usr/bin/env python3
"""
Gosh Remote Dispatch Server
Receives commands from mobile → writes structured task files → Agents pick up on desktop
"""
import json, os, time, glob
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='static')
TASKS_DIR = os.path.dirname(os.path.abspath(__file__)) + '/tasks'
REPORTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/reports'

AGENT_CONFIG = {
    'balance': {'name': '算点小账', 'color': '#50a0ff', 'dir': f'{TASKS_DIR}/balance'},
    'self':    {'name': '恨点小己', 'color': '#ffaa50', 'dir': f'{TASKS_DIR}/self'},
    'yueyu':   {'name': '乐语',     'color': '#dc64b4', 'dir': f'{TASKS_DIR}/yueyu'},
    'gosh':    {'name': '搞点小事', 'color': '#888',     'dir': f'{TASKS_DIR}/gosh'},
}

# Ensure task dirs exist
for cfg in AGENT_CONFIG.values():
    os.makedirs(cfg['dir'], exist_ok=True)


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/api/agents')
def list_agents():
    """Return agent list with pending task counts"""
    result = []
    for key, cfg in AGENT_CONFIG.items():
        pending = glob.glob(f"{cfg['dir']}/*.json")
        result.append({
            'key': key,
            'name': cfg['name'],
            'color': cfg['color'],
            'pending': len(pending),
        })
    return jsonify({'agents': result})


@app.route('/api/dispatch', methods=['POST'])
def dispatch():
    """Receive a task → write to Agent's task directory"""
    data = request.get_json()
    agent = data.get('agent', '').strip()
    content = data.get('content', '').strip()

    if not agent or agent not in AGENT_CONFIG:
        return jsonify({'ok': False, 'error': f'Unknown agent: {agent}'}), 400
    if not content:
        return jsonify({'ok': False, 'error': 'Content is required'}), 400

    ts = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    filename = f"{ts}.json"
    filepath = os.path.join(AGENT_CONFIG[agent]['dir'], filename)

    task = {
        'agent': agent,
        'agent_name': AGENT_CONFIG[agent]['name'],
        'dispatched_at': datetime.now().isoformat(),
        'content': content,
        'status': 'pending',
        'dispatched_by': 'Gosh (via mobile)',
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(task, f, ensure_ascii=False, indent=2)

    return jsonify({'ok': True, 'task_id': ts, 'file': filename})


@app.route('/api/queue/<agent>')
def agent_queue(agent):
    """List pending tasks for a specific agent"""
    if agent not in AGENT_CONFIG:
        return jsonify({'ok': False, 'error': f'Unknown agent: {agent}'}), 400

    tasks = []
    for f in sorted(glob.glob(f"{AGENT_CONFIG[agent]['dir']}/*.json"), reverse=True):
        try:
            with open(f, encoding='utf-8') as fh:
                t = json.load(fh)
            t['file'] = os.path.basename(f)
            tasks.append(t)
        except:
            pass

    return jsonify({'agent': agent, 'agent_name': AGENT_CONFIG[agent]['name'], 'tasks': tasks})


@app.route('/api/queue')
def all_queues():
    """Show all pending tasks across all agents"""
    all_tasks = []
    for key, cfg in AGENT_CONFIG.items():
        for f in sorted(glob.glob(f"{cfg['dir']}/*.json"), reverse=True):
            try:
                with open(f, encoding='utf-8') as fh:
                    t = json.load(fh)
                t['agent_key'] = key
                t['file'] = os.path.basename(f)
                all_tasks.append(t)
            except:
                pass
    all_tasks.sort(key=lambda t: t.get('dispatched_at', ''), reverse=True)
    return jsonify({'tasks': all_tasks})


@app.route('/api/task/<agent>/<task_id>', methods=['DELETE'])
def complete_task(agent, task_id):
    """Mark a task as completed (delete the file)"""
    if agent not in AGENT_CONFIG:
        return jsonify({'ok': False}), 400
    filepath = os.path.join(AGENT_CONFIG[agent]['dir'], f"{task_id}.json")
    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({'ok': True, 'action': 'deleted'})
    return jsonify({'ok': False, 'error': 'Not found'}), 404


if __name__ == '__main__':
    print('Gosh Dispatch Server starting on http://0.0.0.0:8766')
    app.run(host='0.0.0.0', port=8766, debug=False)
