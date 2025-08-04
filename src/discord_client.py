"""
Discord 通信模組 - Discord IP Bot

此模組負責向 Discord 頻道發送 IP 通知訊息。
設計為完全跨平台相容 (MacOS, Windows 10/11, Linux)，並可獨立測試。
"""

import logging
import time
from typing import Dict, Optional, Any
import requests
from urllib3.exceptions import InsecureRequestWarning
import urllib3

# 禁用 SSL 警告以避免在某些環境下的問題
urllib3.disable_warnings(InsecureRequestWarning)


class DiscordClientError(Exception):
    """Discord 通信相關錯誤的基礎例外類別"""

    pass


class WebhookError(DiscordClientError):
    """Webhook 通信相關錯誤"""

    pass


class MessageFormatError(DiscordClientError):
    """訊息格式相關錯誤"""

    pass


class DiscordClient:
    """
    Discord 通信客戶端類別

    功能：
    - 透過 Webhook 發送訊息到指定 Discord 頻道
    - 格式化 IP 地址為 Minecraft 伺服器通知訊息
    - 提供連線測試和錯誤處理機制
    - 支援重試機制確保訊息送達
    """

    def __init__(self, webhook_url: str, config: Optional[Dict[str, Any]] = None):
        """
        初始化 Discord 客戶端

        Args:
            webhook_url: Discord Webhook URL
            config: 設定字典，包含逾時設定、重試次數等
        """
        self.logger = logging.getLogger(__name__)

        # 驗證 Webhook URL
        if not webhook_url or not webhook_url.strip():
            raise ValueError("Webhook URL 不能為空")

        if not webhook_url.startswith("https://discord.com/api/webhooks/"):
            raise ValueError("無效的 Discord Webhook URL 格式")

        self.webhook_url = webhook_url.strip()

        # 預設設定
        self.config = {
            "timeout": 10,
            "retry_attempts": 3,
            "retry_delay": 2,
            "message_template": "Minecraft Server IP: {ip}:25565",
            "max_message_length": 2000,
        }

        # 更新使用者提供的設定
        if config:
            self.config.update(config)

        self.logger.info("Discord 客戶端初始化完成")

    def send_ip_notification(self, ip_address: str) -> bool:
        """
        發送 IP 地址通知到 Discord 頻道

        Args:
            ip_address: 要通知的 IP 地址

        Returns:
            bool: 發送是否成功

        Raises:
            MessageFormatError: 訊息格式錯誤時拋出
            WebhookError: Webhook 通信錯誤時拋出
        """
        if not ip_address or not ip_address.strip():
            raise MessageFormatError("IP 地址不能為空")

        # 格式化訊息
        message = self._format_message(ip_address.strip())

        # 發送訊息
        return self._send_message(message)

    def _format_message(self, ip_address: str) -> str:
        """
        格式化 IP 地址為 Discord 訊息

        Args:
            ip_address: IP 地址

        Returns:
            str: 格式化後的訊息

        Raises:
            MessageFormatError: 格式化失敗時拋出
        """
        # 檢查輸入
        if not ip_address or not ip_address.strip():
            raise MessageFormatError("IP 地址不能為空")

        try:
            message = self.config["message_template"].format(ip=ip_address)

            # 檢查訊息長度
            if len(message) > self.config["max_message_length"]:
                raise MessageFormatError(
                    f"訊息長度超過限制 ({len(message)} > {self.config['max_message_length']})"
                )

            self.logger.debug(f"訊息格式化完成: {message}")
            return message

        except KeyError as e:
            error_msg = f"訊息模板格式錯誤: {e}"
            self.logger.error(error_msg)
            raise MessageFormatError(error_msg)

        except Exception as e:
            error_msg = f"訊息格式化失敗: {e}"
            self.logger.error(error_msg)
            raise MessageFormatError(error_msg)

    def _send_message(self, message: str) -> bool:
        """
        發送訊息到 Discord Webhook

        Args:
            message: 要發送的訊息

        Returns:
            bool: 發送是否成功

        Raises:
            WebhookError: 發送失敗時拋出
        """
        payload = {"content": message}

        last_error = None

        for attempt in range(self.config["retry_attempts"]):
            try:
                self.logger.debug(
                    f"嘗試發送訊息到 Discord (第{attempt + 1}次): {message}"
                )

                response = requests.post(
                    self.webhook_url,
                    json=payload,
                    timeout=self.config["timeout"],
                    headers={"User-Agent": "Discord-IP-Bot/1.0"},
                )

                # 檢查回應狀態
                if response.status_code == 204:
                    self.logger.info("Discord 訊息發送成功")
                    return True
                elif response.status_code == 429:
                    # 處理速率限制
                    retry_after = response.headers.get("Retry-After", "1")
                    try:
                        wait_time = float(retry_after)
                    except ValueError:
                        wait_time = 1

                    self.logger.warning(f"遇到速率限制，等待 {wait_time} 秒後重試")
                    time.sleep(wait_time)
                    continue
                else:
                    error_msg = f"Discord API 回傳錯誤狀態碼: {response.status_code}"
                    if response.text:
                        error_msg += f", 回應內容: {response.text}"
                    raise WebhookError(error_msg)

            except requests.RequestException as e:
                last_error = e
                self.logger.warning(f"發送訊息失敗 (第{attempt + 1}次): {e}")

                if attempt < self.config["retry_attempts"] - 1:
                    time.sleep(self.config["retry_delay"])

        # 所有重試都失敗
        error_msg = f"所有發送嘗試都失敗，最後錯誤: {last_error}"
        self.logger.error(error_msg)
        raise WebhookError(error_msg)

    def test_connection(self) -> bool:
        """
        測試 Discord Webhook 連線狀態

        Returns:
            bool: 連線是否正常

        Raises:
            WebhookError: 連線測試失敗時拋出
        """
        try:
            self.logger.info("測試 Discord Webhook 連線...")

            # 發送測試訊息
            test_message = "🔍 Discord IP Bot 連線測試"
            return self._send_message(test_message)

        except Exception as e:
            error_msg = f"Discord 連線測試失敗: {e}"
            self.logger.error(error_msg)
            raise WebhookError(error_msg)

    def send_minecraft_server_notification(self, ip_data: Dict[str, str]) -> bool:
        """
        發送 Minecraft 伺服器 IP 通知（只使用公共 IP）

        Args:
            ip_data: 包含 IP 資訊的字典

        Returns:
            bool: 發送是否成功

        Raises:
            MessageFormatError: 無有效公共 IP 時拋出
        """
        if not ip_data:
            raise MessageFormatError("IP 資料不能為空")

        # 只使用公共 IP 進行 Minecraft 伺服器通知
        public_ip = ip_data.get("public_ip")

        if not public_ip or public_ip == "無法獲取":
            raise MessageFormatError(
                "無法獲取有效的公共 IP 地址，無法提供 Minecraft 伺服器連線資訊"
            )

        # 發送格式化的 Minecraft 伺服器通知
        return self.send_ip_notification(public_ip)

    def send_multiple_ips(self, ip_data: Dict[str, str]) -> bool:
        """
        發送多個 IP 地址資訊（除錯用，包含詳細資訊）

        Args:
            ip_data: 包含不同類型 IP 的字典

        Returns:
            bool: 發送是否成功
        """
        if not ip_data:
            raise MessageFormatError("IP 資料不能為空")

        # 構建訊息內容
        message_parts = ["🌐 **IP Information (Debug)**"]

        if "local_ip" in ip_data and ip_data["local_ip"] != "無法獲取":
            message_parts.append(f"🏠 Local IP: {ip_data['local_ip']}")

        if "public_ip" in ip_data and ip_data["public_ip"] != "無法獲取":
            message_parts.append(f"🌍 Public IP: {ip_data['public_ip']}:25565")

        # 添加時間戳記
        if "timestamp" in ip_data:
            message_parts.append(f"⏰ Updated: {ip_data['timestamp']}")

        if len(message_parts) == 1:  # 只有標題，沒有實際 IP
            raise MessageFormatError("沒有有效的 IP 地址可發送")

        message = "\n".join(message_parts)
        return self._send_message(message)

    def get_webhook_info(self) -> Dict[str, str]:
        """
        獲取 Webhook 基本資訊（除錯用）

        Returns:
            Dict[str, str]: Webhook 資訊
        """
        return {
            "webhook_url_masked": self.webhook_url[:50] + "...",
            "timeout": str(self.config["timeout"]),
            "retry_attempts": str(self.config["retry_attempts"]),
            "message_template": self.config["message_template"],
        }


def main():
    """
    測試函數 - 獨立測試 Discord 客戶端
    """
    import logging

    # 設定日誌
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    print("=== Discord IP Bot - Discord 客戶端測試 ===")
    print()

    # 注意：實際使用時需要真實的 Webhook URL
    test_webhook_url = "https://discord.com/api/webhooks/test/example"

    try:
        print("📝 建立 Discord 客戶端...")

        # 建立客戶端（使用測試 URL，會失敗但可以測試基本功能）
        client = DiscordClient(test_webhook_url)

        print("✅ Discord 客戶端建立成功")
        print()

        # 顯示設定資訊
        info = client.get_webhook_info()
        print("🔧 客戶端設定:")
        for key, value in info.items():
            print(f"  {key}: {value}")
        print()

        # 測試訊息格式化
        print("🔤 測試 Minecraft 伺服器訊息格式化...")
        test_ip = "203.0.113.1"
        formatted_message = client._format_message(test_ip)
        print(f"✅ 格式化結果: {formatted_message}")
        print()

        # 測試 Minecraft 伺服器通知
        print("🎮 測試 Minecraft 伺服器通知格式...")
        test_ip_data = {
            "local_ip": "192.168.1.100",
            "public_ip": "203.0.113.1",
            "timestamp": "2024-01-01T12:00:00",
        }

        print("💡 新的訊息格式只會顯示公共IP和端口 (玩家連線用)")
        print("💡 訊息範例: 'Minecraft Server IP: 203.0.113.1:25565'")
        print("💡 實際發送需要有效的 Discord Webhook URL")

    except Exception as e:
        print(f"❌ 測試過程發生錯誤: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
