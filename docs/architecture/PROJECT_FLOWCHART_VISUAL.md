# RSS-Person 项目可视化流程图

## 主架构图详细依赖关系图

```mermaid
graph LR
    %% 主程序依赖
    Cloud[daily_report_PRO_cloud.py] -->|导入| Ranker[article_ranker.py]
    Cloud -->|使用| OpenAI[OpenAI SDK<br/>DeepSeek]
    Cloud -->|使用| Paramiko[paramiko<br/>SFTP]
    Cloud -->|使用| Feedparser[feedparser<br/>RSS解析]
    Cloud -->|使用| Requests[requests<br/>HTTP]

    Wechat[daily_report_PRO_wechat.py] -->|导入| Ranker
    Wechat -->|导入| WechatPub[wechat_publisher.py]
    Wechat -->|使用| OpenAI
    Wechat -->|使用| Feedparser

    Server[daily_report_PRO_server.py] -->|导入| Ranker
    Server -->|使用| OpenAI
    Server -->|使用| Feedparser

    %% 工具脚本
    Collector[rss_collector.py] -->|使用| Feedparser
    Collector -->|使用| CurlCffi[curl_cffi<br/>反爬虫]

    Integrate[integrate_to_website.py] -->|使用| SQLite[sqlite3<br/>数据库]

    %% 配置
    Env[.env] -->|配置| Cloud
    Env -->|配置| Wechat
    Env -->|配置| Server

    style Cloud fill:#90EE90
    style Wechat fill:#DDA0DD
    style Server fill:#87CEEB
    style Ranker fill:#FFA500
    style OpenAI fill:#FFB6C1
    style Env fill:#FFD700
```

## 数据流向图

```mermaid
flowchart TD
    Start([定时任务触发<br/>每天 9:00]) --> LoadConf[加载 .env 配置]

    LoadConf --> Collect[采集 RSS 数据<br/>58个源]
    Collect --> Filter[时间过滤<br/>24小时内]

    Filter --> Rank[智能排序<br/>article_ranker.py<br/>0-100分]
    Rank --> Select[选择 Top 15-20 篇]

    Select --> AI[AI 分析<br/>DeepSeek API]
    AI --> Generate[生成 HTML 报告]

    Generate --> Save[保存本地<br/>reports/]

    Save --> Check{版本检查}

    Check -->|cloud版| Upload[SFTP 上传<br/>云服务器]
    Check -->|wechat版| WeChatPub[微信草稿]
    Check -->|server版| End([结束])

    Upload --> End
    WeChatPub --> End

    style Start fill:#FFD700
    style AI fill:#FFB6C1
    style Upload fill:#90EE90
    style WeChatPub fill:#DDA0DD
    style End fill:#87CEEB
```

## RSS 采集策略图

```mermaid
graph TD
    RSS[RSS源列表<br/>58个] --> Strategy{选择采集策略}

    Strategy -->|Twitter/中文| RSSHub[策略1: RSSHub<br/>localhost:1200]
    Strategy -->|AI News/403| CFFI[策略2: curl_cffi<br/>反爬虫]
    Strategy -->|Google/OpenAI| Direct[策略3: 直连+代理<br/>requests]
    Strategy -->|arxiv学术| NoProxy[策略4: 直连无代理<br/>requests]

    RSSHub --> Result[获取 RSS 内容]
    CFFI --> Result
    Direct --> Result
    NoProxy --> Result

    Result --> Parse[feedparser 解析]
    Parse --> Articles[文章列表]

    style RSSHub fill:#FF6B6B
    style CFFI fill:#4ECDC4
    style Direct fill:#45B7D1
    style NoProxy fill:#96CEB4
    style Articles fill:#FFD93D
```

## 文章排序评分流程

```mermaid
graph LR
    Article[原始文章] --> Calc[计算得分]

    Calc --> Source[来源权威性<br/>60%权重]
    Calc --> Content[内容相关性<br/>40%权重]

    Source --> SW[来源权重表<br/>预定义]
    Content --> KW[关键词匹配<br/>高价值词]

    SW --> Score1[来源分<br/>0-60]
    KW --> Score2[内容分<br/>0-40]

    Score1 --> Total[总分<br/>0-100]
    Score2 --> Total

    Total --> Sort[排序]
    Sort --> Top[Top 15-20 篇]

    style Article fill:#E0E0E0
    style Total fill:#FFD700
    style Top fill:#90EE90
```

## 版本功能对比

```mermaid
graph TD
    Base[基础功能<br/>所有版本共有] --> RSS[✅ RSS采集<br/>58个源]
    Base --> Rank[✅ 智能排序<br/>评分系统]
    Base --> AI[✅ AI分析<br/>DeepSeek]
    Base --> HTML[✅ HTML报告<br/>响应式]
    Base --> Local[✅ 本地保存<br/>reports/]

    CloudOnly[Cloud版独有] --> SFTP[✅ SFTP自动上传<br/>云服务器]
    CloudOnly --> CloudLog[✅ 云服务器日志]

    WechatOnly[Wechat版独有] --> WeChat[✅ 微信公众号<br/>草稿发布]

    ServerOnly[Server版独有] --> ServerRun[✅ 服务器本地运行<br/>未来迁移用]

    style Base fill:#E8F5E9
    style CloudOnly fill:#E3F2FD
    style WechatOnly fill:#F3E5F5
    style ServerOnly fill:#FFF3E0
```

## 启动和运行流程

```mermaid
sequenceDiagram
    participant User as 用户
    participant Shell as Terminal
    participant Docker as Docker Compose
    participant Main as 主程序
    participant RSSHub as RSSHub服务
    participant DeepSeek as DeepSeek API
    participant Server as 云服务器

    User->>Shell: 1. 配置 .env
    User->>Docker: 2. docker compose up -d
    Docker-->>Shell: 服务启动成功
    User->>Shell: 3. python3 daily_report_PRO_cloud.py
    Shell->>Main: 启动主程序

    Main->>RSSHub: 采集 RSS 数据
    RSSHub-->>Main: 返回文章列表

    Main->>Main: 智能排序
    Main->>DeepSeek: AI 分析请求
    DeepSeek-->>Main: 返回分析结果

    Main->>Main: 生成 HTML 报告
    Main->>Main: 保存本地

    Main->>Server: SFTP 上传
    Server-->>Main: 上传成功

    Main-->>Shell: 返回成功信息
    Shell-->>User: 显示报告链接
```

## 定时任务自动运行流程

```mermaid
sequenceDiagram
    participant Launchd as macOS launchd
    participant Cron as manage_cron.sh
    participant Main as daily_report_PRO_cloud.py
    participant Log as logs/
    participant Server as 云服务器

    Note over Launchd: 每天 9:00 AM
    Launchd->>Cron: 触发定时任务
    Cron->>Main: 执行主程序

    Main->>Main: 采集 RSS
    Main->>Main: AI 分析
    Main->>Main: 生成报告
    Main->>Server: 上传报告

    Main-->>Log: 写入 stdout.log
    Main-->>Log: 写入 stderr.log

    Main-->>Cron: 执行完成
    Cron-->>Launchd: 任务完成

    Note over Server: 报告已更新
```

## 文件大小和复杂度可视化

```mermaid
pie title 各文件代码行数分布
    "daily_report_PRO_cloud.py" : 881
    "daily_report_PRO_wechat.py" : 615
    "daily_report_PRO_server.py" : 420
    "rss_collector.py" : 324
    "article_ranker.py" : 226
    "wechat_publisher.py" : 87
```

## 外部服务依赖关系

```mermaid
graph TB
    Project[RSS-Person 项目] --> API[DeepSeek API<br/>AI分析服务]
    Project --> DockerServices[Docker Services]

    DockerServices --> RSSHubD[RSSHub<br/>Twitter/中文源]
    DockerServices --> RedisD[Redis<br/>缓存服务]
    DockerServices --> MySQLD[MySQL<br/>wewe-rss数据库]
    DockerServices --> WeweRSSD[wewe-rss<br/>微信公众号源]

    Project --> CloudServer[云服务器 8.135.37.159<br/>SFTP上传]
    Project --> WeChatAPI[微信API<br/>公众号发布]

    style API fill:#FFB6C1
    style CloudServer fill:#90EE90
    style WeChatAPI fill:#DDA0DD
```

---

## 如何查看这些流程图

1. **GitHub/GitLab**: 直接在 Markdown 文件中查看
2. **VS Code**: 安装 "Markdown Preview Mermaid Support" 插件
3. **在线工具**: 访问 https://mermaid.live/ 粘贴代码查看
4. **Typora**: 原生支持 Mermaid 图表
5. **Obsidian**: 原生支持 Mermaid 图表
