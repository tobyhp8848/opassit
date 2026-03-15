# 工作审批流程序推荐

> 本文档记录适合 OPASSIT 企业运营与自动化工作平台的免费、口碑好的工作审批流/工作流程序，便于日后查阅与选型。
> 创建时间：2025 年 3 月

---

## 一、与 Django/Python 集成度高的（优先考虑）

| 方案 | 说明 | 特点 |
|------|------|------|
| **django-approval-workflow** | PyPI 包，生产可用 | 多级审批、角色/策略（ANYONE/CONSENSUS/ROUND_ROBIN）、Approve/Reject/Delegate/Escalate，Django Admin 集成、REST API，易于嵌入现有项目 |
| **django-dynamic-workflows** | PyPI 包 | 可与 django-approval-workflow 联动，支持 Stage/Pipeline，可配置触发和邮件 |
| **django-forms-workflows** | PyPI 包 | 表单 + 审批流程（any/all/sequence），支持子流程、审计、文件上传，偏企业级表单审批 |

---

## 二、国产、中文场景友好的

| 方案 | 说明 | 特点 |
|------|------|------|
| **FlowLong 飞龙工作流** | GitHub 开源 | JSON 模型、国产、仿飞书/钉钉审批，支持加签、驳回、撤销、沟通等，轻量（核心约 8 张表），Apache-2.0 |
| **AntFlow-Activiti** | Gitee 开源 | 仿钉钉，Spring Boot + Vue3，可视化设计器，可独立或嵌入业务系统，流程与业务分离 |

---

## 三、通用开源工作流 / BPM 引擎（偏技术集成）

| 方案 | 说明 | 特点 |
|------|------|------|
| **Flowable** | 知名 BPM 引擎 | BPMN 2.0，社区活跃，Spring Boot 生态好，适合较复杂流程和案例管理 |
| **Camunda 7** | 主流 BPM | BPMN 2.0，REST API 丰富，注意：计划 2025 年 EOL，新项目需评估 |
| **Activiti** | 经典引擎 | 轻量、易上手，适合简单流程，后续演进和社区相对较弱 |

---

## 四、轻量级、审批专用

| 方案 | 说明 | 特点 |
|------|------|------|
| **click2approve** | 文档审批系统 | 轻量、专注文档审批、响应式 UI、邮件通知，可自托管 |
| **flowctl** | 工作流 + 审批 | 审批门控、YAML 配置、团队权限、支持 OIDC SSO |
| **Wexflow** | 工作流引擎 | MIT 许可，100+ 内置活动，支持审批类流程，偏自动化任务编排 |

---

## 五、自动化平台 + 审批能力

| 方案 | 说明 | 特点 |
|------|------|------|
| **n8n** | 工作流自动化 | 自托管免费、节点式设计、有审批节点，偏自动化集成而非纯审批系统 |

---

## 综合推荐（结合 OPASSIT 现有 Django 技术栈）

1. **django-approval-workflow**：最易嵌入当前 Django 项目，可逐步替代或增强现有审批逻辑。
2. **FlowLong 飞龙工作流**：若希望统一采用国产、仿钉钉/飞书的审批体验，可作为独立模块或与现有流程协作。
3. **Flowable**：若未来流程会变复杂、需要 BPMN 标准或外部系统集成，可作为独立引擎通过 API 与 OPASSIT 对接。

---

## 参考链接

- [django-approval-workflow (PyPI)](https://pypi.org/project/django-approval-workflow/)
- [FlowLong 飞龙工作流](https://github.com/aizuda/flowlong) | [文档](https://doc.flowlong.com/)
- [Flowable](https://www.flowable.com/)
- [click2approve](https://github.com/luarvic/click2approve)
- [Wexflow](https://wexflow.github.io/)
- [n8n](https://n8n.io/)
