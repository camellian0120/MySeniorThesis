# jvn_spider/pipelines.py

import json
from collections import defaultdict

class JvnSpiderPipeline:
    def __init__(self):
        self.data = defaultdict(dict)

    def process_item(self, item, spider):
        self.data[item['jvndb_id']] = {
            "title": item['title'],
            "description": item['description'],
            "technologies": item['technologies'],
            "version": item['version']
        }
        return item

    def close_spider(self, spider):
        # JSON ファイルへ出力
        with open('jvn_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)
