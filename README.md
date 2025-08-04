# Discord IP Bot

> 🎮 **Minecraft 伺服器 IP 自動通知系統**  
> 每日自動檢測 IP 變化並發送到 Discord，讓玩家隨時知道伺服器連線資訊

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows-lightgrey.svg)](https://github.com/yourusername/discord-IP-bot)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## ✨ 功能特色

- 🤖 **自動化排程**：每天固定時間自動檢測 IP 變化
- 🎯 **智能變化檢測**：只有 IP 真正變化時才發送通知，避免騷擾
- 📱 **Discord 通知**：IP 變化時自動發送到指定 Discord 頻道
- 💾 **歷史記錄管理**：持久化追蹤 IP 變化歷史和統計資訊
- 🔧 **手動觸發**：支援即時手動執行，無需等待排程
- 🖥️ **實時監控**：可視化狀態介面，隨時了解系統運行情況
- 🌐 **跨平台支援**：完美支援 macOS 和 Windows 10/11
- ⚡ **輕量高效**：記憶體使用 < 40MB，CPU 使用接近 0%
- 🛡️ **穩定可靠**：完善的錯誤處理和重試機制
- 📊 **詳細日誌**：完整的執行歷史和除錯資訊

## 🎮 Minecraft 玩家體驗

當您的伺服器 IP 變化時，玩家會在 Discord 收到：

```
Minecraft Server IP: 36.230.8.13:25565
```

玩家可以直接複製這個地址連線到您的 Minecraft 伺服器！

## 🚀 快速開始

### 1. 環境準備

```bash
# 確保 Python 版本
python --version  # 需要 Python 3.10+

# 複製專案
git clone https://github.com/yourusername/discord-IP-bot.git
cd discord-IP-bot
```

### 2. 安裝依賴

```bash
# 建立虛擬環境
python -m venv venv

# 啟動虛擬環境
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt
```

### 3. Discord 設定

1. **建立 Webhook**：
   - 進入您的 Discord 伺服器
   - 選擇要接收通知的頻道
   - 頻道設定 → 整合 → Webhooks → 新增 Webhook
   - 複製 Webhook URL

2. **設定環境變數**：
   ```bash
   # 編輯 .env 檔案
   cp .env.example .env
   
   # 在 .env 檔案中設定：
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN
   ```

### 4. 測試系統

```bash
# 啟動虛擬環境
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows

# 測試所有功能（不會發送 Discord 訊息）
python main.py --test --verbose

# 檢查系統狀態
python main.py --status
```

## 📖 使用方法

> ⚠️ **重要**：所有操作都必須在虛擬環境中執行

### 啟動虛擬環境

每次使用前，請先啟動虛擬環境：

```bash
# macOS/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate

# 確認虛擬環境已啟動（命令提示符前會顯示 (venv)）
```

### 🤖 排程模式（每日自動執行）

啟動自動化系統，每天 9:00 AM 自動檢測並通知：

```bash
# 1. 啟動虛擬環境
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows

# 2. 啟動排程系統
python main.py --daemon
```

**您會看到：**
```
🤖 Discord IP Bot - 排程模式運行中
============================================================
📅 排程設定: 每天 09:00 AM
⏰ 當前時間: 2024-01-15 14:32:15
⏳ 下次執行: 2024-01-16 09:00:00 (18小時27分鐘後)
📊 執行狀態: 💤 等待中
💻 系統資源: RAM: 35.0MB, CPU: 0.1%
⏱️  運行時間: 2:15:30

📋 執行歷史:
[09:00:15] ✅ 排程 - Discord通知 → Discord發送成功
[09:00:12] ℹ️  排程 - IP變化檢測 → IP無變化，跳過發送
[08:59:08] ✅ 排程 - IP檢測 → 成功

💡 提示: 按 Ctrl+C 停止排程，手動執行請開啟新terminal運行 'source venv/bin/activate && python main.py --manual'
```

**系統行為：**
- 🔄 **每分鐘更新**：狀態畫面每分鐘刷新一次
- 📅 **每日執行**：每天 9:00 AM 自動檢測 IP
- 🎯 **智能通知**：只有 IP 變化時才發送 Discord 通知
  - 🏃 **首次執行**：第一次運行時會發送通知（建立基準）
  - 🔍 **變化檢測**：自動比較當前IP與上次記錄
  - 📝 **歷史追蹤**：所有檢測都會記錄到 `config/ip_history.json`
  - 💡 **節省資源**：相同IP時跳過Discord API調用
- 📊 **即時監控**：顯示系統資源使用和執行歷史
- 🛡️ **自動恢復**：網路異常時自動重試

### 🔧 手動模式（立即執行）

在排程運行時，您可以開啟新終端立即執行：

```bash
# 1. 啟動虛擬環境
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows

# 2. 執行手動模式
python main.py --manual
```

**您會看到：**
```
🔧 手動執行模式
========================================
✅ 手動執行成功！
📱 已發送當前IP到Discord
```

**系統行為：**
- ⚡ **立即執行**：不等待排程時間，馬上檢測並發送
- 🚫 **無衝突**：可在排程運行時安全使用
- 📱 **強制發送**：無論 IP 是否變化都會發送通知
- 📝 **更新歷史**：會記錄到歷史檔案並更新當前IP基準
- ⏱️ **快速完成**：通常在 3-5 秒內完成
- 🎯 **用途場景**：測試系統、手動獲取IP、重建IP基準

### 🧪 測試模式（驗證功能）

驗證所有功能但不發送 Discord 訊息：

```bash
# 1. 啟動虛擬環境
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows

# 2. 執行測試模式
python main.py --test --verbose
```

**您會看到：**
```
🧪 測試模式
========================================
💡 測試模式不會發送Discord訊息

🔧 測試設定...
  ✅ Discord Webhook URL: 已設定
🌐 測試IP檢測...
  🏠 本地IP: 192.168.50.55
  🌍 公共IP: 36.230.8.13
  ✅ IP檢測: 正常
📱 測試Discord連線...
  ✅ Discord連線: 正常

📋 執行完整測試流程...
✅ 測試模式執行成功！
💡 所有功能正常，可以切換到正式模式
```

### 📊 狀態檢查（了解系統狀況）

檢查系統當前狀態和配置：

```bash
# 1. 啟動虛擬環境
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows

# 2. 檢查系統狀態
python main.py --status
```

**您會看到：**
```
📊 Discord IP Bot 系統狀態
==================================================
🔧 測試設定...
  ✅ Discord Webhook URL: 已設定
🌐 測試IP檢測...
  🏠 本地IP: 192.168.50.55
  🌍 公共IP: 36.230.8.13
  ✅ IP檢測: 正常
📱 測試Discord連線...
  ✅ Discord連線: 正常

🤖 排程系統狀態:
  運行狀態: ✅ 運行中
  執行狀態: 💤 等待中
  啟動時間: 2024-01-15 09:00:00
  上次執行: 2024-01-15 09:00:15
  執行次數: 5
  系統資源: {'memory': '35.0MB', 'cpu': '0.1%', 'uptime': '5:30:15'}

🎉 系統狀態檢查完成
```

## 🎯 智能 IP 變化檢測原理

### 🔍 檢測機制

本系統採用先進的智能變化檢測機制，能有效避免不必要的 Discord 通知：

#### 📊 **檢測流程**

1. **🏃 首次執行**
   - 建立 IP 歷史記錄檔案：`config/ip_history.json`
   - 記錄當前 IP 作為基準
   - 發送初始通知到 Discord

2. **🔄 後續檢測（排程模式）**
   - 檢測當前 IP 地址
   - 與歷史記錄中的最後 IP 比較
   - ✅ **IP 有變化** → 發送 Discord 通知 + 更新記錄
   - ⏭️ **IP 無變化** → 跳過通知，僅記錄檢測事件

3. **🔧 手動執行**
   - 總是發送 Discord 通知（無論 IP 是否變化）
   - 更新歷史記錄中的基準 IP
   - 適用於測試或手動獲取當前 IP

#### 📁 **歷史記錄檔案**

系統自動維護詳細的 IP 變化歷史：

```json
{
  "metadata": {
    "total_checks": 42,
    "created_at": "2025-01-04T09:00:00+08:00",
    "last_updated": "2025-01-04T20:21:04+08:00"
  },
  "current": {
    "public_ip": "36.230.8.13",
    "last_updated": "2025-01-04T20:21:04+08:00",
    "last_notification_sent": "2025-01-04T09:00:15+08:00"
  },
  "statistics": {
    "total_ip_changes": 5,
    "total_notifications_sent": 12,
    "check_frequency": {
      "scheduled": 35,
      "manual": 7,
      "test": 15
    }
  }
}
```

#### 🎯 **不同模式行為**

| 模式 | IP 無變化時 | IP 有變化時 | 更新歷史 | 適用場景 |
|------|-------------|-------------|----------|----------|
| 🤖 **排程模式** | ⏭️ 跳過通知 | ✅ 發送通知 | ✅ 是 | 日常自動監控 |
| 🔧 **手動模式** | ✅ 發送通知 | ✅ 發送通知 | ✅ 是 | 測試、強制獲取 |
| 🧪 **測試模式** | ⏭️ 跳過通知 | ⏭️ 跳過通知 | ❌ 否 | 功能驗證 |

### 💡 **使用建議**

- **首次設定**：使用手動模式 (`--manual`) 建立初始基準
- **日常使用**：讓排程模式 (`--daemon`) 自動監控
- **故障排除**：使用測試模式 (`--test`) 驗證功能
- **強制通知**：需要立即通知時使用手動模式

## 🛑 如何終止系統

### 終止排程模式

在運行排程的終端按下：

```
Ctrl + C
```

**您會看到：**
```
🛑 收到終止信號，正在安全關閉排程系統...
⏳ 等待當前任務完成...
✅ 排程系統已安全關閉
💾 執行歷史已保存到 logs/scheduler.log
👋 再見！
```

### 強制終止（如需要）

如果正常終止無效：

```bash
# 查找進程
ps aux | grep "main.py --daemon"

# 強制終止（替換 <PID> 為實際進程ID）
kill -9 <PID>
```

## ⚙️ 配置系統說明

### 配置方式和優先順序

本專案使用多層配置系統，按以下優先順序讀取配置：

1. **環境變數**（最高優先級）- 系統或shell中設定的環境變數
2. **`.env` 文件**（推薦方式）- 專案根目錄的配置文件
3. **程式預設值**（最低優先級）- 程式碼中的預設設定

### 如何配置專案

#### 步驟1：創建配置文件

**初次設定：**
```bash
# 複製範例配置文件
cp .env.example .env
```

**如果沒有 .env.example，手動創建 .env：**
```bash
# 創建 .env 文件
cat > .env << 'EOF'
# Discord IP Bot 配置文件

# Discord Webhook URL（必填）
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN

# 排程時間（24小時制，格式：HH:MM）
SCHEDULE_TIME=21:30

# 日誌級別（DEBUG, INFO, WARNING, ERROR, CRITICAL）
LOG_LEVEL=INFO
EOF
```

#### 步驟2：設定必要參數

編輯 `.env` 文件，設定您的參數：

```bash
# 設定您的 Discord Webhook URL
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/1234567890/your_webhook_token_here

# 設定排程時間（例如：每天晚上9:30執行）
SCHEDULE_TIME=21:30
```

### 常用配置選項

#### 修改排程時間

```bash
# 每天早上9:00執行
SCHEDULE_TIME=09:00

# 每天晚上11:30執行  
SCHEDULE_TIME=23:30

# 每天中午12:00執行
SCHEDULE_TIME=12:00
```

#### 調整日誌級別

```bash
# 詳細除錯資訊（開發用）
LOG_LEVEL=DEBUG

# 一般資訊（預設）
LOG_LEVEL=INFO

# 只顯示警告和錯誤
LOG_LEVEL=WARNING

# 只顯示錯誤
LOG_LEVEL=ERROR
```

#### 自訂 Discord 訊息

```bash
# 預設格式
DISCORD_MESSAGE_TEMPLATE=Minecraft Server IP: {ip}:25565

# 自訂格式
DISCORD_MESSAGE_TEMPLATE=🎮 我的遊戲伺服器：{ip}:25565

# 包含時間的格式
DISCORD_MESSAGE_TEMPLATE=伺服器IP更新：{ip}:25565 (更新時間：{timestamp})
```

#### Discord 連線設定

```bash
# Discord 請求逾時（秒）
DISCORD_TIMEOUT=10

# Discord 重試次數
DISCORD_RETRY_ATTEMPTS=3
```

#### IP 檢測設定

```bash
# IP 檢測逾時（秒）
IP_CHECK_TIMEOUT=10

# IP 檢測重試次數
IP_RETRY_ATTEMPTS=3

# 是否檢測本地IP（true/false）
CHECK_LOCAL_IP=true

# 是否檢測公共IP（true/false）
CHECK_PUBLIC_IP=true
```

### 配置驗證

設定完成後，可以驗證配置是否正確：

```bash
# 啟動虛擬環境
source venv/bin/activate

# 驗證配置
python src/config.py
```

**成功的輸出範例：**
```
=== Discord IP Bot - 設定管理器測試 ===

📝 初始化設定管理器...
✅ 設定管理器初始化成功

🧪 測試特定設定取得:
  應用程式名稱: Discord IP Bot
  排程時間: 21:30
  Discord重試次數: 3
```

### ⚠️ 重要提醒

1. **`.env` 文件包含敏感資訊**，已加入 `.gitignore`，不會被提交到版本控制
2. **設定優先順序**：如果您同時設定了環境變數和 `.env` 文件，環境變數會優先生效
3. **時間格式**：排程時間必須使用24小時制，格式為 `HH:MM`
4. **重新載入**：修改 `.env` 文件後需要重新啟動程式才會生效

## 📂 專案結構

```
discord-IP-bot/
├── main.py                 # 主程式入口
├── requirements.txt        # Python 依賴
├── .env                   # 環境變數設定
├── README.md              # 說明文件
├── src/                   # 核心模組
│   ├── config.py          # 設定管理
│   ├── logger.py          # 日誌系統
│   ├── scheduler.py       # 排程管理
│   ├── ip_detector.py     # IP 檢測
│   └── discord_client.py  # Discord 通信
├── tests/                 # 測試檔案
├── logs/                  # 日誌檔案
│   ├── discord_ip_bot.log # 主要日誌
│   ├── scheduler.log      # 排程日誌
│   └── error.log          # 錯誤日誌
└── data/                  # 資料檔案
    └── ip_history.json    # IP 歷史記錄
```

## 🔧 故障排除

### 常見問題

**Q: 排程沒有執行？**
```bash
# 啟動虛擬環境
source venv/bin/activate

# 檢查排程狀態
python main.py --status

# 查看排程日誌
tail -f logs/scheduler.log
```

**Q: Discord 訊息發送失敗？**
```bash
# 啟動虛擬環境
source venv/bin/activate

# 測試 Discord 連線
python main.py --test

# 檢查 Webhook URL 是否正確
cat .env | grep DISCORD_WEBHOOK_URL
```

**Q: IP 檢測失敗？**
```bash
# 啟動虛擬環境
source venv/bin/activate

# 測試網路連線
curl -s http://api.ipify.org

# 檢查防火牆設定
python main.py --test --verbose
```

### 日誌查看

```bash
# 查看最新日誌
tail -f logs/discord_ip_bot.log

# 查看錯誤日誌
tail -f logs/error.log

# 查看排程歷史
cat logs/scheduler.log
```

## 📊 系統需求

- **Python**: 3.10 或更高版本
- **作業系統**: macOS, Windows 10/11, Linux
- **記憶體**: 最少 100MB 可用記憶體
- **網路**: 穩定的網際網路連線
- **Discord**: Webhook URL（從 Discord 伺服器取得）

## 🔒 安全性

- ✅ **環境變數保護**：敏感資訊存放在 `.env` 檔案
- ✅ **最小權限原則**：只需要 Webhook 權限，無需 Bot Token
- ✅ **本地執行**：所有資料保存在本機，無外部依賴
- ✅ **安全通信**：使用 HTTPS 與 Discord API 通信

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

1. Fork 此專案
2. 建立 feature 分支：`git checkout -b feature/amazing-feature`
3. 提交變更：`git commit -m 'Add amazing feature'`
4. Push 到分支：`git push origin feature/amazing-feature`
5. 開啟 Pull Request

## 📜 授權

此專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 檔案

## 🙏 致謝

感謝所有貢獻者和 Python 開源社群的支援！

---

## 💡 重要提醒

⚠️ **請記住**：所有 `python main.py` 命令都必須在啟動虛擬環境後執行！

```bash
# 每次使用前都要執行
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows

# 確認看到 (venv) 前綴後再執行其他命令
(venv) $ python main.py --daemon
```

---

**💡 提示**: 如果您喜歡這個專案，請給我們一個 ⭐！

**📧 支援**: 如有問題請開啟 [Issue](https://github.com/yourusername/discord-IP-bot/issues)

**🎮 享受遊戲**: 讓您的 Minecraft 伺服器管理變得更輕鬆！