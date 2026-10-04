import argparse
from .backends import ScriptedBackend, LettaBackend
from .experiment import run


def main():
    parser = argparse.ArgumentParser(description='Controlled experience-to-memory experiment')
    parser.add_argument('--backend', choices=['scripted', 'letta'], default='scripted')
    parser.add_argument('--output', default='results/demo')
    parser.add_argument('--repeats', type=int, default=1)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error('--repeats must be at least 1')
    try:
        backend = LettaBackend() if args.backend == 'letta' else ScriptedBackend()
        result = run(backend, args.output, args.repeats)
    except (ValueError, RuntimeError) as exc:
        parser.exit(1, str(exc) + '\n')
    print(result['label'])
    for arm, stats in result['summary'].items():
        print(f'{arm}: {stats["successes"]}/{stats["total"]} correct; {stats["errors"]} errors')
    print(f'Report: {args.output}/report.html')
    if backend.agent_ids:
        print(f'{len(backend.agent_ids)} Letta agents created; IDs recorded in report.json. Agents remain on the server for inspection.')

if __name__ == '__main__':
    main()
