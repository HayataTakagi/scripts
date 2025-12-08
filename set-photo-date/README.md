# set-photo-date

ファイル名から日時を抽出し、写真のEXIF日時を設定するPythonスクリプト

## 概要

このスクリプトは、特定の形式のファイル名（13桁の数字で始まる）から日時情報を抽出し、画像ファイルのEXIF日時データを自動的に設定します。

## ファイル名フォーマット

```
250820092810281.jpeg → 2025/08/20 09:28:10.281
250819111142709_20250820135851386.jpeg → 最初の13桁のみ使用
```

ファイル名の最初の13桁が日時として解釈されます：
- YY: 年（下2桁、2000年代）
- MM: 月
- DD: 日
- HH: 時
- MM: 分
- SS: 秒
- MMM: ミリ秒（最初の1桁のみ使用）

## 前提条件

### exiftoolのインストール

```bash
brew install exiftool
```

### Python

Python 3.10以上が必要です（`str | None` 型アノテーション使用のため）

## 使用方法

### 単一ファイルを処理

```bash
python main.py ./250820092810281.jpeg
```

### ディレクトリ内の全ファイルを処理

```bash
python main.py ./photos/
```

## 動作

1. ファイル名から日時を抽出
2. 以下のEXIF情報を設定：
   - DateTimeOriginal
   - CreateDate
   - ModifyDate
   - SubSecTimeOriginal
   - SubSecCreateDate
   - SubSecModifyDate
3. ファイルシステムの更新日時も設定（macOS）
4. 可能な場合は作成日時も設定（macOS、SetFile使用）

## 対応ファイル形式

- `.jpg` / `.jpeg`
- `.png`
- `.heic`
- `.tiff` / `.tif`

## 注意事項

- exiftoolは元のファイルを上書きします（`-overwrite_original`オプション使用）
- ファイル名の日時パターンに一致しないファイルはスキップされます
- macOSの作成日時設定にはSetFileコマンドが必要ですが、利用できない場合でもスクリプトは正常に動作します

## 実行結果の例

```
処理中: 250820092810281.jpeg
  → 2025:08:20 09:28:10.281
  ✓ 完了

===== 結果 =====
成功: 1
失敗: 0
スキップ: 0
```
