"""
Web 技能 - 网络请求、爬虫等
"""
import json
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse
from .base import BaseSkill, SkillResult, SkillContext
from loguru import logger


class WebSkill(BaseSkill):
    """
    HTTP 请求技能
    发送 HTTP 请求并获取响应
    """
    
    name = "http_request"
    description = "发送 HTTP 请求"
    version = "1.0.0"
    tags = ["web", "http", "api"]
    
    parameters = {
        "url": {
            "type": "str",
            "required": True,
            "description": "请求 URL"
        },
        "method": {
            "type": "str",
            "required": False,
            "default": "GET",
            "description": "HTTP 方法: GET/POST/PUT/DELETE"
        },
        "headers": {
            "type": "dict",
            "required": False,
            "description": "请求头"
        },
        "params": {
            "type": "dict",
            "required": False,
            "description": "URL 参数"
        },
        "data": {
            "type": "dict",
            "required": False,
            "description": "请求体数据"
        },
        "json_data": {
            "type": "dict",
            "required": False,
            "description": "JSON 请求体"
        },
        "timeout": {
            "type": "int",
            "required": False,
            "default": 30,
            "description": "超时时间（秒）"
        }
    }
    
    def _execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """执行 HTTP 请求"""
        import requests
        
        url = kwargs.get("url")
        method = kwargs.get("method", "GET").upper()
        headers = kwargs.get("headers", {})
        params = kwargs.get("params", {})
        data = kwargs.get("data")
        json_data = kwargs.get("json_data")
        timeout = kwargs.get("timeout", 30)
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                data=data,
                json=json_data,
                timeout=timeout
            )
            
            result = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "url": response.url,
                "elapsed": response.elapsed.total_seconds()
            }
            
            # 尝试解析响应内容
            content_type = response.headers.get('content-type', '')
            if 'application/json' in content_type:
                try:
                    result["data"] = response.json()
                except:
                    result["text"] = response.text
            else:
                result["text"] = response.text
            
            if response.status_code < 400:
                return SkillResult.ok(data=result)
            else:
                return SkillResult.error(
                    error=f"HTTP {response.status_code}",
                    data=result
                )
                
        except requests.Timeout:
            return SkillResult.error(f"请求超时（{timeout}秒）")
        except requests.RequestException as e:
            return SkillResult.error(f"请求失败: {str(e)}")
        except Exception as e:
            return SkillResult.error(str(e))


class WebScrapeSkill(BaseSkill):
    """
    网页爬取技能
    爬取网页内容并提取信息
    """
    
    name = "web_scrape"
    description = "爬取网页内容"
    version = "1.0.0"
    tags = ["web", "scrape", "crawler"]
    
    parameters = {
        "url": {
            "type": "str",
            "required": True,
            "description": "目标 URL"
        },
        "selector": {
            "type": "str",
            "required": False,
            "description": "CSS 选择器"
        },
        "extract_text": {
            "type": "bool",
            "required": False,
            "default": True,
            "description": "是否提取文本"
        },
        "extract_links": {
            "type": "bool",
            "required": False,
            "default": False,
            "description": "是否提取链接"
        },
        "extract_images": {
            "type": "bool",
            "required": False,
            "default": False,
            "description": "是否提取图片"
        }
    }
    
    def _execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """执行网页爬取"""
        try:
            from bs4 import BeautifulSoup
            import requests
        except ImportError:
            return SkillResult.error("请安装依赖: pip install beautifulsoup4 requests")
        
        url = kwargs.get("url")
        selector = kwargs.get("selector")
        extract_text = kwargs.get("extract_text", True)
        extract_links = kwargs.get("extract_links", False)
        extract_images = kwargs.get("extract_images", False)
        
        try:
            # 发送请求
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # 解析 HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            result = {
                "title": soup.title.string if soup.title else None,
                "url": url
            }
            
            # 应用选择器
            if selector:
                elements = soup.select(selector)
            else:
                elements = [soup]
            
            # 提取内容
            if extract_text:
                texts = []
                for elem in elements:
                    text = elem.get_text(strip=True, separator='\n')
                    if text:
                        texts.append(text)
                result["texts"] = texts
            
            if extract_links:
                links = []
                for elem in elements:
                    for a in elem.find_all('a', href=True):
                        links.append({
                            "text": a.get_text(strip=True),
                            "href": urljoin(url, a['href'])
                        })
                result["links"] = links
            
            if extract_images:
                images = []
                for elem in elements:
                    for img in elem.find_all('img', src=True):
                        images.append({
                            "alt": img.get('alt', ''),
                            "src": urljoin(url, img['src'])
                        })
                result["images"] = images
            
            return SkillResult.ok(data=result)
            
        except Exception as e:
            return SkillResult.error(str(e))


class APIQuerySkill(BaseSkill):
    """
    API 查询技能
    查询和测试 REST API
    """
    
    name = "api_query"
    description = "查询 REST API"
    version = "1.0.0"
    tags = ["web", "api", "rest"]
    
    parameters = {
        "base_url": {
            "type": "str",
            "required": True,
            "description": "API 基础 URL"
        },
        "endpoint": {
            "type": "str",
            "required": True,
            "description": "API 端点"
        },
        "method": {
            "type": "str",
            "required": False,
            "default": "GET",
            "description": "HTTP 方法"
        },
        "auth": {
            "type": "dict",
            "required": False,
            "description": "认证信息 {type: basic/bearer, token/username/password}"
        }
    }
    
    def _execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """执行 API 查询"""
        import requests
        
        base_url = kwargs.get("base_url")
        endpoint = kwargs.get("endpoint")
        method = kwargs.get("method", "GET")
        auth = kwargs.get("auth", {})
        
        url = urljoin(base_url, endpoint)
        headers = {}
        
        # 处理认证
        auth_type = auth.get("type")
        if auth_type == "bearer":
            headers["Authorization"] = f"Bearer {auth.get('token')}"
        elif auth_type == "basic":
            from requests.auth import HTTPBasicAuth
            auth_obj = HTTPBasicAuth(auth.get("username"), auth.get("password"))
        else:
            auth_obj = None
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                auth=auth_obj if auth_obj else None,
                timeout=30
            )
            
            result = {
                "status_code": response.status_code,
                "success": response.status_code < 400
            }
            
            try:
                result["data"] = response.json()
            except:
                result["text"] = response.text
            
            return SkillResult.ok(data=result)
            
        except Exception as e:
            return SkillResult.error(str(e))


class RSSFeedSkill(BaseSkill):
    """
    RSS 订阅技能
    读取和解析 RSS 订阅
    """
    
    name = "rss_feed"
    description = "读取 RSS 订阅"
    version = "1.0.0"
    tags = ["web", "rss", "feed"]
    
    parameters = {
        "url": {
            "type": "str",
            "required": True,
            "description": "RSS 订阅 URL"
        },
        "limit": {
            "type": "int",
            "required": False,
            "default": 10,
            "description": "返回条目数量"
        }
    }
    
    def _execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """执行 RSS 读取"""
        try:
            import feedparser
        except ImportError:
            return SkillResult.error("请安装 feedparser: pip install feedparser")
        
        url = kwargs.get("url")
        limit = kwargs.get("limit", 10)
        
        try:
            feed = feedparser.parse(url)
            
            entries = []
            for entry in feed.entries[:limit]:
                entries.append({
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "summary": entry.get("summary", "")
                })
            
            result = {
                "feed_title": feed.feed.get("title", ""),
                "feed_description": feed.feed.get("description", ""),
                "feed_link": feed.feed.get("link", ""),
                "total_entries": len(feed.entries),
                "entries": entries
            }
            
            return SkillResult.ok(data=result)
            
        except Exception as e:
            return SkillResult.error(str(e))
