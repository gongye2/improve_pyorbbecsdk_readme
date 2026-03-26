#!/usr/bin/env bash
# =============================================================================
# utils.sh - CI 工具函数库
# =============================================================================

set -euo pipefail

# 颜色定义（仅在支持时）
if [[ -t 1 ]]; then
    readonly RED='\033[0;31m'
    readonly GREEN='\033[0;32m'
    readonly YELLOW='\033[1;33m'
    readonly BLUE='\033[0;34m'
    readonly NC='\033[0m' # No Color
else
    readonly RED=''
    readonly GREEN=''
    readonly YELLOW=''
    readonly BLUE=''
    readonly NC=''
fi

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# 检测操作系统
detect_os() {
    case "$(uname -s)" in
        Linux*)     echo "linux";;
        Darwin*)    echo "macos";;
        CYGWIN*|MINGW*|MSYS*) echo "windows";;
        *)          echo "unknown";;
    esac
}

# 检测架构
detect_arch() {
    case "$(uname -m)" in
        x86_64)     echo "x64";;
        aarch64|arm64) echo "arm64";;
        *)          echo "unknown";;
    esac
}

# 设置 Python 可执行文件路径
get_python_exe() {
    local pyver="$1"
    local os="$(detect_os)"

    if command -v uv &> /dev/null; then
        uv python find "${pyver}"
    elif command -v "python${pyver}" &> /dev/null; then
        command -v "python${pyver}"
    elif command -v python3 &> /dev/null; then
        command -v python3
    else
        command -v python
    fi
}

# 生成 JUnit XML 报告头部
generate_junit_header() {
    local suite_name="$1"
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%S")

    echo "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
    echo "<testsuite name=\"${suite_name}\" timestamp=\"${timestamp}\">"
}

# 生成 JUnit XML 报告尾部
generate_junit_footer() {
    echo "</testsuite>"
}

# 生成测试报告摘要
generate_report_summary() {
    local job_type="$1"
    local status="$2"
    local duration="$3"
    local report_file="${REPO_ROOT:-.}/reports/summary.json"

    mkdir -p "$(dirname "${report_file}")"

    cat > "${report_file}" << EOF
{
  "platform": "${CI_PLATFORM:-local}",
  "job_type": "${job_type}",
  "status": "${status}",
  "duration_seconds": ${duration},
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S")",
  "python_version": "${PYTHON_VERSION:-unknown}",
  "hardware_available": ${HARDWARE_AVAILABLE:-false}
}
EOF
}

# 上传 Artifact (跨平台抽象)
upload_artifact() {
    local name="$1"
    local path="$2"
    local retention_days="${3:-7}"

    log_info "Uploading artifact: ${name}"

    if [[ "${CI_PLATFORM:-}" == "github" ]]; then
        # GitHub Actions - 使用环境变量
        log_info "Artifact will be uploaded by GitHub Actions"
        # 实际由 actions/upload-artifact 处理
    elif [[ "${CI_PLATFORM:-}" == "gitlab" ]]; then
        # GitLab CI - artifacts 在 .gitlab-ci.yml 中定义
        log_info "Artifact will be collected by GitLab CI"
    else
        # 本地运行 - 复制到 reports
        local dest="${REPO_ROOT:-.}/artifacts/${name}"
        mkdir -p "${dest}"
        cp -r "${path}" "${dest}/"
        log_info "Artifact saved to: ${dest}"
    fi
}

# 安装系统依赖 (Linux)
install_linux_deps() {
    log_info "Installing Linux dependencies..."

    if command -v apt-get &> /dev/null; then
        sudo apt-get update -qq
        sudo apt-get install -y --no-install-recommends \
            cmake \
            ninja-build \
            build-essential \
            libusb-1.0-0-dev \
            libudev-dev
    elif command -v yum &> /dev/null; then
        sudo yum install -y cmake ninja-build gcc gcc-c++ libusb-devel
    elif command -v pacman &> /dev/null; then
        sudo pacman -S --noconfirm cmake ninja gcc libusb
    fi
}

# 安装系统依赖 (macOS)
install_macos_deps() {
    log_info "Installing macOS dependencies..."

    if command -v brew &> /dev/null; then
        brew install cmake libusb
    else
        log_error "Homebrew not found. Please install Homebrew first."
        exit 1
    fi
}

# 安装 uv
install_uv() {
    if command -v uv &> /dev/null; then
        log_info "uv is already installed"
        return 0
    fi

    log_info "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
}

# 设置构建环境
setup_build_env() {
    local os="$(detect_os)"

    log_info "Setting up build environment for ${os}..."

    # 安装 uv
    install_uv

    # 安装系统依赖
    case "${os}" in
        linux)
            install_linux_deps
            ;;
        macos)
            install_macos_deps
            ;;
        windows)
            log_info "Windows dependencies should be pre-installed"
            ;;
    esac

    # 设置环境变量
    export UV_LINK_MODE="${UV_LINK_MODE:-copy}"

    log_success "Build environment ready"
}

# 计算执行时间
start_timer() {
    export CI_START_TIME=$(date +%s)
}

end_timer() {
    local end_time=$(date +%s)
    local duration=$((end_time - CI_START_TIME))
    echo "${duration}"
}

# 格式化时间
format_duration() {
    local seconds="$1"
    local mins=$((seconds / 60))
    local secs=$((seconds % 60))
    printf "%02d:%02d" ${mins} ${secs}
}

# 检查是否有 Orbbec 设备连接
check_device_connected() {
    if ! command -v python &> /dev/null; then
        log_warning "Python not found, cannot check device"
        return 1
    fi

    python -c "
from pyorbbecsdk import Context
try:
    ctx = Context()
    devices = ctx.query_devices()
    count = devices.get_count()
    if count > 0:
        print(f'Device found: {count}')
        exit(0)
    else:
        exit(1)
except Exception as e:
    print(f'Error: {e}')
    exit(1)
" 2>/dev/null
}

# 获取设备信息
get_device_info() {
    python -c "
from pyorbbecsdk import Context
try:
    ctx = Context()
    devices = ctx.query_devices()
    for i in range(devices.get_count()):
        dev = devices.get_device_by_index(i)
        info = dev.get_device_info()
        print(f'[{i}] {info.get_name()} - S/N: {info.get_serial_number()}')
except Exception as e:
    print(f'Error: {e}')
" 2>/dev/null || echo "No device info available"
}

# 导出函数供其他脚本使用
export -f log_info
export -f log_success
export -f log_warning
export -f log_error
export -f detect_os
export -f detect_arch
export -f get_python_exe
export -f generate_report_summary
export -f upload_artifact
export -f install_linux_deps
export -f install_macos_deps
export -f install_uv
export -f setup_build_env
export -f start_timer
export -f end_timer
export -f format_duration
export -f check_device_connected
export -f get_device_info
