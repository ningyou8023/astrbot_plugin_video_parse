import re
import os
import uuid
import io
import aiohttp
import asyncio
from pathlib import Path
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import Node, Nodes, Plain, Video, Image
from astrbot.api import logger, AstrBotConfig

try:
    from PIL import Image as PILImage
except Exception:
    PILImage = None

XHS_PATTERN = r"http[s]?://(?:xhslink\.com|xiaohongshu\.com)[a-zA-Z0-9\-\?\=\&\_/\.\%]+"
DY_PATTERN = r"http[s]?://v\.douyin\.com/[a-zA-Z0-9/\-_]+"
KS_PATTERN = r"http[s]?://[a-zA-Z0-9\-\.]*kuaishou\.com/[a-zA-Z0-9\-\?\=\&\_/\.\%]+"
DOUBAO_PATTERN = r"http[s]?://(?:www\.)?doubao\.com/(?:video-sharing\?[a-zA-Z0-9\-\?\=\&\_/\.\%]+|thread/[a-zA-Z0-9\-\?\=\&\_/\.\%]+)"
JIMENG_PATTERN = r"http[s]?://(?:www\.)?jimeng\.jianying\.com/s/[a-zA-Z0-9\-\_]+/?(?:\?[a-zA-Z0-9\-\?\=\&\_/\.\%]+)?"
WXSPH_PATTERN = r"http[s]?://(?:weixin|www\.weixin)\.qq\.com/sph/[a-zA-Z0-9\-_]+(?:\?[a-zA-Z0-9\-\?\=\&\_/\.\%]+)?"
QIANWEN_PATTERN = r"http[s]?://(?:www\.)?qianwen\.com/share/chat/[a-zA-Z0-9]+(?:\?[a-zA-Z0-9\-\?\=\&\_/\.\%]+)?"
TIKTOK_PATTERN = r"http[s]?://(?:(?:vt|vm)\.tiktok\.com/[a-zA-Z0-9\-_]+/?|(?:www\.)?tiktok\.com/[a-zA-Z0-9\-\?\=\&\_/\.\%]+)"

PLUGIN_DATA_DIR = Path("data", "plugins_data", "astrbot_plugin_video_parse")
PLUGIN_DATA_DIR.mkdir(parents=True, exist_ok=True)

@register("video_parse", "柠柚", "聚合视频图文解析插件，支持小红书、抖音、快手、微信视频号、豆包、即梦AI、千问、TikTok等", "1.0.1")
class VideoParsePlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.api_url = getattr(self.config, "api_url", "https://api.nycnm.cn/api/v2/xhs")
        self.dy_api_url = getattr(self.config, "dy_api_url", "https://api.nycnm.cn/api/v2/dy")
        self.ks_api_url = getattr(self.config, "ks_api_url", "https://api.nycnm.cn/api/v2/ks")
        self.doubao_api_url = getattr(self.config, "doubao_api_url", "https://api.nycnm.cn/api/v2/doubao")
        self.jimeng_api_url = getattr(self.config, "jimeng_api_url", "https://api.nycnm.cn/api/v2/jimengai")
        self.wxsph_api_url = getattr(self.config, "wxsph_api_url", "https://api.nycnm.cn/api/v2/wxsph")
        self.qianwen_api_url = getattr(self.config, "qianwen_api_url", "https://api.nycnm.cn/api/v2/qianwen")
        self.tiktok_api_url = getattr(self.config, "tiktok_api_url", "https://api.nycnm.cn/api/v2/tiktok")
        self.api_key = getattr(self.config, "api_key", "")
        self.timeout = getattr(self.config, "timeout", 30)
        self.allowed_groups = getattr(self.config, "allowed_groups", [])
        self.session = aiohttp.ClientSession()

    def _compress_image_bytes(self, image_bytes: bytes, max_size: int = 1024 * 1024, keep_size: bool = False) -> bytes:
        if not image_bytes or len(image_bytes) <= max_size or PILImage is None:
            return image_bytes
        try:
            with PILImage.open(io.BytesIO(image_bytes)) as img:
                img = img.convert("RGB")
                width, height = img.size
                max_edge = 1600
                if not keep_size and max(width, height) > max_edge:
                    scale = max_edge / float(max(width, height))
                    img = img.resize((max(1, int(width * scale)), max(1, int(height * scale))), PILImage.LANCZOS)

                quality = 85
                output = io.BytesIO()
                img.save(output, format="JPEG", quality=quality, optimize=True)
                compressed = output.getvalue()

                while len(compressed) > max_size and quality > 35:
                    quality -= 10
                    output = io.BytesIO()
                    img.save(output, format="JPEG", quality=quality, optimize=True)
                    compressed = output.getvalue()

                return compressed if compressed else image_bytes
        except Exception:
            return image_bytes

    @filter.regex(XHS_PATTERN)
    async def parse_xhs(self, event: AstrMessageEvent):
        """解析小红书"""
        async for result in self._do_parse(event, XHS_PATTERN, self.api_url, "小红书"):
            yield result

    @filter.regex(DY_PATTERN)
    async def parse_dy(self, event: AstrMessageEvent):
        """解析抖音"""
        async for result in self._do_parse(event, DY_PATTERN, self.dy_api_url, "抖音"):
            yield result

    @filter.regex(KS_PATTERN)
    async def parse_ks(self, event: AstrMessageEvent):
        """解析快手"""
        async for result in self._do_parse(event, KS_PATTERN, self.ks_api_url, "快手"):
            yield result

    @filter.regex(DOUBAO_PATTERN)
    async def parse_doubao(self, event: AstrMessageEvent):
        """解析豆包"""
        async for result in self._do_parse(event, DOUBAO_PATTERN, self.doubao_api_url, "豆包"):
            yield result

    @filter.regex(JIMENG_PATTERN)
    async def parse_jimeng(self, event: AstrMessageEvent):
        """解析即梦AI"""
        async for result in self._do_parse(event, JIMENG_PATTERN, self.jimeng_api_url, "即梦AI"):
            yield result

    @filter.regex(WXSPH_PATTERN)
    async def parse_wxsph(self, event: AstrMessageEvent):
        """解析微信视频号"""
        async for result in self._do_parse(event, WXSPH_PATTERN, self.wxsph_api_url, "微信视频号"):
            yield result

    @filter.regex(QIANWEN_PATTERN)
    async def parse_qianwen(self, event: AstrMessageEvent):
        """解析千问"""
        async for result in self._do_parse(event, QIANWEN_PATTERN, self.qianwen_api_url, "千问"):
            yield result

    @filter.regex(TIKTOK_PATTERN)
    async def parse_tiktok(self, event: AstrMessageEvent):
        """解析TikTok"""
        async for result in self._do_parse(event, TIKTOK_PATTERN, self.tiktok_api_url, "TikTok"):
            yield result

    def _clean_url(self, value) -> str:
        if not isinstance(value, str):
            return ""
        return value.strip().strip("`").strip().strip("'").strip('"')

    async def _do_parse(self, event: AstrMessageEvent, pattern: str, api_url: str, platform_name: str):
        """通用的解析主逻辑"""
        # 群组白名单校验：如果是群聊且配置了白名单，则只允许白名单中的群号解析链接
        if not event.is_private_chat():
            group_id = str(event.get_group_id())
            if self.allowed_groups and group_id not in self.allowed_groups:
                return

        msg = event.message_str
        
        # 提取链接
        url_match = re.search(pattern, msg)
        if not url_match:
            return
            
        target_url = url_match.group(0)
        
        if not self.api_key:
            yield event.plain_result("❌ 请先在配置中设置 apikey")
            return
            
        yield event.plain_result(f"⏳ 正在解析{platform_name}中，请稍候...")
        
        try:
            async with self.session.get(
                api_url,
                params={"url": target_url, "apikey": self.api_key},
                timeout=self.timeout,
            ) as resp:
                if resp.status != 200:
                    yield event.plain_result(f"❌ 解析失败，HTTP状态码: {resp.status}")
                    return
                
                try:
                    data = await resp.json()
                except Exception:
                    text_resp = await resp.text()
                    yield event.plain_result(f"❌ 解析失败，接口返回非 JSON 格式数据：{text_resp[:100]}")
                    return
                
                # 判断接口返回状态（根据大部分 nycnm 接口的格式，通常包含 code: 200）
                if str(data.get("code", "")) != "200" and "data" not in data:
                    msg_err = data.get("msg") or "未知错误"
                    yield event.plain_result(f"❌ 解析失败: {msg_err}")
                    return
                
                # 提取数据内容，兼容部分接口把 data 返回成列表的情况
                raw_result_data = data.get("data", {})
                if isinstance(raw_result_data, dict):
                    result_data = raw_result_data
                elif isinstance(raw_result_data, list):
                    result_data = raw_result_data[0] if raw_result_data and isinstance(raw_result_data[0], dict) else {}
                else:
                    result_data = {}
                content_type = str(result_data.get("type", "") or "").strip().lower()
                if platform_name == "千问":
                    title = result_data.get("title", "") or result_data.get("desc", "")
                else:
                    title = (
                        result_data.get("title", "")
                        or result_data.get("desc", "")
                        or result_data.get("prompt", "")
                        or result_data.get("ori_query", "")
                    )
                author = result_data.get("author", "")
                if isinstance(author, dict):
                    author = author.get("name", "") or author.get("nickname", "")
                
                # 获取图片、视频和实况列表
                images = result_data.get("images", [])
                if isinstance(images, str):
                    cleaned_image = self._clean_url(images)
                    images = [cleaned_image] if cleaned_image.startswith("http") else []
                elif isinstance(images, list):
                    images = [self._clean_url(img) for img in images if self._clean_url(img).startswith("http")]
                # 快手视频链接可能在 hd 或 high_bitrate 字段中
                primary_url = self._clean_url(result_data.get("url", ""))
                # 豆包图文/会话型返回里的 url 是分享页，不是媒体直链，不能当视频发。
                if platform_name == "豆包" and content_type in {"conversation", "image", "images"}:
                    primary_url = ""
                video_url = primary_url or self._clean_url(result_data.get("hd", "")) or self._clean_url(result_data.get("high_bitrate", ""))
                videos = result_data.get("videos", [])
                extra_video_urls = []
                if isinstance(videos, list):
                    for item in videos:
                        if isinstance(item, dict):
                            candidate = self._clean_url(item.get("url", "")) or self._clean_url(item.get("video_url", ""))
                        else:
                            candidate = self._clean_url(item)
                        if isinstance(candidate, str) and candidate.startswith("http"):
                            extra_video_urls.append(candidate)
                    if (not isinstance(video_url, str) or not video_url.startswith("http")) and extra_video_urls:
                        video_url = extra_video_urls[0]
                if (not isinstance(video_url, str) or not video_url.startswith("http")):
                    video_backup = result_data.get("video_backup", [])
                    if isinstance(video_backup, list):
                        for item in video_backup:
                            candidate = self._clean_url(item.get("url", "")) if isinstance(item, dict) else self._clean_url(item)
                            if candidate.startswith("http"):
                                video_url = candidate
                                break
                all_video_urls = []
                if isinstance(video_url, str) and video_url.startswith("http"):
                    all_video_urls.append(video_url)
                for candidate in extra_video_urls:
                    if candidate not in all_video_urls:
                        all_video_urls.append(candidate)
                live_videos = result_data.get("live", []) or result_data.get("live_photo", [])
                if isinstance(live_videos, list):
                    live_videos = [self._clean_url(url) for url in live_videos if self._clean_url(url).startswith("http")]

                if not title:
                    if isinstance(images, list) and images and not all_video_urls and not live_videos:
                        title = f"{platform_name}图文解析"
                    elif all_video_urls or live_videos:
                        title = f"{platform_name}视频解析"
                    else:
                        title = f"{platform_name}内容解析"

                # 开始构建合并转发消息
                nodes = Nodes([])
                bot_uin = event.get_self_id()
                bot_name = f"{platform_name}解析Bot"
                
                # 1. 拼接文本信息并添加节点
                text_lines = [f"📝 标题: {title}"] if title else []
                if author:
                    text_lines.append(f"👤 作者: {author}")
                text_content = "\n".join(text_lines) if text_lines else f"{platform_name}解析结果"
                nodes.nodes.append(Node(uin=bot_uin, name=bot_name, content=[Plain(text_content)]))
                
                # 2. 处理图片 (图文解析或实况图文解析)
                if isinstance(images, list) and images:
                    for idx, img_url in enumerate(images, start=1):
                        if isinstance(img_url, str) and img_url.startswith("http"):
                            img_bytes = await self._download_image(img_url, platform_name)
                            if img_bytes:
                                if platform_name == "千问":
                                    img_bytes = self._compress_image_bytes(img_bytes, max_size=1024 * 1024, keep_size=True)
                                else:
                                    img_bytes = self._compress_image_bytes(img_bytes)
                                nodes.nodes.append(Node(uin=bot_uin, name=bot_name, content=[Image.fromBytes(img_bytes)]))
                            else:
                                nodes.nodes.append(Node(uin=bot_uin, name=bot_name, content=[Image.fromURL(img_url)]))
                
                # 3. 处理视频 (短视频解析模式)
                # 提示：在短视频模式下，images字段可能是一个字符串，且 url 字段包含视频链接
                # 抖音图文模式下，url 可能是一个字符串（"当前为图文解析..."），所以我们需要确保 url 也是 http 开头
                if all_video_urls and not (isinstance(images, list) and len(images) > 0):
                    nodes.nodes.append(Node(uin=bot_uin, name=bot_name, content=[Video.fromURL(all_video_urls[0])]))
                elif all_video_urls:
                    for media_url in all_video_urls:
                        nodes.nodes.append(Node(uin=bot_uin, name=bot_name, content=[Video.fromURL(media_url)]))
                
                # 4. 处理实况图文中的实况视频 (live)
                if isinstance(live_videos, list) and live_videos:
                    for live_url in live_videos:
                        if isinstance(live_url, str) and live_url.startswith("http"):
                            nodes.nodes.append(Node(uin=bot_uin, name=bot_name, content=[Video.fromURL(live_url)]))
                
                # 发送合并转发消息
                yield event.chain_result([nodes])
                
        except asyncio.TimeoutError:
            yield event.plain_result("❌ 请求接口超时，请稍后再试")
        except Exception as e:
            logger.error(f"{platform_name}解析异常: {e}")
            yield event.plain_result("❌ 解析发生异常，请稍后再试")

    async def _download_image(self, image_url: str, platform_name: str = "小红书") -> bytes:
        """异步下载图片并返回字节数据，带有防盗链请求头"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
        }
        
        # 根据不同平台设置 Referer
        if platform_name == "抖音":
            headers["Referer"] = "https://www.douyin.com/"
        elif platform_name == "快手":
            headers["Referer"] = "https://www.kuaishou.com/"
        elif platform_name == "豆包":
            headers["Referer"] = "https://www.doubao.com/"
        elif platform_name == "即梦AI":
            headers["Referer"] = "https://jimeng.jianying.com/"
        elif platform_name == "微信视频号":
            headers["Referer"] = "https://weixin.qq.com/"
        elif platform_name == "千问":
            headers["Referer"] = "https://www.qianwen.com/"
        elif platform_name == "TikTok":
            headers["Referer"] = "https://www.tiktok.com/"
        else:
            headers["Referer"] = "https://www.xiaohongshu.com/"

        try:
            async with self.session.get(image_url, headers=headers, timeout=aiohttp.ClientTimeout(total=self.timeout)) as resp:
                if resp.status == 200:
                    return await resp.read()
                else:
                    logger.error(f"图片下载失败，状态码: {resp.status}")
        except Exception as e:
            logger.error(f"图片下载异常: {e}")
        return None

    async def cleanup_file(self, file_path: str, delay: int = 15):
        """延迟删除临时文件"""
        await asyncio.sleep(delay)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"✅ 已清理临时视频文件: {file_path}")
        except Exception as e:
            logger.error(f"❌ 清理临时文件失败: {e}")
