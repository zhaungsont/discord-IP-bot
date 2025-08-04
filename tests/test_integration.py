"""
模組整合測試

測試 IP detector 與 Discord client 模組間的整合功能
"""

import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import sys
import os

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ip_detector import IPDetector
from discord_client import DiscordClient


class TestModuleIntegration(unittest.TestCase):
    """模組整合測試類別"""

    def setUp(self):
        """測試前準備"""
        # 建立臨時目錄
        self.test_dir = tempfile.mkdtemp()

        # IP detector 設定
        self.ip_config = {
            "timeout": 5,
            "retry_attempts": 2,
            "history_file": os.path.join(self.test_dir, "test_ip_history.json"),
        }

        # Discord client 設定
        self.webhook_url = "https://discord.com/api/webhooks/123456789/test-webhook"
        self.discord_config = {
            "timeout": 5,
            "retry_attempts": 2,
        }

    def tearDown(self):
        """測試後清理"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("requests.get")  # Mock IP detector 的網路請求
    @patch("requests.post")  # Mock Discord client 的網路請求
    def test_complete_ip_notification_flow(self, mock_discord_post, mock_ip_get):
        """測試完整的IP檢測到Discord通知流程"""

        # 設定 IP detector 的 mock 回應
        mock_ip_response = MagicMock()
        mock_ip_response.status_code = 200
        mock_ip_response.text = "203.0.113.100"
        mock_ip_get.return_value = mock_ip_response

        # 設定 Discord client 的 mock 回應
        mock_discord_response = MagicMock()
        mock_discord_response.status_code = 204
        mock_discord_post.return_value = mock_discord_response

        # 建立模組實例
        ip_detector = IPDetector(self.ip_config)
        discord_client = DiscordClient(self.webhook_url, self.discord_config)

        # 執行完整流程
        # 1. 檢測IP
        ip_result = ip_detector.check_and_update()
        self.assertTrue(ip_result["success"])

        # 2. 獲取IP資訊
        current_ips = ip_result["current_ips"]
        self.assertIn("local_ip", current_ips)
        self.assertIn("public_ip", current_ips)

        # 3. 發送到Discord（使用公共IP）
        if current_ips["public_ip"] != "無法獲取":
            notification_result = discord_client.send_ip_notification(
                current_ips["public_ip"]
            )
            self.assertTrue(notification_result)

        # 4. 或發送多IP資訊
        multi_ip_result = discord_client.send_multiple_ips(current_ips)
        self.assertTrue(multi_ip_result)

        # 驗證調用
        self.assertTrue(mock_ip_get.called)
        self.assertTrue(mock_discord_post.called)

        print("✅ 完整IP檢測到Discord通知流程測試通過")

    @patch("requests.get")
    @patch("requests.post")
    def test_ip_change_notification(self, mock_discord_post, mock_ip_get):
        """測試IP變化時的通知邏輯"""

        # 設定 Discord mock
        mock_discord_response = MagicMock()
        mock_discord_response.status_code = 204
        mock_discord_post.return_value = mock_discord_response

        # 建立模組實例
        ip_detector = IPDetector(self.ip_config)
        discord_client = DiscordClient(self.webhook_url, self.discord_config)

        # 第一次檢測 - 初始IP
        mock_ip_response_1 = MagicMock()
        mock_ip_response_1.status_code = 200
        mock_ip_response_1.text = "203.0.113.100"
        mock_ip_get.return_value = mock_ip_response_1

        result1 = ip_detector.check_and_update()
        self.assertTrue(result1["success"])
        self.assertTrue(result1["comparison"]["changed"])  # 首次執行應該有變化

        # 第二次檢測 - 相同IP
        result2 = ip_detector.check_and_update()
        self.assertTrue(result2["success"])
        self.assertFalse(result2["comparison"]["changed"])  # 相同IP，無變化

        # 第三次檢測 - 不同IP
        mock_ip_response_2 = MagicMock()
        mock_ip_response_2.status_code = 200
        mock_ip_response_2.text = "203.0.113.200"  # 不同的IP
        mock_ip_get.return_value = mock_ip_response_2

        result3 = ip_detector.check_and_update()
        self.assertTrue(result3["success"])
        self.assertTrue(result3["comparison"]["changed"])  # IP變化了

        # 只有在IP變化時才發送通知
        if result3["comparison"]["changed"]:
            current_ips = result3["current_ips"]
            if current_ips["public_ip"] != "無法獲取":
                notification_result = discord_client.send_ip_notification(
                    current_ips["public_ip"]
                )
                self.assertTrue(notification_result)

        print("✅ IP變化通知邏輯測試通過")

    def test_error_handling_integration(self):
        """測試整合流程中的錯誤處理"""

        # 建立模組實例
        ip_detector = IPDetector(self.ip_config)
        discord_client = DiscordClient(self.webhook_url, self.discord_config)

        # 測試無效IP的處理
        try:
            discord_client.send_ip_notification("")
            self.fail("應該拋出 MessageFormatError")
        except Exception as e:
            self.assertIn("MessageFormatError", str(type(e)))

        # 測試空IP資料的處理
        try:
            discord_client.send_multiple_ips({})
            self.fail("應該拋出 MessageFormatError")
        except Exception as e:
            self.assertIn("MessageFormatError", str(type(e)))

        print("✅ 錯誤處理整合測試通過")

    def test_configuration_integration(self):
        """測試模組間的配置整合"""

        # 建立具有自定義配置的模組
        custom_ip_config = {
            "timeout": 3,
            "retry_attempts": 1,
            "history_file": os.path.join(self.test_dir, "custom_ip_history.json"),
        }

        custom_discord_config = {
            "timeout": 3,
            "retry_attempts": 1,
            "message_template": "Server IP: {ip}",
        }

        ip_detector = IPDetector(custom_ip_config)
        discord_client = DiscordClient(self.webhook_url, custom_discord_config)

        # 驗證配置
        self.assertEqual(ip_detector.config["timeout"], 3)
        self.assertEqual(discord_client.config["timeout"], 3)
        self.assertEqual(discord_client.config["message_template"], "Server IP: {ip}")

        # 測試自定義訊息格式
        formatted_message = discord_client._format_message("192.168.1.100")
        self.assertEqual(formatted_message, "Server IP: 192.168.1.100")

        print("✅ 配置整合測試通過")


class TestIntegrationEndToEnd(unittest.TestCase):
    """端到端整合測試"""

    def setUp(self):
        """測試前準備"""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """測試後清理"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("requests.get")
    @patch("requests.post")
    def test_minecraft_server_ip_notification(self, mock_discord_post, mock_ip_get):
        """測試 Minecraft 伺服器 IP 通知的完整流程"""

        # 模擬真實環境的設定
        webhook_url = "https://discord.com/api/webhooks/123456789/test-webhook"

        # 設定網路 mock
        mock_ip_response = MagicMock()
        mock_ip_response.status_code = 200
        mock_ip_response.text = "203.0.113.42"  # 模擬的Minecraft伺服器IP
        mock_ip_get.return_value = mock_ip_response

        mock_discord_response = MagicMock()
        mock_discord_response.status_code = 204
        mock_discord_post.return_value = mock_discord_response

        # 建立系統
        ip_config = {
            "history_file": os.path.join(self.test_dir, "minecraft_ip_history.json")
        }
        ip_detector = IPDetector(ip_config)
        discord_client = DiscordClient(webhook_url)

        # 執行完整的Minecraft伺服器IP通知流程
        try:
            # 1. 檢測IP
            ip_result = ip_detector.check_and_update()
            self.assertTrue(ip_result["success"])

            # 2. 提取伺服器IP（這裡假設使用公共IP）
            server_ip = ip_result["current_ips"]["public_ip"]

            # 3. 發送Minecraft伺服器通知
            if server_ip != "無法獲取":
                notification_sent = discord_client.send_ip_notification(server_ip)
                self.assertTrue(notification_sent)

                # 驗證訊息格式
                call_args = mock_discord_post.call_args
                sent_message = call_args[1]["json"]["content"]
                expected_message = f"Minecraft Server IP Updated: {server_ip}:25565"
                self.assertEqual(sent_message, expected_message)

                print(f"✅ Minecraft伺服器IP通知發送成功: {sent_message}")
            else:
                self.fail("無法獲取有效的伺服器IP")

        except Exception as e:
            self.fail(f"端到端測試失敗: {e}")


def run_integration_tests():
    """執行整合測試"""
    print("=== Discord IP Bot - 模組整合測試 ===")
    print()

    # 執行所有整合測試
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    if result.wasSuccessful():
        print("\n✅ 所有整合測試通過！")
        print("🔗 IP detector 與 Discord client 模組整合正常")
    else:
        print(f"\n❌ 有 {len(result.failures)} 個測試失敗, {len(result.errors)} 個錯誤")


if __name__ == "__main__":
    run_integration_tests()
