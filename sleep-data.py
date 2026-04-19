かえ 日付時刻 輸入 日付時刻
た・た・た・た・た・た
かわいい道心_かわん
 # 💰大小 たんちょう
・・・・・。たんんんんん
輸入 OS

# 定数
local_tz = ・・・・・。ガーミンガーミン garmin_password = os。サロンガンガンガン(「GARMIN_PASSWORD」ちょう）「ニューヨーク/New_York」)

# 💰大大小
・・・・・()
設定 = サロン_個()

def get_sleep_data(カロン):
 今日 = 日付時刻。今日().日付()
 我々 カツカ。get_sleep_data(今日。むかむかむ())

def ・・・・・_月間(秒):
 分 = (秒 たたは 0) // 60
 我々 f"{分 // 60}h {分 % 60}m"

def ・・・・・_時間(サササ):
    我々 (
 日時。utcfromtimestamp(サササ / 1000).ぶるぶるぶる(「%Y-%m-%dT%H:%M:%S。000Z」)
 たしかたししししし
    )

def ・・・・・エ_時間_読ゆく(サササ):
    我々 (
 日時。そりゃくしょしゃくしょしゃ(サササ / 1000, 、 、 local_tz).ぶるぶるぶる(「%H:%M」)
 サササ むしつく 「不明」
    )

def format_date_for_name(よリープ_日付):
 我々 日時。ぶるぶるぶる(sleep_date、 「%Y-%m-%d」).ぶるぶるぶる(「%d.%m。%Y") むしリープ_日付 むし以外 「不明」

def sleep_data_exists(サデータベース、database_id、sleep_date):
 ササ = むォ〜〜。・・・・・。ねエリ(
 database_id=database_id、
 ・キャーキャー={「ひょろうん」: 「ひょろうん」, 「ひょろうん」: {「寝」: sleep_date}}
    )
 結果 = クエリ。得る(「結月」、 [])
 戻々 結果[0] たし たし # そりそり

def create_sleep_data(サワサワサワ、サワサワサワ_id、サワサワサワ_サワサワサワ、サワサワ_サワサワ_サワサワ=サワサワ):
 daily_sleep = sleep_data。得る(‘dailysleepdto’、 {})
 たしだ daily_sleep:
 我々
    
 sleep_date = daily_sleep。得る(「日付不明」, 「日付不明」)
 total_sleep = 合計(
        (daily_sleep。得る(k、0) まやは 0) たせにく k ち [「remsleepSeconds」、‘lightSleepSeconds’、‘remsleepSeconds’]
    )
    
    
 _エサ_エサ_エサ == 0:
        印刷(f"睡看過ちょうん {よリープ_日付} 総睡看著間は0やんちょうが）
 我々

 ・・・・・ = {
 「日付」: {「むしむ」: [{「ゆううううう」: {「ココちゃん」: format_date_for_name（デュー_date_for_name）デュー_date_for_name}}]},
 「むつむつ」: {「む_む」: [{「ゆううううう」: {「ココちゃん」: f"{・・・・・エ_時間_読ゆく(daily_sleep。得る(「ガンガンガンガンGMT」))} → {・・・・・_時間_読ゆく(daily_sleep。get('sleepEndTimestampGMT'))}"}}]},
 「たんんんん」: {「日付」: {「むむむ」: ・・・・・_日他}},
 「完全日日付/時分」: {「日付」: {「むむむ」: ・ォーマト_時間（daily_sleep。得る(「GMT」)), 「終珊」: 日・日・日_日間（daily_sleep。看看(‘sleepEndTimestampGMT’))}},
 「たんちょうちゃん、たんちょうちゃん、たんちょうちゃん、たんちょうちゃん {「番号」: トータルスリープ（total_sleep / 3600, 1)},
 「軽い睡看（h）」: {「番号」: ・・・・・（daily_sleep。得(‘lightSleepSeconds’, 0) / 3600, 1)},
 「深い看（h）」: {「番号」: ・・・・・（daily_sleep。得う「�デープ」ープ秒, 0) / 3600, 1)},
 「ハァァァ（h）」: {「番号」: ・・・・・（daily_sleep。得る(‘remSleepSeconds’, 0) / 3600, 1)},
 「起床時道（h）」: {「番号」: ・・・・・（daily_sleep。得る (「覚醒時の睡看看」, 0) / 3600, 1)},
 「よえ〜〜〜」: {「む_む」: [{「ゆううううう」: {「ココちゃん」: トータル_寝（total_sleep）}}]},
 「軽い睡看」: {「む_む」: [{「ゆううううう」: {「ココちゃん」: ・・・・・_日間（daily_sleep。得(‘lightSleepSeconds’, 0))}}]},
 「深い看」: {「む_む」: [{「ゆううううう」: {「ココちゃん」: ・・・・・_日間（daily_sleep。得る(「デャープスリープ秒」, 0))}}]},
 「たんちょうちょう」: {「む_む」: [{「ゆううううう」: {「ココちゃん」: ・・・・・_日間（daily_sleep。得る(‘remSleepSeconds’, 0))}}]},
 「目覚いんんんんん」: {「む_む」: [{「ゆううううう」: {「ココちゃん」: ・・・・・_日間（daily_sleep。得(「覚醒時の的的的的的数」, 0))}}]},
 「安静時の心情」: {「番号」: sleep_data。得 (「えい〜えい〜」, 0)}
    }
    
 むつむつむつ。・ペジ。作我に（親={「むぅイ_id」: ・キャーキャー_id}, 、 、 、 、 、 ペンちゃん=ペンちゃん={「粉文子」: 「😴」})
 印刷（f"早読みのちょうちゃん: {早読みのちょうちゃん_早読みのちょうちゃん}")

def サツ():
 ・_・・・・・()

 # 💰大小 たんちょう
 garmin_email = os。ガーミン(「GARMIN_EMAIL」)
 garmin_password = os。ガーミン(「GARMIN_PASSWORD」ちょう）
 notion_token = os。ノーショントークン(「NOTION_TOKEN」)
 database_id = os。ノーション(「NOTION_SLEEP_DB_ID」)

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
