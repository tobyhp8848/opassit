"""用户软删除与已删除列表测试"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse

from .models import UserProfile

User = get_user_model()


class UserSoftDeleteTestCase(TestCase):
    """软删除、已删除列表、恢复功能测试"""

    def setUp(self):
        self.admin = User.objects.create_superuser("admin", "admin@test.com", "admin123")
        self.staff = User.objects.create_user("staff", "staff@test.com", "staff123", is_staff=True)
        self.normal = User.objects.create_user("normal", "normal@test.com", "normal123")
        self.client = Client()
        self.client.login(username="admin", password="admin123")

    def test_soft_delete_writes_deleted_at(self):
        """软删除后 profile.deleted_at 应被正确设置"""
        url = reverse("accounts:user_delete", kwargs={"pk": self.normal.pk})
        resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)

        self.normal.refresh_from_db()
        profile = UserProfile.objects.get(user=self.normal)
        self.assertIsNotNone(profile.deleted_at)
        self.assertEqual(profile.deleted_by_id, self.admin.pk)
        self.assertFalse(self.normal.is_active)

    def test_deleted_user_appears_in_deleted_list(self):
        """软删除后用户应出现在已删除用户列表"""
        url_delete = reverse("accounts:user_delete", kwargs={"pk": self.normal.pk})
        self.client.post(url_delete, follow=True)

        url_deleted = reverse("accounts:user_deleted_list")
        resp = self.client.get(url_deleted)
        self.assertEqual(resp.status_code, 200)

        users = list(resp.context["users"])
        usernames = [u.username for u in users]
        self.assertIn("normal", usernames)

    def test_deleted_user_excluded_from_main_list(self):
        """软删除后用户不应出现在主用户列表"""
        url_delete = reverse("accounts:user_delete", kwargs={"pk": self.normal.pk})
        self.client.post(url_delete, follow=True)

        url_list = reverse("accounts:user_list")
        resp = self.client.get(url_list)
        self.assertEqual(resp.status_code, 200)

        users = list(resp.context["users"])
        usernames = [u.username for u in users]
        self.assertNotIn("normal", usernames)

    def test_restore_clears_deleted_at(self):
        """恢复后 deleted_at 应被清除，用户回到主列表"""
        # 先软删除
        profile, _ = UserProfile.objects.get_or_create(
            user=self.normal, defaults={"organization": None}
        )
        profile.deleted_at = timezone.now()
        profile.deleted_by = self.admin
        profile.save()
        self.normal.is_active = False
        self.normal.save()

        url_restore = reverse("accounts:user_restore", kwargs={"pk": self.normal.pk})
        resp = self.client.post(url_restore, follow=True)
        self.assertEqual(resp.status_code, 200)

        self.normal.refresh_from_db()
        profile.refresh_from_db()
        self.assertIsNone(profile.deleted_at)
        self.assertIsNone(profile.deleted_by_id)
        self.assertTrue(self.normal.is_active)

    def test_user_without_profile_can_be_soft_deleted(self):
        """无 profile 的用户软删除时应创建 profile 并设置 deleted_at"""
        user_no_profile = User.objects.create_user("noprofile", "np@test.com", "np123")
        self.assertFalse(UserProfile.objects.filter(user=user_no_profile).exists())

        url = reverse("accounts:user_delete", kwargs={"pk": user_no_profile.pk})
        resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)

        profile = UserProfile.objects.get(user=user_no_profile)
        self.assertIsNotNone(profile.deleted_at)
