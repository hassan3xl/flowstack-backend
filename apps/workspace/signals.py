# workspace/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Project, Task, ActivityLog, WorkspaceMember

@receiver(post_save, sender=Task)
def log_task_activity(sender, instance, created, **kwargs):
    if created:
        ActivityLog.objects.create(
            workspace=instance.project.workspace,
            actor=instance.created_by,
            action_type='create_task',
            target_id=instance.id,
            target_text=instance.title
        )
    elif instance.status == 'completed' and instance.completed_at:
        # Avoid duplicate logs if saved multiple times
        ActivityLog.objects.create(
            workspace=instance.project.workspace,
            actor=instance.assigned_to or instance.created_by, # Fallback
            action_type='complete_task',
            target_id=instance.id,
            target_text=instance.title
        )

@receiver(post_save, sender=Project)
def log_project_creation(sender, instance, created, **kwargs):
    if created:
        ActivityLog.objects.create(
            workspace=instance.workspace,
            actor=instance.created_by,
            action_type='create_project',
            target_id=instance.id,
            target_text=instance.title
        )