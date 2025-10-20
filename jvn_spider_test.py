# imports
import scrapy
import re

# Jvn/Cveから取得してくる情報
class JvnScrapyItem(scrapy.Item):
    title = scrapy.Field()   # jvn's title
    content = scrapy.Field() # cve's contents
    product = scrapy.Field() # cve product status: product
    pass

# Jvnのクローリング
class JvnSpiderTestSpider(scrapy.Spider):
    name = "jvn_spider"
    allowed_domains = ["jvndb.jvn.jp"]
    start_urls = ["https://jvndb.jvn.jp/ja/contents/2025/JVNDB-2025-005907.html"]

    # 実行する関数
    def parse(self, response):
        """
        レスポンスに対するパース処理
        """

        # response.css で scrapy デフォルトの css セレクタを利用できる
        for post in response.css('body').getall():
            
            # cveのurlの抽出
            res_url=response.css('a::attr(href)').getall()
            res_cve=[]
            for loop in res_url:
                if loop.startswith("https://www.cve.org/CVERecord"):
                    res_cve.append(loop)

            # items に定義した Post のオブジェクトを生成して次の処理へ渡す
            yield JvnScrapyItem(
                title=response.css('title::text').getall(),
                content=res_cve[0],
                product=res_cve[0],
            )

        # 再帰的にページングを辿るための処理
        older_post_link = response.css('.blog-pagination a.next-posts-link::attr(href)').extract_first()
        if older_post_link is None:
            # リンクが取得できなかった場合は最後のページなので処理を終了
            return

        # URLが相対パスだった場合に絶対パスに変換する
        older_post_link = response.urljoin(older_post_link)
        # 次のページをのリクエストを実行する
        yield scrapy.Request(older_post_link, callback=self.parse)
