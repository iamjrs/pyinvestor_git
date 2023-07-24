import sys

content = f'''home = {sys.exec_prefix}
include-system-site-packages = false
version = 3.7.4'''

with open('venv\\pyvenv.cfg', 'w') as f:
    f.write(content)
    f.close()