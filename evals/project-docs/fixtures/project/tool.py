"""Small standard-library CLI used as documentation evidence."""
import argparse
import json
from pathlib import Path


class Runner:
    def __init__(self, batch_size=8):
        if isinstance(batch_size, bool) or not isinstance(batch_size, int) or batch_size <= 0:
            raise ValueError('batch_size must be a positive integer')
        self.batch_size = batch_size

    @classmethod
    def from_config(cls, config):
        if set(config) - {'batch_size'}:
            raise ValueError('unknown configuration field')
        return cls(batch_size=config.get('batch_size', 16))

    def summarize(self, rows):
        count = len(rows)
        return {'rows': count, 'batch_size': self.batch_size,
                'batches': (count + self.batch_size - 1) // self.batch_size}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output-dir', type=Path, default=Path('results'))
    parser.add_argument('--config', type=Path)
    parser.add_argument('--batch-size', type=int)
    parser.add_argument('--backend', choices=('cpu',), default='cpu')
    args = parser.parse_args(argv)
    config = json.loads(args.config.read_text()) if args.config else {}
    if args.batch_size is not None:
        config['batch_size'] = args.batch_size
    runner = Runner.from_config(config)
    report = runner.summarize(json.loads(args.input.read_text()))
    report['backend'] = args.backend
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / 'report.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(f'Completed: {output}')


if __name__ == '__main__':
    main()
