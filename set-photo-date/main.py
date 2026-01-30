#!/usr/bin/env python3
"""
ファイル名から日時を抽出し、写真のEXIF日時を設定するスクリプト

ファイル名フォーマット:
  250820092810281.jpeg → 2025/08/20 09:28:10.281
  250819111142709_20250820135851386.jpeg → 最初の13桁のみ使用
  20251104_100346.jpg → 2025/11/04 10:03:46.000

使用方法:
  python set_photo_date.py <ファイルまたはディレクトリ>
  python set_photo_date.py ./photos/
  python set_photo_date.py ./photo.jpeg

必要なツール:
  brew install exiftool
"""

import subprocess
import sys
import os
import re
from pathlib import Path


def check_exiftool():
    """exiftoolがインストールされているか確認"""
    try:
        subprocess.run(["exiftool", "-ver"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def parse_datetime_from_filename(filename: str) -> tuple[str, str] | None:
    """
    ファイル名から日時を抽出

    Args:
        filename: ファイル名（拡張子含む）

    Returns:
        (EXIF形式の日時文字列 "YYYY:MM:DD HH:MM:SS", ミリ秒) のタプル または None
    """
    # 拡張子を除いたベース名を取得
    base_name = Path(filename).stem

    # パターン1: 13桁形式 (YYMMDDHHMMSSm)
    match = re.match(r'^(\d{13})', base_name)
    if match:
        digits = match.group(1)

        # パース: YYMMDDHHMMSSMMM
        try:
            yy = int(digits[0:2])
            month = int(digits[2:4])
            day = int(digits[4:6])
            hour = int(digits[6:8])
            minute = int(digits[8:10])
            second = int(digits[10:12])

            # 年を4桁に変換（2000年代と仮定）
            year = 2000 + yy

            # 値の妥当性チェック
            if not (1 <= month <= 12):
                return None
            if not (1 <= day <= 31):
                return None
            if not (0 <= hour <= 23):
                return None
            if not (0 <= minute <= 59):
                return None
            if not (0 <= second <= 59):
                return None

            # EXIF形式: "YYYY:MM:DD HH:MM:SS"
            # SubSecTimeOriginal用のミリ秒も返す
            datetime_str = f"{year:04d}:{month:02d}:{day:02d} {hour:02d}:{minute:02d}:{second:02d}"
            subsec = digits[12:15]  # ミリ秒3桁

            return datetime_str, subsec

        except (ValueError, IndexError):
            pass

    # パターン2: YYYYMMDD_HHMMSS 形式
    match = re.match(r'^(\d{8})_(\d{6})', base_name)
    if match:
        date_part = match.group(1)  # YYYYMMDD
        time_part = match.group(2)  # HHMMSS

        try:
            year = int(date_part[0:4])
            month = int(date_part[4:6])
            day = int(date_part[6:8])
            hour = int(time_part[0:2])
            minute = int(time_part[2:4])
            second = int(time_part[4:6])

            # 値の妥当性チェック
            if not (1 <= month <= 12):
                return None
            if not (1 <= day <= 31):
                return None
            if not (0 <= hour <= 23):
                return None
            if not (0 <= minute <= 59):
                return None
            if not (0 <= second <= 59):
                return None

            # EXIF形式: "YYYY:MM:DD HH:MM:SS"
            datetime_str = f"{year:04d}:{month:02d}:{day:02d} {hour:02d}:{minute:02d}:{second:02d}"
            return datetime_str, "000"

        except (ValueError, IndexError):
            pass

    return None


def set_photo_date(filepath: Path, datetime_str: str, subsec: str) -> bool:
    """
    exiftoolを使って写真の日時を設定

    Args:
        filepath: 写真ファイルのパス
        datetime_str: "YYYY:MM:DD HH:MM:SS" 形式の日時
        subsec: ミリ秒（3桁）

    Returns:
        成功したかどうか
    """
    try:
        # exiftoolコマンドを構築
        # -overwrite_original: バックアップファイルを作らない
        cmd = [
            "exiftool",
            "-overwrite_original",
            f"-DateTimeOriginal={datetime_str}",
            f"-CreateDate={datetime_str}",
            f"-ModifyDate={datetime_str}",
            f"-SubSecTimeOriginal={subsec}",
            f"-SubSecCreateDate={subsec}",
            f"-SubSecModifyDate={subsec}",
            str(filepath)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            return True
        else:
            print(f"  エラー: {result.stderr.strip()}")
            return False

    except Exception as e:
        print(f"  例外: {e}")
        return False


def set_file_dates(filepath: Path, datetime_str: str) -> bool:
    """
    ファイルの作成日時・更新日時も設定（macOS）

    Args:
        filepath: ファイルのパス
        datetime_str: "YYYY:MM:DD HH:MM:SS" 形式の日時
    """
    try:
        # "YYYY:MM:DD HH:MM:SS" → "YYYYMMDDHHMMSS" に変換
        dt_clean = datetime_str.replace(":", "").replace(" ", "")
        # touch -t 形式: YYYYMMDDhhmm.ss
        touch_format = f"{dt_clean[:12]}.{dt_clean[12:14]}"

        # 更新日時を設定
        subprocess.run(["touch", "-t", touch_format, str(filepath)], check=True)

        # macOSの作成日時を設定（SetFileを使用）
        # SetFileは Developer Tools が必要な場合がある
        try:
            # SetFile形式: "MM/DD/YYYY HH:MM:SS"
            parts = datetime_str.split(" ")
            date_parts = parts[0].split(":")
            setfile_date = f"{date_parts[1]}/{date_parts[2]}/{date_parts[0]} {parts[1]}"
            subprocess.run(["SetFile", "-d", setfile_date, str(filepath)],
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # SetFileが使えない場合は無視
            pass

        return True
    except Exception as e:
        print(f"  ファイル日時設定エラー: {e}")
        return False


def process_file(filepath: Path) -> bool:
    """単一ファイルを処理"""
    filename = filepath.name

    # 対応する拡張子かチェック
    if filepath.suffix.lower() not in ['.jpg', '.jpeg', '.png', '.heic', '.tiff', '.tif']:
        return False

    result = parse_datetime_from_filename(filename)
    if result is None:
        print(f"スキップ: {filename} (日時パターンに一致しません)")
        return False

    datetime_str, subsec = result
    print(f"処理中: {filename}")
    print(f"  → {datetime_str}.{subsec}")

    # EXIF日時を設定
    if set_photo_date(filepath, datetime_str, subsec):
        # ファイルシステムの日時も設定
        set_file_dates(filepath, datetime_str)
        print(f"  ✓ 完了")
        return True
    else:
        print(f"  ✗ 失敗")
        return False


def main():
    # exiftoolの確認
    if not check_exiftool():
        print("エラー: exiftoolがインストールされていません")
        print("インストール方法: brew install exiftool")
        sys.exit(1)

    # 引数チェック
    if len(sys.argv) < 2:
        print("使用方法: python set_photo_date.py <ファイルまたはディレクトリ>")
        print("例:")
        print("  python set_photo_date.py ./photos/")
        print("  python set_photo_date.py ./250820092810281.jpeg")
        sys.exit(1)

    target = Path(sys.argv[1])

    if not target.exists():
        print(f"エラー: {target} が見つかりません")
        sys.exit(1)

    success_count = 0
    fail_count = 0
    skip_count = 0

    if target.is_file():
        # 単一ファイル
        if process_file(target):
            success_count += 1
        else:
            fail_count += 1
    elif target.is_dir():
        # ディレクトリ内の全ファイル
        files = list(target.glob("*"))
        print(f"{len(files)} 個のファイルを検出\n")

        for filepath in sorted(files):
            if filepath.is_file():
                result = parse_datetime_from_filename(filepath.name)
                if result is None:
                    skip_count += 1
                    continue

                if process_file(filepath):
                    success_count += 1
                else:
                    fail_count += 1

    print(f"\n===== 結果 =====")
    print(f"成功: {success_count}")
    print(f"失敗: {fail_count}")
    print(f"スキップ: {skip_count}")


if __name__ == "__main__":
    main()
