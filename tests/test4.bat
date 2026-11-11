@echo off
setlocal
cd /d "%~dp0.."

echo === testfilter.json: A -^> {B, TEST_C}, B -^> {TEST_D, E}, E -^> F ===

call :run TEST
call :run _

del _test_filter.ini 2>nul
pause
endlocal
exit /b 0

:run
(
echo [app]
echo package_name = A
echo repository = C:\Users\ushak\Documents\KISproject\UshakovIlyaIKBO-60-25\testjsons\testfilter.json
echo repo_mode = file
echo max_depth = 5
echo filter_substring = %~1
) > _test_filter.ini

echo --- filter_substring = '%~1' ---
py main.py -c _test_filter.ini
echo exit code: %ERRORLEVEL%
echo.
exit /b 0