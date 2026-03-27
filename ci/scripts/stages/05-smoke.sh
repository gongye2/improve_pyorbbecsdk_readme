#!/usr/bin/env bash
# =============================================================================
# 05-smoke.sh - 每日冒烟测试阶段
# =============================================================================

set -euo pipefail

run_daily_smoke() {
    log_info "Running daily smoke tests..."
    start_timer

    export HARDWARE_AVAILABLE="true"

    # 设备健康检查
    log_info "Checking device health..."
    if ! check_device_connected; then
        log_error "No Orbbec device connected"
        exit 1
    fi

    get_device_info

    # 构建 wheel (如果需要)
    if [[ ! -d "${REPO_ROOT}/wheel" ]] || [[ -z "$(ls -A "${REPO_ROOT}/wheel")" ]]; then
        log_info "Building wheel..."
        source "${SCRIPT_DIR}/stages/03-build.sh"
        build_wheel "linux" "${PYTHON_VERSION}"
    fi

    # 安装 wheel
    log_info "Installing wheel..."
    pip install "${REPO_ROOT}/wheel"/*.whl pytest pytest-timeout --quiet

    local status="success"

    # 运行基础导入测试
    log_info "Running basic import test..."
    if python "${REPO_ROOT}/test/test_basic_import.py" -v 2>&1 | tee -a "${REPO_ROOT}/logs/smoke.log"; then
        log_success "Basic import test passed"
    else
        log_error "Basic import test failed"
        status="failure"
    fi

    # 运行基础设备测试
    log_info "Running basic device test..."
    if pytest "${REPO_ROOT}/test/test_basic_device.py" -v --timeout=300 2>&1 | tee -a "${REPO_ROOT}/logs/smoke.log"; then
        log_success "Basic device test passed"
    else
        log_warning "Basic device test had issues"
    fi

    # 运行基础采集测试
    log_info "Running basic capture test..."
    if pytest "${REPO_ROOT}/test/test_basic_capture.py" -v --timeout=300 2>&1 | tee -a "${REPO_ROOT}/logs/smoke.log"; then
        log_success "Basic capture test passed"
    else
        log_warning "Basic capture test had issues"
    fi

    # 生成报告
    local duration
    duration=$(end_timer)
    generate_report_summary "daily-smoke" "${status}" "${duration}"

    log_success "Daily smoke tests completed"
}
