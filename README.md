# Discord IP Bot

> 🎮 **Minecraft 伺服器 IP 自動通知系統**  
> 每日自動檢測 IP 變化並發送到 Discord，讓玩家隨時知道伺服器連線資訊

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows-lightgrey.svg)](https://github.com/yourusername/discord-IP-bot)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## ✨ 功能特色

- 🤖 **自動化排程**：每天固定時間自動檢測 IP 變化
- 📱 **Discord 通知**：IP 變化時自動發送到指定 Discord 頻道
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
- ⏱️ **快速完成**：通常在 3-5 秒內完成

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

## ⚙️ 自訂設定

### 修改排程時間

編輯 `.env` 檔案：

```bash
# 改為每天 10:30 AM 執行
SCHEDULE_TIME=10:30
```

### 修改訊息格式

```bash
# 自訂 Discord 訊息格式
DISCORD_MESSAGE_TEMPLATE=我的伺服器IP: {ip}:25565
```

### 調整日誌級別

```bash
# 設定詳細除錯資訊
LOG_LEVEL=DEBUG

# 或設定簡潔輸出
LOG_LEVEL=WARNING
```

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