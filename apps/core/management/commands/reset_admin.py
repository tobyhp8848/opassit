"""
重置超级管理员用户名和密码
用法:
  python manage.py reset_admin
  python manage.py reset_admin --username admin --password MyNewPass123
  python manage.py reset_admin --new-username admin --password Admin123!
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "重置超级管理员用户名和密码，确保 is_staff、is_superuser、is_active 为 True"

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            type=str,
            default=None,
            help="要重置的现有用户名，不指定则重置第一个超级管理员",
        )
        parser.add_argument(
            "--new-username",
            type=str,
            default=None,
            help="新的用户名（可选，用于修改用户名）",
        )
        parser.add_argument(
            "--password",
            type=str,
            default="Admin123!",
            help="新密码，默认 Admin123!",
        )

    def handle(self, *args, **options):
        User = get_user_model()
        username = options["username"]
        new_username = options["new_username"]
        new_password = options["password"]

        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"用户 '{username}' 不存在"))
                return
        else:
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                user = User.objects.filter(is_staff=True).first()
            if not user:
                self.stderr.write(
                    self.style.ERROR("未找到管理员用户，请先运行: python manage.py createsuperuser")
                )
                return
            username = user.username

        if new_username and new_username != username:
            if User.objects.filter(username=new_username).exclude(pk=user.pk).exists():
                self.stderr.write(self.style.ERROR(f"用户名 '{new_username}' 已被占用"))
                return
            user.username = new_username
            username = new_username

        user.set_password(new_password)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()

        self.stdout.write(self.style.SUCCESS(f"已将超级管理员重置"))
        self.stdout.write(f"用户名: {username}")
        self.stdout.write(f"密码: {new_password}")
        self.stdout.write("请登录后尽快修改密码")
