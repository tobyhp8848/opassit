"""插入 50 条模拟自动化任务"""
import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.organizations.models import Organization
from apps.automation.models import AutomationTask
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

TASK_NAMES = [
    "每日销售数据同步",
    "库存预警检查",
    "客户订单自动处理",
    "报表定时生成",
    "邮件批量发送",
    "网站数据抓取",
    "API 健康检查",
    "日志归档任务",
    "数据库备份",
    "用户行为分析",
    "价格监控爬虫",
    "竞品信息采集",
    "新闻资讯聚合",
    "工单自动分配",
    "审批流程触发",
    "合同到期提醒",
    "续费到期通知",
    "数据导出任务",
    "同步第三方系统",
    "定时清理临时文件",
    "月度汇总统计",
    "周报自动生成",
    "考勤数据同步",
    "财务对账任务",
    "库存盘点提醒",
    "促销活动预热",
    "会员积分计算",
    "消息推送任务",
    "数据质量校验",
    "敏感词过滤检查",
    "图片压缩处理",
    "文档转换任务",
    "数据脱敏处理",
    "缓存预热任务",
    "会话清理任务",
    "过期订单关闭",
    "优惠券过期处理",
    "积分过期提醒",
    "黑名单同步",
    "白名单更新",
    "规则引擎执行",
    "埋点数据上报",
    "A/B 测试统计",
    "转化漏斗分析",
    "用户画像更新",
    "推荐算法训练",
    "模型定时预测",
    "告警规则检测",
    "资源使用监控",
]


class Command(BaseCommand):
    help = "插入 50 条模拟自动化任务"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=50,
            help="插入任务数量（默认 50）",
        )

    def handle(self, *args, **options):
        count = options["count"]
        user = User.objects.filter(is_staff=True).first()
        orgs = list(Organization.objects.filter(is_active=True)[:10])
        task_types = [c[0] for c in AutomationTask.TaskType.choices]
        statuses = [c[0] for c in AutomationTask.Status.choices]
        config_samples = [
            {},
            {"cron": "0 9 * * *", "target": "https://example.com"},
            {"cron": "0 */2 * * *", "retry": 3},
            {"url": "https://api.example.com/sync", "method": "POST"},
            {"steps": ["fetch", "parse", "save"], "timeout": 300},
        ]

        created = 0
        used_names = set()
        for i in range(count):
            base_name = TASK_NAMES[i % len(TASK_NAMES)]
            name = f"{base_name}_{i + 1}" if base_name in used_names else base_name
            used_names.add(base_name)
            if f"{base_name}_{i + 1}" == name:
                used_names.add(name)

            org = random.choice(orgs) if orgs else None
            task_type = random.choice(task_types)
            status = random.choice(statuses)
            config = random.choice(config_samples)
            last_run = None
            if status in ("active", "error") and random.random() > 0.3:
                last_run = timezone.now() - timedelta(hours=random.randint(1, 72))

            AutomationTask.objects.create(
                name=name,
                task_type=task_type,
                organization=org,
                status=status,
                config=config,
                created_by=user,
                last_run_at=last_run,
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f"成功插入 {created} 条模拟任务"))
