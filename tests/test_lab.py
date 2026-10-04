import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from agent_learning_lab.backends import LettaBackend, ScriptedBackend, parse_object
from agent_learning_lab.experiment import run, attempt
from agent_learning_lab.store import Store
from agent_learning_lab.tasks import TRAIN, TEST, task_input

class LabTests(unittest.TestCase):
    def test_task_prompt_has_no_answer_key(self):
        for task in TRAIN + TEST:
            payload = task_input(task)
            self.assertNotIn('expected', payload)
            self.assertNotIn('reviewer', payload)
            self.assertNotIn('family', payload)

    def test_revision_rejection_and_retirement(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Store(Path(directory) / 'test.sqlite3')
            store.revision('run', 'lesson', 'candidate', {'lesson': 'test'})
            self.assertEqual([], store.active('run'))
            store.revision('run', 'lesson', 'promoted', {'lesson': 'test'})
            self.assertEqual(1, len(store.active('run')))
            store.revision('run', 'lesson', 'retired', {'reason': 'counterexample'})
            self.assertEqual([], store.active('run'))
            self.assertEqual([], store.active('other-run'))
            store.close()

    def test_walkthrough_report_and_split_integrity(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run(ScriptedBackend(), directory, 2)
            self.assertIn('NOT AI PERFORMANCE', result['label'])
            self.assertEqual(8, result['summary']['lessons']['total'])
            self.assertEqual(3, len(result['lessons']))
            self.assertTrue(Path(directory, 'report.html').exists())
            saved = json.loads(Path(directory, 'report.json').read_text())
            self.assertEqual(result['run_id'], saved['run_id'])
            self.assertTrue(all(x['source_task'].startswith('train-') for x in result['lessons']))

    def test_bad_agent_action_is_failure(self):
        class Bad(ScriptedBackend):
            def solve(self, *args):
                return {'action': 'delete_database', 'reason': 'bad'}
        row = attempt(Bad(), TEST[0], [], 'fresh', 'test')
        self.assertFalse(row['success'])
        self.assertIsNotNone(row['error'])

    def test_failed_validation_never_promotes(self):
        class FailsValidation(ScriptedBackend):
            def solve(self, task, *args):
                if task.id.startswith('val-'):
                    return {'action': 'retry_auth', 'reason': 'wrong'}
                return super().solve(task, *args)
        with tempfile.TemporaryDirectory() as directory:
            # All incorrect validation decisions must reject their candidate lessons.
            result = run(FailsValidation(), directory)
            self.assertEqual([], result['lessons'])

    def test_live_contract_fresh_agent_and_no_expected(self):
        with patch.dict('os.environ', {'LETTA_API_KEY': 'test-only'}, clear=True):
            backend = LettaBackend()
        calls = []
        def request(method, path, payload):
            calls.append((method, path, payload))
            if path == '/agents':
                return {'id': 'agent-test-' + str(len(calls))}
            return {'messages': [{'message_type': 'assistant_message', 'content': '{"action":"await_completion","reason":"Wait for future"}'}], 'usage': {'total_tokens': 100}}
        backend.request = request
        for _ in range(2):
            result = backend.solve(TEST[0], [{'lesson': 'test'}], 'lessons')
            self.assertEqual('await_completion', result['action'])
        self.assertEqual(2, len(backend.agent_ids))
        self.assertNotEqual(*backend.agent_ids)
        for _, path, payload in calls:
            if path == '/agents':
                self.assertTrue(payload['memory_blocks'][-1]['read_only'])
                self.assertFalse(payload['include_base_tools'])
            else:
                self.assertNotIn('expected', json.loads(payload['input']))

    def test_json_parser_and_html_escape(self):
        self.assertEqual({'action': 'x'}, parse_object('```json\n{"action":"x"}\n```'))
        for invalid in ('[]', 'not json', '{"action":"x"} trailing'):
            with self.assertRaises((ValueError, json.JSONDecodeError)):
                parse_object(invalid)
        class Markup(ScriptedBackend):
            def reflect(self, *args):
                return {'lesson': '<script>alert(1)</script>', 'scope': 'test'}
        with tempfile.TemporaryDirectory() as directory:
            run(Markup(), directory)
            html = Path(directory, 'report.html').read_text()
            self.assertNotIn('<script>', html)
            self.assertIn('&lt;script&gt;', html)

if __name__ == '__main__':
    unittest.main()
