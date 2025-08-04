"""
IP檢測模組 - Discord IP Bot

此模組負責檢測本地IP和外網IP地址，並提供IP變化比較功能。
設計為完全跨平台相容 (MacOS, Windows 10/11, Linux)。
"""

import socket
import json
import logging
import platform
import subprocess
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
import requests
from urllib3.exceptions import InsecureRequestWarning
import urllib3

# 禁用 SSL 警告以避免在某些環境下的問題
urllib3.disable_warnings(InsecureRequestWarning)


class IPDetectorError(Exception):
    """IP檢測相關錯誤的基礎例外類別"""

    pass


class NetworkError(IPDetectorError):
    """網路連線相關錯誤"""

    pass


class IPDetector:
    """
    IP地址檢測器類別

    功能：
    - 檢測本地內網IP地址（跨平台）
    - 檢測外網公共IP地址
    - 比較IP變化
    - 儲存IP歷史記錄
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化IP檢測器

        Args:
            config: 設定字典，包含逾時設定、重試次數等
        """
        self.logger = logging.getLogger(__name__)

        # 預設設定
        self.config = {
            "timeout": 10,
            "retry_attempts": 3,
            "retry_delay": 2,
            "public_ip_services": [
                "https://api.ipify.org",
                "https://icanhazip.com",
                "https://ident.me",
                "https://checkip.amazonaws.com",
            ],
            "history_file": "logs/ip_history.json",
        }

        # 更新使用者提供的設定
        if config:
            self.config.update(config)

        # 確保日誌目錄存在
        Path(self.config["history_file"]).parent.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"IP檢測器初始化完成 - 平台: {platform.system()}")

    def get_local_ip(self) -> str:
        """
        獲取本地內網IP地址（跨平台方法）

        Returns:
            str: 本地IP地址

        Raises:
            NetworkError: 無法獲取本地IP時拋出
        """
        try:
            # 方法1: 使用socket連接外部地址來獲取本地IP（最可靠的跨平台方法）
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                # 連接到 Google DNS，但不實際發送資料
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                self.logger.debug(f"透過socket方法獲取本地IP: {local_ip}")
                return local_ip

        except Exception as e:
            self.logger.warning(f"Socket方法失敗: {e}，嘗試備用方法")

            try:
                # 方法2: 使用hostname方法（備用）
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)

                # 檢查是否為有效的內網IP
                if self._is_valid_local_ip(local_ip):
                    self.logger.debug(f"透過hostname方法獲取本地IP: {local_ip}")
                    return local_ip
                else:
                    raise NetworkError(f"獲取到無效的本地IP: {local_ip}")

            except Exception as e2:
                error_msg = (
                    f"所有本地IP檢測方法都失敗: socket方法({e}), hostname方法({e2})"
                )
                self.logger.error(error_msg)
                raise NetworkError(error_msg)

    def _is_valid_local_ip(self, ip: str) -> bool:
        """
        檢查是否為有效的本地IP地址

        Args:
            ip: IP地址字串

        Returns:
            bool: 是否為有效的本地IP
        """
        if not ip or ip in ["127.0.0.1", "0.0.0.0"]:
            return False

        # 檢查是否為私有IP範圍
        parts = ip.split(".")
        if len(parts) != 4:
            return False

        try:
            first_octet = int(parts[0])
            second_octet = int(parts[1])

            # 私有IP範圍：
            # 10.0.0.0 - 10.255.255.255
            # 172.16.0.0 - 172.31.255.255
            # 192.168.0.0 - 192.168.255.255
            if (
                first_octet == 10
                or (first_octet == 172 and 16 <= second_octet <= 31)
                or (first_octet == 192 and second_octet == 168)
            ):
                return True

        except ValueError:
            return False

        return False

    def get_public_ip(self) -> str:
        """
        獲取外網公共IP地址

        Returns:
            str: 公共IP地址

        Raises:
            NetworkError: 無法獲取公共IP時拋出
        """
        last_error = None

        for service_url in self.config["public_ip_services"]:
            for attempt in range(self.config["retry_attempts"]):
                try:
                    self.logger.debug(
                        f"嘗試從 {service_url} 獲取公共IP (第{attempt + 1}次)"
                    )

                    response = requests.get(
                        service_url,
                        timeout=self.config["timeout"],
                        verify=False,  # 某些服務可能有SSL問題
                        headers={"User-Agent": "Discord-IP-Bot/1.0"},
                    )

                    if response.status_code == 200:
                        public_ip = response.text.strip()

                        # 驗證返回的IP格式
                        if self._is_valid_ip_format(public_ip):
                            self.logger.debug(f"成功獲取公共IP: {public_ip}")
                            return public_ip
                        else:
                            raise NetworkError(f"無效的IP格式: {public_ip}")
                    else:
                        raise NetworkError(f"HTTP狀態碼: {response.status_code}")

                except requests.RequestException as e:
                    last_error = e
                    self.logger.warning(
                        f"從 {service_url} 獲取IP失敗 (第{attempt + 1}次): {e}"
                    )

                    if attempt < self.config["retry_attempts"] - 1:
                        import time

                        time.sleep(self.config["retry_delay"])

        error_msg = f"所有公共IP服務都無法使用，最後錯誤: {last_error}"
        self.logger.error(error_msg)
        raise NetworkError(error_msg)

    def _is_valid_ip_format(self, ip: str) -> bool:
        """
        檢查IP地址格式是否有效

        Args:
            ip: IP地址字串

        Returns:
            bool: 格式是否有效
        """
        try:
            socket.inet_aton(ip)
            parts = ip.split(".")
            return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
        except socket.error:
            return False

    def get_all_ips(self) -> Dict[str, str]:
        """
        獲取所有IP資訊（本地IP和公共IP）

        Returns:
            Dict[str, str]: 包含local_ip和public_ip的字典

        Raises:
            NetworkError: 無法獲取任何IP時拋出
        """
        result = {}
        errors = []

        # 獲取本地IP
        try:
            result["local_ip"] = self.get_local_ip()
        except NetworkError as e:
            errors.append(f"本地IP獲取失敗: {e}")
            result["local_ip"] = "無法獲取"

        # 獲取公共IP
        try:
            result["public_ip"] = self.get_public_ip()
        except NetworkError as e:
            errors.append(f"公共IP獲取失敗: {e}")
            result["public_ip"] = "無法獲取"

        # 添加額外資訊
        result["timestamp"] = self._get_current_timestamp()
        result["platform"] = platform.system()
        result["hostname"] = socket.gethostname()

        if errors:
            result["errors"] = errors
            self.logger.warning(f"IP獲取過程中發生錯誤: {errors}")

        self.logger.info(f"IP檢測完成: {result}")
        return result

    def _get_current_timestamp(self) -> str:
        """
        獲取當前時間戳記

        Returns:
            str: ISO格式的時間戳記
        """
        from datetime import datetime

        return datetime.now().isoformat()

    def save_ip_history(self, ip_data: Dict[str, str]) -> None:
        """
        儲存IP歷史記錄到檔案

        Args:
            ip_data: IP資料字典
        """
        try:
            history_file = Path(self.config["history_file"])

            # 讀取現有歷史記錄
            history = []
            if history_file.exists():
                try:
                    with open(history_file, "r", encoding="utf-8") as f:
                        history = json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    self.logger.warning("無法讀取現有歷史記錄，建立新的記錄")
                    history = []

            # 添加新記錄
            history.append(ip_data)

            # 限制歷史記錄數量（保持最近100筆）
            if len(history) > 100:
                history = history[-100:]

            # 寫入檔案
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)

            self.logger.debug(f"IP歷史記錄已儲存: {history_file}")

        except Exception as e:
            self.logger.error(f"儲存IP歷史記錄失敗: {e}")

    def get_last_ip_record(self) -> Optional[Dict[str, str]]:
        """
        獲取最後一次記錄的IP資料

        Returns:
            Optional[Dict[str, str]]: 最後一次的IP記錄，如果沒有則返回None
        """
        try:
            history_file = Path(self.config["history_file"])

            if not history_file.exists():
                return None

            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)

            if history:
                return history[-1]

        except Exception as e:
            self.logger.error(f"讀取IP歷史記錄失敗: {e}")

        return None

    def compare_with_last(
        self, current_ips: Dict[str, str]
    ) -> Dict[str, Union[bool, str, Dict]]:
        """
        比較當前IP與上次記錄的IP

        Args:
            current_ips: 當前IP資料

        Returns:
            Dict: 比較結果，包含changed、changes、last_record等資訊
        """
        last_record = self.get_last_ip_record()

        if not last_record:
            self.logger.info("沒有歷史記錄，這是首次執行")
            return {
                "changed": True,
                "is_first_run": True,
                "changes": "首次執行",
                "last_record": None,
                "current_record": current_ips,
            }

        changes = {}
        has_changes = False

        # 比較本地IP
        if current_ips.get("local_ip") != last_record.get("local_ip"):
            changes["local_ip"] = {
                "old": last_record.get("local_ip"),
                "new": current_ips.get("local_ip"),
            }
            has_changes = True

        # 比較公共IP
        if current_ips.get("public_ip") != last_record.get("public_ip"):
            changes["public_ip"] = {
                "old": last_record.get("public_ip"),
                "new": current_ips.get("public_ip"),
            }
            has_changes = True

        result = {
            "changed": has_changes,
            "is_first_run": False,
            "changes": changes if has_changes else "無變化",
            "last_record": last_record,
            "current_record": current_ips,
        }

        if has_changes:
            self.logger.info(f"IP已變化: {changes}")
        else:
            self.logger.info("IP無變化")

        return result

    def check_and_update(self) -> Dict[str, Any]:
        """
        檢查IP並更新歷史記錄（主要方法）

        Returns:
            Dict[str, Any]: 完整的檢查結果
        """
        try:
            # 獲取當前IP
            current_ips = self.get_all_ips()

            # 與上次記錄比較
            comparison = self.compare_with_last(current_ips)

            # 儲存當前記錄
            self.save_ip_history(current_ips)

            # 組合完整結果
            result = {
                "success": True,
                "current_ips": current_ips,
                "comparison": comparison,
                "timestamp": current_ips["timestamp"],
            }

            return result

        except Exception as e:
            error_msg = f"IP檢查過程發生錯誤: {e}"
            self.logger.error(error_msg)

            return {
                "success": False,
                "error": error_msg,
                "timestamp": self._get_current_timestamp(),
            }


def main():
    """
    測試函數 - 獨立測試IP檢測器
    """
    import logging

    # 設定日誌
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    print("=== Discord IP Bot - IP檢測器測試 ===")
    print(f"執行平台: {platform.system()} {platform.release()}")
    print(f"Python版本: {platform.python_version()}")
    print()

    try:
        # 建立IP檢測器
        detector = IPDetector()

        print("📍 開始IP檢測...")

        # 執行完整檢查
        result = detector.check_and_update()

        if result["success"]:
            print("✅ IP檢測成功！")
            print()
            print("📊 當前IP資訊:")
            current_ips = result["current_ips"]
            print(f"  🏠 本地IP: {current_ips.get('local_ip', '未知')}")
            print(f"  🌍 公共IP: {current_ips.get('public_ip', '未知')}")
            print(f"  🖥️  主機名: {current_ips.get('hostname', '未知')}")
            print(f"  ⏰ 時間戳: {current_ips.get('timestamp', '未知')}")

            if "errors" in current_ips:
                print(f"  ⚠️  錯誤: {current_ips['errors']}")

            print()
            print("🔄 變化比較:")
            comparison = result["comparison"]
            if comparison["changed"]:
                if comparison.get("is_first_run"):
                    print("  📝 首次執行，已建立基準記錄")
                else:
                    print("  🚨 檢測到IP變化:")
                    changes = comparison["changes"]
                    if isinstance(changes, dict):
                        for ip_type, change in changes.items():
                            print(f"    {ip_type}: {change['old']} → {change['new']}")
            else:
                print("  ✅ IP無變化")
        else:
            print("❌ IP檢測失敗:")
            print(f"  錯誤: {result['error']}")

    except Exception as e:
        print(f"❌ 測試過程發生未預期錯誤: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
