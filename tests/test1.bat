@echo off
setlocal
cd /d "%~dp0.."

(
echo [app]
echo package_name = A
echo repository = C:\Users\ushak\Documents\KISproject\UshakovIlyaIKBO-60-25\testjsons\testrep.json
echo repo_mode = file
echo max_depth = 5
echo filter_substring = _
) > _test_simple.ini

echo === testrep.json: A -^> B, A -^> C, B -^> D, C -^> D, D -^> E ===
py main.py -c _test_simple.ini
echo exit code: %ERRORLEVEL%

del _test_simple.ini
endlocal