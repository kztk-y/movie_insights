"""
Movie Insights - Scene Detection Core
シーン検出とフレーム抽出のコア機能
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List

import cv2
from scenedetect import open_video, ContentDetector, AdaptiveDetector, ThresholdDetector
from scenedetect.scene_manager import SceneManager


@dataclass
class SceneInfo:
    """シーン情報を保持するデータクラス"""
    scene_num: int
    start_time: float  # 秒
    end_time: float    # 秒
    start_frame: int
    end_frame: int
    thumbnail_path: Optional[str] = None

    @property
    def duration(self) -> float:
        """シーンの長さ（秒）"""
        return self.end_time - self.start_time

    @property
    def start_timecode(self) -> str:
        """開始時間をHH:MM:SS形式で返す"""
        return self._seconds_to_timecode(self.start_time)

    @property
    def end_timecode(self) -> str:
        """終了時間をHH:MM:SS形式で返す"""
        return self._seconds_to_timecode(self.end_time)

    @staticmethod
    def _seconds_to_timecode(seconds: float) -> str:
        """秒をHH:MM:SS形式に変換"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:05.2f}"


class MovieInsights:
    """動画分析のメインクラス"""

    # 検出モードのプリセット
    DETECTION_MODES = {
        "high": {  # 高感度：カット漏れを減らす
            "content_threshold": 20.0,
            "adaptive_threshold": 2.5,
            "min_scene_len": 10,
            "use_adaptive": True,
            "use_threshold": True,
        },
        "standard": {  # 標準：バランス重視
            "content_threshold": 27.0,
            "adaptive_threshold": 3.0,
            "min_scene_len": 15,
            "use_adaptive": True,
            "use_threshold": False,
        },
        "low": {  # 低感度：誤検出を減らす
            "content_threshold": 35.0,
            "adaptive_threshold": 4.0,
            "min_scene_len": 25,
            "use_adaptive": False,
            "use_threshold": False,
        },
    }

    def __init__(
        self,
        threshold: float = 20.0,
        min_scene_len: int = 10,
        mode: Optional[str] = "high",
        adaptive_threshold: float = 2.5,
        use_adaptive: bool = True,
        use_threshold_detector: bool = True,
    ):
        """
        Args:
            threshold: ContentDetectorの閾値（低いほど多くのシーンを検出）
            min_scene_len: 最小シーン長（フレーム数）
            mode: 検出モード ("high", "standard", "low", None) - Noneで個別パラメータを使用
            adaptive_threshold: AdaptiveDetectorの閾値
            use_adaptive: AdaptiveDetectorを使用するか
            use_threshold_detector: ThresholdDetector（フェード検出）を使用するか
        """
        # モードが指定されていれば、プリセットを適用
        if mode is not None and mode in self.DETECTION_MODES:
            preset = self.DETECTION_MODES[mode]
            self.threshold = preset["content_threshold"]
            self.adaptive_threshold = preset["adaptive_threshold"]
            self.min_scene_len = preset["min_scene_len"]
            self.use_adaptive = preset["use_adaptive"]
            self.use_threshold_detector = preset["use_threshold"]
        else:
            # カスタム設定を使用
            self.threshold = threshold
            self.adaptive_threshold = adaptive_threshold
            self.min_scene_len = min_scene_len
            self.use_adaptive = use_adaptive
            self.use_threshold_detector = use_threshold_detector

        self.mode = mode
        self.scenes: List[SceneInfo] = []
        self.video_path: Optional[str] = None
        self.fps: float = 0.0
        self.total_frames: int = 0
        self.duration: float = 0.0

    def detect_scenes(self, video_path: str) -> List[SceneInfo]:
        """
        動画からシーンを検出する

        Args:
            video_path: 動画ファイルのパス

        Returns:
            検出されたシーン情報のリスト
        """
        self.video_path = video_path

        # 動画を開く
        video = open_video(video_path)
        self.fps = video.frame_rate
        self.total_frames = video.duration.get_frames()
        self.duration = self.total_frames / self.fps

        # シーンマネージャーを設定
        scene_manager = SceneManager()

        # ContentDetector: 基本のカット検出
        scene_manager.add_detector(
            ContentDetector(
                threshold=self.threshold,
                min_scene_len=self.min_scene_len
            )
        )

        # AdaptiveDetector: 照明変化に強い検出（オプション）
        if self.use_adaptive:
            scene_manager.add_detector(
                AdaptiveDetector(
                    adaptive_threshold=self.adaptive_threshold,
                    min_scene_len=self.min_scene_len
                )
            )

        # ThresholdDetector: フェード検出（オプション）
        if self.use_threshold_detector:
            scene_manager.add_detector(
                ThresholdDetector(
                    threshold=12,  # 黒フェード検出用
                    min_scene_len=self.min_scene_len
                )
            )

        # シーン検出を実行
        scene_manager.detect_scenes(video)
        scene_list = scene_manager.get_scene_list()

        # シーン情報を変換
        self.scenes = []
        for i, (start, end) in enumerate(scene_list, 1):
            scene = SceneInfo(
                scene_num=i,
                start_time=start.get_seconds(),
                end_time=end.get_seconds(),
                start_frame=start.get_frames(),
                end_frame=end.get_frames()
            )
            self.scenes.append(scene)

        return self.scenes

    def extract_thumbnails(
        self,
        output_dir: str,
        position: float = 0.3
    ) -> List[SceneInfo]:
        """
        各シーンから代表フレーム（サムネイル）を抽出する

        Args:
            output_dir: 出力ディレクトリ
            position: シーン内の抽出位置（0.0-1.0、デフォルトは30%地点）

        Returns:
            サムネイルパスが設定されたシーン情報のリスト
        """
        if not self.video_path or not self.scenes:
            raise ValueError("先にdetect_scenes()を実行してください")

        # 出力ディレクトリを作成
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 動画を開く
        cap = cv2.VideoCapture(self.video_path)

        try:
            for scene in self.scenes:
                # 抽出するフレーム位置を計算
                frame_range = scene.end_frame - scene.start_frame
                target_frame = scene.start_frame + int(frame_range * position)

                # フレームを取得
                cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                ret, frame = cap.read()

                if ret:
                    # サムネイルを保存
                    filename = f"scene_{scene.scene_num:04d}.jpg"
                    filepath = output_path / filename
                    cv2.imwrite(str(filepath), frame)
                    scene.thumbnail_path = str(filepath)
        finally:
            cap.release()

        return self.scenes

    def get_video_info(self) -> dict:
        """動画の基本情報を取得"""
        return {
            "path": self.video_path,
            "fps": self.fps,
            "total_frames": self.total_frames,
            "duration": self.duration,
            "duration_formatted": SceneInfo._seconds_to_timecode(self.duration),
            "scene_count": len(self.scenes)
        }
