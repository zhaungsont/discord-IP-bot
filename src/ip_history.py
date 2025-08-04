#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IP歷史記錄管理模組

提供IP地址變化檢測、歷史記錄存儲和統計分析功能。
設計為跨平台相容，支援自動備份和清理機制。

作者: Discord IP Bot Team
版本: 1.0.0
建立時間: 2025-01-04
"""

import json
import os
import shutil
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import logging


class IPHistoryError(Exception):
    """IP歷史記錄相關錯誤"""

    pass


class IPHistoryFileError(IPHistoryError):
    """IP歷史記錄檔案相關錯誤"""

    pass


class IPHistoryValidationError(IPHistoryError):
    """IP歷史記錄資料驗證錯誤"""

    pass


class IPHistoryManager:
    """
    IP歷史記錄管理器

    負責管理IP地址的歷史記錄，包括：
    - 持久化存儲
    - IP變化檢測
    - 歷史統計分析
    - 自動清理與備份
    - 錯誤處理與恢復
    """

    def __init__(
        self,
        history_file: str = "config/ip_history.json",
        config: Optional[Dict] = None,
    ):
        """
        初始化IP歷史管理器

        Args:
            history_file: 歷史記錄檔案路徑
            config: 配置選項字典

        Raises:
            IPHistoryFileError: 檔案路徑無效或權限問題
        """
        self.history_file = Path(history_file)
        self.logger = logging.getLogger(__name__)

        # 預設配置
        self.config = {
            "keep_days": 30,
            "max_records": 1000,
            "auto_cleanup": True,
            "backup_on_corruption": True,
            "compression": False,
            "encoding": "utf-8",
        }

        # 更新配置
        if config:
            self.config.update(config)

        # 確保目錄存在
        self._ensure_directory()

        # 載入或初始化歷史記錄
        self._history_data = self._load_or_initialize_history()

        self.logger.info(f"IP歷史管理器初始化完成，檔案路徑: {self.history_file}")

    def _ensure_directory(self) -> None:
        """確保歷史記錄檔案的目錄存在"""
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise IPHistoryFileError(f"無法創建目錄 {self.history_file.parent}: {e}")

    def _get_current_timestamp(self) -> str:
        """獲取當前時間戳（ISO格式，包含時區）"""
        return datetime.now(timezone.utc).isoformat()

    def _load_or_initialize_history(self) -> Dict:
        """載入現有歷史記錄或初始化新的記錄"""
        if self.history_file.exists():
            try:
                return self.load_history()
            except Exception as e:
                self.logger.error(f"載入歷史記錄失敗: {e}")
                if self.config["backup_on_corruption"]:
                    self._backup_corrupted_file()
                return self._create_initial_history()
        else:
            return self._create_initial_history()

    def _create_initial_history(self) -> Dict:
        """創建初始歷史記錄結構"""
        initial_data = {
            "metadata": {
                "created_at": self._get_current_timestamp(),
                "last_updated": self._get_current_timestamp(),
                "version": "1.0",
                "total_checks": 0,
            },
            "current": {
                "public_ip": None,
                "local_ip": None,
                "last_updated": None,
                "last_notification_sent": None,
            },
            "statistics": {
                "total_ip_changes": 0,
                "total_notifications_sent": 0,
                "last_change_date": None,
                "check_frequency": {"scheduled": 0, "manual": 0, "test": 0},
            },
            "history": [],
        }

        # 保存初始結構到檔案
        self.save_history(initial_data)
        self.logger.info("創建新的IP歷史記錄檔案")

        return initial_data

    def _backup_corrupted_file(self) -> None:
        """備份損壞的歷史檔案"""
        try:
            backup_file = self.history_file.with_suffix(
                f".corrupted.{int(time.time())}.bak"
            )
            shutil.copy2(self.history_file, backup_file)
            self.logger.warning(f"已備份損壞檔案到: {backup_file}")
        except Exception as e:
            self.logger.error(f"備份損壞檔案失敗: {e}")

    def load_history(self) -> Dict:
        """
        載入IP歷史記錄

        Returns:
            Dict: 歷史記錄資料

        Raises:
            IPHistoryFileError: 檔案讀取失敗
            IPHistoryValidationError: 資料格式無效
        """
        try:
            with open(self.history_file, "r", encoding=self.config["encoding"]) as f:
                data = json.load(f)

            # 驗證資料結構
            self._validate_history_data(data)

            self.logger.debug(
                f"成功載入歷史記錄，共 {len(data.get('history', []))} 筆記錄"
            )
            return data

        except json.JSONDecodeError as e:
            raise IPHistoryValidationError(f"JSON格式錯誤: {e}")
        except FileNotFoundError:
            raise IPHistoryFileError(f"歷史記錄檔案不存在: {self.history_file}")
        except PermissionError:
            raise IPHistoryFileError(f"歷史記錄檔案讀取權限不足: {self.history_file}")
        except Exception as e:
            raise IPHistoryFileError(f"載入歷史記錄失敗: {e}")

    def _validate_history_data(self, data: Dict) -> None:
        """驗證歷史記錄資料結構"""
        required_keys = ["metadata", "current", "statistics", "history"]
        for key in required_keys:
            if key not in data:
                raise IPHistoryValidationError(f"缺少必要欄位: {key}")

        # 驗證元資料
        metadata = data["metadata"]
        if not isinstance(metadata.get("total_checks"), int):
            raise IPHistoryValidationError("total_checks 必須是整數")

        # 驗證歷史記錄格式
        if not isinstance(data["history"], list):
            raise IPHistoryValidationError("history 必須是陣列")

    def save_history(self, history_data: Dict) -> bool:
        """
        保存IP歷史記錄到檔案

        Args:
            history_data: 要保存的歷史記錄資料

        Returns:
            bool: 保存是否成功

        Raises:
            IPHistoryFileError: 檔案寫入失敗
        """
        try:
            # 更新最後修改時間
            history_data["metadata"]["last_updated"] = self._get_current_timestamp()

            # 創建臨時檔案以確保原子性操作
            temp_file = self.history_file.with_suffix(".tmp")

            with open(temp_file, "w", encoding=self.config["encoding"]) as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)

            # 原子性替換
            temp_file.replace(self.history_file)

            self.logger.debug(f"成功保存歷史記錄到 {self.history_file}")
            return True

        except PermissionError:
            raise IPHistoryFileError(f"歷史記錄檔案寫入權限不足: {self.history_file}")
        except OSError as e:
            raise IPHistoryFileError(f"保存歷史記錄失敗: {e}")
        except Exception as e:
            raise IPHistoryFileError(f"未知錯誤，保存歷史記錄失敗: {e}")

    def get_last_public_ip(self) -> Optional[str]:
        """
        獲取上次記錄的公共IP地址

        Returns:
            Optional[str]: 上次記錄的公共IP，如果沒有記錄則返回None
        """
        current_ip = self._history_data["current"]["public_ip"]
        if current_ip and current_ip != "無法獲取":
            return current_ip
        return None

    def has_ip_changed(self, current_public_ip: str) -> bool:
        """
        檢查公共IP是否有變化

        Args:
            current_public_ip: 當前檢測到的公共IP

        Returns:
            bool: IP是否有變化
        """
        if not current_public_ip or current_public_ip == "無法獲取":
            return False

        last_ip = self.get_last_public_ip()

        # 如果沒有歷史記錄，視為有變化
        if last_ip is None:
            self.logger.info("首次記錄IP地址，視為變化")
            return True

        # 比較IP地址
        has_changed = current_public_ip != last_ip

        if has_changed:
            self.logger.info(f"IP地址變化: {last_ip} → {current_public_ip}")
        else:
            self.logger.debug(f"IP地址無變化: {current_public_ip}")

        return has_changed

    def record_ip_check(
        self,
        ip_data: Dict,
        mode: str,
        notification_sent: bool,
        execution_duration: float = 0.0,
    ) -> bool:
        """
        記錄一次IP檢測事件

        Args:
            ip_data: IP檢測結果字典，包含 local_ip 和 public_ip
            mode: 執行模式 ("scheduled", "manual", "test")
            notification_sent: 是否發送了通知
            execution_duration: 執行時間（秒）

        Returns:
            bool: 記錄是否成功
        """
        try:
            current_time = self._get_current_timestamp()
            public_ip = ip_data.get("public_ip")
            local_ip = ip_data.get("local_ip")

            # 檢查IP是否有變化
            ip_changed = (
                self.has_ip_changed(public_ip)
                if public_ip and public_ip != "無法獲取"
                else False
            )

            # 創建歷史記錄項目
            history_item = {
                "timestamp": current_time,
                "public_ip": public_ip,
                "local_ip": local_ip,
                "mode": mode,
                "ip_changed": ip_changed,
                "notification_sent": notification_sent,
                "execution_duration": round(execution_duration, 2),
            }

            # 如果IP有變化，記錄前一個IP
            if ip_changed:
                previous_ip = self.get_last_public_ip()
                if previous_ip:
                    history_item["previous_public_ip"] = previous_ip

            # 更新歷史記錄
            self._history_data["history"].append(history_item)

            # 更新當前IP資訊
            if public_ip and public_ip != "無法獲取":
                self._history_data["current"]["public_ip"] = public_ip
                self._history_data["current"]["last_updated"] = current_time

            if local_ip and local_ip != "無法獲取":
                self._history_data["current"]["local_ip"] = local_ip

            # 更新通知發送時間
            if notification_sent:
                self._history_data["current"]["last_notification_sent"] = current_time

            # 更新統計資訊
            self._update_statistics(mode, ip_changed, notification_sent, current_time)

            # 自動清理舊記錄
            if self.config["auto_cleanup"]:
                self._cleanup_old_records()

            # 保存到檔案
            self.save_history(self._history_data)

            self.logger.info(
                f"記錄IP檢測事件: mode={mode}, IP變化={ip_changed}, 通知發送={notification_sent}"
            )
            return True

        except Exception as e:
            self.logger.error(f"記錄IP檢測事件失敗: {e}")
            return False

    def _update_statistics(
        self, mode: str, ip_changed: bool, notification_sent: bool, timestamp: str
    ) -> None:
        """更新統計資訊"""
        stats = self._history_data["statistics"]
        metadata = self._history_data["metadata"]

        # 更新總檢測次數
        metadata["total_checks"] += 1

        # 更新模式統計
        if mode in stats["check_frequency"]:
            stats["check_frequency"][mode] += 1

        # 更新IP變化統計
        if ip_changed:
            stats["total_ip_changes"] += 1
            stats["last_change_date"] = timestamp

        # 更新通知統計
        if notification_sent:
            stats["total_notifications_sent"] += 1

    def get_history_stats(self) -> Dict:
        """
        獲取歷史統計資訊

        Returns:
            Dict: 包含各種統計資訊的字典
        """
        history_data = self._history_data
        metadata = history_data["metadata"]
        stats = history_data["statistics"]
        current = history_data["current"]

        # 計算額外統計資訊
        history_records = history_data["history"]

        # 最近活動
        recent_activity = []
        if history_records:
            recent_activity = sorted(
                history_records, key=lambda x: x["timestamp"], reverse=True
            )[:10]

        # 統計各種執行模式的比例
        total_checks = metadata["total_checks"]
        frequency_percentage = {}
        if total_checks > 0:
            for mode, count in stats["check_frequency"].items():
                frequency_percentage[mode] = round((count / total_checks) * 100, 1)

        return {
            "metadata": metadata,
            "current_status": current,
            "statistics": stats,
            "frequency_percentage": frequency_percentage,
            "recent_activity": recent_activity,
            "history_file_size": self._get_file_size(),
            "total_history_records": len(history_records),
        }

    def _get_file_size(self) -> str:
        """獲取歷史檔案大小"""
        try:
            if self.history_file.exists():
                size_bytes = self.history_file.stat().st_size
                if size_bytes < 1024:
                    return f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    return f"{size_bytes / 1024:.1f} KB"
                else:
                    return f"{size_bytes / (1024 * 1024):.1f} MB"
            return "0 B"
        except Exception:
            return "未知"

    def cleanup_old_records(self, keep_days: Optional[int] = None) -> int:
        """
        清理舊記錄

        Args:
            keep_days: 保留天數，如果不提供則使用配置中的值

        Returns:
            int: 清理的記錄數量
        """
        if keep_days is None:
            keep_days = self.config["keep_days"]

        return self._cleanup_old_records(keep_days)

    def _cleanup_old_records(self, keep_days: Optional[int] = None) -> int:
        """內部清理舊記錄方法"""
        if keep_days is None:
            keep_days = self.config["keep_days"]

        if keep_days <= 0:
            return 0

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=keep_days)
        cutoff_iso = cutoff_date.isoformat()

        history_records = self._history_data["history"]
        original_count = len(history_records)

        # 過濾舊記錄
        filtered_records = [
            record
            for record in history_records
            if record.get("timestamp", "") >= cutoff_iso
        ]

        # 如果超過最大記錄數，保留最新的記錄
        max_records = self.config["max_records"]
        if len(filtered_records) > max_records:
            filtered_records = sorted(
                filtered_records, key=lambda x: x.get("timestamp", ""), reverse=True
            )[:max_records]

        cleaned_count = original_count - len(filtered_records)

        if cleaned_count > 0:
            self._history_data["history"] = filtered_records
            self.logger.info(f"清理了 {cleaned_count} 筆舊記錄")

        return cleaned_count

    def get_ip_change_timeline(self, days: int = 7) -> List[Dict]:
        """
        獲取IP變化時間線

        Args:
            days: 查詢天數

        Returns:
            List[Dict]: IP變化事件列表
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        cutoff_iso = cutoff_date.isoformat()

        ip_changes = [
            record
            for record in self._history_data["history"]
            if (
                record.get("timestamp", "") >= cutoff_iso
                and record.get("ip_changed", False)
            )
        ]

        return sorted(ip_changes, key=lambda x: x.get("timestamp", ""), reverse=True)

    def export_history(self, output_file: Optional[str] = None) -> str:
        """
        匯出歷史記錄

        Args:
            output_file: 輸出檔案路徑，如果不提供則自動生成

        Returns:
            str: 匯出檔案路徑
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"ip_history_export_{timestamp}.json"

        output_path = Path(output_file)

        try:
            with open(output_path, "w", encoding=self.config["encoding"]) as f:
                json.dump(self._history_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"歷史記錄已匯出到: {output_path}")
            return str(output_path)

        except Exception as e:
            self.logger.error(f"匯出歷史記錄失敗: {e}")
            raise IPHistoryFileError(f"匯出失敗: {e}")


# 測試程式碼
if __name__ == "__main__":
    import tempfile

    # 設定測試日誌
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    print("🧪 測試 IPHistoryManager...")

    # 使用臨時檔案進行測試
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "test_ip_history.json")
        manager = IPHistoryManager(test_file)

        print("✅ IPHistoryManager 初始化成功")

        # 測試記錄IP檢測
        test_ip_data = {"local_ip": "192.168.1.100", "public_ip": "203.0.113.1"}

        success = manager.record_ip_check(test_ip_data, "test", True, 2.5)
        print(f"✅ 記錄IP檢測: {success}")

        # 測試IP變化檢測
        has_changed = manager.has_ip_changed("203.0.113.2")
        print(f"✅ IP變化檢測: {has_changed}")

        # 測試統計資訊
        stats = manager.get_history_stats()
        print(f"✅ 獲取統計資訊: 總檢測次數 = {stats['metadata']['total_checks']}")

        # 測試匯出
        export_file = manager.export_history()
        print(f"✅ 匯出歷史記錄: {export_file}")

        print("🎉 所有測試完成！")
