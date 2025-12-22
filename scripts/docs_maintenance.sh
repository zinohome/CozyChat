#!/bin/bash
# 文档定期维护脚本
#
# 功能:
# 1. 每天生成文档索引
# 2. 每周检查过期文档并发送通知
# 3. 每月生成详细报告
#
# 使用:
#   ./scripts/docs_maintenance.sh daily   # 每日任务
#   ./scripts/docs_maintenance.sh weekly  # 每周任务
#   ./scripts/docs_maintenance.sh monthly # 每月任务
#
# Cron配置示例:
#   0 2 * * * cd /path/to/CozyChat && ./scripts/docs_maintenance.sh daily
#   0 9 * * 1 cd /path/to/CozyChat && ./scripts/docs_maintenance.sh weekly
#   0 9 1 * * cd /path/to/CozyChat && ./scripts/docs_maintenance.sh monthly

set -e

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# 每日任务
daily_task() {
    log_info "开始执行每日文档维护任务..."
    
    # 1. 生成文档索引
    log_info "生成文档索引..."
    python3 scripts/docs_manager.py index
    
    if [ $? -eq 0 ]; then
        log_success "文档索引生成成功"
        
        # 2. 提交索引更新（如果有变化）
        if [ -n "$(git status --porcelain docs/INDEX.md)" ]; then
            log_info "检测到索引文件变化，提交更新..."
            git add docs/INDEX.md
            git commit -m "docs: 自动更新文档索引 [skip ci]"
            
            # 可选：自动推送
            # git push origin main
            
            log_success "索引更新已提交"
        else
            log_info "索引文件无变化"
        fi
    else
        log_error "文档索引生成失败"
        return 1
    fi
    
    log_success "每日文档维护任务完成"
}

# 每周任务
weekly_task() {
    log_info "开始执行每周文档维护任务..."
    
    # 1. 检查过期文档
    log_info "检查过期文档..."
    python3 scripts/docs_manager.py check > /tmp/docs_check_report.txt
    
    if [ $? -eq 0 ]; then
        log_success "过期文档检查完成"
        
        # 2. 统计过期文档数量
        outdated_count=$(grep -c "最后更新:" /tmp/docs_check_report.txt || true)
        
        if [ "$outdated_count" -gt 0 ]; then
            log_warning "发现 $outdated_count 个过期文档（超过30天未更新）"
            
            # 3. 发送通知（可选）
            # 方法1: 通过邮件
            # cat /tmp/docs_check_report.txt | mail -s "CozyChat文档维护提醒" team@example.com
            
            # 方法2: 通过Slack/钉钉/企业微信
            # curl -X POST webhook_url -d "$(cat /tmp/docs_check_report.txt)"
            
            # 方法3: 创建GitHub Issue
            # gh issue create --title "文档维护提醒" --body "$(cat /tmp/docs_check_report.txt)"
            
            log_info "过期文档报告:"
            cat /tmp/docs_check_report.txt
        else
            log_success "所有文档都是最新的！"
        fi
    else
        log_error "过期文档检查失败"
        return 1
    fi
    
    log_success "每周文档维护任务完成"
}

# 每月任务
monthly_task() {
    log_info "开始执行每月文档维护任务..."
    
    # 1. 生成详细报告
    log_info "生成详细报告..."
    python3 scripts/docs_manager.py report
    
    if [ $? -eq 0 ]; then
        log_success "详细报告生成成功"
        
        # 2. 统计分析
        log_info "文档统计分析:"
        
        # 读取报告（如果是JSON格式）
        if command -v jq &> /dev/null; then
            total_docs=$(jq '.total_documents' docs/DOCS_REPORT.json)
            outdated_count=$(jq '.statistics.outdated_count' docs/DOCS_REPORT.json)
            
            log_info "  总文档数: $total_docs"
            log_info "  过期文档: $outdated_count"
            
            # 按状态统计
            log_info "  按状态分布:"
            jq -r '.statistics.by_status | to_entries[] | "    \(.key): \(.value)"' docs/DOCS_REPORT.json
            
            # 按分类统计
            log_info "  按分类分布:"
            jq -r '.statistics.by_category | to_entries[] | "    \(.key): \(.value)"' docs/DOCS_REPORT.json
        else
            log_warning "jq 未安装，跳过JSON解析"
        fi
        
        # 3. 提交报告
        if [ -n "$(git status --porcelain docs/DOCS_REPORT.json)" ]; then
            git add docs/DOCS_REPORT.json
            git commit -m "docs: 自动生成月度文档报告 [skip ci]"
            log_success "月度报告已提交"
        fi
        
        # 4. 发送月度报告（可选）
        # cat docs/DOCS_REPORT.json | mail -s "CozyChat月度文档报告" team@example.com
        
    else
        log_error "详细报告生成失败"
        return 1
    fi
    
    log_success "每月文档维护任务完成"
}

# 主函数
main() {
    local task="${1:-daily}"
    
    log_info "==================================="
    log_info "文档维护任务: $task"
    log_info "==================================="
    
    case "$task" in
        daily)
            daily_task
            ;;
        weekly)
            weekly_task
            ;;
        monthly)
            monthly_task
            ;;
        all)
            daily_task
            weekly_task
            monthly_task
            ;;
        *)
            log_error "未知任务: $task"
            echo "使用方法: $0 {daily|weekly|monthly|all}"
            exit 1
            ;;
    esac
    
    log_info "==================================="
    log_success "所有任务完成！"
    log_info "==================================="
}

# 执行主函数
main "$@"

