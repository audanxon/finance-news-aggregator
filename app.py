from flask import Flask, jsonify, request, render_template_string
import requests
from bs4 import BeautifulSoup
import time
import threading
import json
import os
from datetime import datetime, timedelta
import sqlite3
from urllib.parse import urljoin, urlparse
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 从环境变量获取配置
PORT = int(os.environ.get('PORT', 5000))
FLASK_ENV = os.environ.get('FLASK_ENV', 'production')

# 数据库初始化
def init_db():
    conn = sqlite3.connect('finance_news.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            source TEXT NOT NULL,
            url TEXT UNIQUE,
            published_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    logger.info("数据库初始化完成")

# 爬虫类
class FinanceNewsCrawler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def crawl_dongfangcaifu(self):
        """爬取东方财富网"""
        news_list = []
        try:
            url = "https://finance.eastmoney.com/news/cywjh.html"
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 解析新闻列表
            articles = soup.find_all('p', class_='title')
            for article in articles[:10]:  # 只取前10条
                link_tag = article.find('a')
                if link_tag:
                    title = link_tag.text.strip()
                    url = link_tag.get('href')
                    if url and not url.startswith('http'):
                        url = urljoin('https://finance.eastmoney.com/', url)
                    
                    # 获取新闻详情
                    try:
                        detail_response = self.session.get(url, timeout=10)
                        detail_soup = BeautifulSoup(detail_response.content, 'html.parser')
                        content_elem = detail_soup.find('div', class_='newsContent')
                        content = content_elem.text.strip() if content_elem else "暂无详细内容"
                        
                        news_list.append({
                            'title': title,
                            'content': content[:500] + "..." if len(content) > 500 else content,
                            'source': '东方财富网',
                            'url': url,
                            'published_at': datetime.now().isoformat()
                        })
                    except Exception as e:
                        logger.warning(f"获取东方财富网详情失败: {e}")
                        continue
        except Exception as e:
            logger.error(f"爬取东方财富网失败: {e}")
        
        return news_list
    
    def crawl_sina_finance(self):
        """爬取新浪财经"""
        news_list = []
        try:
            url = "https://finance.sina.com.cn/roll/index.d.html?cid=56247"
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 解析新闻列表
            articles = soup.find_all('li')
            for article in articles[:10]:
                link_tag = article.find('a')
                if link_tag:
                    title = link_tag.text.strip()
                    url = link_tag.get('href')
                    if url and not url.startswith('http'):
                        url = urljoin('https://finance.sina.com.cn/', url)
                    
                    news_list.append({
                        'title': title,
                        'content': '新浪财经新闻',
                        'source': '新浪财经',
                        'url': url,
                        'published_at': datetime.now().isoformat()
                    })
        except Exception as e:
            logger.error(f"爬取新浪财经失败: {e}")
        
        return news_list
    
    def crawl_caijing(self):
        """爬取财经网"""
        news_list = []
        try:
            url = "http://www.caijing.com.cn/"
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 解析新闻列表
            articles = soup.find_all('h3', class_='title')
            for article in articles[:10]:
                link_tag = article.find('a')
                if link_tag:
                    title = link_tag.text.strip()
                    url = link_tag.get('href')
                    if url and not url.startswith('http'):
                        url = urljoin('http://www.caijing.com.cn/', url)
                    
                    news_list.append({
                        'title': title,
                        'content': '财经网新闻',
                        'source': '财经网',
                        'url': url,
                        'published_at': datetime.now().isoformat()
                    })
        except Exception as e:
            logger.error(f"爬取财经网失败: {e}")
        
        return news_list
    
    def crawl_jiemian(self):
        """爬取界面新闻财经板块"""
        news_list = []
        try:
            url = "https://www.jiemian.com/lists/48.html"
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 解析新闻列表
            articles = soup.find_all('div', class_='news-el')
            for article in articles[:10]:
                link_tag = article.find('a')
                if link_tag:
                    title = link_tag.text.strip()
                    url = link_tag.get('href')
                    if url and not url.startswith('http'):
                        url = urljoin('https://www.jiemian.com/', url)
                    
                    news_list.append({
                        'title': title,
                        'content': '界面新闻财经报道',
                        'source': '界面新闻',
                        'url': url,
                        'published_at': datetime.now().isoformat()
                    })
        except Exception as e:
            logger.error(f"爬取界面新闻失败: {e}")
        
        return news_list
    
    def crawl_all_sources(self):
        """爬取所有财经网站"""
        all_news = []
        
        # 依次爬取各网站
        sources = [
            self.crawl_dongfangcaifu,
            self.crawl_sina_finance,
            self.crawl_caijing,
            self.crawl_jiemian
        ]
        
        for source_func in sources:
            try:
                news = source_func()
                all_news.extend(news)
                time.sleep(1)  # 避免请求过于频繁
            except Exception as e:
                logger.error(f"爬取某个网站失败: {e}")
                continue
        
        return all_news

# 定时爬取任务
def scheduled_crawling():
    crawler = FinanceNewsCrawler()
    while True:
        logger.info("开始爬取财经新闻...")
        news_list = crawler.crawl_all_sources()
        
        # 存储到数据库
        conn = sqlite3.connect('finance_news.db')
        cursor = conn.cursor()
        
        added_count = 0
        for news in news_list:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO news (title, content, source, url, published_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (news['title'], news['content'], news['source'], news['url'], news['published_at']))
                if cursor.rowcount > 0:
                    added_count += 1
            except sqlite3.IntegrityError:
                continue  # URL重复，跳过
        
        conn.commit()
        conn.close()
        logger.info(f"爬取完成，新增 {added_count} 条新闻")
        
        # 每小时爬取一次
        time.sleep(3600)

# 启动定时任务
def start_scheduler():
    scheduler_thread = threading.Thread(target=scheduled_crawling, daemon=True)
    scheduler_thread.start()
    logger.info("定时爬取任务已启动")

# Web界面
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>财经资讯聚合平台</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f5f5;
            color: #333;
        }
        
        .header {
            background: linear-gradient(135deg, #2c3e50, #3498db);
            color: white;
            padding: 1rem 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .header h1 i {
            font-size: 1.5em;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .controls {
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            margin-bottom: 2rem;
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            align-items: center;
        }
        
        .control-group {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }
        
        .control-group label {
            font-weight: bold;
            color: #2c3e50;
        }
        
        select, input {
            padding: 0.5rem;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 1rem;
        }
        
        button {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
            font-size: 1rem;
            transition: background-color 0.3s;
        }
        
        button:hover {
            background-color: #2980b9;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            text-align: center;
        }
        
        .stat-card h3 {
            color: #7f8c8d;
            font-size: 1rem;
            margin-bottom: 0.5rem;
        }
        
        .stat-card p {
            font-size: 1.5rem;
            font-weight: bold;
            color: #2c3e50;
        }
        
        .news-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 1.5rem;
        }
        
        .news-card {
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
        }
        
        .news-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.15);
        }
        
        .news-header {
            padding: 1rem;
            background: #f8f9fa;
            border-bottom: 1px solid #eee;
        }
        
        .news-source {
            display: inline-block;
            background: #3498db;
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.8rem;
        }
        
        .news-date {
            float: right;
            color: #7f8c8d;
            font-size: 0.8rem;
        }
        
        .news-body {
            padding: 1rem;
        }
        
        .news-title {
            font-size: 1.1rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
            color: #2c3e50;
            line-height: 1.4;
        }
        
        .news-content {
            color: #555;
            font-size: 0.9rem;
            line-height: 1.5;
            margin-bottom: 1rem;
        }
        
        .news-link {
            display: inline-block;
            background: #3498db;
            color: white;
            text-decoration: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            font-size: 0.9rem;
            transition: background-color 0.3s;
        }
        
        .news-link:hover {
            background: #2980b9;
        }
        
        .pagination {
            display: flex;
            justify-content: center;
            margin-top: 2rem;
            gap: 0.5rem;
        }
        
        .pagination button {
            min-width: 40px;
        }
        
        .loading {
            text-align: center;
            padding: 2rem;
            color: #7f8c8d;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 1rem;
            }
            
            .controls {
                flex-direction: column;
                align-items: stretch;
            }
            
            .news-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 财经资讯聚合平台</h1>
    </div>
    
    <div class="container">
        <div class="controls">
            <div class="control-group">
                <label for="sourceFilter">新闻源</label>
                <select id="sourceFilter">
                    <option value="">全部</option>
                    {% for source in sources %}
                    <option value="{{ source }}">{{ source }}</option>
                    {% endfor %}
                </select>
            </div>
            
            <div class="control-group">
                <label for="searchInput">搜索</label>
                <input type="text" id="searchInput" placeholder="输入关键词...">
            </div>
            
            <div class="control-group">
                <label>&nbsp;</label>
                <button onclick="loadNews()">搜索</button>
            </div>
            
            <div style="margin-left: auto; display: flex; align-items: flex-end;">
                <button onclick="manualCrawl()" style="background-color: #27ae60;">手动更新</button>
            </div>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <h3>总资讯数</h3>
                <p id="totalNews">{{ stats.total_news }}</p>
            </div>
            <div class="stat-card">
                <h3>数据源数</h3>
                <p id="sourceCount">{{ stats.source_stats|length }}</p>
            </div>
            <div class="stat-card">
                <h3>最后更新</h3>
                <p id="lastUpdate">{{ stats.last_update[:10] if stats.last_update else 'N/A' }}</p>
            </div>
            <div class="stat-card">
                <h3>活跃数据源</h3>
                <p id="activeSources">{{ stats.source_stats|length }}</p>
            </div>
        </div>
        
        <div id="newsContainer">
            <div class="news-grid">
                {% for news in news_list %}
                <div class="news-card" data-source="{{ news.source }}">
                    <div class="news-header">
                        <span class="news-source">{{ news.source }}</span>
                        <span class="news-date">{{ news.published_at[:10] if news.published_at else news.created_at[:10] }}</span>
                    </div>
                    <div class="news-body">
                        <h3 class="news-title">{{ news.title }}</h3>
                        <p class="news-content">{{ news.content[:200] }}{% if news.content|length > 200 %}...{% endif %}</p>
                        <a href="{{ news.url }}" target="_blank" class="news-link">查看详情</a>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <div class="pagination" id="pagination">
            {% for i in range(1, pages + 1) %}
            <button onclick="loadPage({{ i }})" {% if i == page %}style="background-color: #2c3e50;"{% endif %}>{{ i }}</button>
            {% endfor %}
        </div>
    </div>
    
    <script>
        let currentPage = {{ page }};
        let totalPages = {{ pages }};
        let currentSource = '';
        let currentSearch = '';
        
        function loadNews() {
            currentSource = document.getElementById('sourceFilter').value;
            currentSearch = document.getElementById('searchInput').value;
            
            const url = `/api/news?page=${currentPage}&limit=20&source=${encodeURIComponent(currentSource)}&search=${encodeURIComponent(currentSearch)}`;
            
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    renderNews(data.data);
                    renderPagination(data.page, data.pages);
                })
                .catch(error => {
                    console.error('Error:', error);
                });
        }
        
        function renderNews(newsList) {
            const container = document.getElementById('newsContainer');
            let html = '<div class="news-grid">';
            
            newsList.forEach(news => {
                html += `
                    <div class="news-card" data-source="${news.source}">
                        <div class="news-header">
                            <span class="news-source">${news.source}</span>
                            <span class="news-date">${news.published_at ? news.published_at.substring(0, 10) : news.created_at.substring(0, 10)}</span>
                        </div>
                        <div class="news-body">
                            <h3 class="news-title">${news.title}</h3>
                            <p class="news-content">${news.content.substring(0, 200)}${news.content.length > 200 ? '...' : ''}</p>
                            <a href="${news.url}" target="_blank" class="news-link">查看详情</a>
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
            container.innerHTML = html;
        }
        
        function renderPagination(page, totalPages) {
            const pagination = document.getElementById('pagination');
            let html = '';
            
            for (let i = 1; i <= totalPages; i++) {
                const activeStyle = i === page ? 'background-color: #2c3e50;' : '';
                html += `<button onclick="loadPage(${i})" style="${activeStyle}">${i}</button>`;
            }
            
            pagination.innerHTML = html;
        }
        
        function loadPage(page) {
            currentPage = page;
            loadNews();
        }
        
        function manualCrawl() {
            fetch('/api/crawl', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                loadNews();
            })
            .catch(error => {
                console.error('Error:', error);
                alert('手动更新失败');
            });
        }
        
        // 绑定搜索输入事件
        document.getElementById('searchInput').addEventListener('keyup', function(event) {
            if (event.key === 'Enter') {
                currentPage = 1;
                loadNews();
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    source = request.args.get('source', '')
    search = request.args.get('search', '')
    
    conn = sqlite3.connect('finance_news.db')
    cursor = conn.cursor()
    
    query = "SELECT * FROM news WHERE 1=1"
    params = []
    
    if source:
        query += " AND source = ?"
        params.append(source)
    
    if search:
        query += " AND (title LIKE ? OR content LIKE ?)"
        params.extend([f'%{search}%', f'%{search}%'])
    
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    offset = (page - 1) * limit
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    news_list = []
    for row in rows:
        news_list.append({
            'id': row[0],
            'title': row[1],
            'content': row[2],
            'source': row[3],
            'url': row[4],
            'published_at': row[5],
            'created_at': row[6]
        })
    
    # 获取总数
    count_query = "SELECT COUNT(*) FROM news WHERE 1=1"
    count_params = []
    
    if source:
        count_query += " AND source = ?"
        count_params.append(source)
    
    if search:
        count_query += " AND (title LIKE ? OR content LIKE ?)"
        count_params.extend([f'%{search}%', f'%{search}%'])
    
    cursor.execute(count_query, count_params)
    total = cursor.fetchone()[0]
    
    # 获取所有新闻源
    cursor.execute("SELECT DISTINCT source FROM news ORDER BY source")
    sources = [row[0] for row in cursor.fetchall()]
    
    # 获取统计信息
    cursor.execute("SELECT COUNT(*) FROM news")
    total_news = cursor.fetchone()[0]
    
    cursor.execute("SELECT MAX(created_at) FROM news")
    last_update = cursor.fetchone()[0]
    
    conn.close()
    
    pages = (total + limit - 1) // limit
    
    return render_template_string(
        HTML_TEMPLATE,
        news_list=news_list,
        page=page,
        pages=pages,
        sources=sources,
        stats={
            'total_news': total_news,
            'last_update': last_update or 'N/A'
        }
    )

@app.route('/api/news', methods=['GET'])
def get_news():
    """获取新闻列表"""
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    source = request.args.get('source', '')
    search = request.args.get('search', '')
    
    conn = sqlite3.connect('finance_news.db')
    cursor = conn.cursor()
    
    query = "SELECT * FROM news WHERE 1=1"
    params = []
    
    if source:
        query += " AND source = ?"
        params.append(source)
    
    if search:
        query += " AND (title LIKE ? OR content LIKE ?)"
        params.extend([f'%{search}%', f'%{search}%'])
    
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    offset = (page - 1) * limit
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    news_list = []
    for row in rows:
        news_list.append({
            'id': row[0],
            'title': row[1],
            'content': row[2],
            'source': row[3],
            'url': row[4],
            'published_at': row[5],
            'created_at': row[6]
        })
    
    # 获取总数
    count_query = "SELECT COUNT(*) FROM news WHERE 1=1"
    count_params = []
    
    if source:
        count_query += " AND source = ?"
        count_params.append(source)
    
    if search:
        count_query += " AND (title LIKE ? OR content LIKE ?)"
        count_params.extend([f'%{search}%', f'%{search}%'])
    
    cursor.execute(count_query, count_params)
    total = cursor.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'data': news_list,
        'total': total,
        'page': page,
        'pages': (total + limit - 1) // limit
    })

@app.route('/api/sources', methods=['GET'])
def get_sources():
    """获取新闻源列表"""
    conn = sqlite3.connect('finance_news.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT source FROM news ORDER BY source")
    sources = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify({'sources': sources})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取统计信息"""
    conn = sqlite3.connect('finance_news.db')
    cursor = conn.cursor()
    
    # 总新闻数
    cursor.execute("SELECT COUNT(*) FROM news")
    total_news = cursor.fetchone()[0]
    
    # 各来源新闻数
    cursor.execute("SELECT source, COUNT(*) FROM news GROUP BY source ORDER BY COUNT(*) DESC")
    source_stats = [{'source': row[0], 'count': row[1]} for row in cursor.fetchall()]
    
    # 最新更新时间
    cursor.execute("SELECT MAX(created_at) FROM news")
    last_update = cursor.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'total_news': total_news,
        'source_stats': source_stats,
        'last_update': last_update
    })

@app.route('/api/crawl', methods=['POST'])
def manual_crawl():
    """手动触发爬取"""
    crawler = FinanceNewsCrawler()
    news_list = crawler.crawl_all_sources()
    
    # 存储到数据库
    conn = sqlite3.connect('finance_news.db')
    cursor = conn.cursor()
    
    added_count = 0
    for news in news_list:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO news (title, content, source, url, published_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (news['title'], news['content'], news['source'], news['url'], news['published_at']))
            if cursor.rowcount > 0:
                added_count += 1
        except sqlite3.IntegrityError:
            continue
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'message': f'手动爬取完成，新增 {added_count} 条新闻',
        'total_crawled': len(news_list)
    })

if __name__ == '__main__':
    init_db()
    start_scheduler()
    app.run(host='0.0.0.0', port=PORT, debug=(FLASK_ENV == 'development'))
