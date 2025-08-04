"""
設定管理模組 - Discord IP Bot

負責讀取和管理應用程式的所有配置資訊
包括環境變數、預設值和設定驗證
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class ConfigError(Exception):
    """設定相關的異常"""

    pass


class ConfigManager:
    """設定管理器"""

    def __init__(self, env_file: str = ".env"):
        """
        初始化設定管理器

        Args:
            env_file: 環境變數檔案路徑
        """
        self.logger = logging.getLogger(__name__)
        self.env_file = env_file
        self.config = {}

        # 載入環境變數
        self._load_environment()

        # 載入所有設定
        self._load_config()

        # 驗證必要設定
        self._validate_config()

        self.logger.info("設定管理器初始化完成")

    def _load_environment(self):
        """載入環境變數"""
        env_path = Path(self.env_file)

        if env_path.exists():
            load_dotenv(env_path)
            self.logger.info(f"環境變數檔案已載入: {env_path}")
        else:
            self.logger.warning(f"環境變數檔案不存在: {env_path}")

    def _load_config(self):
        """載入所有設定"""
        self.config = {
            # Discord 設定
            "discord": {
                "webhook_url": self._get_env("DISCORD_WEBHOOK_URL"),
                "message_template": self._get_env(
                    "DISCORD_MESSAGE_TEMPLATE", "Minecraft Server IP: {ip}:25565"
                ),
                "retry_attempts": self._get_env_int("DISCORD_RETRY_ATTEMPTS", 3),
                "timeout": self._get_env_int("DISCORD_TIMEOUT", 10),
            },
            # 應用程式設定
            "app": {
                "name": self._get_env("APP_NAME", "Discord IP Bot"),
                "log_level": self._get_env("LOG_LEVEL", "INFO"),
                "schedule_time": self._get_env("SCHEDULE_TIME", "09:00"),
                "timezone": self._get_env("TIMEZONE", "Asia/Taipei"),
            },
            # IP 檢測設定
            "ip_detection": {
                "check_public_ip": self._get_env_bool("CHECK_PUBLIC_IP", True),
                "check_local_ip": self._get_env_bool("CHECK_LOCAL_IP", True),
                "timeout": self._get_env_int("IP_CHECK_TIMEOUT", 10),
                "retry_attempts": self._get_env_int("IP_RETRY_ATTEMPTS", 3),
                "save_history": self._get_env_bool("SAVE_IP_HISTORY", True),
            },
            # 系統設定
            "system": {
                "logs_dir": self._get_env("LOGS_DIR", "logs"),
                "data_dir": self._get_env("DATA_DIR", "data"),
                "max_log_files": self._get_env_int("MAX_LOG_FILES", 7),
                "max_log_size_mb": self._get_env_int("MAX_LOG_SIZE_MB", 10),
            },
            # 排程設定
            "scheduler": {
                "daily_time": self._get_env("SCHEDULE_TIME", "09:00"),
                "status_update_interval": self._get_env_int(
                    "STATUS_UPDATE_INTERVAL", 60
                ),
                "max_execution_history": self._get_env_int("MAX_EXECUTION_HISTORY", 50),
            },
            # IP 歷史記錄設定
            "ip_history": {
                "file_path": self._get_env("IP_HISTORY_FILE", "config/ip_history.json"),
                "keep_days": self._get_env_int("IP_HISTORY_KEEP_DAYS", 30),
                "max_records": self._get_env_int("IP_HISTORY_MAX_RECORDS", 1000),
                "auto_cleanup": self._get_env_bool("IP_HISTORY_AUTO_CLEANUP", True),
                "backup_on_corruption": self._get_env_bool(
                    "IP_HISTORY_BACKUP_ON_CORRUPTION", True
                ),
                "compression": self._get_env_bool("IP_HISTORY_COMPRESSION", False),
                "encoding": self._get_env("IP_HISTORY_ENCODING", "utf-8"),
            },
        }

    def _get_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """取得環境變數字串值"""
        value = os.getenv(key, default)
        if value == "":
            return default
        return value

    def _get_env_int(self, key: str, default: int) -> int:
        """取得環境變數整數值"""
        try:
            value = os.getenv(key)
            if value:
                return int(value)
            return default
        except ValueError:
            self.logger.warning(f"環境變數 {key} 不是有效整數，使用預設值: {default}")
            return default

    def _get_env_bool(self, key: str, default: bool) -> bool:
        """取得環境變數布林值"""
        value = os.getenv(key)
        if value is None:
            return default

        return value.lower() in ("true", "1", "yes", "on", "enabled")

    def _validate_config(self):
        """驗證必要設定"""
        errors = []

        # 檢查必要的 Discord Webhook URL
        webhook_url = self.config["discord"]["webhook_url"]
        if not webhook_url:
            errors.append("DISCORD_WEBHOOK_URL 環境變數未設定")
        elif not webhook_url.startswith("https://discord.com/api/webhooks/"):
            errors.append("DISCORD_WEBHOOK_URL 格式不正確")

        # 檢查排程時間格式
        schedule_time = self.config["scheduler"]["daily_time"]
        if schedule_time:
            try:
                hours, minutes = schedule_time.split(":")
                if not (0 <= int(hours) <= 23) or not (0 <= int(minutes) <= 59):
                    errors.append(f"SCHEDULE_TIME 格式不正確: {schedule_time}")
            except ValueError:
                errors.append(f"SCHEDULE_TIME 格式不正確: {schedule_time}")

        # 檢查日誌級別
        log_level = self.config["app"]["log_level"]
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if log_level.upper() not in valid_levels:
            errors.append(f"LOG_LEVEL 不正確: {log_level}, 有效值: {valid_levels}")

        if errors:
            error_msg = "設定驗證失敗:\n" + "\n".join(f"- {error}" for error in errors)
            raise ConfigError(error_msg)

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        取得設定值

        Args:
            section: 設定區塊
            key: 設定鍵
            default: 預設值

        Returns:
            設定值
        """
        try:
            return self.config[section][key]
        except KeyError:
            if default is not None:
                return default
            raise ConfigError(f"設定項目不存在: {section}.{key}")

    def get_discord_config(self) -> Dict[str, Any]:
        """取得 Discord 相關設定"""
        return self.config["discord"].copy()

    def get_app_config(self) -> Dict[str, Any]:
        """取得應用程式設定"""
        return self.config["app"].copy()

    def get_ip_config(self) -> Dict[str, Any]:
        """取得 IP 檢測設定"""
        return self.config["ip_detection"].copy()

    def get_system_config(self) -> Dict[str, Any]:
        """取得系統設定"""
        return self.config["system"].copy()

    def get_scheduler_config(self) -> Dict[str, Any]:
        """取得排程設定"""
        return self.config["scheduler"].copy()

    def get_ip_history_config(self) -> Dict[str, Any]:
        """取得IP歷史記錄相關設定"""
        return self.config["ip_history"].copy()

    def get_history_file_path(self) -> str:
        """取得IP歷史記錄檔案路徑"""
        return self.config["ip_history"]["file_path"]

    def ensure_directories(self):
        """確保必要的目錄存在"""
        directories = [
            self.config["system"]["logs_dir"],
            self.config["system"]["data_dir"],
        ]

        # 加入IP歷史檔案的目錄
        history_file_path = Path(self.config["ip_history"]["file_path"])
        if history_file_path.parent != Path("."):  # 不是當前目錄
            directories.append(str(history_file_path.parent))

        for directory in directories:
            path = Path(directory)
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"建立目錄: {path}")

    def get_all_config(self) -> Dict[str, Any]:
        """取得所有設定（用於除錯）"""
        # 遮蔽敏感資訊
        safe_config = {}
        for section, settings in self.config.items():
            safe_config[section] = {}
            for key, value in settings.items():
                if "webhook" in key.lower() or "token" in key.lower():
                    # 遮蔽敏感資訊
                    if isinstance(value, str) and len(value) > 10:
                        safe_config[section][key] = value[:10] + "..." + value[-5:]
                    else:
                        safe_config[section][key] = "***"
                else:
                    safe_config[section][key] = value

        return safe_config


if __name__ == "__main__":
    """測試模組功能"""
    import sys
    import pprint

    try:
        print("=== Discord IP Bot - 設定管理器測試 ===")
        print()

        # 建立設定管理器
        print("📝 初始化設定管理器...")
        config = ConfigManager()
        print("✅ 設定管理器初始化成功")
        print()

        # 顯示所有設定
        print("🔧 當前設定:")
        pprint.pprint(config.get_all_config(), width=80)
        print()

        # 測試特定設定
        print("🧪 測試特定設定取得:")
        print(f"  應用程式名稱: {config.get('app', 'name')}")
        print(f"  排程時間: {config.get('scheduler', 'daily_time')}")
        print(f"  Discord重試次數: {config.get('discord', 'retry_attempts')}")
        print(f"  IP歷史檔案路徑: {config.get_history_file_path()}")
        print(f"  IP歷史保留天數: {config.get('ip_history', 'keep_days')}")
        print()

        # 測試新的IP歷史配置
        print("📊 IP歷史配置:")
        ip_history_config = config.get_ip_history_config()
        for key, value in ip_history_config.items():
            print(f"  {key}: {value}")
        print()

        # 確保目錄存在
        print("📁 確保必要目錄存在...")
        config.ensure_directories()
        print("✅ 目錄檢查完成")
        print()

        print("🎉 設定管理器測試完成！")

    except ConfigError as e:
        print(f"❌ 設定錯誤: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 未預期錯誤: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
