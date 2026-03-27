#!/usr/bin/env bash
# =============================================================================
# ci-entry.sh - 统一 CI 入口脚本 (GitHub Actions & GitLab CI 通用)
# =============================================================================
# Usage:
#   export CI_JOB_TYPE="lint" && ./ci-entry.sh
#   export CI_JOB_TYPE="build-linux" && export PYTHON_VERSION="3.10" && ./ci-entry.sh
# =============================================================================

set -euo pipefail

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# 加载工具函数
source "${SCRIPT_DIR}/utils.sh"

# 检测 CI 平台
CI_PLATFORM=${CI_PLATFORM:-"local"}
if [[ -n "${GITHUB_ACTIONS:-}" ]]; then
    CI_PLATFORM="github"
elif [[ -n "${GITLAB_CI:-}" ]]; then
    CI_PLATFORM="gitlab"
fi

# 默认环境变量
export CI_JOB_TYPE=${CI_JOB_TYPE:-""}
export PYTHON_VERSION=${PYTHON_VERSION:-"3.10"}
export HARDWARE_AVAILABLE=${HARDWARE_AVAILABLE:-"false"}
export UV_LINK_MODE=${UV_LINK_MODE:-"copy"}

# 日志头
log_info "=========================================="
log_info " CI Entry Script"
log_info " Platform: ${CI_PLATFORM}"
log_info " Job Type: ${CI_JOB_TYPE}"
log_info " Python: ${PYTHON_VERSION}"
log_info "=========================================="

# 参数验证
if [[ -z "${CI_JOB_TYPE}" ]]; then
    log_error "CI_JOB_TYPE is not set"
    log_info "Available job types: lint, build-linux, build-windows, build-macos, test-no-hw, test-hw, daily-smoke, nightly"
    exit 1
fi

# 创建必要的目录
mkdir -p "${REPO_ROOT}/logs"
mkdir -p "${REPO_ROOT}/reports"
mkdir -p "${REPO_ROOT}/wheel"

# 根据 JOB_TYPE 执行不同流程
case "${CI_JOB_TYPE}" in
    "lint")
        log_info "Running lint checks..."
        source "${SCRIPT_DIR}/stages/02-lint.sh"
        run_lint
        ;;

    "build-linux")
        log_info "Building for Linux..."
        source "${SCRIPT_DIR}/stages/03-build.sh"
        build_wheel "linux" "${PYTHON_VERSION}"
        ;;

    "build-windows")
        log_info "Building for Windows..."
        source "${SCRIPT_DIR}/stages/03-build.sh"
        build_wheel "windows" "${PYTHON_VERSION}"
        ;;

    "build-macos")
        log_info "Building for macOS..."
        source "${SCRIPT_DIR}/stages/03-build.sh"
        build_wheel "macos" "${PYTHON_VERSION}"
        ;;

    "test-no-hw")
        log_info "Running tests (no hardware)..."
        source "${SCRIPT_DIR}/stages/04-test.sh"
        run_tests "not hardware"
        ;;

    "test-hw")
        log_info "Running tests (with hardware)..."
        source "${SCRIPT_DIR}/stages/04-test.sh"
        run_tests "hardware"
        ;;

    "daily-smoke")
        log_info "Running daily smoke tests..."
        source "${SCRIPT_DIR}/stages/05-smoke.sh"
        run_daily_smoke
        ;;

    "nightly")
        log_info "Running nightly regression..."
        source "${SCRIPT_DIR}/stages/06-nightly.sh"
        run_nightly
        ;;

    "verify-import")
        log_info "Verifying package import..."
        source "${SCRIPT_DIR}/stages/04-test.sh"
        verify_import
        ;;

    *)
        log_error "Unknown job type: ${CI_JOB_TYPE}"
        log_info "Available job types:"
        log_info "  - lint"
        log_info "  - build-linux"
        log_info "  - build-windows"
        log_info "  - build-macos"
        log_info "  - test-no-hw"
        log_info "  - test-hw"
        log_info "  - daily-smoke"
        log_info "  - nightly"
        log_info "  - verify-import"
        exit 1
        ;;
esac

log_success "Job completed: ${CI_JOB_TYPE}"
