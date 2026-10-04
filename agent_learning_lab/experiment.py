import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from .tasks import ACTIONS, TRAIN, VALIDATION, TEST, task_input
from .store import Store


def attempt(backend, task, context, arm, split):
    start = time.perf_counter()
    error = None
    try:
        response = backend.solve(task, context, arm)
        if response.get('action') not in ACTIONS or not isinstance(response.get('reason'), str):
            raise ValueError('Malformed decision or action outside the allowlist')
    except (ValueError, RuntimeError) as exc:
        response = {'action': None, 'reason': '', 'usage': {}}
        error = str(exc)
    return {'task_id': task.id, 'family': task.family, 'arm': arm, 'split': split,
            'action': response.get('action'), 'reason': response.get('reason'),
            'expected': task.expected, 'success': response.get('action') == task.expected,
            'seconds': round(time.perf_counter() - start, 3), 'error': error,
            'usage': response.get('usage', {})}


def run(backend, output, repeats=1):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    run_id = str(uuid.uuid4())
    store = Store(output / 'memory.sqlite3')
    events, history, candidates = [], [], []
    try:
        for task in TRAIN:
            event = attempt(backend, task, [], 'fresh', 'train')
            events.append(event)
            history.append({'task': task_input(task), 'attempt': event['action'], 'feedback': task.reviewer})
            if event['error']:
                continue
            try:
                candidate = backend.reflect(task, event)
            except (ValueError, RuntimeError) as exc:
                events.append({'task_id': task.id, 'split': 'reflection', 'error': str(exc)})
                continue
            candidate.update(source_task=task.id, family=task.family)
            store.revision(run_id, task.id, 'candidate', candidate)
            candidates.append((task, candidate))

        # Promote only if the candidate passes its designated validation task.
        # This tiny gate is not evidence of broad correctness or novelty.
        for task, candidate in candidates:
            validation = next(t for t in VALIDATION if t.family == task.family)
            event = attempt(backend, validation, [candidate], 'lessons', 'validation')
            events.append(event)
            status = 'promoted' if event['success'] else 'rejected'
            store.revision(run_id, task.id, status, dict(candidate, validation_task=validation.id, validation_success=event['success']))

        lessons = store.active(run_id)
        rows = []
        for repeat in range(repeats):
            # Rotate execution order to reduce a fixed arm-order effect.
            arms = [('fresh', []), ('history', history), ('lessons', lessons)]
            arms = arms[repeat % 3:] + arms[:repeat % 3]
            for task in TEST:
                for arm, context in arms:
                    event = attempt(backend, task, context, arm, 'test')
                    event['repeat'] = repeat
                    rows.append(event)
                    events.append(event)
        summary = {}
        for arm in ('fresh', 'history', 'lessons'):
            group = [row for row in rows if row['arm'] == arm]
            summary[arm] = {'successes': sum(r['success'] for r in group), 'total': len(group),
                            'accuracy': sum(r['success'] for r in group) / len(group),
                            'errors': sum(r['error'] is not None for r in group),
                            'mean_seconds': sum(r['seconds'] for r in group) / len(group)}
        result = {'run_id': run_id, 'created_at': datetime.now(timezone.utc).isoformat(),
                  'backend': backend.name, 'model': backend.model,
                  'label': 'SCRIPTED WALKTHROUGH — NOT AI PERFORMANCE EVIDENCE' if backend.name.startswith('scripted') else 'LIVE LETTA PILOT — SMALL SYNTHETIC TASK SET',
                  'summary': summary, 'lessons': lessons, 'events': events,
                  'agent_ids': backend.agent_ids,
                  'limitations': ['Four synthetic test tasks; no confidence intervals.',
                                  'Single-task validation may accept overgeneralized lessons.',
                                  'Raw history and lessons have different token lengths.',
                                  'Choice-based diagnosis only; no patch generation or execution.',
                                  'No automatic lesson retirement or sleep-time learning yet.']}
        for event in events:
            store.attempt(run_id, event)
        (output / 'report.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        write_html(result, output / 'report.html')
        return result
    finally:
        store.close()


def write_html(result, path):
    from html import escape
    body = '<h1>Agent Learning Lab</h1><p class="label">' + escape(result['label']) + '</p>'
    body += '<p>Model: ' + escape(result['model']) + '</p><h2>Held-out diagnosis results</h2><table><tr><th>Configuration</th><th>Correct</th><th>Errors</th><th>Mean seconds</th></tr>'
    for arm, stats in result['summary'].items():
        body += f'<tr><td>{escape(arm)}</td><td>{stats["successes"]}/{stats["total"]}</td><td>{stats["errors"]}</td><td>{stats["mean_seconds"]:.3f}</td></tr>'
    body += '</table><h2>Promoted lessons</h2>'
    for lesson in result['lessons']:
        body += '<article><b>' + escape(lesson['lesson']) + '</b><p>' + escape(lesson['scope']) + '</p><small>Source: ' + escape(lesson['source_task']) + '</small></article>'
    body += '<h2>Decision audit</h2><table><tr><th>Task</th><th>Configuration</th><th>Action</th><th>Outcome / error</th></tr>'
    for event in result['events']:
        if event.get('split') == 'test':
            body += '<tr>' + ''.join('<td>' + escape(str(value)) + '</td>' for value in (event['task_id'], event['arm'], event['action'], event['error'] or ('correct' if event['success'] else 'incorrect'))) + '</tr>'
    body += '</table><h2>Limits</h2><ul>' + ''.join('<li>' + escape(item) + '</li>' for item in result['limitations']) + '</ul>'
    path.write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Agent Learning Lab</title><style>body{font:16px system-ui;background:#0b1626;color:#e4ecf5;max-width:1000px;margin:40px auto;padding:24px}h1{color:#59dec8}table{border-collapse:collapse;width:100%;margin-bottom:30px}td,th{text-align:left;padding:12px;border-bottom:1px solid #334155}article{padding:18px;background:#15283d;margin:12px 0;border-radius:12px}.label{color:#ffd180;font-weight:bold}</style>' + body + '</html>', encoding='utf-8')
