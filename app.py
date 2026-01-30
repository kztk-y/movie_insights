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
              index=0,  # デフォルトを高感度に                                                                  
              help="高感度: カットを見逃しにくい / 低感度: 誤検出が少ない"                                      
          )                                                                                                     
                                                                                                                
          st.markdown("---")                                                                                    
          st.markdown("#### 詳細設定")                                                                          
                                                                                                                
          # 詳細設定（モードを上書き）                                                                          
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
          # 一時ディレクトリを作成                                                                              
          temp_dir = tempfile.mkdtemp()                                                                         
          video_path = os.path.join(temp_dir, uploaded_file.name)                                               
          output_dir = os.path.join(temp_dir, "frames")                                                         
                                                                                                                
          try:                                                                                                  
              # 動画を一時ファイルに保存                                                                        
              with open(video_path, "wb") as f:                                                                 
                  f.write(uploaded_file.read())                                                                 
                                                                                                                
              st.success(f"📹 {uploaded_file.name} をアップロードしました")                                     
                                                                                                                
              # 分析開始ボタン                                                                                  
              if st.button("🔍 シーン分析を開始", type="primary"):                                              
                  # 分析処理                                                                                    
                  with st.spinner("シーンを検出中..."):                                                         
                      if use_custom:                                                                            
                          insights = MovieInsights(                                                             
                              threshold=threshold,                                                              
                              min_scene_len=min_scene_len,                                                      
                              mode=None,  # カスタム設定                                                        
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
                                                                                                                
                  # サムネイル抽出                                                                              
                  with st.spinner("サムネイルを抽出中..."):                                                     
                      insights.extract_thumbnails(output_dir)                                                   
                                                                                                                
                  video_info = insights.get_video_info()                                                        
                                                                                                                
                  # 結果表示                                                                                    
                  st.markdown("---")                                                                            
                  st.subheader("📊 動画情報")                                                                   
                                                                                                                
                  col1, col2, col3, col4 = st.columns(4)                                                        
                  col1.metric("総再生時間", video_info["duration_formatted"])                                   
                  col2.metric("FPS", f"{video_info['fps']:.2f}")                                                
                  col3.metric("総フレーム数", f"{video_info['total_frames']:,}")                                
                  col4.metric("検出シーン数", len(scenes))                                                      
                                                                                                                
                  # シーン一覧                                                                                  
                  st.markdown("---")                                                                            
                  st.subheader("🎞️ シーン一覧")                                                                 
                                                                                                                
                  # グリッド表示                                                                                
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
                                                                                                                
                  # ダウンロードセクション                                                                      
                  st.markdown("---")                                                                            
                  st.subheader("📥 ダウンロード")                                                               
                                                                                                                
                  download_cols = st.columns(3)                                                                 
                                                                                                                
                  # Excel                                                                                       
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
                                                                                                                
                  # PowerPoint                                                                                  
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
                                                                                                                
                  # ZIP                                                                                         
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
              # セッションが終わったら一時ディレクトリを削除                                                    
              # Note: Streamlitはファイルダウンロード後も状態を保持するため                                     
              # ここでは削除しない（ユーザーが再ダウンロードできるように）                                      
              pass                                                                                              
                                                                                                                
      else:                                                                                                     
          # アップロード前の説明                                                                                
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
