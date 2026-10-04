"""Synthetic diagnosis tasks. Answer keys are never sent in task prompts."""
from dataclasses import dataclass

ACTIONS = ('await_completion', 'increase_timeout', 'idempotency_key', 'increase_retries', 'refresh_credentials', 'retry_auth')

@dataclass(frozen=True)
class Task:
    id: str
    family: str
    prompt: str
    expected: str
    reviewer: str

TRAIN = [
    Task('train-async', 'async', 'A job test reads output before the future finishes. The operation normally completes quickly. Choose the best first fix.', 'await_completion', 'Wait for the completion signal before asserting; extending the timeout does not establish completion.'),
    Task('train-retry', 'retry', 'A payment request commits, its response is lost, and the client retries. Two charges appear. Choose the best first fix.', 'idempotency_key', 'Use a stable idempotency key across retries to prevent duplicate effects.'),
    Task('train-auth', 'auth', 'Requests return 401 after the access token has expired. Repeating the unchanged request fails. Choose the best first fix.', 'refresh_credentials', 'Refresh expired credentials before repeating the request.'),
]
VALIDATION = [
    Task('val-async', 'async', 'A background export test checks the file immediately after scheduling. The export takes 20 ms. The test already has a 5 second deadline.', 'await_completion', ''),
    Task('val-retry', 'retry', 'A webhook handler repeats a committed database update when an acknowledgment is lost, doubling a counter.', 'idempotency_key', ''),
    Task('val-auth', 'auth', 'An API call uses yesterday\'s expired bearer token and receives 401 on every attempt.', 'refresh_credentials', ''),
]
TEST = [
    Task('test-async-transfer', 'async', 'An index rebuild returns a future. A test reads the index immediately and sees the old data. The rebuild completes within the existing deadline.', 'await_completion', ''),
    Task('test-async-exception', 'async', 'A test correctly awaits completion but its configured 10 ms deadline is shorter than the documented normal 100 ms execution time. No missing completion signal exists.', 'increase_timeout', ''),
    Task('test-retry-transfer', 'retry', 'A provisioning request succeeds, but the reply is lost. Retrying creates a second resource for the same logical operation.', 'idempotency_key', ''),
    Task('test-auth-transfer', 'auth', 'A worker repeatedly gets 401 with an expired token. Network connectivity and permissions are otherwise healthy.', 'refresh_credentials', ''),
]

def task_input(task):
    return {'task_id': task.id, 'problem': task.prompt, 'allowed_actions': list(ACTIONS)}
