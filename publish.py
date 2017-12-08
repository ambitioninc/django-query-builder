import subprocess

subprocess.call(['rm', '-r', 'dist/'])
subprocess.call(['pip', 'install', 'wheel'])
subprocess.call(['pip', 'install', 'twine'])
subprocess.call(['python', 'setup.py', 'clean', '--all'])
subprocess.call(['python', 'setup.py', 'register', 'sdist', 'bdist_wheel'])
subprocess.call(['twine', 'upload', 'dist/*'])
subprocess.call(['rm', '-r', 'dist/'])
subprocess.call(['rm', '-r', 'build/'])
