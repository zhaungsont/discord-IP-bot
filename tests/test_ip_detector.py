"""
IP檢測器模組測試

測試 IP detector 的所有功能，確保跨平台相容性
"""

import unittest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ip_detector import IPDetector, NetworkError, IPDetectorError


class TestIPDetector(unittest.TestCase):
    """IP檢測器測試類別"""

    def setUp(self):
        """測試前準備"""
        # 建立臨時目錄用於測試
        self.test_dir = tempfile.mkdtemp()
        self.test_config = {
            "timeout": 5,
            "retry_attempts": 2,
            "retry_delay": 1,
            "history_file": os.path.join(self.test_dir, "test_ip_history.json"),
        }
        self.detector = IPDetector(self.test_config)

    def tearDown(self):
        """測試後清理"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_init(self):
        """測試初始化"""
        self.assertIsInstance(self.detector, IPDetector)
        self.assertEqual(self.detector.config["timeout"], 5)
        self.assertEqual(self.detector.config["retry_attempts"], 2)

    def test_is_valid_local_ip(self):
        """測試本地IP驗證"""
        # 有效的私有IP
        self.assertTrue(self.detector._is_valid_local_ip("192.168.1.100"))
        self.assertTrue(self.detector._is_valid_local_ip("10.0.0.1"))
        self.assertTrue(self.detector._is_valid_local_ip("172.16.0.1"))

        # 無效的IP
        self.assertFalse(self.detector._is_valid_local_ip("127.0.0.1"))
        self.assertFalse(self.detector._is_valid_local_ip("0.0.0.0"))
        self.assertFalse(self.detector._is_valid_local_ip("8.8.8.8"))
        self.assertFalse(self.detector._is_valid_local_ip("invalid"))
        self.assertFalse(self.detector._is_valid_local_ip(""))

    def test_is_valid_ip_format(self):
        """測試IP格式驗證"""
        # 有效格式
        self.assertTrue(self.detector._is_valid_ip_format("192.168.1.1"))
        self.assertTrue(self.detector._is_valid_ip_format("8.8.8.8"))
        self.assertTrue(self.detector._is_valid_ip_format("255.255.255.255"))

        # 無效格式
        self.assertFalse(self.detector._is_valid_ip_format("256.1.1.1"))
        self.assertFalse(self.detector._is_valid_ip_format("192.168.1"))
        self.assertFalse(self.detector._is_valid_ip_format("invalid"))
        self.assertFalse(self.detector._is_valid_ip_format(""))

    def test_get_local_ip(self):
        """測試獲取本地IP"""
        try:
            local_ip = self.detector.get_local_ip()
            self.assertIsInstance(local_ip, str)
            self.assertTrue(self.detector._is_valid_ip_format(local_ip))
            print(f"✓ 本地IP測試通過: {local_ip}")
        except NetworkError as e:
            self.skipTest(f"本地IP獲取失敗，可能是網路環境問題: {e}")

    @patch("requests.get")
    def test_get_public_ip_success(self, mock_get):
        """測試獲取公共IP - 成功情況"""
        # 模擬成功響應
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "203.0.113.1"
        mock_get.return_value = mock_response

        public_ip = self.detector.get_public_ip()
        self.assertEqual(public_ip, "203.0.113.1")
        self.assertTrue(mock_get.called)

    @patch("requests.get")
    def test_get_public_ip_failure(self, mock_get):
        """測試獲取公共IP - 失敗情況"""
        # 模擬請求失敗
        import requests

        mock_get.side_effect = requests.RequestException("Connection failed")

        with self.assertRaises(NetworkError):
            self.detector.get_public_ip()

    @patch("requests.get")
    def test_get_all_ips(self, mock_get):
        """測試獲取所有IP"""
        # 模擬公共IP請求成功
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "203.0.113.1"
        mock_get.return_value = mock_response

        ips = self.detector.get_all_ips()

        self.assertIsInstance(ips, dict)
        self.assertIn("local_ip", ips)
        self.assertIn("public_ip", ips)
        self.assertIn("timestamp", ips)
        self.assertIn("platform", ips)
        self.assertIn("hostname", ips)

        print(f"✓ 所有IP測試通過: {ips}")

    def test_save_and_load_history(self):
        """測試IP歷史記錄儲存和讀取"""
        test_data = {
            "local_ip": "192.168.1.100",
            "public_ip": "203.0.113.1",
            "timestamp": "2024-01-01T12:00:00",
        }

        # 儲存歷史記錄
        self.detector.save_ip_history(test_data)

        # 讀取歷史記錄
        last_record = self.detector.get_last_ip_record()

        self.assertIsNotNone(last_record)
        self.assertEqual(last_record["local_ip"], "192.168.1.100")
        self.assertEqual(last_record["public_ip"], "203.0.113.1")

        print("✓ 歷史記錄測試通過")

    def test_compare_with_last_first_run(self):
        """測試首次執行的IP比較"""
        current_ips = {"local_ip": "192.168.1.100", "public_ip": "203.0.113.1"}

        comparison = self.detector.compare_with_last(current_ips)

        self.assertTrue(comparison["changed"])
        self.assertTrue(comparison["is_first_run"])
        self.assertEqual(comparison["changes"], "首次執行")
        self.assertIsNone(comparison["last_record"])

        print("✓ 首次執行比較測試通過")

    def test_compare_with_last_no_changes(self):
        """測試無變化的IP比較"""
        # 先儲存一筆記錄
        test_data = {"local_ip": "192.168.1.100", "public_ip": "203.0.113.1"}
        self.detector.save_ip_history(test_data)

        # 使用相同的IP進行比較
        comparison = self.detector.compare_with_last(test_data)

        self.assertFalse(comparison["changed"])
        self.assertFalse(comparison["is_first_run"])
        self.assertEqual(comparison["changes"], "無變化")

        print("✓ 無變化比較測試通過")

    def test_compare_with_last_with_changes(self):
        """測試有變化的IP比較"""
        # 先儲存一筆記錄
        old_data = {"local_ip": "192.168.1.100", "public_ip": "203.0.113.1"}
        self.detector.save_ip_history(old_data)

        # 使用不同的IP進行比較
        new_data = {"local_ip": "192.168.1.101", "public_ip": "203.0.113.2"}
        comparison = self.detector.compare_with_last(new_data)

        self.assertTrue(comparison["changed"])
        self.assertFalse(comparison["is_first_run"])
        self.assertIsInstance(comparison["changes"], dict)
        self.assertIn("local_ip", comparison["changes"])
        self.assertIn("public_ip", comparison["changes"])

        print("✓ 有變化比較測試通過")

    @patch("requests.get")
    def test_check_and_update_success(self, mock_get):
        """測試完整的檢查和更新流程"""
        # 模擬公共IP請求成功
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "203.0.113.1"
        mock_get.return_value = mock_response

        result = self.detector.check_and_update()

        self.assertTrue(result["success"])
        self.assertIn("current_ips", result)
        self.assertIn("comparison", result)
        self.assertIn("timestamp", result)

        print("✓ 完整流程測試通過")


class TestIPDetectorIntegration(unittest.TestCase):
    """IP檢測器整合測試（需要真實網路連線）"""

    def setUp(self):
        """測試前準備"""
        self.test_dir = tempfile.mkdtemp()
        self.test_config = {
            "history_file": os.path.join(self.test_dir, "integration_test_history.json")
        }
        self.detector = IPDetector(self.test_config)

    def tearDown(self):
        """測試後清理"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_real_ip_detection(self):
        """真實IP檢測測試（需要網路連線）"""
        try:
            result = self.detector.check_and_update()

            if result["success"]:
                print("✓ 真實網路IP檢測成功")
                print(f"  本地IP: {result['current_ips'].get('local_ip')}")
                print(f"  公共IP: {result['current_ips'].get('public_ip')}")
            else:
                print(f"⚠ 真實網路IP檢測失敗: {result.get('error')}")
                self.skipTest("需要網路連線才能執行此測試")

        except Exception as e:
            self.skipTest(f"網路環境不可用: {e}")


def run_manual_test():
    """手動測試函數"""
    print("=== IP檢測器手動測試 ===")
    print()

    try:
        # 建立臨時配置
        temp_dir = tempfile.mkdtemp()
        config = {"history_file": os.path.join(temp_dir, "manual_test_history.json")}

        detector = IPDetector(config)

        print("🔍 執行IP檢測...")
        result = detector.check_and_update()

        if result["success"]:
            print("✅ 檢測成功！")
            ips = result["current_ips"]
            print(f"本地IP: {ips.get('local_ip')}")
            print(f"公共IP: {ips.get('public_ip')}")
            print(f"平台: {ips.get('platform')}")
            print(f"主機名: {ips.get('hostname')}")

            # 測試第二次執行（檢查比較功能）
            print()
            print("🔄 執行第二次檢測（測試比較功能）...")
            result2 = detector.check_and_update()

            if result2["success"]:
                comparison = result2["comparison"]
                if comparison["changed"]:
                    print("🚨 檢測到變化")
                else:
                    print("✅ 無變化（正常）")
        else:
            print(f"❌ 檢測失敗: {result['error']}")

        # 清理
        shutil.rmtree(temp_dir, ignore_errors=True)

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
        unittest.main(argv=[""], defaultTest="TestIPDetector", exit=False, verbosity=2)
    elif choice == "2":
        unittest.main(
            argv=[""], defaultTest="TestIPDetectorIntegration", exit=False, verbosity=2
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
