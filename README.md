# Movie Insights

動画をAIでシーン分割して、提案スライド素材に変換するツール

## 機能

- 動画ファイルをアップロード
- AIがシーン変わり目を自動検出（PySceneDetect使用）
- 各シーンの代表フレームを自動抽出
- Excel形式でシーン一覧を出力（サムネイル付き）
- PowerPoint形式でグリッドレイアウトスライドを出力
- 画像ファイル一式をZIPでダウンロード

## 技術スタック

- **シーン検出**: PySceneDetect
- **フレーム抽出**: OpenCV
- **Excel出力**: openpyxl
- **PowerPoint出力**: python-pptx
- **Web UI**: Streamlit

## ローカル実行

```bash
pip install -r requirements.txt
streamlit run app.py
```

## ライセンス

MIT License
