"""                                                                                                           
  Movie Insights - Streamlit Web UI                                                                             
  動画シーン分析アプリケーション                                                                                
  """                                                                                                           
                                                                                                                
  import os                                                                                                     
  import tempfile                                                                                               
  import shutil                                                                                                 
  from pathlib import Path                                                                                      
                                                                                                                
  import streamlit as st                                                                                        
                                                                                                                
  from scene_detector import MovieInsights                                                                      
  from exporters import export_to_excel, export_to_pptx, export_images_zip                                      
                                                                                                                
                                                                                                                
  # ページ設定                                                                                                  
  st.set_page_config(                                                                                           
      page_title="Movie Insights",                                                                              
      page_icon="🎬",                                                                                           
      layout="wide"                                                                                             
  )                                                                                                             
                                                                                                                
  # カスタムCSS                                                                                                 
  st.markdown("""                                                                                               
  <style>                                                                                                       
      .stProgress > div > div > div > div {                                                                     
          background-color: #4CAF50;                                                                            
      }                                                                                                         
      .scene-card {                                                                                             
          border: 1px solid #ddd;                                                                               
          border-radius: 8px;                                                                                   
          padding: 10px;                                                                                        
          margin: 5px;                                                                                          
      }                                                                                                         
  </style>                                                                                                      
  """, unsafe_allow_html=True)                                                                                  
                                                                                                                
                                                                                                                
  def main():                                                                                                   
      st.title("🎬 Movie Insights")                                                                             
      st.markdown("動画をAIでシーン分割して、提案スライド素材に変換")                                           
                                                                                                                
      # サイドバー：設定                                                                                        
      with st.sidebar:                                                                                          
          st.header("⚙️ 検出設定")                                                                              
                                                                                                                
          # 検出モード選択                                                                                      
          detection_mode = st.radio(                                                                            
              "検出モード",                                                                                     
              options=["high", "standard", "low"],                                                              
              format_func=lambda x: {                                                                           
                  "high": "🔍 高感度（カット漏れを減らす）",                                                    
                  "standard": "⚖️ 標準（バランス重視）",                                                        
                  "low": "🎯 低感度（誤検出を減らす）"                                                          
              }[x],                                                                                             
              index=0,                                                                                          
              help="高感度: カットを見逃しにくい / 低感度: 誤検出が少ない"                                      
          )                                                                                                     
                                                                                                                
          st.markdown("---")                                                                                    
          st.markdown("#### 詳細設定")                                                                          
                                                                                                                
          use_custom = st.checkbox("カスタム設定を使用", value=False)                                           
                                                                                                                
          if use_custom:                                                                                        
              threshold = st.slider(                                                                            
                  "検出感度（閾値）",                                                                           
                  min_value=10.0,                                                                               
                  max_value=50.0,                                                                               
                  value=20.0,                                                                                   
                  step=1.0,                                                                                     
                  help="低いほど多くのシーンを検出します"                                                       
              )                                                                                                 
                                                                                                                
              min_scene_len = st.slider(                                                                        
                  "最小シーン長（フレーム）",                                                                   
                  min_value=5,                                                                                  
                  max_value=60,                                                                                 
                  value=10,                                                                                     
                  help="これより短いシーンは無視されます"                                                       
              )                                                                                                 
                                                                                                                
              use_adaptive = st.checkbox(                                                                       
                  "AdaptiveDetector を使用",                                                                    
                  value=True,                                                                                   
                  help="照明変化に強い検出器を追加"                                                             
              )                                                                                                 
                                                                                                                
              use_threshold = st.checkbox(                                                                      
                  "フェード検出を使用",                                                                         
                  value=True,                                                                                   
                  help="黒フェードなどを検出"                                                                   
              )                                                                                                 
          else:                                                                                                 
              threshold = None                                                                                  
              min_scene_len = None                                                                              
              use_adaptive = None                                                                               
              use_threshold = None                                                                              
                                                                                                                
          st.markdown("---")                                                                                    
          st.markdown("### 📊 出力オプション")                                                                  
                                                                                                                
          export_excel = st.checkbox("Excel (xlsx)", value=True)                                                
          export_pptx = st.checkbox("PowerPoint (pptx)", value=True)                                            
          export_zip = st.checkbox("画像ZIP", value=True)                                                       
                                                                                                                
      # メインエリア：ファイルアップロード                                                                      
      uploaded_file = st.file_uploader(                                                                         
          "動画ファイルをアップロード",                                                                         
          type=["mp4", "avi", "mov", "mkv", "webm"],                                                            
          help="対応形式: MP4, AVI, MOV, MKV, WebM"                                                             
      )                                                                                                         
                                                                                                                
      if uploaded_file:                                                                                         
          temp_dir = tempfile.mkdtemp()                                                                         
          video_path = os.path.join(temp_dir, uploaded_file.name)                                               
          output_dir = os.path.join(temp_dir, "frames")                                                         
                                                                                                                
          try:                                                                                                  
              with open(video_path, "wb") as f:                                                                 
                  f.write(uploaded_file.read())                                                                 
                                                                                                                
              st.success(f"📹 {uploaded_file.name} をアップロードしました")                                     
                                                                                                                
              if st.button("🔍 シーン分析を開始", type="primary"):                                              
                  with st.spinner("シーンを検出中..."):                                                         
                      if use_custom:                                                                            
                          insights = MovieInsights(                                                             
                              threshold=threshold,                                                              
                              min_scene_len=min_scene_len,                                                      
                              mode=None,                                                                        
                              use_adaptive=use_adaptive,                                                        
                              use_threshold_detector=use_threshold,                                             
                          )                                                                                     
                      else:                                                                                     
                          insights = MovieInsights(mode=detection_mode)                                         
                      scenes = insights.detect_scenes(video_path)                                               
                                                                                                                
                  if not scenes:                                                                                
                      st.warning("シーンが検出されませんでした。閾値を下げてみてください。")                    
                      return                                                                                    
                                                                                                                
                  st.success(f"✅ {len(scenes)} シーンを検出しました")                                          
                                                                                                                
                  with st.spinner("サムネイルを抽出中..."):                                                     
                      insights.extract_thumbnails(output_dir)                                                   
                                                                                                                
                  video_info = insights.get_video_info()                                                        
                                                                                                                
                  st.markdown("---")                                                                            
                  st.subheader("📊 動画情報")                                                                   
                                                                                                                
                  col1, col2, col3, col4 = st.columns(4)                                                        
                  col1.metric("総再生時間", video_info["duration_formatted"])                                   
                  col2.metric("FPS", f"{video_info['fps']:.2f}")                                                
                  col3.metric("総フレーム数", f"{video_info['total_frames']:,}")                                
                  col4.metric("検出シーン数", len(scenes))                                                      
                                                                                                                
                  st.markdown("---")                                                                            
                  st.subheader("🎞️ シーン一覧")                                                                 
                                                                                                                
                  cols_per_row = 4                                                                              
                  for i in range(0, len(scenes), cols_per_row):                                                 
                      cols = st.columns(cols_per_row)                                                           
                      for j, col in enumerate(cols):                                                            
                          idx = i + j                                                                           
                          if idx < len(scenes):                                                                 
                              scene = scenes[idx]                                                               
                              with col:                                                                         
                                  if scene.thumbnail_path and os.path.exists(scene.thumbnail_path):             
                                      st.image(scene.thumbnail_path, use_container_width=True)                  
                                  st.caption(                                                                   
                                      f"**#{scene.scene_num}** | "                                              
                                      f"{scene.start_timecode} - {scene.end_timecode}\n"                        
                                      f"({scene.duration:.1f}秒)"                                               
                                  )                                                                             
                                                                                                                
                  st.markdown("---")                                                                            
                  st.subheader("📥 ダウンロード")                                                               
                                                                                                                
                  download_cols = st.columns(3)                                                                 
                                                                                                                
                  if export_excel:                                                                              
                      excel_path = os.path.join(temp_dir, "scene_report.xlsx")                                  
                      export_to_excel(scenes, video_info, excel_path)                                           
                      with open(excel_path, "rb") as f:                                                         
                          download_cols[0].download_button(                                                     
                              "📊 Excel ダウンロード",                                                          
                              f.read(),                                                                         
                              file_name="scene_report.xlsx",                                                    
                              mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"          
                          )                                                                                     
                                                                                                                
                  if export_pptx:                                                                               
                      pptx_path = os.path.join(temp_dir, "scene_slides.pptx")                                   
                      export_to_pptx(scenes, video_info, pptx_path)                                             
                      with open(pptx_path, "rb") as f:                                                          
                          download_cols[1].download_button(                                                     
                              "📽️ PowerPoint ダウンロード",                                                     
                              f.read(),                                                                         
                              file_name="scene_slides.pptx",                                                    
                              mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"  
                          )                                                                                     
                                                                                                                
                  if export_zip:                                                                                
                      zip_path = os.path.join(temp_dir, "scene_images.zip")                                     
                      export_images_zip(scenes, zip_path)                                                       
                      with open(zip_path, "rb") as f:                                                           
                          download_cols[2].download_button(                                                     
                              "📦 画像ZIP ダウンロード",                                                        
                              f.read(),                                                                         
                              file_name="scene_images.zip",                                                     
                              mime="application/zip"                                                            
                          )                                                                                     
                                                                                                                
          finally:                                                                                              
              pass                                                                                              
                                                                                                                
      else:                                                                                                     
          st.markdown("""                                                                                       
          ### 使い方                                                                                            
                                                                                                                
          1. **動画をアップロード** - MP4, AVI, MOV, MKV, WebMに対応                                            
          2. **設定を調整**（オプション）- サイドバーで検出感度を変更                                           
          3. **分析を開始** - ボタンをクリック                                                                  
          4. **結果をダウンロード** - Excel, PowerPoint, 画像ZIPから選択                                        
                                                                                                                
          ---                                                                                                   
                                                                                                                
          ### 出力形式                                                                                          
                                                                                                                
          | 形式 | 内容 |                                                                                       
          |------|------|                                                                                       
          | **Excel** | シーン一覧（サムネイル付き） |                                                          
          | **PowerPoint** | グリッドレイアウトスライド |                                                       
          | **ZIP** | サムネイル画像一式 |                                                                      
          """)                                                                                                  
                                                                                                                
                                                                                                                
  if __name__ == "__main__":                                                                                    
      main()                                                                                                    
                                                                                                                
  ペーストしたら「Commit changes」を押してください。                                                            
                                                                                                                
✻ Worked for 36s                                                                                                
                                                                                                                
❯ あ、でもスペース詰めたよ                                                                                      
                                                                                                                
⏺ それなら、scene_detector.py も同じ問題があるかもしれません。                                                  
                                                                                                                
  GitHubで scene_detector.py を開いて、1行目の """ の前にスペースがないか確認してください。                     
                                                                                                                
  もしスペースがあれば、同じように詰めてコミットしてください。                                                  
                                                                                                                
  その後、https://movieinsights.streamlit.app/ を再度確認してみてください。                                     
                                                                                                                
❯ [IMG: /tmp/zeami/but11.png]                                                                                   
                                                                                                                
                                                                                                                
⏺ Read 1 file (ctrl+o to expand)                                                                                
                                                                                                                
⏺ こちらも同じ問題があります。1行目が空行で、2行目以降に余分なスペースが入っています。                          
                                                                                                                
  ✏️ボタンを押して編集し、1行目の空行を削除して、各行の先頭のスペースを詰めてください。                         ─
                                                                                                                
  または、全部消して、以下をペーストしてください：                                                              
                                                                                                                
  """                                                                                                           
  Movie Insights - Scene Detection Core                                                                         
  シーン検出とフレーム抽出のコア機能                                                                            
  """                                                                                                           
                                                                                                                
  import os                                                                                                     
  from dataclasses import dataclass                                                                             
  from pathlib import Path                                                                                      
  from typing import Optional, List                                                                             
                                                                                                                
  import cv2                                                                                                    
  from scenedetect import open_video, SceneManager, ContentDetector, AdaptiveDetector, ThresholdDetector        
                                                                                                                
                                                                                                                
  @dataclass                                                                                                    
  class SceneInfo:                                                                                              
      """シーン情報を保持するデータクラス"""                                                                    
      scene_num: int                                                                                            
      start_time: float                                                                                         
      end_time: float                                                                                           
      start_frame: int                                                                                          
      end_frame: int                                                                                            
      thumbnail_path: Optional[str] = None                                                                      
                                                                                                                
      @property                                                                                                 
      def duration(self) -> float:                                                                              
          return self.end_time - self.start_time                                                                
                                                                                                                
      @property                                                                                                 
      def start_timecode(self) -> str:                                                                          
          return self._seconds_to_timecode(self.start_time)                                                     
                                                                                                                
      @property                                                                                                 
      def end_timecode(self) -> str:                                                                            
          return self._seconds_to_timecode(self.end_time)                                                       
                                                                                                                
      @staticmethod                                                                                             
      def _seconds_to_timecode(seconds: float) -> str:                                                          
          h = int(seconds // 3600)                                                                              
          m = int((seconds % 3600) // 60)                                                                       
          s = seconds % 60                                                                                      
          return f"{h:02d}:{m:02d}:{s:05.2f}"                                                                   
                                                                                                                
                                                                                                                
  class MovieInsights:                                                                                          
      """動画分析のメインクラス"""                                                                              
                                                                                                                
      DETECTION_MODES = {                                                                                       
          "high": {                                                                                             
              "content_threshold": 20.0,                                                                        
              "adaptive_threshold": 2.5,                                                                        
              "min_scene_len": 10,                                                                              
              "use_adaptive": True,                                                                             
              "use_threshold": True,                                                                            
          },                                                                                                    
          "standard": {                                                                                         
              "content_threshold": 27.0,                                                                        
              "adaptive_threshold": 3.0,                                                                        
              "min_scene_len": 15,                                                                              
              "use_adaptive": True,                                                                             
              "use_threshold": False,                                                                           
          },                                                                                                    
          "low": {                                                                                              
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
          if mode is not None and mode in self.DETECTION_MODES:                                                 
              preset = self.DETECTION_MODES[mode]                                                               
              self.threshold = preset["content_threshold"]                                                      
              self.adaptive_threshold = preset["adaptive_threshold"]                                            
              self.min_scene_len = preset["min_scene_len"]                                                      
              self.use_adaptive = preset["use_adaptive"]                                                        
              self.use_threshold_detector = preset["use_threshold"]                                             
          else:                                                                                                 
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
          self.video_path = video_path                                                                          
                                                                                                                
          video = open_video(video_path)                                                                        
          self.fps = video.frame_rate                                                                           
          self.total_frames = video.duration.get_frames()                                                       
          self.duration = self.total_frames / self.fps                                                          
                                                                                                                
          scene_manager = SceneManager()                                                                        
                                                                                                                
          scene_manager.add_detector(                                                                           
              ContentDetector(                                                                                  
                  threshold=self.threshold,                                                                     
                  min_scene_len=self.min_scene_len                                                              
              )                                                                                                 
          )                                                                                                     
                                                                                                                
          if self.use_adaptive:                                                                                 
              scene_manager.add_detector(                                                                       
                  AdaptiveDetector(                                                                             
                      adaptive_threshold=self.adaptive_threshold,                                               
                      min_scene_len=self.min_scene_len                                                          
                  )                                                                                             
              )                                                                                                 
                                                                                                                
          if self.use_threshold_detector:                                                                       
              scene_manager.add_detector(                                                                       
                  ThresholdDetector(                                                                            
                      threshold=12,                                                                             
                      min_scene_len=self.min_scene_len                                                          
                  )                                                                                             
              )                                                                                                 
                                                                                                                
          scene_manager.detect_scenes(video)                                                                    
          scene_list = scene_manager.get_scene_list()                                                           
                                                                                                                
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
                                                                                                                
      def extract_thumbnails(self, output_dir: str, position: float = 0.3) -> List[SceneInfo]:                  
          if not self.video_path or not self.scenes:                                                            
              raise ValueError("先にdetect_scenes()を実行してください")                                         
                                                                                                                
          output_path = Path(output_dir)                                                                        
          output_path.mkdir(parents=True, exist_ok=True)                                                        
                                                                                                                
          cap = cv2.VideoCapture(self.video_path)                                                               
                                                                                                                
          try:                                                                                                  
              for scene in self.scenes:                                                                         
                  frame_range = scene.end_frame - scene.start_frame                                             
                  target_frame = scene.start_frame + int(frame_range * position)                                
                                                                                                                
                  cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)                                                
                  ret, frame = cap.read()                                                                       
                                                                                                                
                  if ret:                                                                                       
                      filename = f"scene_{scene.scene_num:04d}.jpg"                                             
                      filepath = output_path / filename                                                         
                      cv2.imwrite(str(filepath), frame)                                                         
                      scene.thumbnail_path = str(filepath)                                                      
          finally:                                                                                              
              cap.release()                                                                                     
                                                                                                                
          return self.scenes                                                                                    
                                                                                                                
      def get_video_info(self) -> dict:                                                                         
          return {                                                                                              
              "path": self.video_path,                                                                          
              "fps": self.fps,                                                                                  
              "total_frames": self.total_frames,                                                                
              "duration": self.duration,                                                                        
              "duration_formatted": SceneInfo._seconds_to_timecode(self.duration),                              
              "scene_count": len(self.scenes)                                                                   
          }
