# rs_spider.py
import scrapy
from w3lib.html import remove_tags
import re

class RsSpider(scrapy.Spider):
    name = "rs"
    allowed_domains = ["rules.sonarsource.com"]
    start_urls = ["https://rules.sonarsource.com/php/"]

    # 日本語コメント：一覧ページから RSPEC ページへのリンクを取得
    def parse(self, response):
        try:
            links = response.css(
                'ol.RulesListstyles__StyledOl-sc-6thbbv-0 a::attr(href)'
            ).getall()

            for link in links:
                url = response.urljoin(link)
                yield scrapy.Request(url, callback=self.parse_detail)

        except Exception as e:
            self.logger.error(f"一覧ページのパースエラー: {e}")

    # 日本語コメント：詳細ページのスクレイピング
    def parse_detail(self, response):
        try:
            # タイトル取得
            title = response.css("h1::text").get()
            if title:
                title = title.strip()

            # 説明部分
            desc_html = response.css(
                "section.RuleDetailsstyles__StyledDescription-sc-r16ye-7.epAbRB"
            ).get()

            description = ""
            if desc_html:
                description = remove_tags(desc_html)
                description = re.sub(r"\s+", " ", description).strip()

            yield {
                "title": title,
                "description": description,
                "url": response.url,
            }

        except Exception as e:
            self.logger.error(f"詳細ページのパースエラー ({response.url}): {e}")
