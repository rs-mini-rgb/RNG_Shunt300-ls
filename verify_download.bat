@echo off
REM Verify RNG Shunt300 Live Simulator Download Integrity
REM Place this script in the same folder as your downloaded files

setlocal enabledelayedexpansion
cls

echo.
echo ================================================
echo   RNG Shunt300 LS - Download Verification
echo ================================================
echo.

set "SETUP_HASH=3983151A8AFA6D6A2113120FFD1CF0DFF15B0CD6A2BBD933F36C2485EEFD5940"
set "ZIP_HASH=6A86B98A5C9C4FDBC6CFF8FE8C5250CA37FF3131A7F2FBB4609E28736DF793B0"

REM Check for Setup.exe
if exist "Renogy_Shunt300LS_Setup.exe" (
    echo Checking: Renogy_Shunt300LS_Setup.exe
    for /f "tokens=*" %%A in ('certutil -hashfile "Renogy_Shunt300LS_Setup.exe" SHA256 ^| findstr /v "SHA256"') do (
        set "ACTUAL_SETUP=%%A"
    )
    
    REM Remove spaces from hash
    for /f "tokens=*" %%A in ('echo !ACTUAL_SETUP!') do set "ACTUAL_SETUP=%%A"
    
    if /i "!ACTUAL_SETUP!"=="!SETUP_HASH!" (
        echo [PASS] Setup.exe hash is valid
        echo.
    ) else (
        echo [FAIL] Setup.exe hash does not match!
        echo Expected: !SETUP_HASH!
        echo Actual:   !ACTUAL_SETUP!
        echo.
        echo WARNING: Do not run this file!
        echo.
    )
) else (
    echo Setup.exe not found
    echo.
)

REM Check for Portable.zip
if exist "Renogy_Shunt300LS_Portable.zip" (
    echo Checking: Renogy_Shunt300LS_Portable.zip
    for /f "tokens=*" %%A in ('certutil -hashfile "Renogy_Shunt300LS_Portable.zip" SHA256 ^| findstr /v "SHA256"') do (
        set "ACTUAL_ZIP=%%A"
    )
    
    REM Remove spaces from hash
    for /f "tokens=*" %%A in ('echo !ACTUAL_ZIP!') do set "ACTUAL_ZIP=%%A"
    
    if /i "!ACTUAL_ZIP!"=="!ZIP_HASH!" (
        echo [PASS] Portable.zip hash is valid
        echo.
    ) else (
        echo [FAIL] Portable.zip hash does not match!
        echo Expected: !ZIP_HASH!
        echo Actual:   !ACTUAL_ZIP!
        echo.
        echo WARNING: Do not use this file!
        echo.
    )
) else (
    echo Portable.zip not found
    echo.
)

echo ================================================
echo Verification complete
echo ================================================
echo.
pause
