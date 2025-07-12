
from flask import Flask, render_template, jsonify
from threading import Thread, Lock
import psutil
import time
from collections import deque
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import hashlib
import schedule
import json

app = Flask(__name__, template_folder='./templates')

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

class URLManager:
    def __init__(self):
        self.new_urls = set()
        self.old_urls = set()
    
    def add_new_url(self, url):
        url_hash = hashlib.md5(url.encode()).hexdigest()
        if url and url_hash not in self.old_urls:
            self.new_urls.add(url_hash)
    
    def get_url(self):
        if self.new_urls:
            return self.new_urls.pop()
        return None

crawler_stats = {
    'running': False,
    'start_time': None,
    'urls_crawled': 0,
    'cpu_usage': deque(maxlen=300),
    'memory_usage': deque(maxlen=300),
    'network_io': deque(maxlen=300),
    'request_logs': deque(maxlen=1000),
    'error_logs': deque(maxlen=500),
    'url_manager': URLManager(),
    'lock': Lock(),
    'metrics': {
        'success_rate': 0,
        'avg_response_time': 0,
        'pages_per_minute': 0
    }
}

class EnhancedCrawler(Thread):
    def __init__(self, seed_urls):
        super().__init__()
        for url in seed_urls:
            crawler_stats['url_manager'].add_new_url(url)

    def run(self):
        crawler_stats['running'] = True
        crawler_stats['start_time'] = time.time()
        while crawler_stats['running']:
            self.update_metrics()
            self.crawl_next()
            time.sleep(1)

    def crawl_next(self):
        url = crawler_stats['url_manager'].get_url()
        if url:
            try:
                start_time = time.time()
                response = requests.get(url, timeout=10)
                response_time = time.time() - start_time
                
                log_entry = {
                    'time': time.strftime("%H:%M:%S"),
                    'url': url,
                    'status': response.status_code,
                    'response_time': response_time,
                    'size': len(response.content)
                }
                
                if response.status_code == 200:
                    self.process_content(url, response.text)
                
                with crawler_stats['lock']:
                    crawler_stats['request_logs'].append(log_entry)
                    crawler_stats['urls_crawled'] += 1
            except Exception as e:
                error_log = {'time': time.strftime("%H:%M:%S"), 'url': url, 'error': str(e)}
                with crawler_stats['lock']:
                    crawler_stats['error_logs'].append(error_log)

    def process_content(self, url, html):
        soup = BeautifulSoup(html, 'html.parser')
        links = {urljoin(url, a['href']) for a in soup.find_all('a', href=True)}
        for link in links:
            crawler_stats['url_manager'].add_new_url(link)

    def update_metrics(self):
        with crawler_stats['lock']:
            total = len(crawler_stats['request_logs'])
            success = sum(1 for log in crawler_stats['request_logs'] if log['status'] == 200)
            crawler_stats['metrics']['success_rate'] = (success/total)*100 if total else 0
            crawler_stats['metrics']['avg_response_time'] = sum(log['response_time'] for log in crawler_stats['request_logs'])/total if total else 0
            crawler_stats['cpu_usage'].append(psutil.cpu_percent())
            crawler_stats['memory_usage'].append(psutil.virtual_memory().percent)
            crawler_stats['network_io'].append(psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv)

@app.route('/')
def dashboard():
    return render_template('enhanced_dashboard.html', stats=crawler_stats)

@app.route('/api/data')
def get_data():
    return jsonify({
        'metrics': crawler_stats['metrics'],
        'system': {
            'cpu': list(crawler_stats['cpu_usage']),
            'memory': list(crawler_stats['memory_usage']),
            'network': list(crawler_stats['network_io'])
        },
        'logs': {
            'requests': list(crawler_stats['request_logs'])[-20:],
            'errors': list(crawler_stats['error_logs'])[-10:]
        }
    })

if __name__ == '__main__':
    app.run(debug=True)
