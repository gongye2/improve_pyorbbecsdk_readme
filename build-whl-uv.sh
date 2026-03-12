#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# uv-optimized pyorbbecsdk2 build script (Linux)
# ============================================================
# Features:
#   - Support command-line arguments for Python versions
#   - Offline mode support with --offline flag
#   - Configurable cleanup options
#   - Build single or multiple Python versions
# ============================================================

export UV_LINK_MODE=copy

# Set UV offline mode if requested
UV_OFFLINE="${UV_OFFLINE:-}"

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ============================================================
# Default configuration
# ============================================================

# Default Python versions to build
PYTHON_VERSIONS=()

# Build options
OFFLINE_MODE=false
CLEAN_BUILD=true
CLEAN_ONLY=false

# Directory paths
WHEEL_DIR="$ROOT_DIR/wheel"
INSTALL_DIR="$ROOT_DIR/install"
INSTALL_LIB_DIR="$INSTALL_DIR/lib/pyorbbecsdk"
SHARED_DST_DIR="$INSTALL_LIB_DIR/shared"
ENV_SETUP_SRC="$ROOT_DIR/scripts/env_setup"

# ============================================================
# Usage function
# ============================================================

show_usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS] [VERSION...]

Build pyorbbecsdk wheel packages for specified Python versions.

Options:
  --offline       Offline mode, skip network downloads (requires local pybind11)
  --no-clean      Don't clean build directories before building
  --clean         Clean build directories before building (default)
  --clean-only    Only clean, don't build
  -h, --help      Show this help message

Arguments:
  VERSION         Python version (e.g., 3.10, 3.11) or 'all' for 3.8-3.13

Examples:
  $(basename "$0") 3.10                    # Build Python 3.10
  $(basename "$0") 3.8 3.9 3.10            # Build multiple versions
  $(basename "$0") all                     # Build all versions (3.8-3.13)
  $(basename "$0") --offline 3.10          # Offline build
  $(basename "$0") --clean all             # Clean and build all versions
  $(basename "$0") --clean-only            # Clean only, don't build
EOF
}

# ============================================================
# Parse command-line arguments
# ============================================================

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --offline)
                OFFLINE_MODE=true
                export UV_OFFLINE=1
                shift
                ;;
            --no-clean)
                CLEAN_BUILD=false
                shift
                ;;
            --clean)
                CLEAN_BUILD=true
                shift
                ;;
            --clean-only)
                CLEAN_ONLY=true
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            all)
                # Build all supported Python versions (3.8-3.13)
                PYTHON_VERSIONS=("3.8" "3.9" "3.10" "3.11" "3.12" "3.13")
                shift
                ;;
            3.*)
                PYTHON_VERSIONS+=("$1")
                shift
                ;;
            *)
                echo "Error: Unknown option or version: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    # Default to 3.10 if no versions specified
    if [[ ${#PYTHON_VERSIONS[@]} -eq 0 ]]; then
        PYTHON_VERSIONS=("3.10")
    fi
}

# ============================================================
# Cleanup functions
# ============================================================

# Check and confirm deletion of a single path
confirm_delete() {
    local path="$1"
    local name="$2"

    if [ -e "$path" ]; then
        echo -n "  Found: $name - delete? (y/n/a=all/s=skip-all): "
        read -r response

        case "$response" in
            y|Y)
                rm -rf "$path"
                echo "    Deleted: $name"
                return 0
                ;;
            a|A)
                rm -rf "$path"
                echo "    Deleted: $name"
                return 0
                ;;
            s|S)
                echo "    Skipped: $name"
                return 1
                ;;
            *)
                echo "    Skipped: $name"
                return 1
                ;;
        esac
    fi
    return 1
}

# Interactive cleanup confirmation
interactive_cleanup() {
    local skip_all=false
    local allow_all=false

    echo ">>> Checking for existing build artifacts to clean"
    echo ""

    # Define paths to check
    local paths_to_check=(
        "$ROOT_DIR/build:build directory"
        "$ROOT_DIR/dist:dist directory"
        "$ROOT_DIR/install:install directory"
        "$ROOT_DIR/wheel:wheel directory"
    )

    # Check for build_* directories
    for dir in "$ROOT_DIR"/build_*; do
        if [ -d "$dir" ]; then
            local dirname
            dirname="$(basename "$dir")"
            paths_to_check+=("$dir:$dirname directory")
        fi
    done

    # Check if anything exists
    local has_items=false
    for item in "${paths_to_check[@]}"; do
        local path="${item%%:*}"
        if [ -e "$path" ]; then
            has_items=true
            break
        fi
    done

    if [ "$has_items" = "false" ]; then
        echo "  No build artifacts found, nothing to clean."
        echo ""
        mkdir -p "$ROOT_DIR/wheel"
        return
    fi

    # Confirm each path
    for item in "${paths_to_check[@]}"; do
        local path="${item%%:*}"
        local name="${item#*:}"

        if [ "$skip_all" = "true" ]; then
            echo "  Skipped: $name"
            continue
        fi

        if [ "$allow_all" = "true" ]; then
            rm -rf "$path"
            echo "  Deleted: $name"
            continue
        fi

        if [ -e "$path" ]; then
            echo -n "  Found: $name - delete? (y=yes/n=no/d=this dir only/s=skip-all/a=allow-all): "
            read -r response

            case "$response" in
                y|Y)
                    rm -rf "$path"
                    echo "    Deleted: $name"
                    ;;
                d|D)
                    rm -rf "$path"
                    echo "    Deleted: $name"
                    skip_all=true
                    ;;
                a|A)
                    rm -rf "$path"
                    echo "    Deleted: $name"
                    allow_all=true
                    ;;
                s|S)
                    echo "    Skipped: $name"
                    skip_all=true
                    ;;
                *)
                    echo "    Skipped: $name"
                    ;;
            esac
        fi
    done

    echo ""
    mkdir -p "$ROOT_DIR/wheel"
}

# Per-version cleanup
per_version_cleanup() {
    local PYVER="$1"
    local BUILD_DIR="$ROOT_DIR/build_$PYVER"

    rm -rf "$BUILD_DIR" "$INSTALL_DIR" "$ROOT_DIR/dist"
    mkdir -p "$BUILD_DIR"
    mkdir -p "$SHARED_DST_DIR"
}

# ============================================================
# Get pybind11 directory
# ============================================================

get_pybind11_dir() {
    local PYVER="$1"

    if [ "$OFFLINE_MODE" = "true" ]; then
        # Offline mode: use local venv pybind11
        local VENV_PYBIND11="$ROOT_DIR/venv$(echo "$PYVER" | tr -d '.')/share/cmake/pybind11"
        if [ -d "$VENV_PYBIND11" ]; then
            echo "$VENV_PYBIND11"
        else
            echo "Error: Offline mode requires pybind11 in local venv" >&2
            echo "Expected path: $VENV_PYBIND11" >&2
            echo "" >&2
            echo "To set up offline environment, run:" >&2
            echo "  uv venv venv$(echo "$PYVER" | tr -d '.') --python $PYVER" >&2
            echo "  uv pip install pybind11 -e . --python venv$(echo "$PYVER" | tr -d '.')/bin/python" >&2
            echo "  (or use 'uv pip install pybind11' in the venv)" >&2
            exit 1
        fi
    else
        # Online mode: use uv run --with pybind11
        uv run --python "$PYVER" --with pybind11 python - <<'EOF'
import pybind11
print(pybind11.get_cmake_dir())
EOF
    fi
}

# ============================================================
# Main build logic
# ============================================================

build_version() {
    local PYVER="$1"

    echo
    echo "==========================================="
    echo " Building pyorbbecsdk for Python $PYVER"
    echo "==========================================="

    local BUILD_DIR="$ROOT_DIR/build_$PYVER"

    # Per-version cleanup
    if [ "$CLEAN_BUILD" = "true" ]; then
        per_version_cleanup "$PYVER"
    else
        mkdir -p "$BUILD_DIR"
        mkdir -p "$SHARED_DST_DIR"
    fi

    # Resolve Python interpreter
    echo "Resolving Python interpreter..."
    local PYTHON_EXE
    PYTHON_EXE="$(uv python find "$PYVER")"
    echo "Using Python: $PYTHON_EXE"

    # Resolve pybind11 CMake directory
    echo "Resolving pybind11 CMake directory..."
    local PYBIND11_DIR
    PYBIND11_DIR="$(get_pybind11_dir "$PYVER")"
    echo "pybind11_DIR=$PYBIND11_DIR"

    # CMake configure & build
    pushd "$BUILD_DIR" >/dev/null

    cmake .. \
        -DCMAKE_BUILD_TYPE=Release \
        -DPython3_EXECUTABLE="$PYTHON_EXE" \
        -Dpybind11_DIR="$PYBIND11_DIR" \
        -DCMAKE_INSTALL_PREFIX="$INSTALL_DIR" \
        -DCMAKE_C_COMPILER=gcc \
        -DCMAKE_CXX_COMPILER=g++

    cmake --build . --target install -j"$(nproc)"

    popd >/dev/null

    # Copy extra runtime files
    echo "Copying extra runtime files..."

    if [ -d "$ROOT_DIR/examples" ]; then
        cp -r "$ROOT_DIR/examples" "$INSTALL_LIB_DIR/"
    fi

    if [ -d "$ROOT_DIR/config" ]; then
        cp -r "$ROOT_DIR/config" "$INSTALL_LIB_DIR/"
    fi

    if [ -f "$ROOT_DIR/requirements.txt" ]; then
        mkdir -p "$INSTALL_LIB_DIR/examples"
        cp "$ROOT_DIR/requirements.txt" "$INSTALL_LIB_DIR/examples/"
    fi

    if [ -d "$ENV_SETUP_SRC" ]; then
        cp "$ENV_SETUP_SRC"/*.rules "$SHARED_DST_DIR/" 2>/dev/null || true
        cp "$ENV_SETUP_SRC"/*.sh    "$SHARED_DST_DIR/" 2>/dev/null || true
    fi

    # Copy pyi stub files
    echo "Copying pyi stub files..."
    STUBS_DIR="$ROOT_DIR/stubs"
    if [ -d "$STUBS_DIR" ]; then
        # Copy __init__.pyi and pyorbbecsdk.pyi
        for pyi_file in "__init__.pyi" "pyorbbecsdk.pyi"; do
            if [ -f "$STUBS_DIR/$pyi_file" ]; then
                cp "$STUBS_DIR/$pyi_file" "$INSTALL_LIB_DIR/"
                echo "  Copied $pyi_file"
            else
                echo "  Warning: $pyi_file not found in $STUBS_DIR"
            fi
        done
    else
        echo "  Warning: stubs directory not found at $STUBS_DIR"
    fi

    # Build wheel via uv
    echo "Building wheel..."
    uv build --wheel --python "$PYVER" --link-mode copy

    # auditwheel (skip py38 if needed)
    if [ -d "$ROOT_DIR/dist" ]; then
        if [[ "$PYVER" != "3.8" ]]; then
            echo "Repairing wheel with auditwheel..."
            uv run --python "$PYVER" --with auditwheel auditwheel repair "$ROOT_DIR"/dist/*.whl \
                --exclude libEGL* \
                --exclude libGLES* \
                --exclude libGL* \
                --exclude libOrbbecSDK.so* \
                --exclude libdepthengine.so* \
                --exclude libFilterProcessor.so \
                --exclude libob_*.so \
                --exclude libfirmwareupdater.so \
                --exclude libob_frame_processor.so \
                -w "$ROOT_DIR/dist/"
        fi

        cp "$ROOT_DIR"/dist/*.whl "$WHEEL_DIR/"
        rm -rf "$ROOT_DIR/dist"
    fi

    echo "Finished Python $PYVER"
}

# ============================================================
# Detect architecture & set LD_LIBRARY_PATH
# ============================================================

setup_arch() {
    ARCH="$(uname -m)"
    case "$ARCH" in
        x86_64)
            export LD_LIBRARY_PATH="$ROOT_DIR/sdk/lib/linux_x64:${LD_LIBRARY_PATH:-}"
            ;;
        aarch64)
            export LD_LIBRARY_PATH="$ROOT_DIR/sdk/lib/arm64:${LD_LIBRARY_PATH:-}"
            ;;
        *)
            echo "Unsupported architecture: $ARCH"
            exit 1
            ;;
    esac
}

# ============================================================
# Final cleanup
# ============================================================

final_cleanup() {
    echo
    echo "Final cleanup..."

    rm -rf "$ROOT_DIR"/build_* \
           "$ROOT_DIR/build" \
           "$ROOT_DIR/install"

    find "$ROOT_DIR/src" -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true
}

# ============================================================
# Main entry point
# ============================================================

main() {
    parse_args "$@"

    # Setup architecture
    setup_arch

    # Global cleanup (always run first)
    if [ "$CLEAN_BUILD" = "true" ]; then
        interactive_cleanup
    else
        mkdir -p "$ROOT_DIR/wheel"
    fi

    # Clean only mode
    if [ "$CLEAN_ONLY" = "true" ]; then
        echo ">>> Clean completed (no build requested)"
        exit 0
    fi

    # Build each version
    for PYVER in "${PYTHON_VERSIONS[@]}"; do
        build_version "$PYVER"
    done

    # Final cleanup
    final_cleanup

    echo
    echo "==========================================="
    echo " All builds completed"
    echo " Wheels are located in: $WHEEL_DIR"
    echo "==========================================="
}

# Run main
main "$@"
