#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# uv-optimized pyorbbecsdk2 build script (Linux)
# ============================================================

export UV_LINK_MODE=copy

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ============================================================
# Global cleanup
# ============================================================

echo ">>> Global pre-cleanup"

rm -rf "$ROOT_DIR/build" \
       "$ROOT_DIR/wheel" \
       "$ROOT_DIR/install" \
       "$ROOT_DIR/dist"

mkdir -p "$ROOT_DIR/wheel"

# ============================================================
# Configuration
# ============================================================

PYTHON_VERSIONS=("3.10")
WHEEL_DIR="$ROOT_DIR/wheel"
INSTALL_DIR="$ROOT_DIR/install"
INSTALL_LIB_DIR="$INSTALL_DIR/lib/pyorbbecsdk"
SHARED_DST_DIR="$INSTALL_LIB_DIR/shared"
ENV_SETUP_SRC="$ROOT_DIR/scripts/env_setup"

# ============================================================
# Detect architecture & set LD_LIBRARY_PATH
# ============================================================

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

# ============================================================
# Build loop
# ============================================================

for PYVER in "${PYTHON_VERSIONS[@]}"; do
    echo
    echo "==========================================="
    echo " Building pyorbbecsdk for Python $PYVER"
    echo "==========================================="

    BUILD_DIR="$ROOT_DIR/build_$PYVER"

    # ----------------------------
    # Per-version cleanup
    # ----------------------------

    rm -rf "$BUILD_DIR" "$INSTALL_DIR" "$ROOT_DIR/dist"

    mkdir -p "$BUILD_DIR"
    mkdir -p "$SHARED_DST_DIR"

    # ----------------------------
    # Resolve Python & pybind11 via uv
    # ----------------------------

    echo "Resolving Python interpreter..."
    PYTHON_EXE="$(uv python find "$PYVER")"
    echo "Using Python: $PYTHON_EXE"

    echo "Resolving pybind11 CMake directory..."
    PYBIND11_DIR="$(uv run --python "$PYVER" --with pybind11 \
        python - <<'EOF'
import pybind11
print(pybind11.get_cmake_dir())
EOF
)"
    echo "pybind11_DIR=$PYBIND11_DIR"

    # ----------------------------
    # CMake configure & build
    # ----------------------------

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

    # ----------------------------
    # Copy extra runtime files
    # ----------------------------

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

    # ----------------------------
    # Build wheel via uv
    # ----------------------------

    echo "Building wheel..."
    uv build --wheel --python "$PYVER" --link-mode copy

    # ----------------------------
    # auditwheel (skip py38 if needed)
    # ----------------------------

    if [ -d "$ROOT_DIR/dist" ]; then
        if [[ "$PYVER" != "3.8" ]]; then
            echo "Repairing wheel with auditwheel..."
            uv run --python $PYVER --with auditwheel auditwheel repair "$ROOT_DIR"/dist/*.whl \
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

    echo "✔ Finished Python $PYVER"
done

# ============================================================
# Final cleanup (keep wheel/)
# ============================================================

echo
echo "Final cleanup..."
rm -rf "$ROOT_DIR"/build_* \
       "$ROOT_DIR/build" \
       "$ROOT_DIR/install"

find "$ROOT_DIR/src" -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true

echo
echo "==========================================="
echo " All builds completed"
echo " Wheels are located in: $WHEEL_DIR"
echo "==========================================="