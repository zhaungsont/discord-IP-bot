#!/usr/bin/env python3
"""
虛擬環境設定腳本 - Discord IP Bot

此腳本幫助建立和設定Python虛擬環境，確保專案在隔離環境中執行。
支援 Windows、MacOS 和 Linux。
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def check_python_version():
    """檢查Python版本是否符合要求"""
    current_version = sys.version_info
    required_version = (3, 10)

    print(
        f"當前Python版本: {current_version.major}.{current_version.minor}.{current_version.micro}"
    )
    print(f"要求Python版本: {required_version[0]}.{required_version[1]}+")

    if current_version[:2] < required_version:
        print(
            f"❌ Python版本過低，需要Python {required_version[0]}.{required_version[1]}或更高版本"
        )
        return False

    print("✅ Python版本符合要求")
    return True


def create_venv():
    """建立虛擬環境"""
    venv_path = Path("venv")

    if venv_path.exists():
        print("📁 虛擬環境目錄已存在")
        return True

    try:
        print("🔧 建立虛擬環境...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ 虛擬環境建立成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 建立虛擬環境失敗: {e}")
        return False


def get_activation_command():
    """獲取虛擬環境啟動命令"""
    system = platform.system()

    if system == "Windows":
        return "venv\\Scripts\\activate"
    else:  # MacOS, Linux
        return "source venv/bin/activate"


def install_dependencies():
    """安裝依賴套件"""
    system = platform.system()

    if system == "Windows":
        pip_path = Path("venv/Scripts/pip")
    else:
        pip_path = Path("venv/bin/pip")

    if not pip_path.exists():
        print("❌ 找不到虛擬環境中的pip")
        return False

    try:
        print("📦 安裝依賴套件...")
        subprocess.run([str(pip_path), "install", "-r", "requirements.txt"], check=True)
        print("✅ 依賴套件安裝成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 安裝依賴套件失敗: {e}")
        return False


def create_env_file():
    """建立環境變數檔案"""
    env_file = Path(".env")
    env_example = Path(".env.example")

    if env_file.exists():
        print("📄 .env 檔案已存在")
        return True

    # 建立 .env.example 檔案
    env_example_content = """# Discord IP Bot 環境變數設定

# Discord Webhook 設定 (唯一需要的Discord配置)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN

# 應用程式設定
APP_NAME=Discord IP Bot
LOG_LEVEL=INFO
SCHEDULE_TIME=08:00

# IP檢測設定
CHECK_PUBLIC_IP=true
CHECK_LOCAL_IP=true
IP_CHECK_TIMEOUT=10
"""

    try:
        with open(env_example, "w", encoding="utf-8") as f:
            f.write(env_example_content)
        print("✅ .env.example 檔案建立成功")

        # 複製到 .env
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(env_example_content)
        print("✅ .env 檔案建立成功")
        print("⚠️  請編輯 .env 檔案，填入正確的Discord設定")

        return True
    except Exception as e:
        print(f"❌ 建立環境變數檔案失敗: {e}")
        return False


def create_gitignore():
    """建立.gitignore檔案"""
    gitignore_file = Path(".gitignore")

    if gitignore_file.exists():
        print("📄 .gitignore 檔案已存在")
        return True

    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# 虛擬環境
venv/
env/
ENV/

# 環境變數
.env

# 日誌檔案
logs/
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# MacOS
.DS_Store

# Windows
Thumbs.db
ehthumbs.db
Desktop.ini

# 專案特定
config/local.json
src/__pycache__/
tests/__pycache__/
"""

    try:
        with open(gitignore_file, "w", encoding="utf-8") as f:
            f.write(gitignore_content)
        print("✅ .gitignore 檔案建立成功")
        return True
    except Exception as e:
        print(f"❌ 建立.gitignore檔案失敗: {e}")
        return False


def test_installation():
    """測試安裝是否成功"""
    system = platform.system()

    if system == "Windows":
        python_path = Path("venv/Scripts/python")
    else:
        python_path = Path("venv/bin/python")

    if not python_path.exists():
        print("❌ 找不到虛擬環境中的Python")
        return False

    try:
        print("🧪 測試IP檢測器模組...")
        result = subprocess.run(
            [
                str(python_path),
                "-c",
                "import sys; sys.path.append('src'); from ip_detector import IPDetector; print('✅ IP檢測器模組載入成功')",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        print(result.stdout.strip())
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 模組測試失敗: {e}")
        print(f"錯誤輸出: {e.stderr}")
        return False


def print_next_steps():
    """列印後續步驟說明"""
    system = platform.system()
    activation_cmd = get_activation_command()

    print("\n" + "=" * 60)
    print("🎉 環境設定完成！")
    print("=" * 60)
    print()
    print("📝 後續步驟:")
    print(f"1. 啟動虛擬環境:")
    print(f"   {activation_cmd}")
    print()
    print("2. 編輯環境變數檔案:")
    print("   編輯 .env 檔案，填入您的Discord設定")
    print()
    print("3. 測試IP檢測器:")

    if system == "Windows":
        print("   python src\\ip_detector.py")
        print("   或者")
        print("   python tests\\test_ip_detector.py")
    else:
        print("   python src/ip_detector.py")
        print("   或者")
        print("   python tests/test_ip_detector.py")

    print()
    print("4. 執行完整測試:")
    print("   python -m pytest tests/ -v")
    print()
    print("💡 提示:")
    print("- 所有開發工作都應在虛擬環境中進行")
    print("- 使用 'deactivate' 命令退出虛擬環境")
    print("- 每次開啟新終端都需要重新啟動虛擬環境")


def main():
    """主函數"""
    print("🚀 Discord IP Bot - 虛擬環境設定")
    print(f"💻 作業系統: {platform.system()} {platform.release()}")
    print("=" * 50)

    # 檢查Python版本
    if not check_python_version():
        return False

    print()

    # 建立虛擬環境
    if not create_venv():
        return False

    print()

    # 安裝依賴套件
    if not install_dependencies():
        return False

    print()

    # 建立環境檔案
    if not create_env_file():
        return False

    print()

    # 建立.gitignore
    if not create_gitignore():
        return False

    print()

    # 測試安裝
    if not test_installation():
        return False

    # 列印後續步驟
    print_next_steps()

    return True


if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print("\n❌ 設定過程中發生錯誤，請檢查上述訊息")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ 設定過程被中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 未預期錯誤: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
