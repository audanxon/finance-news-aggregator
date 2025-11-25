# 财经资讯聚合平台

一个基于Python Flask的财经资讯爬取和聚合平台，自动从多个财经网站收集最新资讯。

## 功能特性

- 🕷️ 自动爬取多个财经网站
- 📊 Web界面展示资讯
- 🔍 搜索和筛选功能
- 📈 统计信息展示
- ⏰ 定时自动更新
- 📱 响应式设计

## 数据源

- 东方财富网
- 新浪财经
- 财经网
- 界面新闻

## 快速开始

### 使用Docker部署（推荐）

#### 1. 使用预构建的Docker镜像

#### 2. 使用Docker Compose

```bash
# 创建 docker-compose.yml 文件，内容如下：
version: '3.8'

services:
  finance-aggregator:
    build: .
    ports:
      - "5000:5000"
    environment:
      - PORT=5000
      - FLASK_ENV=production
    volumes:
      - ./finance_news.db:/app/finance_news.db
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
# 克隆项目
git clone https://github.com/your-username/finance-news-aggregator.git
cd finance-news-aggregator

# 构建Docker镜像
docker build -t finance-news-aggregator .

# 运行容器
docker run -d -p 5000:5000 --name finance-aggregator finance-news-aggregator

# 访问应用
# 打开浏览器访问 http://localhost:5000

# 下载 docker-compose.yml 文件后执行
docker-compose up -d

# 访问应用
# 打开浏览器访问 http://localhost:5000
