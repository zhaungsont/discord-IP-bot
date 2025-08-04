"""
排程系統模組 - Discord IP Bot

負責管理定時任務、實時狀態顯示和系統監控
支援每日自動執行和手動觸發模式
"""

import os
import sys
import time
import signal
import schedule
import psutil
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

try:
    from .config import ConfigManager
    from .logger import LoggerManager
    from .ip_detector import IPDetector
    from .discord_client import DiscordClient
except ImportError:
    # 用於直接執行此模組時
    from config import ConfigManager
    from logger import LoggerManager
    from ip_detector import IPDetector
    from discord_client import DiscordClient


class ExecutionRecord:
    """執行記錄"""

    def __init__(
        self,
        mode: str,
        action: str,
        result: str,
        details: str = "",
        timestamp: datetime = None,
    ):
        self.timestamp = timestamp or datetime.now()
        self.mode = mode
        self.action = action
        self.result = result
        self.details = details

    def __str__(self):
        time_str = self.timestamp.strftime("%H:%M:%S")
        status_icon = (
            "✅"
            if "成功" in self.result or "完成" in self.result
            else "❌" if "失敗" in self.result else "ℹ️"
        )
        return f"[{time_str}] {status_icon} {self.mode} - {self.action} → {self.result}"


class SchedulerManager:
    """排程管理器"""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        初始化排程管理器

        Args:
            config_manager: 設定管理器實例
        """
        self.config = config_manager or ConfigManager()
        self.log_manager = LoggerManager(self.config)
        self.logger = self.log_manager.get_logger("scheduler")
        self.scheduler_logger = self.log_manager.get_scheduler_logger()

        # 核心組件
        self.ip_detector = IPDetector()
        webhook_url = self.config.get("discord", "webhook_url")
        self.discord_client = DiscordClient(webhook_url)

        # 狀態管理
        self.is_running = False
        self.is_executing = False
        self.execution_history: List[ExecutionRecord] = []
        self.execution_lock = threading.Lock()
        self.last_execution_time = None
        self.start_time = datetime.now()

        # 排程設定
        scheduler_config = self.config.get_scheduler_config()
        self.daily_time = scheduler_config["daily_time"]
        self.status_update_interval = scheduler_config["status_update_interval"]
        self.max_history = scheduler_config["max_execution_history"]

        # 系統監控
        self.process = psutil.Process()

        # 設定信號處理
        self._setup_signal_handlers()

        self.logger.info("排程管理器初始化完成")

    def _setup_signal_handlers(self):
        """設定信號處理器"""

        def signal_handler(signum, frame):
            self.logger.info(f"收到信號 {signum}，正在安全關閉...")
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def _add_execution_record(
        self, mode: str, action: str, result: str, details: str = ""
    ):
        """添加執行記錄"""
        record = ExecutionRecord(mode, action, result, details)
        self.execution_history.append(record)

        # 保持歷史記錄數量在限制內
        if len(self.execution_history) > self.max_history:
            self.execution_history = self.execution_history[-self.max_history :]

    def _get_next_scheduled_time(self) -> Optional[datetime]:
        """取得下次排程執行時間"""
        try:
            jobs = schedule.jobs
            if not jobs:
                return None

            next_run = min(job.next_run for job in jobs if job.next_run)
            return next_run
        except Exception:
            return None

    def _get_system_info(self) -> Dict[str, str]:
        """取得系統資訊"""
        try:
            memory_mb = self.process.memory_info().rss / 1024 / 1024
            cpu_percent = self.process.cpu_percent()

            return {
                "memory": f"{memory_mb:.1f}MB",
                "cpu": f"{cpu_percent:.1f}%",
                "uptime": str(datetime.now() - self.start_time).split(".")[0],
            }
        except Exception as e:
            self.logger.error(f"取得系統資訊失敗: {e}")
            return {"memory": "N/A", "cpu": "N/A", "uptime": "N/A"}

    def _clear_screen(self):
        """清除螢幕"""
        os.system("clear" if os.name == "posix" else "cls")

    def _display_status(self):
        """顯示實時狀態"""
        self._clear_screen()

        current_time = datetime.now()
        next_run = self._get_next_scheduled_time()
        system_info = self._get_system_info()

        print("🤖 Discord IP Bot - 排程模式運行中")
        print("=" * 60)
        print(f"📅 排程設定: 每天 {self.daily_time}")
        print(f"⏰ 當前時間: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")

        if next_run:
            time_diff = next_run - current_time
            if time_diff.total_seconds() > 0:
                hours, remainder = divmod(time_diff.total_seconds(), 3600)
                minutes, _ = divmod(remainder, 60)
                print(
                    f"⏳ 下次執行: {next_run.strftime('%Y-%m-%d %H:%M:%S')} ({int(hours)}小時{int(minutes)}分鐘後)"
                )
            else:
                print("⏳ 下次執行: 即將執行...")
        else:
            print("⏳ 下次執行: 排程未設定")

        print(f"📊 執行狀態: {'🔄 執行中...' if self.is_executing else '💤 等待中'}")
        print(f"💻 系統資源: RAM: {system_info['memory']}, CPU: {system_info['cpu']}")
        print(f"⏱️  運行時間: {system_info['uptime']}")
        print()

        # 顯示執行歷史（最近10次）
        print("📋 執行歷史:")
        if self.execution_history:
            for record in self.execution_history[-10:]:
                print(f"  {record}")
        else:
            print("  暫無執行記錄")

        print()
        if self.last_execution_time:
            print(
                f"🕐 上次執行: {self.last_execution_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )

        print(
            "💡 提示: 按 Ctrl+C 停止排程，手動執行請開啟新terminal運行 'python main.py --manual'"
        )
        print("-" * 60)

    def _execute_ip_check(self, mode: str = "排程") -> bool:
        """
        執行IP檢測任務

        Args:
            mode: 執行模式

        Returns:
            是否成功
        """
        with self.execution_lock:
            self.is_executing = True
            success = False

            try:
                self.logger.info(f"開始執行IP檢測 - 模式: {mode}")
                self._add_execution_record(mode, "開始執行", "初始化中...")

                # 檢測IP
                ip_result = self.ip_detector.check_and_update()

                if not ip_result["success"]:
                    self._add_execution_record(mode, "IP檢測", "失敗", "無法獲取IP")
                    self.log_manager.log_execution(mode, "IP檢測", "失敗")
                    return False

                current_ips = ip_result["current_ips"]
                public_ip = current_ips.get("public_ip", "無法獲取")

                if public_ip == "無法獲取":
                    self._add_execution_record(mode, "IP檢測", "失敗", "公共IP無法獲取")
                    self.log_manager.log_execution(
                        mode, "IP檢測", "失敗", ip="無法獲取"
                    )
                    return False

                self._add_execution_record(mode, "IP檢測", "成功", f"IP: {public_ip}")

                # 決定是否發送Discord通知
                should_send = False
                send_reason = ""

                if mode == "手動" or mode == "測試":
                    should_send = True
                    send_reason = f"{mode}執行"
                else:
                    # 排程模式：檢查IP是否有變化
                    ip_changed = ip_result.get("ip_changed", False)
                    if ip_changed:
                        should_send = True
                        send_reason = "IP已變化"
                        old_ip = ip_result.get("previous_ips", {}).get(
                            "public_ip", "未知"
                        )
                        self.log_manager.log_ip_change(old_ip, public_ip, mode)
                    else:
                        send_reason = "IP無變化，跳過發送"
                        self.log_manager.log_no_ip_change(public_ip, mode)

                # 發送Discord通知
                if should_send and mode != "測試":
                    try:
                        discord_success = (
                            self.discord_client.send_minecraft_server_notification(
                                current_ips
                            )
                        )
                        if discord_success:
                            self._add_execution_record(
                                mode, "Discord通知", "發送成功", f"IP: {public_ip}"
                            )
                            self.log_manager.log_discord_send(public_ip, True, mode)
                        else:
                            self._add_execution_record(
                                mode, "Discord通知", "發送失敗", f"IP: {public_ip}"
                            )
                            self.log_manager.log_discord_send(public_ip, False, mode)
                            return False
                    except Exception as e:
                        self._add_execution_record(
                            mode, "Discord通知", "發送失敗", f"錯誤: {str(e)}"
                        )
                        self.logger.error(f"Discord發送失敗: {e}")
                        return False
                else:
                    self._add_execution_record(
                        mode, "Discord通知", send_reason, f"IP: {public_ip}"
                    )

                self._add_execution_record(mode, "任務完成", "成功", f"IP: {public_ip}")
                success = True
                self.last_execution_time = datetime.now()

            except Exception as e:
                self._add_execution_record(mode, "執行失敗", "異常", str(e))
                self.logger.error(f"執行IP檢測任務失敗: {e}")
                success = False

            finally:
                self.is_executing = False

            return success

    def scheduled_task(self):
        """排程任務：檢測IP變化，有變化才發送"""
        self.scheduler_logger.info("開始執行排程任務")
        success = self._execute_ip_check("排程")
        result = "完成" if success else "失敗"
        self.scheduler_logger.info(f"排程任務執行{result}")

    def manual_task(self) -> bool:
        """手動任務：立即檢測並發送當前IP"""
        self.logger.info("執行手動任務")
        success = self._execute_ip_check("手動")
        self.log_manager.log_manual_execution(
            ip="已處理" if success else "失敗", success=success
        )
        return success

    def test_task(self) -> bool:
        """測試任務：檢測IP但不發送Discord"""
        self.logger.info("執行測試任務")
        success = self._execute_ip_check("測試")
        if success:
            # 取得最後檢測的IP
            try:
                ip_result = self.ip_detector.check_and_update()
                public_ip = ip_result.get("current_ips", {}).get("public_ip", "未知")
                self.log_manager.log_test_execution(public_ip)
            except Exception:
                self.log_manager.log_test_execution("檢測失敗")
        return success

    def start_daemon(self):
        """啟動守護程式模式"""
        self.logger.info("啟動排程守護程式")
        print("🤖 Discord IP Bot - 排程模式啟動中...")
        print("=" * 60)
        print(f"📅 排程設定: 每天 {self.daily_time}")
        print(f"⏰ 啟動時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 檢查設定
        try:
            discord_config = self.config.get_discord_config()
            print(
                f"🔧 Discord配置: {'✅ 已設定' if discord_config['webhook_url'] else '❌ 未設定'}"
            )

            # 測試Discord連線
            test_result = self.discord_client.test_connection()
            print(f"📱 Discord連線: {'✅ 正常' if test_result else '❌ 失敗'}")

        except Exception as e:
            print(f"⚠️  設定檢查失敗: {e}")

        print()
        print("⚡ 排程系統啟動中...")

        # 設定排程
        schedule.every().day.at(self.daily_time).do(self.scheduled_task)
        self._add_execution_record(
            "系統", "排程啟動", "成功", f"每日 {self.daily_time}"
        )

        self.is_running = True
        print("✅ 排程系統已啟動")
        time.sleep(2)  # 短暫延遲，讓用戶看到啟動訊息

        try:
            while self.is_running:
                self._display_status()
                schedule.run_pending()
                time.sleep(self.status_update_interval)

        except KeyboardInterrupt:
            self.stop()

        except Exception as e:
            self.logger.error(f"排程系統異常: {e}")
            self.stop()

    def stop(self):
        """停止排程系統"""
        self.logger.info("正在停止排程系統...")
        self.is_running = False
        self._add_execution_record("系統", "排程停止", "成功", "使用者中斷")

        print()
        print("🛑 收到終止信號，正在安全關閉排程系統...")

        # 等待當前任務完成
        if self.is_executing:
            print("⏳ 等待當前任務完成...")
            while self.is_executing:
                time.sleep(0.5)

        # 清理排程
        schedule.clear()

        print("✅ 排程系統已安全關閉")
        print(
            f"💾 執行歷史已保存到 {self.config.get('system', 'logs_dir')}/scheduler.log"
        )
        print("👋 再見！")

    def get_status_info(self) -> Dict[str, Any]:
        """取得狀態資訊"""
        return {
            "is_running": self.is_running,
            "is_executing": self.is_executing,
            "start_time": self.start_time,
            "last_execution": self.last_execution_time,
            "next_scheduled": self._get_next_scheduled_time(),
            "execution_count": len(self.execution_history),
            "system_info": self._get_system_info(),
        }


if __name__ == "__main__":
    """測試模組功能"""
    import argparse

    parser = argparse.ArgumentParser(description="Discord IP Bot 排程系統測試")
    parser.add_argument("--daemon", action="store_true", help="啟動守護程式模式")
    parser.add_argument("--manual", action="store_true", help="執行手動任務")
    parser.add_argument("--test", action="store_true", help="執行測試任務")
    parser.add_argument("--status", action="store_true", help="顯示狀態資訊")

    args = parser.parse_args()

    try:
        print("=== Discord IP Bot - 排程系統測試 ===")
        print()

        # 建立排程管理器
        scheduler = SchedulerManager()

        if args.daemon:
            scheduler.start_daemon()
        elif args.manual:
            print("🔧 執行手動任務...")
            success = scheduler.manual_task()
            print(f"✅ 手動任務{'成功' if success else '失敗'}")
        elif args.test:
            print("🧪 執行測試任務...")
            success = scheduler.test_task()
            print(f"✅ 測試任務{'成功' if success else '失敗'}")
        elif args.status:
            print("📊 系統狀態:")
            status = scheduler.get_status_info()
            for key, value in status.items():
                print(f"  {key}: {value}")
        else:
            print("💡 使用說明:")
            print("  --daemon  啟動守護程式模式")
            print("  --manual  執行手動任務")
            print("  --test    執行測試任務")
            print("  --status  顯示狀態資訊")

    except Exception as e:
        print(f"❌ 測試過程發生錯誤: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
