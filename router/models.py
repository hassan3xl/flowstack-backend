# from django.db import models
# import uuid
# from core.models import CustomUser

# # Create your models here.


# class ActivityLog(models.Model):
#     class ActionChoices(models.TextChoices):
#         CREATE = "create", "Create"
#         UPDATE = "update", "Update"
#         DELETE = "delete", "Delete"
#         COMPLETE = "complete", "Complete"
#         SHARE = "share", "Share"
#         ARCHIVE = "archive", "Archive"

#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     user = models.ForeignKey(
#         CustomUser, on_delete=models.CASCADE, related_name="activities"
#     )
#     action = models.CharField(max_length=10, choices=ActionChoices.choices)
#     resource_type = models.CharField(max_length=50)  # 'todo_list', 'todo_item', etc.
#     resource_id = models.UUIDField()
#     description = models.TextField()
#     ip_address = models.GenericIPAddressField(blank=True, null=True)
#     user_agent = models.TextField(blank=True)

#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         db_table = "activity_logs"
#         ordering = ["-created_at"]

#     def __str__(self):
#         return f"{self.user.email} - {self.action} - {self.resource_type}"