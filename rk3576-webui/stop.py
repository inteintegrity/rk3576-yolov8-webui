"""Stop only the process recorded for this application."""
from pathlib import Path
import os, signal
root=Path(__file__).resolve().parent
pid=int((root/'server.pid').read_text())
cmd=Path(f'/proc/{pid}/cmdline').read_bytes()
cwd=Path(f'/proc/{pid}/cwd').resolve()
if b'server.py' not in cmd or cwd!=root:
    raise RuntimeError('PID does not belong to this application; refusing to stop it')
os.kill(pid,signal.SIGTERM)
(root/'server.pid').unlink()
print('WebUI server stopped. Allow any current worker to finish before restarting.')
