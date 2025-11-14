# jvn_spider.py
from bs4 import BeautifulSoup
import scrapy
import re
from pprint import pprint
from jvn_spider.items import JvnItem


class JvnSpider(scrapy.Spider):
    name = "jvn_spider"
    allowed_domains = ["jvndb.jvn.jp", "cve.org"]

    # 検索ページをスタートURLとして指定
    start_urls = [
        "https://jvndb.jvn.jp/search/index.php?"
        "mode=_vulnerability_search_IA_VulnSearch"
        "&lang=ja"
        "&keyword=wordpress"
        "&useSynonym=1"
        "&vendor="
        "&product="
        "&datePublicFromYear="
        "&datePublicFromMonth="
        "&datePublicToYear=2023"
        "&datePublicToMonth=03"
        "&dateLastPublishedFromYear="
        "&dateLastPublishedFromMonth="
        "&dateLastPublishedToYear="
        "&dateLastPublishedToMonth="
        "&v3Severity%5B%5D=01"
        "&v3Severity%5B%5D=02"
        "&v3Severity%5B%5D=03"
        "&cwe="
        "&searchProductId="
    ]

    def parse(self, response):
        """検索結果ページからJVNDB詳細ページへのリンクを抽出"""
        # 個別JVNDBページリンク
        links = response.css("a::attr(href)").re(r"^/ja/contents/\d{4}/JVNDB-\d{4}-\d+\.html$")
        self.logger.info(f"{len(links)} 件のJVNDBリンクを発見")

        # 個別ページを解析用にリクエスト
        for link in links:
            url = response.urljoin(link)
            yield scrapy.Request(url, callback=self.parse_detail)

        # --- 自動で次ページに遷移 ---
        if links:
            # 現在の pageNo を取得（デフォルト1）
            current_page_no = response.url.split("&pageNo=")[-1] if "&pageNo=" in response.url else "1"
            try:
                next_page_no = int(current_page_no) + 1
            except ValueError:
                next_page_no = 2

            # 次ページのURLを作成
            base_url = re.sub(r"&pageNo=\d+", "", response.url)  # 既存の pageNo を削除
            next_page_url = f"{base_url}&pageNo={next_page_no}"

            # 次ページを確認するためのリクエスト（リンクが存在すれば parse が呼ばれる）
            self.logger.info(f"次のページに移動: {next_page_url}")
            yield scrapy.Request(next_page_url, callback=self.parse)
        else:
            self.logger.info("次ページが存在しないためクロールを終了します")

    def parse_detail(self, response):
        """個別のJVNDBページを解析"""
        item = JvnItem()
        try:
            # --- 1. JVNDB-ID抽出 ---
            jvndb_id = response.css('font::text').getall()
            for loop in jvndb_id:
                if re.fullmatch(r'JVNDB-[0-9]*-[0-9]*', loop):
                    item['jvndb_id'] = loop

            # --- 2. タイトル抽出 ---
            title = response.css('h2::text').getall()
            for loop in title:
                if re.match(r'.*\W.*', loop):
                    item['title'] = re.sub('\xa0', ' ', loop)

            # --- 3. 影響を受ける技術/バージョン ---
            tech_blocks = response.css("blockquote").getall()
            tech_data = ""
            for loop in tech_blocks:
                if re.match(r'<blockquote>[\s\S]*?<ul>[\s\S]*?<li>[\s\S]*?</blockquote>', loop):
                    tech_data = loop
                    break

            if tech_data:
                soup = BeautifulSoup(tech_data, "html.parser")
                text = soup.get_text(separator="\n", strip=True)
                cleaned_text = re.sub(r"\s*\n\s*", "\n", text)
                cleaned_text = re.sub(r"\xa0", " ", cleaned_text)
                cleaned_text = cleaned_text.strip()
                item["technologies"] = cleaned_text
            else:
                item["technologies"] = ""

            # --- 4. CVE URL抽出 ---
            cve_url = response.css("a::attr(href)").re_first(
                r"https://www\.cve\.org/CVERecord\?id=CVE-\d{4}-\d+"
            )

            if cve_url:
                request = scrapy.Request(
                    cve_url,
                    callback=self.parse_cve,
                    meta={
                        "item": item,
                        "playwright": True,
                        "playwright_include_page": True,
                    },
                )
                yield request
            else:
                self.logger.warning(f"CVE URL が見つかりませんでした ({item.get('jvndb_id')})")
                item['description'] = ""
                yield item

        except Exception as e:
            self.logger.error(f"解析中にエラーが発生しました: {e}")

    async def parse_cve(self, response):
        """CVE.orgの<p class='content cve-x-scroll'>を抽出"""
        item = response.meta['item']
        page = response.meta["playwright_page"]

        try:
            await page.wait_for_selector("p.content.cve-x-scroll", timeout=10000)
            elements = await page.query_selector_all("p.content.cve-x-scroll")
            texts = [await el.inner_text() for el in elements]
            joined_text = "\n".join([t.strip() for t in texts])
            cleaned_text = re.sub(r"\s+\n", "\n", joined_text).strip()
            item["description"] = cleaned_text
            await page.close()

        except Exception as e:
            self.logger.error(f"CVEページ解析中にエラーが発生しました: {e}")
            item["description"] = ""
            try:
                await page.close()
            except:
                pass

        yield item
