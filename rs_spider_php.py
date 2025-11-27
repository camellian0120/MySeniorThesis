# rs_spider.py

# ─────────────────────────────────────────────
# import
# ─────────────────────────────────────────────
import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose
from w3lib.html import remove_tags
import re


# ─────────────────────────────────────────────
# Item 定義
# ─────────────────────────────────────────────
class RsItem(scrapy.Item):
    title = scrapy.Field()
    description = scrapy.Field()
    url = scrapy.Field()


# ─────────────────────────────────────────────
# Spider
# ─────────────────────────────────────────────
class RsSpider(scrapy.Spider):
    name = "rs"
    allowed_domains = ["rules.sonarsource.com"]
    start_urls = ["https://rules.sonarsource.com/php/"]

    # 最初のページから RSPEC の一覧リンクを抽出
    def parse(self, response):

        try:
            # <ol> 内の RSPEC リンクを取得
            links = response.css(
                'ol.RulesListstyles__StyledOl-sc-6thbbv-0 a::attr(href)'
            ).getall()

            for link in links:
                url = response.urljoin(link)
                yield scrapy.Request(url, callback=self.parse_detail)

        except Exception as e:
            self.logger.error(f"一覧ページ解析中にエラー: {e}")

    # 詳細ページのスクレイピング
    def parse_detail(self, response):
        try:
            item = RsItem()

            # タイトル取得
            title = response.css("h1::text").get()
            if title:
                title = title.strip()

            # 説明部分
            desc_html = response.css(
                "section.RuleDetailsstyles__StyledDescription-sc-r16ye-7.epAbRB"
            ).get()

            # HTMLタグ除去
            description = ""
            if desc_html:
                description = remove_tags(desc_html)
                # 不要な改行や空白を整形
                description = re.sub(r"\s+", " ", description).strip()

            item["title"] = title
            item["description"] = description
            item["url"] = response.url

            yield item

        except Exception as e:
            self.logger.error(f"詳細ページ解析中にエラー ({response.url}): {e}")
