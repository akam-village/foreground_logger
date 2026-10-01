# 最前面アプリの最小ロガー（Windows 11）

Python 3の標準ライブラリのみ。pipインストール不要。
`foreground_logger.py` 1ファイルで動作します。管理者権限は通常不要です。

## 起動・停止

`foreground_logger.py`、`start_logger.cmd`、`stop_logger.cmd` を同じフォルダに置きます。
`start_logger.cmd` のダブルクリックで起動、`stop_logger.cmd` で停止できます。
常駐するのはPythonのロガープロセスです。起動用cmdは別プロセスを起動して終了し、
停止用cmdは停止通知を送るPythonプロセスの終了を待って終了します。ロガーの停止完了までは待ちません。
Pythonが見つからない場合や停止コマンドがエラーになった場合は、cmdがキー入力待ちになります。
起動時はPATH上の `pyw.exe`、停止時は `py.exe` を優先します。
それぞれが見つからない場合のみ、PATH上の `pythonw.exe` / `python.exe` を使用します。
選択したPythonの実行に失敗しても、もう一方へ切り替えません。
初回は下記のコンソール起動でログ出力を確認してください。

```powershell
python "C:\Tools\foreground_logger.py"
```

Ctrl+Cで停止します。常駐時はPythonの `pythonw.exe` を使ってコンソールを表示せず起動します。
PowerShell例（Pythonのインストール先に合わせて変更）：

```powershell
& "C:\Path\To\Python\pythonw.exe" "C:\Tools\foreground_logger.py"
```

停止は同じWindowsログオンセッションから実行します。

```powershell
python "C:\Tools\foreground_logger.py" --stop
```

自動起動する場合はWin+R → `shell:startup` にショートカットを置き、リンク先に
`"C:\Path\To\Python\pythonw.exe" "C:\Tools\foreground_logger.py"` を指定します。
解除はショートカットを削除し、上記停止コマンドを実行します。
cmdを利用する場合は `start_logger.cmd` のショートカットを `shell:startup` に置いても構いません。
同じWindowsログオンセッション内では、名前付きイベントにより後から起動したロガーが自動的に終了します。
別セッションでの起動は防ぎません。同じログへ出力する場合、記録が重複・混在する可能性があります。
トレイアイコンやGUIはありません。

## 出力と仕様

Windowsが管理するデスクトップの `foreground.log` にUTF-8で追記します。
OneDriveへ移動したデスクトップもWindows APIで取得します。
日時（ローカル時刻・UTCオフセット付き）、イベント、exe名、ウィンドウタイトルをタブ区切りで記録します。

```text
2026-10-01T22:00:00+09:00	START		
2026-10-01T22:00:00+09:00	APP	Code.exe	foreground_logger.py - Visual Studio Code
2026-10-01T22:02:10+09:00	APP	EXCEL.EXE	作業記録.xlsx - Excel
2026-10-01T22:05:00+09:00	STOP		
```

- 起動直後に最前面ウィンドウとPIDを取得し、その後は処理時間に加えて1秒待機します。PIDが変わった場合だけexe名を照会します。
- APP行は初回と、exe名またはウィンドウタイトルが変わった場合だけ追記します。起動時にSTART行、正常停止時にSTOP行も追記します。
- タイトル内のタブと改行は、タブ区切り形式を維持するため空白へ置換します。
- 待機はOSの待機API。単一スレッドで動作し、プロセス優先度を「通常以下」に設定します（設定失敗の検出は行いません）。
- キー入力、画面画像、全プロセス一覧は取得しません。
- 周期はファイル先頭の `INTERVAL_MS = 1000` で変更できます。
- 実メモリはPythonランタイム分を含みます。CPU負荷・メモリ使用量の実測は行っていません。
- 1秒未満の切り替えは取りこぼし、記録時刻も切り替えから通常最大約1秒遅れます。負荷やスリープ復帰によってさらに遅れる場合があります。
- exe名を取得できない場合は `UNKNOWN`、最前面ウィンドウがない場合は `NO_FOREGROUND`。
  取得失敗は同じPIDのままでは再試行しません。
- アイドル、画面ロック、実作業時間を判定する機能はありません。スリープ中の時間も除外しません。
  一部のパッケージアプリはホストプロセス名になる場合があります。
- 異常終了やWindows終了ではSTOP行が残らない場合があります。ログは自動削除・ローテーションしません。
  ログを整理する場合は停止してから移動または削除してください。
- デスクトップが同期対象ならログも同期対象になります。

## 検証

モックWin32 APIによる検証用コード・結果は同梱していないため、このフォルダだけでは検証済みという記述を確認できません。
Windows実機での動作と負荷は未検証です。起動に失敗する場合は `pythonw.exe` ではなく
`python` で実行してエラーメッセージを確認してください。
