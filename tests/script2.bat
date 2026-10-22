@echo off
cd /d "%~dp0.."
py src/terminal.py --config config.xml --vfs-path ./data/other.json
pause