@echo off
rem Builds the mod's code for RimWorld 1.5 and 1.6: 1.5\Assemblies\IsoRim.dll and 1.6\Assemblies\IsoRim.dll.
rem Needs the free .NET SDK and an internet connection the first time.
cd /d "%~dp0Source"

where dotnet >nul 2>nul
if errorlevel 1 (
  echo The .NET SDK is not installed.
  echo Download ".NET SDK" from https://dotnet.microsoft.com/download , install it, then run this file again.
  pause
  exit /b 1
)

rem An old single build at the top would be loaded by both game versions: remove it.
if exist "..\Assemblies" rmdir /s /q "..\Assemblies"
if exist "obj" rmdir /s /q "obj"

for %%V in (1.6 1.5) do (
  echo.
  echo ===== Building for RimWorld %%V =====
  dotnet build -c Release -nologo -p:RimWorldVersion=%%V
  if errorlevel 1 (
    echo.
    echo BUILD FAILED for RimWorld %%V. See the errors above.
    pause
    exit /b 1
  )
)

echo.
echo Done. 1.5\Assemblies and 1.6\Assemblies are ready. Start RimWorld and enable the mod.
pause
