@echo off
rem Copies what players need into ..\IsoRim_Release, ready to upload to the Steam Workshop.
rem Run build.bat first.
cd /d "%~dp0"
if not exist 1.6\Assemblies\IsoRim.dll (
  echo 1.6\Assemblies\IsoRim.dll is missing: run build.bat first.
  pause
  exit /b 1
)
set OUT=..\IsoRim_Release
if exist "%OUT%" rmdir /s /q "%OUT%"
mkdir "%OUT%"
for %%D in (About 1.5 1.6 Defs Models Textures LUTs Shaders) do xcopy /e /i /q "%%D" "%OUT%\%%D" >nul
copy README.txt "%OUT%" >nul
copy LICENSE.txt "%OUT%" >nul 2>nul
echo Done: %OUT%
pause
