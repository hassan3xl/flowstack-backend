# workspace/services.py
from django.db import transaction
from .models import Task, ActivityLog, Project, ProjectMember, WorkspaceMember, Comment
from notifications.notification_services import NotificationService
from django.utils import timezone


def create_project_service(user, workspace, project_data):
    with transaction.atomic():
        # 1. Create the Project
        project = Project.objects.create(
            created_by=user,
            workspace=workspace,
            **project_data
        )

        # 2. Add the Creator as the first Member (Write Access)
        ProjectMember.objects.create(
            project=project,
            user=user,
            permission='write'
        )

        # 3. Log Activity
        ActivityLog.objects.create(
            workspace=workspace,
            actor=user,
            action_type='create_project',
            target_id=project.id,
            target_text=project.title
        )

        # 4. Notify All Workspace Members (If configured to do so)
        # Usually, we only notify everyone if the project is PUBLIC.
        if project.visibility == 'public':
            # Get all user objects in this workspace (excluding the creator)
            members = WorkspaceMember.objects.filter(
                workspace=workspace
            ).exclude(user=user).select_related('user')
            
            recipients = [m.user for m in members]

            NotificationService.send_bulk_notification(
                recipients=recipients,
                actor=user,
                title="New Project Created",
                message=f"{user.profile.username} created a new project: {project.title}",
                target_obj=project,
                category='system_alert' 
            )

        return project
    
def start_task_service(user, task):
    """
    Moves task to IN_PROGRESS, sets started_by, logs activity.
    """
    with transaction.atomic():
        # 1. Update Task
        task.status = 'in_progress' # or Task.StatusChoices.IN_PROGRESS
        task.started_by = user
        task.save()

        # 2. Log Activity
        ActivityLog.objects.create(
            workspace=task.project.workspace,
            actor=user,
            action_type='start_task',
            target_id=task.id,
            target_text=task.title
        )
        
        # 3. Notification (Optional: Notify Creator if different from Starter)
        if task.created_by and task.created_by != user:
             NotificationService.send_notification(
                recipient=task.created_by,
                actor=user,
                title="Task Started",
                message=f"{user.profile.username} started working on {task.title}",
                target_obj=task,
                category='task_updated'
            )
            
    return task

def complete_task_service(user, task):
    """
    Moves task to COMPLETED, sets timestamp, logs activity, notifies creator.
    """
    with transaction.atomic():
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.save()

        ActivityLog.objects.create(
            workspace=task.project.workspace,
            actor=user,
            action_type='complete_task',
            target_id=task.id,
            target_text=task.title
        )

        # Notify Creator (if it wasn't them)
        if task.created_by and task.created_by != user:
            NotificationService.send_notification(
                recipient=task.created_by,
                actor=user,
                title="Task Completed",
                message=f"{user.profile.username} completed {task.title}",
                target_obj=task,
                category='task_completed',
                type='success'
            )
            
    return task

# --- PROJECT MEMBER SERVICES ---

def add_project_member_service(actor, project, target_user, role='read'):
    with transaction.atomic():
        # 1. Create Membership
        member = ProjectMember.objects.create(
            project=project,
            user=target_user,
            permission=role
        )

        # 2. Log Activity
        ActivityLog.objects.create(
            workspace=project.workspace,
            actor=actor,
            action_type='add_project_member',
            target_id=project.id,
            target_text=f"{target_user.profile.username} to {project.title}"
        )

        # 3. Notify the New Member
        NotificationService.send_notification(
            recipient=target_user,
            actor=actor,
            title="Added to Project",
            message=f"You have been added to the project: {project.title}",
            target_obj=project,
            category='project_invite'
        )
    return member

# --- COMMENT SERVICES ---

def create_comment_service(user, task, content):
    with transaction.atomic():
        # 1. Create Comment
        comment = Comment.objects.create(
            task=task,
            author=user,
            content=content
        )

        # 2. Log Activity
        ActivityLog.objects.create(
            workspace=task.project.workspace,
            actor=user,
            action_type='comment',
            target_id=task.id,
            target_text=f"Comment on {task.title}"
        )

        # 3. Notify Relevant People (Assignee + Creator)
        recipients = set()
        if task.assigned_to: recipients.add(task.assigned_to)
        if task.created_by: recipients.add(task.created_by)
        
        # Don't notify the person who commented
        if user in recipients: recipients.remove(user)

        if recipients:
            NotificationService.send_bulk_notification(
                recipients=list(recipients),
                actor=user,
                title="New Comment",
                message=f"{user.username} commented on {task.title}",
                target_obj=task,
                category='comment_mention'
            )
            
    return comment