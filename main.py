#!/usr/bin/env python3
"""
Discord IP Bot - 主程式

Minecraft 伺服器 IP 地址自動通知系統
支援排程自動執行和手動觸發模式

使用方式:
    python main.py --daemon    # 啟動排程守護程式
    python main.py --manual    # 手動執行
    python main.py --test      # 測試模式
    python main.py --status    # 顯示狀態
    python main.py --check     # 檢查設定
"""

import sys
import argparse
from pathlib import Path

# 確保 src 目錄在 Python 路徑中
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from src.config import ConfigManager, ConfigError
    from src.logger import LoggerManager
    from src.scheduler import SchedulerManager
    from src.ip_detector import IPDetector, NetworkError
    from src.discord_client import DiscordClient, WebhookError
except ImportError as e:
    print(f"❌ 模組導入失敗: {e}")
    print("💡 請確保所有必要的模組都已正確安裝")
    sys.exit(1)


class IPBotApplication:
    """Discord IP Bot 主應用程式"""

    def __init__(self):
        """初始化應用程式"""
        self.config = None
        self.log_manager = None
        self.logger = None
        self.scheduler = None

        try:
            # 初始化核心組件
            self.config = ConfigManager()
            self.log_manager = LoggerManager(self.config)
            self.logger = self.log_manager.get_logger("main")

            self.logger.info("Discord IP Bot 應用程式啟動")

        except ConfigError as e:
            print(f"❌ 設定錯誤: {e}")
            print("💡 請檢查 .env 檔案和環境變數設定")
            sys.exit(1)
        except Exception as e:
            print(f"❌ 初始化失敗: {e}")
            sys.exit(1)

    def run_daemon_mode(self):
        """運行守護程式模式"""
        self.logger.info("啟動守護程式模式")

        try:
            self.scheduler = SchedulerManager(self.config)
            self.scheduler.start_daemon()
        except KeyboardInterrupt:
            self.logger.info("使用者中斷守護程式")
        except Exception as e:
            self.logger.error(f"守護程式異常: {e}")
            print(f"❌ 守護程式運行失敗: {e}")
            sys.exit(1)

    def run_manual_mode(self):
        """運行手動模式"""
        self.logger.info("執行手動模式")

        print("🔧 手動執行模式")
        print("=" * 40)

        try:
            # 使用排程管理器執行手動任務
            self.scheduler = SchedulerManager(self.config)
            success = self.scheduler.manual_task()

            if success:
                print("✅ 手動執行成功！")
                print("📱 已發送當前IP到Discord")
            else:
                print("❌ 手動執行失敗")
                print("💡 請檢查網路連線和設定")
                sys.exit(1)

        except Exception as e:
            self.logger.error(f"手動執行失敗: {e}")
            print(f"❌ 手動執行失敗: {e}")
            sys.exit(1)

    def run_test_mode(self, verbose: bool = False):
        """運行測試模式"""
        self.logger.info("執行測試模式")

        print("🧪 測試模式")
        print("=" * 40)
        print("💡 測試模式不會發送Discord訊息")
        print()

        try:
            # 測試各個組件
            self._test_config()
            self._test_ip_detection()
            self._test_discord_connection()

            if verbose:
                self._show_detailed_info()

            # 執行測試任務
            print("📋 執行完整測試流程...")
            self.scheduler = SchedulerManager(self.config)
            success = self.scheduler.test_task()

            if success:
                print("✅ 測試模式執行成功！")
                print("💡 所有功能正常，可以切換到正式模式")
            else:
                print("❌ 測試執行失敗")
                sys.exit(1)

        except Exception as e:
            self.logger.error(f"測試執行失敗: {e}")
            print(f"❌ 測試執行失敗: {e}")
            sys.exit(1)

    def show_status(self):
        """顯示系統狀態"""
        print("📊 Discord IP Bot 系統狀態")
        print("=" * 50)

        try:
            # 檢查各組件狀態
            self._test_config()
            self._test_ip_detection()
            self._test_discord_connection()

            # 如果有排程系統在運行，顯示其狀態
            try:
                self.scheduler = SchedulerManager(self.config)
                status = self.scheduler.get_status_info()

                print()
                print("🤖 排程系統狀態:")
                print(
                    f"  運行狀態: {'✅ 運行中' if status['is_running'] else '❌ 未運行'}"
                )
                print(
                    f"  執行狀態: {'🔄 執行中' if status['is_executing'] else '💤 等待中'}"
                )
                print(
                    f"  啟動時間: {status['start_time'].strftime('%Y-%m-%d %H:%M:%S') if status['start_time'] else 'N/A'}"
                )
                print(
                    f"  上次執行: {status['last_execution'].strftime('%Y-%m-%d %H:%M:%S') if status['last_execution'] else '尚未執行'}"
                )
                print(f"  執行次數: {status['execution_count']}")
                print(f"  系統資源: {status['system_info']}")

            except Exception as e:
                print(f"⚠️  無法取得排程狀態: {e}")

            print()
            print("🎉 系統狀態檢查完成")

        except Exception as e:
            self.logger.error(f"狀態檢查失敗: {e}")
            print(f"❌ 狀態檢查失敗: {e}")
            sys.exit(1)

    def check_configuration(self):
        """檢查設定"""
        print("🔧 設定檢查")
        print("=" * 40)

        try:
            # 顯示安全的設定資訊
            config_info = self.config.get_all_config()

            for section, settings in config_info.items():
                print(f"\n📋 [{section.upper()}]:")
                for key, value in settings.items():
                    print(f"  {key}: {value}")

            print()
            print("✅ 設定檢查完成")

        except Exception as e:
            print(f"❌ 設定檢查失敗: {e}")
            sys.exit(1)

    def _test_config(self):
        """測試設定"""
        print("🔧 測試設定...")
        try:
            discord_config = self.config.get_discord_config()
            webhook_url = discord_config.get("webhook_url")

            if webhook_url:
                print("  ✅ Discord Webhook URL: 已設定")
            else:
                print("  ❌ Discord Webhook URL: 未設定")
                raise ConfigError("Discord Webhook URL 未設定")

        except Exception as e:
            print(f"  ❌ 設定測試失敗: {e}")
            raise

    def _test_ip_detection(self):
        """測試IP檢測"""
        print("🌐 測試IP檢測...")
        try:
            ip_detector = IPDetector()

            # 測試本地IP
            local_ip = ip_detector.get_local_ip()
            print(f"  🏠 本地IP: {local_ip}")

            # 測試公共IP
            public_ip = ip_detector.get_public_ip()
            print(f"  🌍 公共IP: {public_ip}")

            if public_ip and public_ip != "無法獲取":
                print("  ✅ IP檢測: 正常")
            else:
                print("  ❌ IP檢測: 失敗")
                raise NetworkError("無法獲取公共IP")

        except Exception as e:
            print(f"  ❌ IP檢測失敗: {e}")
            raise

    def _test_discord_connection(self):
        """測試Discord連線"""
        print("📱 測試Discord連線...")
        try:
            webhook_url = self.config.get("discord", "webhook_url")
            discord_client = DiscordClient(webhook_url)

            # 測試連線
            test_result = discord_client.test_connection()

            if test_result:
                print("  ✅ Discord連線: 正常")
            else:
                print("  ❌ Discord連線: 失敗")
                raise WebhookError("Discord連線測試失敗")

        except Exception as e:
            print(f"  ❌ Discord測試失敗: {e}")
            raise

    def _show_detailed_info(self):
        """顯示詳細資訊"""
        print()
        print("📄 詳細資訊:")

        # 顯示版本資訊
        import platform

        print(f"  Python版本: {platform.python_version()}")
        print(f"  作業系統: {platform.system()} {platform.release()}")

        # 顯示設定檔案位置
        print(f"  設定檔案: {self.config.env_file}")

        # 顯示日誌檔案位置
        logs_dir = self.config.get("system", "logs_dir")
        print(f"  日誌目錄: {logs_dir}/")

        # 顯示最近的執行記錄
        recent_logs = self.log_manager.get_recent_logs(3, "scheduler")
        if recent_logs:
            print("  最近執行:")
            for log_line in recent_logs:
                print(f"    {log_line.strip()}")


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description="Discord IP Bot - Minecraft 伺服器 IP 自動通知系統",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  python main.py --daemon          啟動排程守護程式（每天自動執行）
  python main.py --manual          手動執行一次（立即發送當前IP）
  python main.py --test            測試模式（不發送Discord訊息）
  python main.py --status          顯示系統狀態
  python main.py --check           檢查設定
  python main.py --test --verbose  詳細測試模式

注意:
  - 守護程式模式會持續運行，按 Ctrl+C 停止
  - 手動模式可在守護程式運行時使用（開啟新終端）
  - 測試模式用於驗證功能但不發送Discord訊息
        """,
    )

    # 主要模式選項（互斥）
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--daemon", action="store_true", help="啟動排程守護程式")
    mode_group.add_argument("--manual", action="store_true", help="手動執行一次")
    mode_group.add_argument(
        "--test", action="store_true", help="測試模式（不發送Discord）"
    )
    mode_group.add_argument("--status", action="store_true", help="顯示系統狀態")
    mode_group.add_argument("--check", action="store_true", help="檢查設定")

    # 附加選項
    parser.add_argument("--verbose", "-v", action="store_true", help="顯示詳細資訊")
    parser.add_argument("--version", action="version", version="Discord IP Bot v1.0")

    args = parser.parse_args()

    try:
        # 建立應用程式實例
        app = IPBotApplication()

        # 根據參數執行相應功能
        if args.daemon:
            app.run_daemon_mode()
        elif args.manual:
            app.run_manual_mode()
        elif args.test:
            app.run_test_mode(verbose=args.verbose)
        elif args.status:
            app.show_status()
        elif args.check:
            app.check_configuration()

    except KeyboardInterrupt:
        print("\n👋 使用者中斷，程式結束")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 程式執行失敗: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
