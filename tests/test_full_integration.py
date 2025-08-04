"""
完整整合測試 - Discord IP Bot

測試所有模組的整合功能和端到端流程
"""

import os
import sys
import unittest
import time
import threading
from unittest.mock import patch, MagicMock
from pathlib import Path

# 確保可以導入 src 模組
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from config import ConfigManager
    from logger import LoggerManager
    from scheduler import SchedulerManager
    from ip_detector import IPDetector
    from discord_client import DiscordClient
except ImportError as e:
    print(f"無法導入模組: {e}")
    sys.exit(1)


class TestFullIntegration(unittest.TestCase):
    """完整整合測試"""

    def setUp(self):
        """測試前準備"""
        # 確保測試環境乾淨
        os.environ.pop("DISCORD_WEBHOOK_URL", None)

        # 設定測試用的環境變數
        self.test_webhook_url = "https://discord.com/api/webhooks/test/example"
        os.environ["DISCORD_WEBHOOK_URL"] = self.test_webhook_url
        os.environ["LOG_LEVEL"] = "DEBUG"
        os.environ["SCHEDULE_TIME"] = "09:00"

    def tearDown(self):
        """測試後清理"""
        # 清理測試環境變數
        test_vars = ["DISCORD_WEBHOOK_URL", "LOG_LEVEL", "SCHEDULE_TIME"]
        for var in test_vars:
            os.environ.pop(var, None)

    def test_config_logger_integration(self):
        """測試設定管理器與日誌系統整合"""
        print("🧪 測試設定管理器與日誌系統整合...")

        # 建立設定管理器
        config = ConfigManager()
        self.assertIsNotNone(config)

        # 建立日誌管理器
        log_manager = LoggerManager(config)
        self.assertIsNotNone(log_manager)

        # 測試日誌記錄
        logger = log_manager.get_logger("test")
        logger.info("整合測試日誌")

        # 測試排程日誌
        log_manager.log_execution("測試", "整合測試", "成功", test="true")

        print("  ✅ 設定與日誌整合測試通過")

    @patch("src.ip_detector.requests.get")
    def test_ip_detection_integration(self, mock_get):
        """測試IP檢測與其他模組整合"""
        print("🧪 測試IP檢測整合...")

        # 模擬網路回應
        mock_response = MagicMock()
        mock_response.text = "203.0.113.1"
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # 建立配置
        config = ConfigManager()

        # 測試IP檢測
        ip_detector = IPDetector()
        ip_result = ip_detector.check_and_update()

        self.assertTrue(ip_result["success"])
        self.assertIn("current_ips", ip_result)

        current_ips = ip_result["current_ips"]
        self.assertIn("local_ip", current_ips)
        self.assertIn("public_ip", current_ips)

        print(f"  🏠 檢測到本地IP: {current_ips['local_ip']}")
        print(f"  🌍 檢測到公共IP: {current_ips['public_ip']}")
        print("  ✅ IP檢測整合測試通過")

    @patch("src.discord_client.requests.post")
    def test_discord_integration(self, mock_post):
        """測試Discord客戶端整合"""
        print("🧪 測試Discord客戶端整合...")

        # 模擬Discord API回應
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response

        # 建立配置
        config = ConfigManager()

        # 建立Discord客戶端
        discord_client = DiscordClient(self.test_webhook_url)

        # 測試連線
        test_result = discord_client.test_connection()
        self.assertTrue(test_result)

        # 測試發送IP通知
        test_ip_data = {
            "local_ip": "192.168.1.100",
            "public_ip": "203.0.113.1",
            "timestamp": "2024-01-01T12:00:00",
        }

        result = discord_client.send_minecraft_server_notification(test_ip_data)
        self.assertTrue(result)

        # 檢查發送的訊息內容
        self.assertTrue(mock_post.called)
        call_args = mock_post.call_args
        sent_message = call_args[1]["json"]["content"]
        expected_message = "Minecraft Server IP: 203.0.113.1:25565"
        self.assertEqual(sent_message, expected_message)

        print(f"  📱 發送訊息: {sent_message}")
        print("  ✅ Discord整合測試通過")

    @patch("src.discord_client.requests.post")
    @patch("src.ip_detector.requests.get")
    def test_scheduler_integration(self, mock_ip_get, mock_discord_post):
        """測試排程系統整合"""
        print("🧪 測試排程系統整合...")

        # 模擬IP檢測回應
        mock_ip_response = MagicMock()
        mock_ip_response.text = "203.0.113.1"
        mock_ip_response.status_code = 200
        mock_ip_get.return_value = mock_ip_response

        # 模擬Discord回應
        mock_discord_response = MagicMock()
        mock_discord_response.status_code = 204
        mock_discord_post.return_value = mock_discord_response

        # 建立排程管理器
        config = ConfigManager()
        scheduler = SchedulerManager(config)

        # 測試手動任務
        success = scheduler.manual_task()
        self.assertTrue(success)

        # 檢查執行歷史
        self.assertGreater(len(scheduler.execution_history), 0)

        # 測試狀態資訊
        status = scheduler.get_status_info()
        self.assertIn("is_running", status)
        self.assertIn("system_info", status)

        print(f"  📋 執行歷史記錄: {len(scheduler.execution_history)} 筆")
        print(f"  💻 系統資源: {status['system_info']}")
        print("  ✅ 排程系統整合測試通過")

    @patch("src.discord_client.requests.post")
    @patch("src.ip_detector.requests.get")
    def test_end_to_end_workflow(self, mock_ip_get, mock_discord_post):
        """測試端到端工作流程"""
        print("🧪 測試端到端工作流程...")

        # 模擬IP檢測回應
        mock_ip_response = MagicMock()
        mock_ip_response.text = "36.230.8.13"  # 使用真實的公共IP
        mock_ip_response.status_code = 200
        mock_ip_get.return_value = mock_ip_response

        # 模擬Discord回應
        mock_discord_response = MagicMock()
        mock_discord_response.status_code = 204
        mock_discord_post.return_value = mock_discord_response

        # 步驟1: 初始化所有組件
        print("  📝 步驟1: 初始化組件...")
        config = ConfigManager()
        log_manager = LoggerManager(config)
        scheduler = SchedulerManager(config)

        # 步驟2: 執行IP檢測
        print("  🌐 步驟2: 執行IP檢測...")
        ip_detector = IPDetector()
        ip_result = ip_detector.check_and_update()
        self.assertTrue(ip_result["success"])

        current_ips = ip_result["current_ips"]
        public_ip = current_ips.get("public_ip")
        self.assertIsNotNone(public_ip)

        # 步驟3: 發送Discord通知
        print("  📱 步驟3: 發送Discord通知...")
        webhook_url = config.get("discord", "webhook_url")
        discord_client = DiscordClient(webhook_url)

        send_result = discord_client.send_minecraft_server_notification(current_ips)
        self.assertTrue(send_result)

        # 步驟4: 記錄執行結果
        print("  📋 步驟4: 記錄執行結果...")
        log_manager.log_execution("測試", "端到端測試", "成功", ip=public_ip)

        # 驗證最終結果
        self.assertTrue(mock_discord_post.called)
        call_args = mock_discord_post.call_args
        sent_message = call_args[1]["json"]["content"]

        print(f"  ✅ 完整流程成功！發送訊息: {sent_message}")
        print("  ✅ 端到端測試通過")

    def test_error_handling_integration(self):
        """測試錯誤處理整合"""
        print("🧪 測試錯誤處理整合...")

        # 測試無效的Webhook URL
        with self.assertRaises(ValueError):
            DiscordClient("invalid_url")

        # 測試缺少環境變數
        os.environ.pop("DISCORD_WEBHOOK_URL", None)

        try:
            from config import ConfigError

            with self.assertRaises(ConfigError):
                ConfigManager()
        finally:
            # 恢復環境變數
            os.environ["DISCORD_WEBHOOK_URL"] = self.test_webhook_url

        print("  ✅ 錯誤處理整合測試通過")

    @patch("src.discord_client.requests.post")
    @patch("src.ip_detector.requests.get")
    def test_minecraft_server_notification_format(self, mock_ip_get, mock_discord_post):
        """測試Minecraft伺服器通知格式"""
        print("🧪 測試Minecraft伺服器通知格式...")

        # 模擬回應
        mock_ip_response = MagicMock()
        mock_ip_response.text = "36.230.8.13"
        mock_ip_response.status_code = 200
        mock_ip_get.return_value = mock_ip_response

        mock_discord_response = MagicMock()
        mock_discord_response.status_code = 204
        mock_discord_post.return_value = mock_discord_response

        # 執行完整流程
        config = ConfigManager()
        scheduler = SchedulerManager(config)
        success = scheduler.manual_task()

        self.assertTrue(success)
        self.assertTrue(mock_discord_post.called)

        # 檢查訊息格式
        call_args = mock_discord_post.call_args
        sent_message = call_args[1]["json"]["content"]

        # 驗證格式：應該是 "Minecraft Server IP: {ip}:25565"
        self.assertIn("Minecraft Server IP:", sent_message)
        self.assertIn("36.230.8.13", sent_message)
        self.assertIn(":25565", sent_message)

        expected_format = "Minecraft Server IP: 36.230.8.13:25565"
        self.assertEqual(sent_message, expected_format)

        print(f"  🎮 Minecraft通知格式: {sent_message}")
        print("  ✅ Minecraft通知格式測試通過")


class TestMainApplication(unittest.TestCase):
    """主應用程式測試"""

    def setUp(self):
        """測試前準備"""
        self.test_webhook_url = "https://discord.com/api/webhooks/test/example"
        os.environ["DISCORD_WEBHOOK_URL"] = self.test_webhook_url

    def tearDown(self):
        """測試後清理"""
        os.environ.pop("DISCORD_WEBHOOK_URL", None)

    @patch("src.discord_client.requests.post")
    @patch("src.ip_detector.requests.get")
    def test_main_application_manual_mode(self, mock_ip_get, mock_discord_post):
        """測試主應用程式手動模式"""
        print("🧪 測試主應用程式手動模式...")

        # 模擬回應
        mock_ip_response = MagicMock()
        mock_ip_response.text = "36.230.8.13"
        mock_ip_response.status_code = 200
        mock_ip_get.return_value = mock_ip_response

        mock_discord_response = MagicMock()
        mock_discord_response.status_code = 204
        mock_discord_post.return_value = mock_discord_response

        # 導入主應用程式
        main_path = project_root / "main.py"
        sys.path.insert(0, str(project_root))

        try:
            import main

            app = main.IPBotApplication()

            # 測試手動模式
            app.run_manual_mode()

            # 驗證Discord發送
            self.assertTrue(mock_discord_post.called)

            print("  ✅ 主應用程式手動模式測試通過")

        except Exception as e:
            self.fail(f"主應用程式測試失敗: {e}")


def run_integration_tests():
    """運行整合測試"""
    print("🚀 Discord IP Bot - 整合測試開始")
    print("=" * 60)

    # 建立測試套件
    test_suite = unittest.TestSuite()

    # 添加測試案例
    test_suite.addTest(unittest.makeSuite(TestFullIntegration))
    test_suite.addTest(unittest.makeSuite(TestMainApplication))

    # 運行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    print()
    print("=" * 60)
    if result.wasSuccessful():
        print("🎉 所有整合測試通過！")
        print("✅ 系統已準備就緒，可以投入使用")
        return True
    else:
        print("❌ 部分測試失敗")
        print(f"失敗: {len(result.failures)}, 錯誤: {len(result.errors)}")
        return False


if __name__ == "__main__":
    """直接執行整合測試"""
    success = run_integration_tests()
    sys.exit(0 if success else 1)
