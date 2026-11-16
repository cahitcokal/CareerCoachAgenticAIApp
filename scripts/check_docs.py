"""Check bilingual project Markdown structure and local file links."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {'.git', '.venv', 'venv', '.idea', 'node_modules', 'htmlcov', '__pycache__', '.agents', '.codex'}
BILINGUAL_EXEMPT_NAMES = {'readme.md', 'troubleshooting.md'}


def check():
    errors = []
    checked = 0
    for path in ROOT.rglob('*'):
        relative = path.relative_to(ROOT)
        if (path.suffix.lower() != '.md'
                or any(part in EXCLUDED_DIRS for part in relative.parts)):
            continue
        checked += 1
        text = path.read_text(encoding='utf-8')
        content = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        for heading in (() if path.name.lower() in BILINGUAL_EXEMPT_NAMES else ('## Türkçe', '## English')):
            if heading not in content.splitlines():
                errors.append(f'{relative}: missing {heading}')
        for link in re.findall(r'\]\(([^)]+)\)', content):
            target = link.strip().strip('<>').split('#', 1)[0]
            if not target or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', target):
                continue
            if not (path.parent / target).exists():
                errors.append(f'{relative}: missing linked file {target}')
    for error in errors:
        print(error)
    print(f'Checked {checked} Markdown files (README/troubleshooting exempt from bilingual headings only); {len(errors)} errors.')
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(check())
