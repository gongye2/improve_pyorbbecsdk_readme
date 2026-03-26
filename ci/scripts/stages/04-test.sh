#!/usr/bin/env bash
# =============================================================================
# 04-test.sh - 测试阶段
# =============================================================================

set -euo pipefail

run_tests() {
    local markers="$1"

    log_info "Running tests with markers: ${markers}"
    start_timer

    # 安装测试依赖
    log_info "Installing test dependencies..."
    pip install pytest pytest-timeout --quiet

    # 检查 wheel 是否已安装
    if ! python -c "import pyorbbecsdk" 2>/dev/null; then
        log_error "pyorbbecsdk not installed. Please build and install first."
        exit 1
    fi

    # 运行测试
    log_info "Running pytest..."
    local status="success"

    if pytest "${REPO_ROOT}/test" \
        -v \
        -m "${markers}" \
        --timeout=60 \
        --junit-xml="${REPO_ROOT}/reports/pytest.xml" \
        --tb=short \
        2>&1 | tee "${REPO_ROOT}/logs/pytest.log"; then
        log_success "Tests passed"
    else
        log_warning "Some tests failed or were skipped"
        # 非硬件测试失败时退出
        if [[ "${markers}" == "not hardware" ]]; then
            status="failure"
        fi
    fi

    # 生成报告
    local duration
    duration=$(end_timer)
    generate_report_summary "test-${markers// /-}" "${status}" "${duration}"

    if [[ "${status}" == "failure" ]]; then
        exit 1
    fi

    log_success "Test stage completed"
}

verify_import() {
    log_info "Verifying package import..."
    start_timer

    local status="success"

    # 检查 wheel 是否已安装
    if ! python -c "import pyorbbecsdk" 2>/dev/null; then
        log_error "pyorbbecsdk import failed"
        status="failure"
    else
        log_success "pyorbbecsdk imported successfully"

        # 检查版本
        local version
        version=$(python -c "import pyorbbecsdk; print(pyorbbecsdk.__version__)" 2>/dev/null || echo "unknown")
        log_info "Package version: ${version}"

        # 检查关键类
        if python -c "from pyorbbecsdk import Context, Pipeline, Config" 2>/dev/null; then
            log_success "Key classes imported successfully"
        else
            log_error "Failed to import key classes"
            status="failure"
        fi
    fi

    # 生成报告
    local duration
    duration=$(end_timer)
    generate_report_summary "verify-import" "${status}" "${duration}"

    if [[ "${status}" == "failure" ]]; then
        exit 1
    fi

    log_success "Import verification completed"
}
