import subprocess

subprocess.call(['pip', 'install', 'wheel'])
subprocess.call(['python', 'setup.py', 'clean', '--all'])
subprocess.call(['python', 'setup.py', 'register', 'sdist', 'bdist_wheel', 'upload'])
