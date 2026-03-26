#!/usr/bin/env bash
# =============================================================================
# 03-build.sh - 构建阶段
# =============================================================================

set -euo pipefail

build_wheel() {
    local os="$1"
    local pyver="$2"

    log_info "Building wheel for ${os} with Python ${pyver}..."
    start_timer

    # 设置环境
    setup_build_env

    local build_script
    case "${os}" in
        linux)
            build_script="${REPO_ROOT}/scripts/build_whl/build-whl-uv.sh"
            ;;
        windows)
            build_script="${REPO_ROOT}/scripts/build_whl/build-whl-uv.ps1"
            ;;
        macos)
            build_script="${REPO_ROOT}/scripts/build_whl/build-whl-uv-macos.sh"
            ;;
        *)
            log_error "Unknown OS: ${os}"
            exit 1
            ;;
    esac

    # 检查构建脚本是否存在
    if [[ ! -f "${build_script}" ]]; then
        log_error "Build script not found: ${build_script}"
        exit 1
    fi

    # 执行构建
    log_info "Executing: ${build_script} ${pyver} --clean"

    local status="success"
    if [[ "${os}" == "windows" ]]; then
        # Windows 使用 PowerShell
        if powershell -ExecutionPolicy Bypass -Command "& '${build_script}' ${pyver} -Clean -Yes" 2>&1 | tee "${REPO_ROOT}/logs/build-${os}-py${pyver}.log"; then
            log_success "Windows build completed"
        else
            log_error "Windows build failed"
            status="failure"
        fi
    else
        # Linux/macOS 使用 Bash
        if bash "${build_script}" "${pyver}" --clean 2>&1 | tee "${REPO_ROOT}/logs/build-${os}-py${pyver}.log"; then
            log_success "${os} build completed"
        else
            log_error "${os} build failed"
            status="failure"
        fi
    fi

    # 验证输出
    if [[ -d "${REPO_ROOT}/wheel" ]]; then
        local wheel_count
        wheel_count=$(find "${REPO_ROOT}/wheel" -name "*.whl" | wc -l)
        log_info "Generated ${wheel_count} wheel files"

        if [[ ${wheel_count} -eq 0 ]]; then
            log_error "No wheel files generated"
            status="failure"
        fi
    else
        log_error "Wheel directory not found"
        status="failure"
    fi

    # 生成报告
    local duration
    duration=$(end_timer)
    generate_report_summary "build-${os}" "${status}" "${duration}"

    if [[ "${status}" == "failure" ]]; then
        exit 1
    fi

    log_success "Build stage completed for ${os}"
}
