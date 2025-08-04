#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IP歷史管理系統單元測試 - Discord IP Bot

測試 IPHistoryManager 類別的所有功能：
- 歷史記錄創建和載入
- IP變化檢測
- 統計分析
- 清理功能
- 錯誤處理

作者: Discord IP Bot Team
版本: 1.0.0
建立時間: 2025-01-04
"""

import sys
import os
import json
import tempfile
import unittest
from unittest.mock import patch, mock_open
from datetime import datetime, timezone, timedelta
from pathlib import Path

# 確保可以導入src模組
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.ip_history import (
    IPHistoryManager,
    IPHistoryError,
    IPHistoryFileError,
    IPHistoryValidationError,
)


class TestIPHistoryManager(unittest.TestCase):
    """IPHistoryManager 單元測試"""

    def setUp(self):
        """測試前準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.history_file = os.path.join(self.temp_dir, "test_ip_history.json")
        self.config = {
            "keep_days": 30,
            "max_records": 100,
            "auto_cleanup": True,
            "backup_on_corruption": True,
        }

    def tearDown(self):
        """測試後清理"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_new_history_file(self):
        """測試初始化新的歷史檔案"""
        manager = IPHistoryManager(self.history_file, self.config)

        # 檢查檔案是否被創建
        self.assertTrue(Path(self.history_file).exists())

        # 檢查初始結構
        with open(self.history_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("metadata", data)
        self.assertIn("current", data)
        self.assertIn("statistics", data)
        self.assertIn("history", data)
        self.assertEqual(data["metadata"]["total_checks"], 0)
        self.assertEqual(len(data["history"]), 0)

    def test_init_existing_history_file(self):
        """測試載入現有的歷史檔案"""
        # 創建現有歷史檔案
        existing_data = {
            "metadata": {
                "created_at": "2025-01-01T00:00:00+00:00",
                "last_updated": "2025-01-01T00:00:00+00:00",
                "version": "1.0",
                "total_checks": 5,
            },
            "current": {
                "public_ip": "203.0.113.1",
                "local_ip": "192.168.1.100",
                "last_updated": "2025-01-01T00:00:00+00:00",
                "last_notification_sent": None,
            },
            "statistics": {
                "total_ip_changes": 1,
                "total_notifications_sent": 1,
                "last_change_date": "2025-01-01T00:00:00+00:00",
                "check_frequency": {"scheduled": 3, "manual": 2, "test": 0},
            },
            "history": [
                {
                    "timestamp": "2025-01-01T00:00:00+00:00",
                    "public_ip": "203.0.113.1",
                    "local_ip": "192.168.1.100",
                    "mode": "manual",
                    "ip_changed": True,
                    "notification_sent": True,
                    "execution_duration": 2.5,
                }
            ],
        }

        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(existing_data, f)

        # 載入現有檔案
        manager = IPHistoryManager(self.history_file, self.config)

        # 檢查資料是否正確載入
        self.assertEqual(manager.get_last_public_ip(), "203.0.113.1")
        stats = manager.get_history_stats()
        self.assertEqual(stats["metadata"]["total_checks"], 5)

    def test_has_ip_changed_first_run(self):
        """測試首次執行時的IP變化檢測"""
        manager = IPHistoryManager(self.history_file, self.config)

        # 首次執行應該視為有變化
        has_changed = manager.has_ip_changed("203.0.113.1")
        self.assertTrue(has_changed)

    def test_has_ip_changed_same_ip(self):
        """測試相同IP的變化檢測"""
        manager = IPHistoryManager(self.history_file, self.config)

        # 記錄第一個IP
        ip_data = {"public_ip": "203.0.113.1", "local_ip": "192.168.1.100"}
        manager.record_ip_check(ip_data, "test", False, 1.0)

        # 相同IP應該不算變化
        has_changed = manager.has_ip_changed("203.0.113.1")
        self.assertFalse(has_changed)

    def test_has_ip_changed_different_ip(self):
        """測試不同IP的變化檢測"""
        manager = IPHistoryManager(self.history_file, self.config)

        # 記錄第一個IP
        ip_data = {"public_ip": "203.0.113.1", "local_ip": "192.168.1.100"}
        manager.record_ip_check(ip_data, "test", False, 1.0)

        # 不同IP應該算變化
        has_changed = manager.has_ip_changed("203.0.113.2")
        self.assertTrue(has_changed)

    def test_record_ip_check_success(self):
        """測試成功記錄IP檢測事件"""
        manager = IPHistoryManager(self.history_file, self.config)

        ip_data = {"public_ip": "203.0.113.1", "local_ip": "192.168.1.100"}

        success = manager.record_ip_check(ip_data, "manual", True, 2.5)
        self.assertTrue(success)

        # 檢查記錄是否正確
        stats = manager.get_history_stats()
        self.assertEqual(stats["metadata"]["total_checks"], 1)
        self.assertEqual(stats["statistics"]["total_notifications_sent"], 1)
        self.assertEqual(stats["statistics"]["check_frequency"]["manual"], 1)

        # 檢查當前IP是否更新
        self.assertEqual(manager.get_last_public_ip(), "203.0.113.1")

    def test_record_ip_check_with_change(self):
        """測試記錄IP變化事件"""
        manager = IPHistoryManager(self.history_file, self.config)

        # 記錄第一個IP
        ip_data1 = {"public_ip": "203.0.113.1", "local_ip": "192.168.1.100"}
        manager.record_ip_check(ip_data1, "scheduled", True, 1.0)

        # 記錄變化的IP
        ip_data2 = {"public_ip": "203.0.113.2", "local_ip": "192.168.1.100"}
        manager.record_ip_check(ip_data2, "scheduled", True, 1.5)

        # 檢查統計
        stats = manager.get_history_stats()
        self.assertEqual(stats["statistics"]["total_ip_changes"], 2)  # 首次 + 變化
        self.assertEqual(stats["metadata"]["total_checks"], 2)

    def test_get_history_stats(self):
        """測試獲取歷史統計資訊"""
        manager = IPHistoryManager(self.history_file, self.config)

        # 記錄一些測試資料
        test_data = [
            ("203.0.113.1", "scheduled", True, 1.0),
            ("203.0.113.1", "manual", True, 1.2),
            ("203.0.113.2", "scheduled", True, 1.5),
            ("203.0.113.2", "test", False, 0.8),
        ]

        for ip, mode, sent, duration in test_data:
            ip_data = {"public_ip": ip, "local_ip": "192.168.1.100"}
            manager.record_ip_check(ip_data, mode, sent, duration)

        stats = manager.get_history_stats()

        # 檢查基本統計
        self.assertEqual(stats["metadata"]["total_checks"], 4)
        self.assertEqual(stats["statistics"]["total_notifications_sent"], 3)
        self.assertEqual(stats["total_history_records"], 4)

        # 檢查模式頻率
        self.assertEqual(stats["statistics"]["check_frequency"]["scheduled"], 2)
        self.assertEqual(stats["statistics"]["check_frequency"]["manual"], 1)
        self.assertEqual(stats["statistics"]["check_frequency"]["test"], 1)

        # 檢查百分比
        self.assertEqual(stats["frequency_percentage"]["scheduled"], 50.0)
        self.assertEqual(stats["frequency_percentage"]["manual"], 25.0)
        self.assertEqual(stats["frequency_percentage"]["test"], 25.0)

    def test_cleanup_old_records(self):
        """測試清理舊記錄功能"""
        manager = IPHistoryManager(self.history_file, self.config)

        # 創建一些舊記錄
        old_time = datetime.now(timezone.utc) - timedelta(days=35)
        recent_time = datetime.now(timezone.utc)

        # 手動添加歷史記錄
        history_data = manager._history_data
        history_data["history"] = [
            {
                "timestamp": old_time.isoformat(),
                "public_ip": "203.0.113.1",
                "mode": "scheduled",
                "ip_changed": False,
                "notification_sent": False,
            },
            {
                "timestamp": recent_time.isoformat(),
                "public_ip": "203.0.113.2",
                "mode": "manual",
                "ip_changed": True,
                "notification_sent": True,
            },
        ]
        manager.save_history(history_data)

        # 清理舊記錄（保留30天）
        cleaned_count = manager.cleanup_old_records(30)

        # 檢查是否清理了舊記錄
        self.assertEqual(cleaned_count, 1)
        stats = manager.get_history_stats()
        self.assertEqual(stats["total_history_records"], 1)

    def test_export_history(self):
        """測試匯出歷史記錄功能"""
        manager = IPHistoryManager(self.history_file, self.config)

        # 記錄一些測試資料
        ip_data = {"public_ip": "203.0.113.1", "local_ip": "192.168.1.100"}
        manager.record_ip_check(ip_data, "manual", True, 1.0)

        # 匯出歷史記錄
        export_file = os.path.join(self.temp_dir, "export_test.json")
        result_file = manager.export_history(export_file)

        # 檢查匯出檔案
        self.assertEqual(result_file, export_file)
        self.assertTrue(Path(export_file).exists())

        # 檢查匯出內容
        with open(export_file, "r", encoding="utf-8") as f:
            exported_data = json.load(f)

        self.assertIn("metadata", exported_data)
        self.assertIn("history", exported_data)
        self.assertEqual(len(exported_data["history"]), 1)

    def test_get_ip_change_timeline(self):
        """測試獲取IP變化時間線"""
        manager = IPHistoryManager(self.history_file, self.config)

        # 記錄IP變化事件
        test_ips = ["203.0.113.1", "203.0.113.2", "203.0.113.3"]

        for ip in test_ips:
            ip_data = {"public_ip": ip, "local_ip": "192.168.1.100"}
            manager.record_ip_check(ip_data, "scheduled", True, 1.0)

        # 獲取變化時間線
        timeline = manager.get_ip_change_timeline(days=7)

        # 應該有2個變化事件（第一個是首次記錄，後面2個是變化）
        self.assertEqual(len(timeline), 3)  # 所有記錄都算IP變化（包括首次）

    def test_invalid_history_data_validation(self):
        """測試無效歷史資料的驗證"""
        manager = IPHistoryManager(self.history_file, self.config)

        # 測試缺少必要欄位的資料
        invalid_data = {"metadata": {}}  # 缺少其他必要欄位

        with self.assertRaises(IPHistoryValidationError):
            manager._validate_history_data(invalid_data)

    def test_corrupted_file_handling(self):
        """測試損壞檔案的處理"""
        # 創建損壞的JSON檔案
        with open(self.history_file, "w") as f:
            f.write("invalid json content {")

        # 應該能處理損壞檔案並創建新的
        manager = IPHistoryManager(self.history_file, self.config)

        # 檢查是否創建了新的有效檔案
        stats = manager.get_history_stats()
        self.assertEqual(stats["metadata"]["total_checks"], 0)

    @patch("builtins.open", side_effect=PermissionError("Permission denied"))
    def test_permission_error_handling(self, mock_file):
        """測試權限錯誤的處理"""
        with self.assertRaises(IPHistoryFileError):
            IPHistoryManager(self.history_file, self.config)

    def test_edge_case_empty_ip(self):
        """測試空IP地址的邊界情況"""
        manager = IPHistoryManager(self.history_file, self.config)

        # 測試空IP
        has_changed = manager.has_ip_changed("")
        self.assertFalse(has_changed)

        # 測試"無法獲取"的IP
        has_changed = manager.has_ip_changed("無法獲取")
        self.assertFalse(has_changed)

    def test_max_records_limit(self):
        """測試最大記錄數限制"""
        config = self.config.copy()
        config["max_records"] = 5
        manager = IPHistoryManager(self.history_file, config)

        # 記錄超過最大數量的記錄
        for i in range(10):
            ip_data = {"public_ip": f"203.0.113.{i}", "local_ip": "192.168.1.100"}
            manager.record_ip_check(ip_data, "test", False, 1.0)

        # 檢查是否保持在限制內
        stats = manager.get_history_stats()
        self.assertLessEqual(stats["total_history_records"], 5)

    def test_thread_safety_simulation(self):
        """測試線程安全的模擬（基本測試）"""
        manager = IPHistoryManager(self.history_file, self.config)

        # 模擬並發操作
        import threading

        def record_ip():
            ip_data = {"public_ip": "203.0.113.1", "local_ip": "192.168.1.100"}
            manager.record_ip_check(ip_data, "test", False, 1.0)

        threads = []
        for i in range(5):
            thread = threading.Thread(target=record_ip)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # 檢查所有記錄都被正確處理
        stats = manager.get_history_stats()
        self.assertEqual(stats["metadata"]["total_checks"], 5)


class TestIPHistoryManagerIntegration(unittest.TestCase):
    """IP歷史管理系統整合測試"""

    def setUp(self):
        """測試前準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.history_file = os.path.join(self.temp_dir, "integration_test.json")

    def tearDown(self):
        """測試後清理"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_realistic_usage_scenario(self):
        """測試真實使用場景"""
        manager = IPHistoryManager(self.history_file)

        # 模擬一天的使用情況
        scenarios = [
            # 早上9點排程執行 - 首次執行
            ("203.0.113.1", "scheduled", True),
            # 上午11點手動執行 - IP無變化
            ("203.0.113.1", "manual", True),
            # 下午2點排程執行 - IP無變化
            ("203.0.113.1", "scheduled", False),  # 應該跳過發送
            # 晚上8點IP變化
            ("203.0.113.2", "scheduled", True),
            # 晚上8點30分手動檢查
            ("203.0.113.2", "manual", True),
            # 測試模式
            ("203.0.113.2", "test", False),
        ]

        for ip, mode, expected_notify in scenarios:
            ip_data = {"public_ip": ip, "local_ip": "192.168.1.100"}

            # 檢查是否應該通知
            has_changed = manager.has_ip_changed(ip)
            should_notify = (mode == "manual") or (mode == "scheduled" and has_changed)

            self.assertEqual(
                should_notify, expected_notify, f"模式 {mode}, IP {ip} 的通知邏輯不正確"
            )

            # 記錄檢測結果
            manager.record_ip_check(ip_data, mode, should_notify, 1.0)

        # 檢查最終統計
        stats = manager.get_history_stats()
        self.assertEqual(stats["metadata"]["total_checks"], 6)
        self.assertEqual(stats["statistics"]["total_notifications_sent"], 4)
        self.assertEqual(stats["statistics"]["total_ip_changes"], 2)  # 首次 + 變化

    def test_performance_with_large_history(self):
        """測試大量歷史記錄的性能"""
        manager = IPHistoryManager(self.history_file)

        import time

        # 記錄大量歷史資料
        start_time = time.time()

        for i in range(100):
            ip_data = {"public_ip": f"203.0.113.{i % 10}", "local_ip": "192.168.1.100"}
            manager.record_ip_check(ip_data, "test", False, 1.0)

        end_time = time.time()
        duration = end_time - start_time

        # 性能檢查：100次操作應該在合理時間內完成
        self.assertLess(duration, 10.0, "大量記錄操作耗時過長")

        # 檢查資料完整性
        stats = manager.get_history_stats()
        self.assertEqual(stats["metadata"]["total_checks"], 100)


if __name__ == "__main__":
    # 設定測試日誌
    import logging

    logging.basicConfig(
        level=logging.WARNING,  # 減少測試期間的日誌輸出
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    print("🧪 開始執行 IP 歷史管理系統單元測試...")
    print("=" * 60)

    # 執行測試
    unittest.main(verbosity=2)
