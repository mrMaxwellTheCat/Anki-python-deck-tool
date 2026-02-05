# PowerShell script to install anki-yaml-tool system-wide on Windows
# This script copies the built executable to a user directory and adds it to PATH

$ErrorActionPreference = "Stop"

# Define installation directory
$InstallDir = "$env:LOCALAPPDATA\Programs\anki-yaml-tool"
$ExeName = "anki-yaml-tool.exe"

# Get the project root directory (parent of scripts)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$DistDir = Join-Path $ProjectRoot "dist"
$ExePath = Join-Path $DistDir $ExeName

Write-Host "==================================="
Write-Host "Anki YAML Tool System-Wide Installer"
Write-Host "==================================="
Write-Host ""

# Check if executable exists
if (-not (Test-Path $ExePath)) {
    Write-Host "Error: Executable not found at: $ExePath" -ForegroundColor Red
    Write-Host "Please build the executable first using: make build-exe" -ForegroundColor Yellow
    Write-Host "Or run the VS Code task: 'Build Executable (Local)'" -ForegroundColor Yellow
    exit 1
}

Write-Host "Found executable: $ExePath" -ForegroundColor Green

# Create installation directory if it doesn't exist
if (-not (Test-Path $InstallDir)) {
    Write-Host "Creating installation directory: $InstallDir"
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}

# Copy executable to installation directory
Write-Host "Copying executable to: $InstallDir"
Copy-Item -Path $ExePath -Destination (Join-Path $InstallDir $ExeName) -Force

# Check if directory is in PATH
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
$PathsArray = $UserPath -split ";"

if ($PathsArray -notcontains $InstallDir) {
    Write-Host ""
    Write-Host "Adding installation directory to user PATH..." -ForegroundColor Yellow

    # Add to user PATH
    $NewPath = "$UserPath;$InstallDir"
    [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")

    Write-Host "PATH updated successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "IMPORTANT: You need to restart your terminal for PATH changes to take effect." -ForegroundColor Cyan
    Write-Host "After restarting, you can run 'anki-yaml-tool' from anywhere." -ForegroundColor Cyan
}
else {
    Write-Host ""
    Write-Host "Installation directory is already in PATH." -ForegroundColor Green
    Write-Host "You can now run 'anki-yaml-tool' from anywhere!" -ForegroundColor Green
}

Write-Host ""
Write-Host "==================================="
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "==================================="
Write-Host ""
Write-Host "Executable location: $InstallDir\$ExeName"
Write-Host ""
Write-Host "To test, open a NEW terminal and run:"
Write-Host "  anki-yaml-tool --help" -ForegroundColor Cyan
Write-Host ""
