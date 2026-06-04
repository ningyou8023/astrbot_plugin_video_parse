# 视频图文解析插件 (astrbot_plugin_video_parse)

这是一个适用于 AstrBot 的平台解析插件，目前支持**小红书**、**抖音**、**快手**、**微信视频号**、**豆包**、**千问API**、**即梦AI**、**TikTok**的链接自动解析。

## 特性
- 自动检测并解析小红书、抖音、快手、微信视频号、豆包、千问API、即梦AI、TikTok分享链接。
- 提取并发送标题和作者信息。
- 支持图文模式（多图合并发送）。
- 支持短视频模式（提取视频链接发送）。
- 支持实况图文（Live 视频解析）。
- **群组白名单**：支持在配置中设置允许解析的群聊，未配置的群聊将忽略链接（留空则默认所有群聊均可解析）。注：此配置绝对不会影响私聊，私聊发链接永远会自动解析。

## 配置说明
请在 AstrBot 的插件配置界面中填写：
- **小红书API地址**：解析接口的地址（默认为 `https://api.nycnm.cn/api/v2/xhs`）
- **抖音API地址**：解析接口的地址（默认为 `https://api.nycnm.cn/api/v2/dy`）
- **快手API地址**：解析接口的地址（默认为 `https://api.nycnm.cn/api/v2/ks`）
- **微信视频号API地址**：解析接口的地址（默认为 `https://api.nycnm.cn/api/v2/wxsph`）
- **豆包API地址**：解析接口的地址（默认为 `https://api.nycnm.cn/api/v2/douy`）
- **千问API地址**：解析接口的地址（默认为 `https://api.nycnm.cn/api/v2/qianwen`）
- **即梦AI API地址**：解析接口的地址（默认为 `https://api.nycnm.cn/api/v2/jimengai`）
- **TikTok API地址**：解析接口的地址（默认为 `https://api.nycnm.cn/api/v2/tiktok`）
- **API Key**：必填，你获取的接口密钥
- **请求超时时间**：请求接口和下载资源的超时时间，默认30秒
- **允许解析的群组**：群聊白名单配置，填入群号即可。注：此配置绝对不会影响私聊，私聊发链接永远会自动解析。
