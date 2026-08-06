"""Deploy helper: temporarily move excluded dirs out, run wrangler, move back.

Workaround for wrangler 4.114 .assetsignore bug where .assetsignore patterns
don't reliably exclude new directories (caught 2026-07-28: the internal-tools/
directory added the same day was deployed despite multiple .assetsignore
patterns including `internal-tools/`, `**/internal-tools/`, etc.).

Strategy:
  1. Move excluded directories to tmp/_excluded_<timestamp>/
  2. Run wrangler deploy
  3. Move them back

This guarantees the assets uploaded to CF Pages never include
internal-tools, qa/, scripts/, tmp/, etc., regardless of .assetsignore
parsing behavior.
"""
import shutil
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path('.')
EXCLUDED_DIRS = ['internal-tools', 'qa', 'scripts', 'tmp', '__pycache__', 'docs']
BACKUP_ROOT = None

def move_out():
    global BACKUP_ROOT
    ts = time.strftime('%Y%m%d_%H%M%S')
    # Backup goes OUTSIDE the project tree to avoid the self-move bug
    # when 'tmp' is in EXCLUDED_DIRS. Use the user's home directory.
    home = Path.home()
    backup = home / f'.weddingai_deploy_exclude_{ts}'
    backup.mkdir(parents=True, exist_ok=True)
    BACKUP_ROOT = backup
    moved = []
    for d in EXCLUDED_DIRS:
        src = ROOT / d
        if src.exists():
            dst = backup / d
            shutil.move(str(src), str(dst))
            moved.append(d)
    print(f'Moved out: {moved}')

def move_back():
    if BACKUP_ROOT is None:
        return
    moved = []
    for d in EXCLUDED_DIRS:
        src = BACKUP_ROOT / d
        if src.exists():
            dst = ROOT / d
            if dst.exists():
                # Restore one level at a time, merging if needed
                for child in src.iterdir():
                    target = dst / child.name
                    if target.exists():
                        # Merge: move into target
                        if child.is_dir():
                            for sub in child.iterdir():
                                shutil.move(str(sub), str(target / sub.name))
                            child.rmdir()
                        else:
                            child.unlink()
                    else:
                        shutil.move(str(child), str(target))
                src.rmdir()
            else:
                shutil.move(str(src), str(dst))
            moved.append(d)
    BACKUP_ROOT.rmdir()
    print(f'Moved back: {moved}')

if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in ('deploy', 'restore'):
        print('Usage: deploy.py [deploy|restore]')
        sys.exit(1)
    if sys.argv[1] == 'deploy':
        move_out()
        try:
            # On Windows, Python's subprocess.run(['npx', ...]) with shell=False
            # fails because CreateProcess doesn't search PATH for the .cmd
            # extension. Use npx.cmd explicitly. On non-Windows, npx works
            # without the extension.
            npx_cmd = 'npx.cmd' if sys.platform == 'win32' else 'npx'
            r = subprocess.run([
                npx_cmd, '--yes', 'wrangler@4.114', 'pages', 'deploy', '.',
                '--project-name=weddingai-video', '--commit-dirty=true'
            ], shell=False)
            sys.exit(r.returncode)
        finally:
            move_back()
    elif sys.argv[1] == 'restore':
        # Manual restore in case deploy failed mid-flight
        move_back()
