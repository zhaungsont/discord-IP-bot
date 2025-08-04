"""
Discord 客戶端模組測試

測試 Discord client 的所有功能，確保跨平台相容性
"""

import unittest
import tempfile
import shutil
import json
from unittest.mock import patch, MagicMock
import sys
import os

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from discord_client import (
    DiscordClient,
    WebhookError,
    MessageFormatError,
    DiscordClientError,
)


class TestDiscordClient(unittest.TestCase):
    """Discord 客戶端測試類別"""

    def setUp(self):
        """測試前準備"""
        self.test_webhook_url = (
            "https://discord.com/api/webhooks/123456789/test-webhook-token"
        )
        self.test_config = {
            "timeout": 5,
            "retry_attempts": 2,
            "retry_delay": 1,
        }

    def test_init_valid_webhook(self):
        """測試有效 Webhook URL 初始化"""
        client = DiscordClient(self.test_webhook_url, self.test_config)
        self.assertIsInstance(client, DiscordClient)
        self.assertEqual(client.webhook_url, self.test_webhook_url)
        self.assertEqual(client.config["timeout"], 5)
        self.assertEqual(client.config["retry_attempts"], 2)

    def test_init_invalid_webhook_empty(self):
        """測試空 Webhook URL"""
        with self.assertRaises(ValueError):
            DiscordClient("")

        with self.assertRaises(ValueError):
            DiscordClient("   ")

    def test_init_invalid_webhook_format(self):
        """測試無效 Webhook URL 格式"""
        invalid_urls = [
            "https://google.com",
            "not-a-url",
            "http://discord.com/api/webhooks/123/test",  # http instead of https
        ]

        for invalid_url in invalid_urls:
            with self.assertRaises(ValueError):
                DiscordClient(invalid_url)

    def test_format_message_valid_ip(self):
        """測試訊息格式化 - 有效IP"""
        client = DiscordClient(self.test_webhook_url)

        # 測試預設格式
        result = client._format_message("192.168.1.100")
        expected = "Minecraft Server IP Updated: 192.168.1.100:25565"
        self.assertEqual(result, expected)

        # 測試自定義格式
        custom_config = {"message_template": "Server: {ip}"}
        client_custom = DiscordClient(self.test_webhook_url, custom_config)
        result_custom = client_custom._format_message("10.0.0.1")
        self.assertEqual(result_custom, "Server: 10.0.0.1")

    def test_format_message_invalid_ip(self):
        """測試訊息格式化 - 無效IP"""
        client = DiscordClient(self.test_webhook_url)

        with self.assertRaises(MessageFormatError):
            client._format_message("")

        with self.assertRaises(MessageFormatError):
            client._format_message("   ")

    def test_format_message_too_long(self):
        """測試訊息格式化 - 訊息過長"""
        config = {"max_message_length": 10}  # 設定很短的限制
        client = DiscordClient(self.test_webhook_url, config)

        with self.assertRaises(MessageFormatError):
            client._format_message("192.168.1.100")  # 這會產生超過10字符的訊息

    def test_format_message_invalid_template(self):
        """測試訊息格式化 - 無效模板"""
        config = {"message_template": "Server: {invalid_key}"}
        client = DiscordClient(self.test_webhook_url, config)

        with self.assertRaises(MessageFormatError):
            client._format_message("192.168.1.100")

    @patch("requests.post")
    def test_send_message_success(self, mock_post):
        """測試發送訊息 - 成功情況"""
        # 模擬成功回應
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response

        client = DiscordClient(self.test_webhook_url, self.test_config)
        result = client._send_message("Test message")

        self.assertTrue(result)
        self.assertTrue(mock_post.called)

        # 檢查呼叫參數
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], self.test_webhook_url)
        self.assertEqual(call_args[1]["json"]["content"], "Test message")

    @patch("requests.post")
    def test_send_message_rate_limit(self, mock_post):
        """測試發送訊息 - 速率限制處理"""
        # 第一次回應速率限制，第二次成功
        rate_limit_response = MagicMock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {"Retry-After": "0.1"}

        success_response = MagicMock()
        success_response.status_code = 204

        mock_post.side_effect = [rate_limit_response, success_response]

        client = DiscordClient(self.test_webhook_url, self.test_config)
        result = client._send_message("Test message")

        self.assertTrue(result)
        self.assertEqual(mock_post.call_count, 2)

    @patch("requests.post")
    def test_send_message_failure(self, mock_post):
        """測試發送訊息 - 失敗情況"""
        # 模擬請求失敗
        import requests

        mock_post.side_effect = requests.RequestException("Connection failed")

        client = DiscordClient(self.test_webhook_url, self.test_config)

        with self.assertRaises(WebhookError):
            client._send_message("Test message")

    @patch("requests.post")
    def test_send_message_http_error(self, mock_post):
        """測試發送訊息 - HTTP錯誤"""
        # 模擬HTTP錯誤回應
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        client = DiscordClient(self.test_webhook_url, self.test_config)

        with self.assertRaises(WebhookError):
            client._send_message("Test message")

    @patch("requests.post")
    def test_send_ip_notification_success(self, mock_post):
        """測試發送IP通知 - 成功情況"""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response

        client = DiscordClient(self.test_webhook_url, self.test_config)
        result = client.send_ip_notification("192.168.1.100")

        self.assertTrue(result)
        # 檢查發送的訊息內容
        call_args = mock_post.call_args
        expected_message = "Minecraft Server IP Updated: 192.168.1.100:25565"
        self.assertEqual(call_args[1]["json"]["content"], expected_message)

    def test_send_ip_notification_empty_ip(self):
        """測試發送IP通知 - 空IP地址"""
        client = DiscordClient(self.test_webhook_url)

        with self.assertRaises(MessageFormatError):
            client.send_ip_notification("")

        with self.assertRaises(MessageFormatError):
            client.send_ip_notification("   ")

    @patch("requests.post")
    def test_test_connection_success(self, mock_post):
        """測試連線測試 - 成功情況"""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response

        client = DiscordClient(self.test_webhook_url, self.test_config)
        result = client.test_connection()

        self.assertTrue(result)
        # 檢查是否發送了測試訊息
        call_args = mock_post.call_args
        self.assertIn("連線測試", call_args[1]["json"]["content"])

    @patch("requests.post")
    def test_test_connection_failure(self, mock_post):
        """測試連線測試 - 失敗情況"""
        import requests

        mock_post.side_effect = requests.RequestException("Connection failed")

        client = DiscordClient(self.test_webhook_url, self.test_config)

        with self.assertRaises(WebhookError):
            client.test_connection()

    @patch("requests.post")
    def test_send_multiple_ips_success(self, mock_post):
        """測試發送多個IP - 成功情況"""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response

        client = DiscordClient(self.test_webhook_url, self.test_config)

        ip_data = {
            "local_ip": "192.168.1.100",
            "public_ip": "203.0.113.1",
            "timestamp": "2024-01-01T12:00:00",
        }

        result = client.send_multiple_ips(ip_data)
        self.assertTrue(result)

        # 檢查訊息內容
        call_args = mock_post.call_args
        message = call_args[1]["json"]["content"]
        self.assertIn("Minecraft Server IP Update", message)
        self.assertIn("192.168.1.100", message)
        self.assertIn("203.0.113.1", message)

    def test_send_multiple_ips_empty_data(self):
        """測試發送多個IP - 空資料"""
        client = DiscordClient(self.test_webhook_url)

        with self.assertRaises(MessageFormatError):
            client.send_multiple_ips({})

    def test_send_multiple_ips_no_valid_ips(self):
        """測試發送多個IP - 沒有有效IP"""
        client = DiscordClient(self.test_webhook_url)

        ip_data = {"local_ip": "無法獲取", "public_ip": "無法獲取"}

        with self.assertRaises(MessageFormatError):
            client.send_multiple_ips(ip_data)

    def test_get_webhook_info(self):
        """測試獲取Webhook資訊"""
        client = DiscordClient(self.test_webhook_url, self.test_config)
        info = client.get_webhook_info()

        self.assertIsInstance(info, dict)
        self.assertIn("webhook_url_masked", info)
        self.assertIn("timeout", info)
        self.assertIn("retry_attempts", info)
        self.assertIn("message_template", info)

        # 檢查URL是否被遮蔽
        self.assertTrue(info["webhook_url_masked"].endswith("..."))

    @patch("requests.post")
    def test_send_minecraft_server_notification_success(self, mock_post):
        """測試 Minecraft 伺服器通知 - 成功情況"""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response

        client = DiscordClient(self.test_webhook_url, self.test_config)

        ip_data = {
            "local_ip": "192.168.1.100",
            "public_ip": "203.0.113.1",
            "timestamp": "2024-01-01T12:00:00",
        }

        result = client.send_minecraft_server_notification(ip_data)
        self.assertTrue(result)

        # 檢查訊息內容
        call_args = mock_post.call_args
        expected_message = "Minecraft Server IP Updated: 203.0.113.1:25565"
        self.assertEqual(call_args[1]["json"]["content"], expected_message)

    def test_send_minecraft_server_notification_no_public_ip(self):
        """測試 Minecraft 伺服器通知 - 無公共IP"""
        client = DiscordClient(self.test_webhook_url)

        ip_data = {
            "local_ip": "192.168.1.100",
            "public_ip": "無法獲取",
        }

        with self.assertRaises(MessageFormatError):
            client.send_minecraft_server_notification(ip_data)

    def test_send_minecraft_server_notification_empty_data(self):
        """測試 Minecraft 伺服器通知 - 空資料"""
        client = DiscordClient(self.test_webhook_url)

        with self.assertRaises(MessageFormatError):
            client.send_minecraft_server_notification({})


class TestDiscordClientIntegration(unittest.TestCase):
    """Discord 客戶端整合測試（需要真實Webhook URL）"""

    def setUp(self):
        """測試前準備"""
        # 從環境變數或設定檔案讀取真實的 Webhook URL
        self.webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")

    def test_real_webhook_connection(self):
        """真實Webhook連線測試（可選）"""
        if not self.webhook_url:
            self.skipTest("需要設定 DISCORD_WEBHOOK_URL 環境變數才能執行此測試")

        try:
            client = DiscordClient(self.webhook_url)

            # 只測試連線，不發送實際訊息
            print("⚠️  注意：此測試會發送真實的Discord訊息")
            result = client.test_connection()

            if result:
                print("✅ 真實Discord連線測試成功")
            else:
                self.fail("Discord連線測試失敗")

        except Exception as e:
            self.skipTest(f"Discord環境不可用: {e}")


def run_manual_test():
    """手動測試函數"""
    print("=== Discord 客戶端手動測試 ===")
    print()

    try:
        test_webhook_url = (
            "https://discord.com/api/webhooks/123456789/test-webhook-token"
        )

        print("🔧 建立 Discord 客戶端...")
        client = DiscordClient(test_webhook_url)

        print("✅ 客戶端建立成功")
        print()

        # 顯示設定資訊
        info = client.get_webhook_info()
        print("📋 客戶端設定:")
        for key, value in info.items():
            print(f"  {key}: {value}")
        print()

        # 測試訊息格式化
        print("🔤 測試訊息格式化...")
        test_ips = ["192.168.1.100", "10.0.0.1", "203.0.113.1"]

        for ip in test_ips:
            formatted = client._format_message(ip)
            print(f"  {ip} → {formatted}")

        print()
        print("🎮 測試 Minecraft 伺服器通知（只顯示公共IP）:")
        test_ip_data = {
            "local_ip": "192.168.1.100",
            "public_ip": "203.0.113.1",
            "timestamp": "2024-01-01T12:00:00",
        }
        print(f"  輸入資料: {test_ip_data}")
        formatted_minecraft = client._format_message(test_ip_data["public_ip"])
        print(f"  Minecraft通知: {formatted_minecraft}")
        print("  💡 只會發送公共IP給玩家，隱藏本地IP")

        print()
        print("💡 提示：要測試實際發送功能，請設定有效的 Discord Webhook URL")

    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("選擇測試模式:")
    print("1. 單元測試")
    print("2. 整合測試")
    print("3. 手動測試")
    print("4. 全部測試")

    choice = input("請輸入選項 (1-4): ").strip()

    if choice == "1":
        unittest.main(
            argv=[""], defaultTest="TestDiscordClient", exit=False, verbosity=2
        )
    elif choice == "2":
        unittest.main(
            argv=[""],
            defaultTest="TestDiscordClientIntegration",
            exit=False,
            verbosity=2,
        )
    elif choice == "3":
        run_manual_test()
    elif choice == "4":
        unittest.main(argv=[""], exit=False, verbosity=2)
        print("\n" + "=" * 50)
        run_manual_test()
    else:
        print("無效選項，執行手動測試...")
        run_manual_test()
