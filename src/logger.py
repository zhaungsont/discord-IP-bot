"""
日誌系統模組 - Discord IP Bot

負責統一管理應用程式的日誌輸出
包括檔案輪轉、格式化和多級別日誌
"""

import os
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional

try:
    from .config import ConfigManager
except ImportError:
    # 用於直接執行此模組時
    from config import ConfigManager


class LoggerManager:
    """日誌管理器"""

    def __init__(
        self,
        config_manager: Optional[ConfigManager] = None,
        name: str = "discord_ip_bot",
    ):
        """
        初始化日誌管理器

        Args:
            config_manager: 設定管理器實例
            name: 日誌器名稱
        """
        self.config = config_manager or ConfigManager()
        self.name = name
        self.logger = None

        # 確保日誌目錄存在
        self._ensure_log_directory()

        # 設定日誌系統
        self._setup_logging()

    def _ensure_log_directory(self):
        """確保日誌目錄存在"""
        logs_dir = Path(self.config.get("system", "logs_dir"))
        logs_dir.mkdir(parents=True, exist_ok=True)

    def _setup_logging(self):
        """設定日誌系統"""
        # 取得設定
        app_config = self.config.get_app_config()
        system_config = self.config.get_system_config()

        # 建立主要日誌器
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(getattr(logging, app_config["log_level"].upper()))

        # 清除現有處理器（避免重複）
        self.logger.handlers.clear()

        # 設定日誌格式
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # 控制台處理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)

        # 檔案處理器（一般日誌）
        log_file = Path(system_config["logs_dir"]) / "discord_ip_bot.log"
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=system_config["max_log_size_mb"] * 1024 * 1024,  # MB to bytes
            backupCount=system_config["max_log_files"],
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)

        # 錯誤日誌處理器
        error_log_file = Path(system_config["logs_dir"]) / "error.log"
        error_handler = logging.handlers.RotatingFileHandler(
            filename=error_log_file,
            maxBytes=system_config["max_log_size_mb"] * 1024 * 1024,
            backupCount=system_config["max_log_files"],
            encoding="utf-8",
        )
        error_handler.setFormatter(formatter)
        error_handler.setLevel(logging.ERROR)
        self.logger.addHandler(error_handler)

        # 排程專用日誌處理器
        scheduler_log_file = Path(system_config["logs_dir"]) / "scheduler.log"
        scheduler_handler = logging.handlers.RotatingFileHandler(
            filename=scheduler_log_file,
            maxBytes=system_config["max_log_size_mb"] * 1024 * 1024,
            backupCount=system_config["max_log_files"],
            encoding="utf-8",
        )
        scheduler_formatter = logging.Formatter(
            fmt="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        scheduler_handler.setFormatter(scheduler_formatter)
        scheduler_handler.setLevel(logging.INFO)

        # 建立排程專用日誌器
        scheduler_logger = logging.getLogger(f"{self.name}.scheduler")
        scheduler_logger.setLevel(logging.INFO)
        scheduler_logger.handlers.clear()
        scheduler_logger.addHandler(scheduler_handler)
        scheduler_logger.addHandler(console_handler)  # 也輸出到控制台
        scheduler_logger.propagate = False  # 避免重複輸出

        self.logger.info("日誌系統初始化完成")

    def get_logger(self, module_name: str = None) -> logging.Logger:
        """
        取得日誌器

        Args:
            module_name: 模組名稱

        Returns:
            日誌器實例
        """
        if module_name:
            logger_name = f"{self.name}.{module_name}"
            logger = logging.getLogger(logger_name)
            logger.setLevel(self.logger.level)

            # 如果沒有處理器，使用主要日誌器的處理器
            if not logger.handlers:
                for handler in self.logger.handlers:
                    logger.addHandler(handler)

            return logger

        return self.logger

    def get_scheduler_logger(self) -> logging.Logger:
        """取得排程專用日誌器"""
        return logging.getLogger(f"{self.name}.scheduler")

    def log_execution(self, mode: str, action: str, result: str, **kwargs):
        """
        記錄執行日誌

        Args:
            mode: 執行模式 (排程/手動/測試)
            action: 執行動作
            result: 執行結果
            **kwargs: 額外資訊
        """
        scheduler_logger = self.get_scheduler_logger()

        # 構建日誌訊息
        message_parts = [f"[{mode}]", action, f"→ {result}"]

        # 添加額外資訊
        if kwargs:
            extra_info = ", ".join(f"{k}={v}" for k, v in kwargs.items())
            message_parts.append(f"({extra_info})")

        message = " ".join(message_parts)
        scheduler_logger.info(message)

    def log_ip_change(self, old_ip: str, new_ip: str, mode: str = "排程"):
        """記錄IP變化"""
        self.log_execution(
            mode=mode,
            action="IP變化檢測",
            result="IP已變化",
            old_ip=old_ip,
            new_ip=new_ip,
        )

    def log_no_ip_change(self, current_ip: str, mode: str = "排程"):
        """記錄IP無變化"""
        self.log_execution(
            mode=mode, action="IP變化檢測", result="IP無變化", ip=current_ip
        )

    def log_discord_send(self, ip: str, success: bool, mode: str = "排程"):
        """記錄Discord發送結果"""
        result = "Discord發送成功" if success else "Discord發送失敗"
        self.log_execution(mode=mode, action="Discord通知", result=result, ip=ip)

    def log_manual_execution(self, ip: str, success: bool):
        """記錄手動執行"""
        result = "執行成功" if success else "執行失敗"
        self.log_execution(mode="手動", action="手動執行", result=result, ip=ip)

    def log_test_execution(self, ip: str):
        """記錄測試執行"""
        self.log_execution(mode="測試", action="測試執行", result="測試完成", ip=ip)

    def log_system_info(self, **info):
        """記錄系統資訊"""
        logger = self.get_logger("system")
        for key, value in info.items():
            logger.info(f"系統資訊 - {key}: {value}")

    def log_config_info(self, config_summary: dict):
        """記錄設定資訊"""
        logger = self.get_logger("config")
        logger.info("應用程式設定:")
        for section, settings in config_summary.items():
            logger.info(f"  [{section}]")
            for key, value in settings.items():
                logger.info(f"    {key}: {value}")

    def get_recent_logs(self, lines: int = 50, log_type: str = "scheduler") -> list:
        """
        取得最近的日誌記錄

        Args:
            lines: 行數
            log_type: 日誌類型 (scheduler/error/main)

        Returns:
            日誌行列表
        """
        system_config = self.config.get_system_config()

        log_files = {
            "scheduler": "scheduler.log",
            "error": "error.log",
            "main": "discord_ip_bot.log",
        }

        log_file = Path(system_config["logs_dir"]) / log_files.get(
            log_type, "scheduler.log"
        )

        if not log_file.exists():
            return []

        try:
            with open(log_file, "r", encoding="utf-8") as f:
                lines_list = f.readlines()
                return lines_list[-lines:] if len(lines_list) > lines else lines_list
        except Exception as e:
            self.logger.error(f"讀取日誌檔案失敗: {e}")
            return []

    def cleanup_old_logs(self):
        """清理舊日誌檔案"""
        system_config = self.config.get_system_config()
        logs_dir = Path(system_config["logs_dir"])

        if not logs_dir.exists():
            return

        # 清理超過保留數量的日誌檔案
        for log_pattern in ["*.log.*", "*.log.1", "*.log.2"]:
            log_files = list(logs_dir.glob(log_pattern))
            log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # 保留最新的 max_log_files 個檔案
            max_files = system_config["max_log_files"]
            for old_file in log_files[max_files:]:
                try:
                    old_file.unlink()
                    self.logger.info(f"清理舊日誌檔案: {old_file}")
                except Exception as e:
                    self.logger.error(f"清理日誌檔案失敗: {e}")


def setup_logging(config_manager: Optional[ConfigManager] = None) -> LoggerManager:
    """
    設定日誌系統的便利函數

    Args:
        config_manager: 設定管理器實例

    Returns:
        日誌管理器實例
    """
    return LoggerManager(config_manager)


if __name__ == "__main__":
    """測試模組功能"""
    import sys

    try:
        print("=== Discord IP Bot - 日誌系統測試 ===")
        print()

        # 建立配置管理器
        print("📝 初始化設定管理器...")
        config = ConfigManager()

        # 建立日誌管理器
        print("📋 初始化日誌系統...")
        log_manager = LoggerManager(config)
        print("✅ 日誌系統初始化成功")
        print()

        # 取得日誌器並測試
        logger = log_manager.get_logger("test")

        print("🧪 測試不同級別的日誌輸出:")
        logger.debug("這是 DEBUG 級別的日誌")
        logger.info("這是 INFO 級別的日誌")
        logger.warning("這是 WARNING 級別的日誌")
        logger.error("這是 ERROR 級別的日誌")
        print()

        # 測試排程日誌
        print("📅 測試排程專用日誌:")
        log_manager.log_execution("測試", "IP檢測", "成功", ip="192.168.1.100")
        log_manager.log_ip_change("192.168.1.100", "192.168.1.101", "測試")
        log_manager.log_discord_send("192.168.1.101", True, "測試")
        print()

        # 測試系統資訊日誌
        print("💻 測試系統資訊日誌:")
        log_manager.log_system_info(
            platform="macOS", python_version="3.12.10", memory_usage="25.3MB"
        )
        print()

        # 檢查日誌檔案
        print("📁 檢查日誌檔案:")
        recent_logs = log_manager.get_recent_logs(5, "scheduler")
        for i, line in enumerate(recent_logs[-3:], 1):
            print(f"  {i}. {line.strip()}")
        print()

        print("🎉 日誌系統測試完成！")
        print("📂 日誌檔案位置:")
        print("  - 主要日誌: logs/discord_ip_bot.log")
        print("  - 排程日誌: logs/scheduler.log")
        print("  - 錯誤日誌: logs/error.log")

    except Exception as e:
        print(f"❌ 測試過程發生錯誤: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
