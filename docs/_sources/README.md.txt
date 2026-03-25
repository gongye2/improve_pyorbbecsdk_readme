# Docs应用文档

**编译：**

```bash
cd docs
./autobuild.sh all

```

**打开文档：**

```bash
cd docs
./autobuild.sh run

```

或

进入_html目录，手动点击index.html打开

# Docs应用文档详细说明

**采用方式：**

1、文档格式 markdown

2、文档转换工具 Sphinx

3、托管 github

<br>

# gitlab：

本项目源码地址： https://code.orbbec.com.cn/OrbbecSDK/pyorbbecsdk

# github （待上线）

本项目源码地址 ：  待上线
本应用文档阅读链接 ： 待上线

<br>

# API Reference 自动生成

本项目的 API Reference 文档是从 pyi stub 文件自动生成的。

## 生成 API 文档

API 文档 RST 文件通常已经生成，只有修改了脚本或添加新类时才需要重新生成：

```bash
# 从项目根目录（目前许手动修改pyi路径，因为使用的是绝对路径; 此外必须要在安装了pyorbbecsdk2的虚拟环境）
python scripts/generate_api_docs.py
```

脚本参数：
- `--dry-run`: 预览生成的内容，不写入文件
- `--check`: 检查文件是否最新（用于 CI）
- `--stubs-dir PATH`: 指定 stubs 目录路径

## 添加新类到 API Reference

1. 编辑 `scripts/generate_api_docs.py`，在 `MODULES` 字典中添加类名：
   ```python
   MODULES = {
       "core": {
           "title": "Core Classes",
           "classes": [
               # ... 现有类 ...
               "NewClass",  # 添加新类
           ],
       },
   }
   ```

2. 运行脚本生成新的 RST 文件：
   ```bash
   python scripts/generate_api_docs.py
   ```

3. 重新构建文档：
   ```bash
   cd docs && make html
   ```

## 目录结构

```
docs/source/5_API_Reference/     # API 参考（从 pyi 自动生成）
├── index.rst
├── core.rst                     # 核心类（Context, Device, Config 等）
├── pipeline.rst                 # Pipeline 和 FrameSet
├── frame.rst                    # 各类 Frame
├── stream_profile.rst           # 流配置
├── filter.rst                   # 过滤器
└── utils.rst                    # 工具函数和枚举
```

## API Reference 与 Application Guide 的关系

| 文档类型 | 维护方式 | 内容特点 |
|---------|---------|---------|
| **Application Guide** | 手动编写 | 教程式，解决具体问题，包含使用场景和案例 |
| **API Reference** | 自动生成 | 参考式，查阅类/方法定义，从 pyi 文件生成 |

### 交叉引用

在 Application Guide 中引用 API：
```rst
查看 :class:`~pyorbbecsdk.Context` 获取更多信息。
```

在 API Reference 中引用教程：
```rst
.. seealso::
   查看 :doc:`../4_Application_Guide/basic_usage` 了解用法。
```

<br>

# 文档编写规范

1、框图、软件框架建议原则上采用processon、visio工具绘图，目的是为了保持风格统一（特殊图除外）

2、采用标准markdown格式，可使用vscode的Editor插件编辑

<br>

# 编译环境

pip3 install sphinx

pip3 install recommonmark

pip3 install sphinx_markdown_tables

pip3 install sphinx_rtd_theme

pip3 install sphinx_book_theme

# 编译

- 执行编译脚本 ./autobuild 编译（推荐，该脚本编译后会打包docs文档及渲染设置）。 也支持sphinx原生编译指令make html
- 打开docs/index.html查看效果

<br>

# 提交

git add 、git commit 添加注释、git push提交代码

提交完后，务必要上线网页打开检查一下，检查网页效果无误

<br>

# 定制化部分

说明：定制化的配置都在**conf.py**中设置。也需要安装一些支持库

1. 更改样式主题。我这里以 `sphinx_rtd_theme`为例子，其他主题可自行百度。

* 安装 `sphinx_rtd_theme`:    ` pip install sphinx_rtd_theme`

2. 安装markdown语法支持插件：`pip install myst-parser`
3. 安装支持mermaid渲染插件: `pip install sphinxcontrib.mermaid`
4. 安装代码块一键复制按钮插件：`pip install sphinx_copybutton`
5. 可以使用vscode 编辑markdown文件文档，推荐安装markdown预览编辑插件
