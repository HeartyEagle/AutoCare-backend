from icrawler.builtin import GoogleImageCrawler, ImageDownloader
import threading
import json


class DynamicImage:
    CACHE_FILE = "dynapic_cache.json"

    class CustomLinkPrinter(ImageDownloader):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.file_urls = []

        def get_filename(self, task, default_ext):
            file_idx = self.fetched_num + self.file_idx_offset
            return '{:04d}.{}'.format(file_idx, default_ext)

        def download(self, task, default_ext, timeout=5, max_retry=3, overwrite=False, **kwargs):
            file_url = task['file_url']
            filename = self.get_filename(task, default_ext)

            task['success'] = True
            task['filename'] = filename

            if not self.signal.get('reach_max_num'):
                self.file_urls.append(file_url)

            self.fetched_num += 1

            if self.reach_max_num():
                self.signal.set(reach_max_num=True)

            return

    def __init__(self, enable_cache: bool = False):
        self.enable_cache = enable_cache
        self.results = {}
        self.lock = threading.Lock()
        self.init_params = {
            'downloader_cls': self.CustomLinkPrinter,
        }
        self._initialize_cache()

    def _initialize_cache(self):
        try:
            with open(self.CACHE_FILE, "r") as f:
                json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            with open(self.CACHE_FILE, "w") as f:
                json.dump({}, f)

    def _crawl_and_store(self, keyword, index):
        google_crawler = GoogleImageCrawler(
            downloader_cls=self.CustomLinkPrinter,
            log_level=50
        )
        google_crawler.crawl(keyword=keyword, max_num=index+1)
        file_urls = google_crawler.downloader.file_urls
        result = file_urls[index] if index < len(file_urls) else None

        with self.lock:
            self.results[(keyword, index)] = result

    def _key_exists_in_cache(self, keyword: str, index=0):
        try:
            with open(self.CACHE_FILE, "r") as cache_file:
                cache_data = json.load(cache_file)
                return f"{index}𥪝{keyword}" in cache_data
        except (FileNotFoundError, json.JSONDecodeError):
            return False

    def _load_cache(self, keyword: str, index=0):
        try:
            with open(self.CACHE_FILE, "r") as cache_file:
                cache_data = json.load(cache_file)
                return cache_data.get(f"{index}𥪝{keyword}")
        except (FileNotFoundError, json.JSONDecodeError):
            raise Exception(
                f"Failed to access \"{self.CACHE_FILE}:{keyword}.\"")

    def _save_cache(self, keyword: str, result: str, index=0):
        if result is None:
            print(
                f"Warning: No result found for {keyword} (index {index}), skipping cache.")
            return

        try:
            with self.lock:
                try:
                    with open(self.CACHE_FILE, "r") as cache_file:
                        cache_data = json.load(cache_file)
                except (FileNotFoundError, json.JSONDecodeError):
                    cache_data = {}

                cache_data[f"{index}𥪝{keyword}"] = result

                with open(self.CACHE_FILE, "w") as new_cache:
                    json.dump(cache_data, new_cache, indent=4)
        except Exception as e:
            print(f"Error saving cache: {e}")

    def by_keyword(self, keyword: str, index=0):
        if self.enable_cache and self._key_exists_in_cache(keyword, index):
            return self._load_cache(keyword, index)

        self._crawl_and_store(keyword, index)
        result = self.results.get((keyword, index))

        if self.enable_cache:
            self._save_cache(keyword, result, index)

        return result

    def by_keywords(self, keywords: list):
        results = {}
        threads = []

        def process_keyword(keyword):
            if self.enable_cache and self._key_exists_in_cache(keyword, 0):
                results[keyword] = self._load_cache(keyword, 0)
            else:
                self._crawl_and_store(keyword, 0)
                result = self.results.get((keyword, 0))
                if self.enable_cache:
                    self._save_cache(keyword, result, 0)
                results[keyword] = result

        for keyword in keywords:
            thread = threading.Thread(target=process_keyword, args=(keyword,))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        return results
