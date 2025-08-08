# 多模态数据分析能力示例程序

本目录包含了对话式CRM系统多模态数据分析功能的完整示例程序，展示了如何使用语音识别、行为分析、高价值客户识别和数据融合等核心功能。

## 📁 示例文件说明

### 🚀 快速开始
- **`quick_start_multimodal.py`** - 最简单的多模态分析示例，适合快速了解基本功能

### 🎯 完整演示
- **`multimodal_analysis_demo.py`** - 完整的多模态数据分析演示，包含所有核心功能

### 🎤 专项功能演示
- **`speech_analysis_example.py`** - 语音识别和分析专项演示
- **`behavior_analysis_example.py`** - 客户行为分析专项演示

## 🏃‍♂️ 运行方式

### 环境准备
确保已安装项目依赖：
```bash
# 使用uv安装依赖
uv sync

# 或使用pip安装
pip install -r requirements.txt
```

### 运行示例

#### 1. 快速开始示例
```bash
# 最简单的入门示例
python examples/quick_start_multimodal.py
```

#### 2. 完整功能演示
```bash
# 运行完整的多模态分析演示
python examples/multimodal_analysis_demo.py
```

#### 3. 语音分析专项演示
```bash
# 语音识别和分析功能演示
python examples/speech_analysis_example.py
```

#### 4. 行为分析专项演示
```bash
# 客户行为分析功能演示
python examples/behavior_analysis_example.py
```

## 🎯 功能演示内容

### 🎤 语音识别和文本转换
- ✅ 单个音频文件处理
- ✅ 批量音频文件处理
- ✅ 多语言支持 (中文、英文、日文等)
- ✅ 音频质量验证
- ✅ 情感和意图识别
- ✅ 错误处理机制

### 📊 客户行为数据分析
- ✅ 多维度行为指标分析
- ✅ 客户行为画像生成
- ✅ 访问模式识别
- ✅ 转化路径分析
- ✅ 异常行为检测
- ✅ 时间窗口对比分析

### 🏆 高价值客户识别
- ✅ 多模态价值评分算法
- ✅ 客户价值指标计算
- ✅ 风险因素识别
- ✅ 机会点发现
- ✅ 智能推荐生成

### 🔄 多模态数据融合
- ✅ 跨模态数据整合
- ✅ 特征融合算法
- ✅ 置信度评估
- ✅ 异常检测
- ✅ 端到端分析管道

### ⚡ 性能和扩展性
- ✅ 批量处理能力
- ✅ 并发分析支持
- ✅ 性能基准测试
- ✅ 错误恢复机制

## 📋 示例输出说明

### 语音分析输出示例
```
🎤 单个音频分析示例
------------------------------
📝 转录文本: 我们公司正在寻找一个CRM系统，能否介绍一下你们的解决方案？
🎯 置信度: 92.00%
😊 情感分析: positive
🎭 情绪识别: interested
🗣️  语速: 125.3 词/分钟
⏸️  停顿频率: 0.12
🔊 语音质量:
     clarity: 0.88
     volume: 0.75
     pitch_stability: 0.82
🔑 关键词: CRM, 系统, 解决方案, 介绍
💡 意图识别: product_inquiry
```

### 行为分析输出示例
```
📊 基础客户行为分析示例
----------------------------------------
👤 客户ID: behavior_demo_001
📅 数据时间跨度: 21天
📊 会话数量: 15

📈 参与度指标:
   平均参与度评分: 0.78
   总页面浏览量: 89
   总点击次数: 45
   平均会话时长: 245.3 秒
   跳出率: 23.5%

👤 客户行为画像:
   客户类型: high_value
   综合评分: 0.85
   参与水平: high
   数字化成熟度: advanced
```

### 高价值客户识别输出示例
```
🏆 高价值客户识别结果
🎯 识别出 2 个高价值客户

🏆 高价值客户 #1
   客户ID: customer_001
   综合评分: 0.89
   预测价值: 0.92
   🎯 主要推荐行动:
      1. 立即分配顶级销售代表
      2. 安排高管层面会议
      3. 提供定制化解决方案演示
```

## 🔧 自定义和扩展

### 修改分析参数
```python
# 在代码中修改分析请求参数
request = MultimodalAnalysisRequest(
    customer_id="your_customer_id",
    analysis_type="high_value_identification",  # 可选: behavior_pattern_analysis, sentiment_analysis
    modalities=[
        DataModalityType.TEXT,
        DataModalityType.VOICE,
        DataModalityType.BEHAVIOR
    ],
    time_range={
        'start': datetime.now() - timedelta(days=30),  # 修改时间范围
        'end': datetime.now()
    },
    parameters={'detailed_analysis': True}  # 添加自定义参数
)
```

### 添加自定义数据
```python
# 创建自定义行为数据
custom_behavior = BehaviorData(
    customer_id="custom_customer",
    session_id="custom_session",
    page_views=[
        {"url": "/your-page", "timestamp": datetime.now(), "duration": 120}
    ],
    click_events=[
        {"element": "your_button", "timestamp": datetime.now()}
    ],
    time_spent={"/your-page": 120.0},
    interaction_patterns={"custom_metric": 0.8},
    engagement_score=0.75,
    conversion_indicators=["custom_conversion"],
    timestamp=datetime.now()
)
```

## 🐛 故障排除

### 常见问题

1. **ImportError: No module named 'src'**
   ```bash
   # 确保从项目根目录运行
   cd /path/to/hicrm
   python examples/quick_start_multimodal.py
   ```

2. **依赖缺失错误**
   ```bash
   # 重新安装依赖
   uv sync
   # 或
   pip install numpy pydantic
   ```

3. **异步运行错误**
   ```python
   # 确保使用 asyncio.run()
   if __name__ == "__main__":
       asyncio.run(main())
   ```

### 调试模式
在示例代码中添加调试信息：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 相关文档

- [多模态数据分析设计文档](../.kiro/specs/conversational-crm/design.md)
- [API接口文档](../docs/api.md)
- [测试文档](../tests/test_multimodal_analysis.py)

## 🤝 贡献

欢迎提交改进建议和新的示例程序！请确保：
1. 代码风格一致
2. 添加适当的注释和文档
3. 包含错误处理
4. 提供清晰的输出说明

## 📄 许可证

本示例程序遵循项目的MIT许可证。