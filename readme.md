# 使用Python编写的一套QQ机器人框架

## 功能
- [x] 接入bing ai
- [x] 支持多账号
- [x] 知乎链接预览截图
- [x] github链接readme预览截图
- [x] 随机加速gif
- [x] 戳戳群友头像随机发送即时生成的表情包
- [x] 调用Tim官方客户端发送群消息，避免风控发不出消息
- [x] 调用Midjourney实现AI绘画
- [x] 调用StableDiffusion实现AI绘画
- [x] 接入chatgpt聊天，可以设置AI人格
- [x] 发送B站视频链接或者BV、AV号进行分析视频并AI总结视频内容
- [x] 总结任意网页
- [x] 维基百科、萌娘百科搜索
- [x] 聊天指令管理开关各个插件
- [x] 斗牛棋牌游戏
- [x] 21点棋牌游戏
- [x] 24点算数游戏
- [x] 活跃度系统，群成员发言一次加一点活跃度，签到、连续签到获得额外奖励，活跃度有排行榜
- [x] 文字转语音聊天
- [x] 发送知乎链接自动截图预览，支持知乎专栏、知乎问答
- [x] 发送github链接自动截图预览readme
- [x] ~~调用吐司在线画图实现AI绘画，吐司加了验证码，暂时放弃~~
- [x] ~~原神抽卡模拟，已不再更新~~
 
# 环境

## Python版本

Python3.11

## 第三方依赖库

`pip install -r requirements.txt`

### 初始化

运行`init.bat`，会下载一些必要文件和登录知乎


## 配置自带的插件参数

打开`config.json`修改对应参数, 

运行了`init.bat`之后会自动生成`config.json`

[参数文档](doc/config.md)

## 对接mirai(不推荐)

[配置mirai](doc/mirai.md)

然后运行[client/mirai/main.py](client/mirai/main.py)即可

## 对接onebot(墙裂推荐)

运行[client/onebot/main.py](client/onebot/main.py)即可

然后配置LLOneBot,详情见[LLOneBot](https://github.com/linyuchen/LiteLoaderQQNT-OneBotApi)

对接其他onebot框架只需修改`config.json`的`ONEBOT_HTTP_API`即可

# 备份

需要备份`msgplugins/superplugin/db.sqlite3`,`config.json`

# 插件开发

参考[msgplugins/example.py](msgplugins/example.py)

# TODO
- [ ] 完善本文档
- [x] 命令菜单使用图片生成并美化
- [ ] 画图引擎切换命令

# 许可证

```
Copyright (C) 2019-2023.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
```
