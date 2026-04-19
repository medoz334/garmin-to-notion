から 日付時刻 輸入 日付時刻
から ガーミンコネクト 輸入 ガーミン
から notion_クライアント 輸入 クライアント
から ドテンヴ 輸入 load_dotenv、dotenv_values
輸入 ピッツ
輸入 OS

# 定数
local_tz = pytz。タイムゾーン(「アメリカ/New_York」)

# 環境変数をロードする
ロード_ドーテン()
設定 = ドテンブ_値()

def get_sleep_data(ガーミン):
 今日 = 日付時刻。今日().日付()
    戻る ガーミン。get_sleep_data(今日。アイソフォーマット())

def フォーマット_期間(秒):
 分 = (秒 または 0) // 60
    戻る f"{分 // 60}h {分 % 60}m"

def フォーマット_時間(タイムスタンプ):
    戻る (
 日時。utcfromtimestamp(タイムスタンプ / 1000).ストルタイム(「%Y-%m-%dT%H:%M:%S。000Z」)
        もし タイムスタンプ それ以外 なし
    )

def フォーマット_時間_読み取り可能(タイムスタンプ):
    戻る (
 日時。タイムスタンプから(タイムスタンプ / 1000, 、 local_tz).ストルタイム(「%H:%M」)
        もし タイムスタンプ それ以外 「不明」
    )

def format_date_for_name(スリープ_日付):
    戻る 日時。ストルタイム(sleep_date、 「%Y-%m-%d」).ストルタイム(「%d.%m。%Y") もし スリープ_日付 それ以外 「不明」

def sleep_data_exists(クライアント、database_id、sleep_date):
 クエリ = クライアント。データベース.クエリ(
 database_id=database_id、
 フィルター={「プロパティ」: 「ロングデート」, 「日付」: {「等しい」: sleep_date}}
    )
 結果 = クエリ。得る(「結果」, [])
    戻る 結果[0] もし 結果 それ以外 なし  # IndexError を引き起こす代わりに None を返すようにします

def create_sleep_data(クライアント、database_id、sleep_data、skip_zero_sleep=真実):
 daily_sleep = sleep_data。得る(‘dailysleepdto’, {})
    もし ない daily_sleep:
        戻る
    
 sleep_date = daily_sleep。得る(「カレンダー日付」, 「日付不明」)
 total_sleep = 合計(
        (daily_sleep。得る(k、 0) または 0) のために k で [「ディープスリープ秒」, ‘lightSleepSeconds’, ‘remSleepSeconds’]
    )
    
    
    もし スキップ_ゼロ_スリープ そして total_sleep == 0:
        印刷(f"睡眠データをスキップします {スリープ_日付} 総睡眠時間は0インチなので)
        戻る

 プロパティ = {
        「日付」: {「タイトル」: [{「テキスト」: {「コンテンツ」: format_date_for_name(スリープ_日付)}}]},
        「タイムズ」: {「リッチ_テキスト」: [{「テキスト」: {「コンテンツ」: f"{フォーマット_時間_読み取り可能(daily_sleep。得る(「スリープスタートタイムスタンプGMT」))} → {フォーマット_時間_読み取り可能(daily_sleep。get('sleepEndTimestampGMT'))}"}}]},
        「ロングデート」: {「日付」: {「スタート」: sleep_date}},
        「完全な日付/時刻」: {「日付」: {「スタート」: フォーマット_時間(daily_sleep。得る(「スリープスタートタイムスタンプGMT」)), 「終わり」: フォーマット_時間(daily_sleep。得る(‘sleepEndTimestampGMT’))}},
        「トータルスリープ（h）」: {「番号」: ラウンド(total_sleep / 3600, 1)},
        「軽い睡眠（h）」: {「番号」: ラウンド(daily_sleep。得る(‘lightSleepSeconds’, 0) / 3600, 1)},
        「深い眠り（h）」: {「番号」: ラウンド(daily_sleep。得る(「ディープスリープ秒」, 0) / 3600, 1)},
        「レム睡眠（h）」: {「番号」: ラウンド(daily_sleep。得る(‘remSleepSeconds’, 0) / 3600, 1)},
        「起床時間（h）」: {「番号」: ラウンド(daily_sleep。得る(「覚醒時の睡眠秒数」, 0) / 3600, 1)},
        「トータルスリープ」: {「リッチ_テキスト」: [{「テキスト」: {「コンテンツ」: フォーマット_期間(total_sleep)}}]},
        「軽い睡眠」: {「リッチ_テキスト」: [{「テキスト」: {「コンテンツ」: フォーマット_期間(daily_sleep。得る(‘lightSleepSeconds’, 0))}}]},
        「深い眠り」: {「リッチ_テキスト」: [{「テキスト」: {「コンテンツ」: フォーマット_期間(daily_sleep。得る(「ディープスリープ秒」, 0))}}]},
        「レム睡眠」: {「リッチ_テキスト」: [{「テキスト」: {「コンテンツ」: フォーマット_期間(daily_sleep。得る(‘remSleepSeconds’, 0))}}]},
        「目覚めの時間」: {「リッチ_テキスト」: [{「テキスト」: {「コンテンツ」: フォーマット_期間(daily_sleep。得る(「覚醒時の睡眠秒数」, 0))}}]},
        「安静時の心拍数」: {「番号」: sleep_data。得る(「ハートレートを休ませる」, 0)}
    }
    
 クライアント。ページ.作成する(親={「データベース_id」: database_id}, 、 プロパティ=プロパティ、アイコン={「絵文字」: 「😴」})
    印刷(f"次のスリープエントリを作成しました: {スリープ_日付}")

def メイン():
    ロード_ドーテン()

    # 環境変数を使用して Garmin クライアントと Notion クライアントを初期化します
 garmin_email = os。ゲテンヴ(「GARMIN_EMAIL」)
 garmin_password = os。ゲテンヴ(「GARMIN_PASSWORD」です)
 notion_token = os。ゲテンヴ(「NOTION_TOKEN」)
 database_id = os。ゲテンヴ(「NOTION_SLEEP_DB_ID」)

    # --- トークン キャッシュを使用した Garmin ログイン (429 件のリクエストが多すぎないようにするため）---
 token_dir = os。パス.エクスパンダ(オス。ゲテンヴ(「ガーミン_トークン_ディレクトリ」, 「~/.garth」))
 ガーミン = ガーミン(garmin_email、garmin_パスワード)
    試す:
        # 保存したトークンが利用可能な場合は再利用します（SSO ヒットなし）
 ガーミン。ログイン(トークン_ディレクトリ)
        印刷(f"キャッシュされたトークンでログインしました {トークン_ディレクトリ}")
    以外 例外 として e:
        # Fall back to a fresh SSO login, then persist tokens for next runs
        print(f"Cached login failed ({e.__class__.__name__}): {e}. Doing fresh login...")
        garmin.login()
        try:
            garmin.garth.dump(token_dir)
            print(f"Saved new tokens to {token_dir}")
        except Exception as dump_err:
            print(f"Warning: could not save tokens: {dump_err}")
    # ----------------------------------------------------------------------

    client = Client(auth=notion_token)

    data = get_sleep_data(garmin)
    if data:
        sleep_date = data.get('dailySleepDTO', {}).get('calendarDate')
        if sleep_date and not sleep_data_exists(client, database_id, sleep_date):
            create_sleep_data(client, database_id, data, skip_zero_sleep=True)

if __name__ == '__main__':
    main()
