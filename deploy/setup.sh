#!/usr/bin/env bash
set -e

# ============================================
# FlowMind 一键部署脚本
# 适用: Ubuntu 20.04+ / Debian 11+ / CentOS 8+
# ============================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()  { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# ---------- 配置 ----------
APP_DIR="/opt/flowmind"
REPO_URL="https://github.com/confusedstardust/FlowMind.git"
DOMAIN="${1:-localhost}"

# ---------- 检查 root ----------
if [ "$EUID" -ne 0 ]; then
    err "请用 root 运行: sudo bash setup.sh [你的域名]"
fi

# ---------- 1. 安装系统依赖 ----------
log "安装系统依赖..."
if command -v apt &>/dev/null; then
    apt update -qq
    apt install -y -qq python3 python3-venv python3-pip nginx git
elif command -v yum &>/dev/null; then
    yum install -y python3 python3-pip nginx git
else
    err "不支持的系统，请手动安装 Python 3.10+, nginx, git"
fi

# ---------- 2. 拉取代码 ----------
log "拉取项目代码..."
if [ -d "$APP_DIR" ]; then
    cd "$APP_DIR"
    git pull origin main
else
    git clone "$REPO_URL" "$APP_DIR"
    cd "$APP_DIR"
fi

# ---------- 3. 创建 venv 并安装依赖 ----------
log "创建 Python 虚拟环境..."
python3 -m venv venv
"$APP_DIR/venv/bin/pip" install -r requirements.txt -q

# ---------- 4. 配置 .env ----------
if [ ! -f "$APP_DIR/.env" ]; then
    warn "请配置 DeepSeek API Key..."
    read -rp "请输入 DeepSeek API Key (sk-...): " API_KEY
    cat > "$APP_DIR/.env" << EOF
DEEPSEEK_API_KEY=$API_KEY
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
EOF
    log ".env 已创建"
else
    log ".env 已存在，跳过"
fi

# ---------- 5. 设置权限 ----------
chown -R www-data:www-data "$APP_DIR"
chmod 600 "$APP_DIR/.env"

# ---------- 6. 安装 systemd 服务 ----------
log "配置 systemd 服务..."
cp "$APP_DIR/deploy/flowmind.service" /etc/systemd/system/flowmind.service
systemctl daemon-reload
systemctl enable flowmind
systemctl restart flowmind
log "FlowMind 服务已启动"

# ---------- 7. 配置 nginx ----------
log "配置 nginx..."
sed "s/your-domain.com/$DOMAIN/g" "$APP_DIR/deploy/flowmind.nginx.conf" > /etc/nginx/sites-available/flowmind
ln -sf /etc/nginx/sites-available/flowmind /etc/nginx/sites-enabled/flowmind

# 确保默认站点不冲突
rm -f /etc/nginx/sites-enabled/default

nginx -t && systemctl reload nginx
log "nginx 已配置"

# ---------- 完成 ----------
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  FlowMind 部署完成！${NC}"
echo -e "${GREEN}  访问地址: http://$DOMAIN${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "常用命令:"
echo "  查看状态:  systemctl status flowmind"
echo "  查看日志:  journalctl -u flowmind -f"
echo "  重启服务:  systemctl restart flowmind"
echo "  更新代码:  cd $APP_DIR && git pull && systemctl restart flowmind"
