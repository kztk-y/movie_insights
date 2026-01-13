#!/usr/bin/env python3
"""
Movie Insights - Command Line Interface
コマンドラインから動画シーン分析を実行
"""

import os
from pathlib import Path

import click

from scene_detector import MovieInsights
from exporters import export_to_excel, export_to_pptx, export_images_zip


@click.command()
@click.argument("video_path", type=click.Path(exists=True))
@click.option(
    "-o", "--output",
    type=click.Path(),
    default="./output",
    help="出力ディレクトリ（デフォルト: ./output）"
)
@click.option(
    "-t", "--threshold",
    type=float,
    default=27.0,
    help="検出感度の閾値（10-50、低いほど多く検出、デフォルト: 27.0）"
)
@click.option(
    "-m", "--min-scene-len",
    type=int,
    default=15,
    help="最小シーン長（フレーム数、デフォルト: 15）"
)
@click.option(
    "--no-excel",
    is_flag=True,
    help="Excel出力をスキップ"
)
@click.option(
    "--no-pptx",
    is_flag=True,
    help="PowerPoint出力をスキップ"
)
@click.option(
    "--no-zip",
    is_flag=True,
    help="ZIP出力をスキップ"
)
def main(
    video_path: str,
    output: str,
    threshold: float,
    min_scene_len: int,
    no_excel: bool,
    no_pptx: bool,
    no_zip: bool
):
    """
    動画ファイルをシーン分析して各種形式で出力する

    VIDEO_PATH: 分析する動画ファイルのパス
    """
    video_path = Path(video_path).resolve()
    output_dir = Path(output).resolve()

    click.echo(f"🎬 Movie Insights")
    click.echo(f"=" * 50)
    click.echo(f"入力: {video_path.name}")
    click.echo(f"出力: {output_dir}")
    click.echo(f"閾値: {threshold}")
    click.echo(f"最小シーン長: {min_scene_len} フレーム")
    click.echo()

    # 出力ディレクトリを作成
    output_dir.mkdir(parents=True, exist_ok=True)
    frames_dir = output_dir / "frames"
    frames_dir.mkdir(exist_ok=True)

    # シーン検出
    click.echo("🔍 シーンを検出中...")
    insights = MovieInsights(
        threshold=threshold,
        min_scene_len=min_scene_len
    )

    try:
        scenes = insights.detect_scenes(str(video_path))
    except Exception as e:
        click.echo(f"❌ エラー: {e}", err=True)
        raise click.Abort()

    if not scenes:
        click.echo("⚠️ シーンが検出されませんでした。閾値を下げてみてください。")
        return

    click.echo(f"✅ {len(scenes)} シーンを検出しました")

    # サムネイル抽出
    click.echo("🖼️ サムネイルを抽出中...")
    insights.extract_thumbnails(str(frames_dir))
    click.echo(f"✅ サムネイルを {frames_dir} に保存しました")

    video_info = insights.get_video_info()

    # 動画情報を表示
    click.echo()
    click.echo("📊 動画情報:")
    click.echo(f"  総再生時間: {video_info['duration_formatted']}")
    click.echo(f"  FPS: {video_info['fps']:.2f}")
    click.echo(f"  総フレーム数: {video_info['total_frames']:,}")
    click.echo(f"  検出シーン数: {len(scenes)}")
    click.echo()

    # 出力ファイルを生成
    click.echo("📁 出力ファイルを生成中...")

    if not no_excel:
        excel_path = output_dir / "scene_report.xlsx"
        export_to_excel(scenes, video_info, str(excel_path))
        click.echo(f"  ✅ Excel: {excel_path.name}")

    if not no_pptx:
        pptx_path = output_dir / "scene_slides.pptx"
        export_to_pptx(scenes, video_info, str(pptx_path))
        click.echo(f"  ✅ PowerPoint: {pptx_path.name}")

    if not no_zip:
        zip_path = output_dir / "scene_images.zip"
        export_images_zip(scenes, str(zip_path))
        click.echo(f"  ✅ ZIP: {zip_path.name}")

    click.echo()
    click.echo("🎉 完了！")
    click.echo(f"出力先: {output_dir}")


if __name__ == "__main__":
    main()
