# jvn_spider.py
# imports ##########
# クローリング用
import scrapy
from jvn_spider.items import JvnItem
from scrapy_playwright.page import PageCoroutine

# 文字列置換用
import re
# テスト用
from pprint import pprint

# メインのクローラ
class JvnSpider(scrapy.Spider):
    # 呼び出し用の名前
    name = "jvn_spider"
    
    # 許可されるドメイン
    allowed_domains = ["jvndb.jvn.jp", "cve.org"]

    # 開始地点のドメイン
    start_urls = [
        "https://jvndb.jvn.jp/ja/contents/2025/JVNDB-2025-016156.html",
        "https://jvndb.jvn.jp/ja/contents/2024/JVNDB-2024-007579.html"
    ]

    # メインの処理
    def parse(self, response):
        # クラスからアイテムを形成
        item = JvnItem()

        # 実行してみる
        try:
            # 1. JVNの脆弱性のタイトルを抽出
            # <font face="arial, geneva, helvetica"> よりフォントが強制されている部分を判別
            # 複数ある場合は大文字英+数+ハイフンのみが含まれているものを選択
            jvndb_id = response.css('font::text').getall()  # jvndb_id = ['JVNDB-2025-016156']

            # jsonに追加
            for loop in jvndb_id:
                if re.fullmatch(r'JVNDB-[0-9]*-[0-9]*', loop):
                    item['jvndb_id'] = loop
            
            # 2. JVNDB-ID を抽出
            # <h2> テキストをすべて取得、複数ある場合は日本語が含まれているかで判別
            title = response.css('h2::text').getall()   # title = ['Linux\xa0Foundation\xa0の\xa0Python\xa0用\xa0pytorch\xa0における脆弱性']
            
            # 半角スペースを正常にしてjsonに追加
            for loop in title:
                if re.match(r'.*\W.*', loop):
                    item['title'] = re.sub('\xa0', ' ', loop)

            # 3. 影響を受ける技術/バージョン
            # blockquote属性をすべて取得してから先頭にある<ul><li>属性のついたものとする
            tech = response.css("blockquote").getall()

            # 先頭の要素を取り出す
            for loop in tech:
                if re.match(r'<blockquote>[\s\S]*?<ul>[\s\S]*?<li>[\s\S]*?[\s\S]*?</blockquote>', loop):
                    tech_data = loop
                    break

            # 可能ならここで不要なタグやエスケープ文字を外して、データをjsonに追加
            # 最初の要素は技術情報に
            count = 0

            # テスト
            pprint(tech_data)
            print(tech_data)
            print(type(tech_data))

            # 技術情報を埋める
            item['technologies'] = tech_data

            # バージョン情報を埋める
            item['version'] = tech_data

            # 4. cve.orgからDescriptionを抽出
            # cve.org/CVERecordのURLを抽出する
            cve_url = response.css("a::attr(href)").re_first(r"https://www\.cve\.org/CVERecord\?id=CVE-\d{4}-\d+")

            # ページが見つかったなら実行
            if cve_url:
                # 次のページへ遷移して Description を取得
                request = scrapy.Request(cve_url, callback=self.parse_cve)
                quest.meta['item'] = item
                yield request
            
            # ページが見つからなかったらdescriptionは空欄にして終了 
            else:
                self.logger.warning("CVE URL が見つかりませんでした")
                item['description'] = ""
                yield item

        # 例外処理の定義
        except Exception as e:
            self.logger.error(f"解析中にエラーが発生しました: {e}")

    # CVE用からのスクレイピング
    def parse_cve(self, response):
        item = response.meta['item']
        # 4. CVE の Description を抽出
        try:
            # descriptionを取得してjsonに追加
            desc = response.css('').getall()
            print(desc)
            item['description'] = desc
        
        # エラーが起きた場合は例外+空欄で終了
        except Exception as e:
            self.logger.error(f"CVEページ解析中にエラーが発生しました: {e}")
            item['description'] = ""
        
        # 完成したjsonを引き渡す
        yield item
