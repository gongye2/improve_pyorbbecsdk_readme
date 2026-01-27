$env:UV_LINK_MODE = "copy"
# ============================================================
# uv-optimized pyorbbecsdk2 build script (Windows)
# ============================================================

# ============================
# Global pre-run cleanup
# ============================

$GlobalBuildDir = Join-Path $PSScriptRoot "build"
$WheelDir = Join-Path $PSScriptRoot "wheel"

if (Test-Path $GlobalBuildDir) {
    Write-Host "Removing global build directory..."
    Remove-Item -Recurse -Force $GlobalBuildDir
}

if (Test-Path $WheelDir) {
    Write-Host "Removing wheel directory..."
    Remove-Item -Recurse -Force $WheelDir
}

New-Item -ItemType Directory -Force $WheelDir | Out-Null

# 1. Configuration
$PythonVersions = @("3.10")
$WheelDir = Join-Path $PSScriptRoot "wheel"
$InstallDir = Join-Path $PSScriptRoot "install"
# NOTE: This path must match what setup.py / pyproject expects
$InstallLibDir = Join-Path $InstallDir "lib\pyorbbecsdk"
$SharedDstDir = Join-Path $InstallLibDir "shared"

# 2. Initialize output directories
if (-not (Test-Path $WheelDir)) {
    New-Item -ItemType Directory -Force $WheelDir
}

foreach ($ver in $PythonVersions) {
    Write-Host "`n>>> Building pyorbbecsdk for Python $ver..." -ForegroundColor Cyan

    # --- Per-Python-version cleanup ---
    $BuildDir = Join-Path $PSScriptRoot "build_$ver"
    $GlobalBuildDir = Join-Path $PSScriptRoot "build"

    if (Test-Path $BuildDir) {
        Write-Host "Removing $BuildDir"
        Remove-Item -Recurse -Force $BuildDir
    }

    if (Test-Path $GlobalBuildDir) {
        Write-Host "Removing build directory"
        Remove-Item -Recurse -Force $GlobalBuildDir
    }

    if (Test-Path $InstallDir) {
        Write-Host "Removing install directory"
        Remove-Item -Recurse -Force $InstallDir
    }

    if (Test-Path "dist") {
        Write-Host "Removing dist directory"
        Remove-Item -Recurse -Force "dist"
    }

    # Recreate required directory structure
    New-Item -ItemType Directory -Force $BuildDir | Out-Null
    New-Item -ItemType Directory -Force $InstallLibDir | Out-Null
    New-Item -ItemType Directory -Force $SharedDstDir | Out-Null

    # --- 3. Resolve environment paths dynamically ---
    Write-Host "Resolving pybind11 CMake directory..."
    $pybind11_DIR = uv run --python $ver --with pybind11 python -c "import pybind11; print(pybind11.get_cmake_dir())"
    $python_EXE = uv python find $ver
    Write-Host "Using Python interpreter: $python_EXE"

    # --- 4. CMake configure and build ---
    Push-Location $BuildDir
    cmake -G "Visual Studio 17 2022" -A x64 `
          -DCMAKE_BUILD_TYPE=Release `
          -DPython3_EXECUTABLE="$python_EXE" `
          -Dpybind11_DIR="$pybind11_DIR" `
          -DCMAKE_INSTALL_PREFIX="$InstallDir" ..

    if ($LASTEXITCODE -ne 0) {
        throw "CMake configuration failed (Python $ver)"
    }

    # Build and run CMake install (installs .pyd into install directory)
    cmake --build . --config Release --target install --parallel
    Pop-Location

    # --- 5. Build wheel ---
    Write-Host "Building wheel package..."
    # --no-isolation ensures setuptools can see files prepared in install/
    uv build --wheel --python $ver --link-mode copy

    # Collect artifacts
    if (Test-Path "dist") {
        Get-ChildItem "dist\*.whl" | Copy-Item -Destination $WheelDir -Force
        Write-Host "Python $ver build succeeded: $(Get-ChildItem dist\*.whl | Select-Object -ExpandProperty Name)" -ForegroundColor Green
    }
}

Write-Host "`nAll builds completed. Wheels are located in: $WheelDir" -ForegroundColor Magenta

# ============================
# Final cleanup (keep wheel)
# ============================

Write-Host "`nStarting final cleanup of build artifacts..." -ForegroundColor Yellow

$CleanupDirs = @(
    "build",
    "dist",
    "install"
)

# Remove build_3.xx directories
Get-ChildItem -Path $PSScriptRoot -Directory -Filter "build_*" -ErrorAction SilentlyContinue |
    ForEach-Object {
        Write-Host "Deleting $($_.FullName)"
        Remove-Item -Recurse -Force $_.FullName
    }

foreach ($dir in $CleanupDirs) {
    $path = Join-Path $PSScriptRoot $dir
    if (Test-Path $path) {
        Write-Host "Deleting $path"
        Remove-Item -Recurse -Force $path
    }
}

# Remove setuptools egg-info directories generated during build
$SrcDir = Join-Path $PSScriptRoot "src"
if (Test-Path $SrcDir) {
    Get-ChildItem -Path $SrcDir -Directory -Filter "*.egg-info" -ErrorAction SilentlyContinue |
        ForEach-Object {
            Write-Host "Deleting egg-info directory $($_.FullName)"
            Remove-Item -Recurse -Force $_.FullName
        }
}

Write-Host "Final cleanup complete. Only the wheel directory is preserved." -ForegroundColor Green
