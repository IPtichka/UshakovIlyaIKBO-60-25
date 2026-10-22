@echo off
cd /d "%~dp0.."
py src/terminal.py --vfs-path ./data/otherBIG.json --startup-script ./startup/simple.txt
pause