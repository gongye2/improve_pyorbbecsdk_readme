#!/usr/bin/env pwsh
#Requires -Version 5.1
<#
.SYNOPSIS
    uv-optimized pyorbbecsdk2 build script (Windows)

.DESCRIPTION
    Build pyorbbecsdk wheel packages for specified Python versions using uv.

.PARAMETER Version
    Python version(s) to build (e.g., "3.10", "3.11"). Use "all" for 3.8-3.13.

.PARAMETER Offline
    Offline mode, skip network downloads (requires local pybind11 in venv).

.PARAMETER NoClean
    Don't clean build directories before building.

.PARAMETER Clean
    Clean build directories before building (default).

.PARAMETER CleanOnly
    Only clean, don't build.

.PARAMETER Yes
    Automatically confirm all cleanup prompts (skip interactive mode).

.EXAMPLE
    .\build-whl-uv.ps1 3.10
    # Build for Python 3.10

.EXAMPLE
    .\build-whl-uv.ps1 3.8, 3.9, 3.10
    # Build for multiple Python versions

.EXAMPLE
    .\build-whl-uv.ps1 all
    # Build all supported versions (3.8-3.13)

.EXAMPLE
    .\build-whl-uv.ps1 3.10 -Offline
    # Offline build (requires local venv with pybind11)

.EXAMPLE
    .\build-whl-uv.ps1 -CleanOnly
    # Clean only, don't build

.EXAMPLE
    .\build-whl-uv.ps1 all -Yes
    # Build all versions, auto-confirm all cleanups
#>

[CmdletBinding()]
param(
    [Parameter(Position = 0, ValueFromRemainingArguments = $true)]
    [string[]]$Version = @(),

    [switch]$Offline,

    [switch]$NoClean,

    [switch]$Clean,

    [switch]$CleanOnly,

    [switch]$Yes
)

$ErrorActionPreference = "Stop"

# ============================================================
# Global variables for tracking cleanup failures
# ============================================================

$script:CleanupFailed = @()
$script:CleanupSkipped = @()
$script:AutoConfirm = $Yes.IsPresent

# ============================================================
# Configuration
# ============================================================

$env:UV_LINK_MODE = "copy"

if ($Offline) {
    $env:UV_OFFLINE = "1"
}

$ROOT_DIR = $PSScriptRoot

# Build options
$OFFLINE_MODE = $Offline.IsPresent
$CLEAN_BUILD = if ($NoClean.IsPresent) { $false } else { $true }
$CLEAN_ONLY = $CleanOnly.IsPresent

# Directory paths
$WHEEL_DIR = Join-Path $ROOT_DIR "wheel"
$INSTALL_DIR = Join-Path $ROOT_DIR "install"
$INSTALL_LIB_DIR = Join-Path $INSTALL_DIR "lib\pyorbbecsdk"
$SHARED_DST_DIR = Join-Path $INSTALL_LIB_DIR "shared"
$ENV_SETUP_SRC = Join-Path $ROOT_DIR "scripts\env_setup"

# Parse Python versions
$PYTHON_VERSIONS = @()
foreach ($v in $Version) {
    switch -Wildcard ($v) {
        "all" {
            $PYTHON_VERSIONS = @("3.8", "3.9", "3.10", "3.11", "3.12", "3.13")
        }
        "3.*" {
            $PYTHON_VERSIONS += $v
        }
        default {
            if ($v -match '^3\.\d+$') {
                $PYTHON_VERSIONS += $v
            } else {
                Write-Error "Unknown option or version: $v"
                exit 1
            }
        }
    }
}

# Default to 3.10 if no versions specified
if ($PYTHON_VERSIONS.Count -eq 0) {
    $PYTHON_VERSIONS = @("3.10")
}

# ============================================================
# Helper Functions
# ============================================================

function Show-Usage {
    @"
Usage: $(Split-Path -Leaf $PSCommandPath) [OPTIONS] [VERSION...]

Build pyorbbecsdk wheel packages for specified Python versions.

Options:
  -Offline        Offline mode, skip network downloads (requires local pybind11)
  -NoClean        Don't clean build directories before building
  -Clean          Clean build directories before building (default)
  -CleanOnly      Only clean, don't build
  -Yes            Auto-confirm all cleanup prompts (non-interactive)
  -?, -Help       Show this help message

Arguments:
  VERSION         Python version (e.g., 3.10, 3.11) or 'all' for 3.8-3.13

Examples:
  $(Split-Path -Leaf $PSCommandPath) 3.10              # Build Python 3.10
  $(Split-Path -Leaf $PSCommandPath) 3.8, 3.9, 3.10    # Build multiple versions
  $(Split-Path -Leaf $PSCommandPath) all               # Build all versions (3.8-3.13)
  $(Split-Path -Leaf $PSCommandPath) 3.10 -Offline     # Offline build
  $(Split-Path -Leaf $PSCommandPath) -CleanOnly        # Clean only, don't build
  $(Split-Path -Leaf $PSCommandPath) all -Yes          # Auto-confirm cleanups
"@ | Write-Host
}

# Show help if requested
if ($Version -contains "-?" -or $Version -contains "-Help" -or $Version -contains "--help" -or $Version -contains "-h") {
    Show-Usage
    exit 0
}

# Remove a directory with error handling, returns $true if success or not exists
function Remove-DirectorySafe {
    param(
        [string]$Path,
        [string]$Name
    )

    if (-not (Test-Path $Path)) {
        return $true
    }

    try {
        Remove-Item -Recurse -Force $Path -ErrorAction Stop
        Write-Host "    Deleted: $Name"
        return $true
    }
    catch {
        Write-Warning "    Failed to delete: $Name - $($_.Exception.Message)"
        $script:CleanupFailed += "$Name ($Path)"
        return $false
    }
}

# Confirm deletion interactively
function Confirm-Delete {
    param(
        [string]$Path,
        [string]$Name
    )

    if (-not (Test-Path $Path)) {
        return $true
    }

    Write-Host -NoNewline "  Found: $Name - delete? (y=yes/n=no/a=all/s=skip-all): "
    $response = Read-Host

    switch ($response.ToLower()) {
        "y" {
            return (Remove-DirectorySafe -Path $Path -Name $Name)
        }
        "a" {
            $script:AutoConfirm = $true
            return (Remove-DirectorySafe -Path $Path -Name $Name)
        }
        "s" {
            Write-Host "    Skipped: $Name"
            $script:CleanupSkipped += "$Name ($Path)"
            return $false
        }
        default {
            Write-Host "    Skipped: $Name"
            $script:CleanupSkipped += "$Name ($Path)"
            return $false
        }
    }
}

function Invoke-InteractiveCleanup {
    Write-Host ">>> Checking for existing build artifacts to clean"
    Write-Host ""

    # Collect paths to check
    $pathsToCheck = @(
        @{ Path = (Join-Path $ROOT_DIR "build"); Name = "build directory" },
        @{ Path = (Join-Path $ROOT_DIR "dist"); Name = "dist directory" },
        @{ Path = (Join-Path $ROOT_DIR "install"); Name = "install directory" },
        @{ Path = $WHEEL_DIR; Name = "wheel directory" }
    )

    # Check for build_* directories
    Get-ChildItem -Path $ROOT_DIR -Directory -Filter "build_*" -ErrorAction SilentlyContinue | ForEach-Object {
        $pathsToCheck += @{ Path = $_.FullName; Name = "$($_.Name) directory" }
    }

    # Check if anything exists
    $hasItems = $false
    foreach ($item in $pathsToCheck) {
        if (Test-Path $item.Path) {
            $hasItems = $true
            break
        }
    }

    if (-not $hasItems) {
        Write-Host "  No build artifacts found, nothing to clean."
        Write-Host ""
        New-Item -ItemType Directory -Force $WHEEL_DIR | Out-Null
        return
    }

    # Process each path
    $skipAll = $false
    foreach ($item in $pathsToCheck) {
        $path = $item.Path
        $name = $item.Name

        if ($skipAll) {
            Write-Host "  Skipped: $name"
            $script:CleanupSkipped += "$name ($path)"
            continue
        }

        if ($script:AutoConfirm) {
            Remove-DirectorySafe -Path $path -Name $name | Out-Null
        }
        else {
            $result = Confirm-Delete -Path $path -Name $name
            if (-not $result -and -not $script:AutoConfirm) {
                # User chose skip-all
                $skipAll = $true
            }
        }
    }

    Write-Host ""
    New-Item -ItemType Directory -Force $WHEEL_DIR | Out-Null
}

function Invoke-PerVersionCleanup {
    param([string]$PyVer)

    $buildDir = Join-Path $ROOT_DIR "build_$PyVer"
    $distDir = Join-Path $ROOT_DIR "dist"

    Write-Host "  Cleaning build artifacts for Python $PyVer..."

    Remove-DirectorySafe -Path $buildDir -Name "build_$PyVer directory" | Out-Null
    Remove-DirectorySafe -Path $INSTALL_DIR -Name "install directory" | Out-Null
    Remove-DirectorySafe -Path $distDir -Name "dist directory" | Out-Null

    # Recreate required directories
    New-Item -ItemType Directory -Force $buildDir | Out-Null
    New-Item -ItemType Directory -Force $SHARED_DST_DIR | Out-Null
}

function Get-Pybind11Dir {
    param([string]$PyVer)

    if ($OFFLINE_MODE) {
        # Offline mode: use local venv pybind11
        $venvSuffix = $PyVer.Replace(".", "")
        $venvPybind11 = Join-Path $ROOT_DIR "venv$venvSuffix\share\cmake\pybind11"

        if (Test-Path $venvPybind11) {
            return $venvPybind11
        } else {
            Write-Error @"
Offline mode requires pybind11 in local venv
Expected path: $venvPybind11

To set up offline environment, run:
  uv venv venv$venvSuffix --python $PyVer
  uv pip install pybind11 -e . --python venv$venvSuffix\Scripts\python.exe
  (or use 'uv pip install pybind11' in the venv)
"@
            exit 1
        }
    } else {
        # Online mode: use uv run --with pybind11
        $output = uv run --python $PyVer --with pybind11 python -c "import pybind11; print(pybind11.get_cmake_dir())"
        return $output.Trim()
    }
}

function Invoke-BuildVersion {
    param([string]$PyVer)

    Write-Host ""
    Write-Host "==========================================="
    Write-Host " Building pyorbbecsdk for Python $PyVer"
    Write-Host "==========================================="

    $BUILD_DIR = Join-Path $ROOT_DIR "build_$PyVer"

    # Per-version cleanup
    if ($CLEAN_BUILD) {
        Invoke-PerVersionCleanup $PyVer
    } else {
        New-Item -ItemType Directory -Force $BUILD_DIR | Out-Null
        New-Item -ItemType Directory -Force $SHARED_DST_DIR | Out-Null
    }

    # Resolve Python interpreter
    Write-Host "Resolving Python interpreter..."
    $PYTHON_EXE = uv python find $PyVer
    Write-Host "Using Python: $PYTHON_EXE"

    # Resolve pybind11 CMake directory
    Write-Host "Resolving pybind11 CMake directory..."
    $PYBIND11_DIR = Get-Pybind11Dir $PyVer
    Write-Host "pybind11_DIR=$PYBIND11_DIR"

    # CMake configure & build
    Push-Location $BUILD_DIR

    try {
        cmake -G "Visual Studio 17 2022" -A x64 `
            -DCMAKE_BUILD_TYPE=Release `
            -DPython3_EXECUTABLE="$PYTHON_EXE" `
            -Dpybind11_DIR="$PYBIND11_DIR" `
            -DCMAKE_INSTALL_PREFIX="$INSTALL_DIR" `
            "$ROOT_DIR"

        if ($LASTEXITCODE -ne 0) {
            throw "CMake configuration failed (Python $PyVer)"
        }

        cmake --build . --config Release --target install --parallel

        if ($LASTEXITCODE -ne 0) {
            throw "CMake build failed (Python $PyVer)"
        }
    }
    finally {
        Pop-Location
    }

    # Copy extra runtime files
    Write-Host "Copying extra runtime files..."

    $examplesDir = Join-Path $ROOT_DIR "examples"
    $configDir = Join-Path $ROOT_DIR "config"
    $requirementsFile = Join-Path $ROOT_DIR "requirements.txt"

    if (Test-Path $examplesDir) {
        Copy-Item -Recurse -Force $examplesDir $INSTALL_LIB_DIR
    }

    if (Test-Path $configDir) {
        Copy-Item -Recurse -Force $configDir $INSTALL_LIB_DIR
    }

    if (Test-Path $requirementsFile) {
        $examplesDest = Join-Path $INSTALL_LIB_DIR "examples"
        New-Item -ItemType Directory -Force $examplesDest | Out-Null
        Copy-Item -Force $requirementsFile $examplesDest
    }

    if (Test-Path $ENV_SETUP_SRC) {
        Get-ChildItem -Path $ENV_SETUP_SRC -Filter "*.ps1" -ErrorAction SilentlyContinue |
            Copy-Item -Destination $SHARED_DST_DIR -Force -ErrorAction SilentlyContinue
        Get-ChildItem -Path $ENV_SETUP_SRC -Filter "*.md" -ErrorAction SilentlyContinue |
            Copy-Item -Destination $SHARED_DST_DIR -Force -ErrorAction SilentlyContinue
        Get-ChildItem -Path $ENV_SETUP_SRC -Filter "setup_env.py" -ErrorAction SilentlyContinue |
            Copy-Item -Destination $SHARED_DST_DIR -Force -ErrorAction SilentlyContinue
    }

    # Copy pyi stub files
    Write-Host "Copying pyi stub files..."
    $STUBS_DIR = Join-Path $ROOT_DIR "stubs"
    if (Test-Path $STUBS_DIR) {
        $pyiFiles = @("__init__.pyi", "pyorbbecsdk.pyi")
        foreach ($pyiFile in $pyiFiles) {
            $srcPath = Join-Path $STUBS_DIR $pyiFile
            if (Test-Path $srcPath) {
                Copy-Item -Force $srcPath $INSTALL_LIB_DIR
                Write-Host "  Copied $pyiFile"
            } else {
                Write-Host "  Warning: $pyiFile not found in $STUBS_DIR"
            }
        }
    } else {
        Write-Host "  Warning: stubs directory not found at $STUBS_DIR"
    }

    # Build wheel via uv
    Write-Host "Building wheel..."
    uv build --wheel --python $PyVer --link-mode copy

    $distDir = Join-Path $ROOT_DIR "dist"
    if (Test-Path $distDir) {
        Get-ChildItem (Join-Path $distDir "*.whl") | Copy-Item -Destination $WHEEL_DIR -Force
        Remove-DirectorySafe -Path $distDir -Name "dist directory" | Out-Null
    }

    Write-Host "Finished Python $PyVer"
}

function Invoke-FinalCleanup {
    Write-Host ""
    Write-Host ">>> Final cleanup..."

    # Remove build_* directories
    Get-ChildItem -Path $ROOT_DIR -Directory -Filter "build_*" -ErrorAction SilentlyContinue |
        ForEach-Object {
            Remove-DirectorySafe -Path $_.FullName -Name "$($_.Name) directory" | Out-Null
        }

    $dirsToRemove = @(
        @{ Path = (Join-Path $ROOT_DIR "build"); Name = "build directory" },
        @{ Path = (Join-Path $ROOT_DIR "install"); Name = "install directory" },
        @{ Path = (Join-Path $ROOT_DIR "dist"); Name = "dist directory" }
    )

    foreach ($dir in $dirsToRemove) {
        Remove-DirectorySafe -Path $dir.Path -Name $dir.Name | Out-Null
    }

    # Remove egg-info directories
    $srcDir = Join-Path $ROOT_DIR "src"
    if (Test-Path $srcDir) {
        Get-ChildItem -Path $srcDir -Directory -Filter "*.egg-info" -ErrorAction SilentlyContinue |
            ForEach-Object {
                Remove-DirectorySafe -Path $_.FullName -Name "$($_.Name)" | Out-Null
            }
    }
}

function Show-CleanupReport {
    Write-Host ""
    Write-Host "==========================================="

    if ($script:CleanupFailed.Count -eq 0 -and $script:CleanupSkipped.Count -eq 0) {
        Write-Host " Cleanup completed successfully"
        Write-Host " All temporary files were removed"
    }
    else {
        if ($script:CleanupFailed.Count -gt 0) {
            Write-Host " Cleanup completed with FAILURES:"
            Write-Host ""
            Write-Host "  Failed to delete the following items:"
            foreach ($item in $script:CleanupFailed) {
                Write-Host "    - $item" -ForegroundColor Red
            }
        }

        if ($script:CleanupSkipped.Count -gt 0) {
            Write-Host ""
            Write-Host "  Skipped the following items (user requested):"
            foreach ($item in $script:CleanupSkipped) {
                Write-Host "    - $item" -ForegroundColor Yellow
            }
        }

        Write-Host ""
        Write-Host "  You may need to manually remove these files/directories"
        Write-Host "  or run the script with -CleanOnly to try again."
    }

    Write-Host ""
    Write-Host " Wheels are located in: $WHEEL_DIR"
    Write-Host "==========================================="
}

# ============================================================
# Main Entry Point
# ============================================================

# Global cleanup (always run first)
if ($CLEAN_BUILD) {
    Invoke-InteractiveCleanup
} else {
    New-Item -ItemType Directory -Force $WHEEL_DIR | Out-Null
}

# Clean only mode
if ($CLEAN_ONLY) {
    Show-CleanupReport
    Write-Host ""
    Write-Host ">>> Clean completed (no build requested)"
    exit 0
}

# Build each version
foreach ($PyVer in $PYTHON_VERSIONS) {
    Invoke-BuildVersion $PyVer
}

# Final cleanup
Invoke-FinalCleanup

# Show final report
Show-CleanupReport
