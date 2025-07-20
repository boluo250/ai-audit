# Mermaid 输出目录

这个目录用于存储智能合约业务流程分析生成的 Mermaid 图表文件。

## 📁 目录结构

```
src/codebaseQA/mermaid_output/
├── {project_id_1}/
│   ├── {project_id_1}_business_flow.mmd
│   ├── {project_id_1}_folder1.mmd
│   └── {project_id_1}_global_overview.mmd
├── {project_id_2}/
│   └── {project_id_2}_business_flow.mmd
└── README.md (本文件)
```

## 🎯 文件命名规则

### 小项目（增量分析）
- `{project_id}_business_flow.mmd` - 完整的业务流程图

### 大项目（文件夹级别分析）
- `{project_id}_{folder_name}.mmd` - 文件夹级别的业务流程图
- `{project_id}_global_overview.mmd` - 项目全局概览图

## 🔄 文件生成逻辑

1. **首次运行**：系统会生成新的 Mermaid 文件并保存到对应项目目录
2. **重复运行**：系统会检查是否已存在 Mermaid 文件
   - 如果存在：跳过生成，直接使用现有文件
   - 如果不存在：重新生成

## 📊 文件用途

这些 Mermaid 文件用于：

1. **业务流程提取**：Planning 模块从这些文件中提取业务流程
2. **函数匹配**：将业务流程中的步骤匹配到实际的函数
3. **上下文扩展**：为业务流程添加相关的函数上下文
4. **任务创建**：基于扩展后的业务流程创建分析任务

## 🛠️ 相关代码文件

- `src/main.py` - 负责生成和保存 Mermaid 文件
- `src/planning/business_flow_utils.py` - 负责读取和解析 Mermaid 文件
- `src/planning/planning_processor.py` - 负责从 Mermaid 文件提取业务流程
- `src/code_summarizer/` - 负责生成 Mermaid 业务流程图

## 📝 使用示例

```python
# 在 main.py 中生成
output_dir = f"src/codebaseQA/mermaid_output/{project.id}"
mermaid_file = f"{output_dir}/{project.id}_business_flow.mmd"

# 在 planning 模块中读取
mermaid_contents = BusinessFlowUtils.load_mermaid_files(
    project.mermaid_output_dir, 
    project.project_id
)
```

## 🔧 维护说明

- 如果需要重新生成 Mermaid 文件，请删除对应的项目目录
- 文件采用 UTF-8 编码
- 建议定期清理不需要的项目目录以节省空间

---

**注意**：这个目录结构替代了之前的 `./output/{project_id}/` 结构，提供了更好的组织和管理。 