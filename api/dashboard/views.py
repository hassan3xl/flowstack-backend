from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q, Case, When, IntegerField
from django.utils import timezone
from datetime import timedelta

from core.models import CustomUser, UserProfile, Project, ProjectItem, SharedListAccess, UserSettings

class UserDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get comprehensive dashboard data for the authenticated user
        """
        user = request.user
        
        try:
            # 1. User Profile Information
            profile_data = self._get_user_profile(user)
            
            # 2. Project Statistics
            project_stats = self._get_project_stats(user)
            
            # 3. Recent Projects
            recent_projects = self._get_recent_projects(user)
            
            # 4. Upcoming Tasks
            upcoming_tasks = self._get_upcoming_tasks(user)
            
            # 5. Shared Projects
            shared_projects = self._get_shared_projects(user)
            
            # 6. Quick Statistics
            quick_stats = self._get_quick_stats(user)
            
            # 7. User Settings
            user_settings = self._get_user_settings(user)
            
            dashboard_data = {
                "user": profile_data,
                "statistics": project_stats,
                "recent_projects": recent_projects,
                "upcoming_tasks": upcoming_tasks,
                "shared_projects": shared_projects,
                "quick_stats": quick_stats,
                "settings": user_settings,
            }
            
            return Response(dashboard_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Error fetching dashboard data: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_user_profile(self, user):
        """Get user profile information"""
        try:
            profile = UserProfile.objects.get(user=user)
            return {
                "id": str(user.id),
                "email": user.email,
                "first_name": profile.first_name,
                "last_name": profile.last_name,
                "full_name": profile.get_full_name(),
                "bio": profile.bio,
                "avatar": profile.avatar.url if profile.avatar else None,
                "phone_number": profile.phone_number,
                "email_notifications": profile.email_notifications,
                "member_since": user.created_at.strftime("%Y-%m-%d"),
            }
        except UserProfile.DoesNotExist:
            # Return basic user info if profile doesn't exist
            return {
                "id": str(user.id),
                "email": user.email,
                "first_name": "",
                "last_name": "",
                "full_name": "",
                "bio": "",
                "avatar": None,
                "phone_number": "",
                "email_notifications": True,
                "member_since": user.created_at.strftime("%Y-%m-%d"),
            }
    
    def _get_project_stats(self, user):
        """Get project statistics for the user"""
        # User's own projects
        user_projects = Project.objects.filter(owner=user, is_archived=False)
        
        # Total projects count
        total_projects = user_projects.count()
        
        # Projects by visibility
        visibility_stats = user_projects.values('visibility').annotate(count=Count('id'))
        
        # Project items statistics
        project_items = ProjectItem.objects.filter(project__owner=user)
        
        # Items by status
        status_stats = project_items.values('status').annotate(count=Count('id'))
        
        # Items by priority
        priority_stats = project_items.values('priority').annotate(count=Count('id'))
        
        return {
            "total_projects": total_projects,
            "visibility_distribution": {item['visibility']: item['count'] for item in visibility_stats},
            "items_by_status": {item['status']: item['count'] for item in status_stats},
            "items_by_priority": {item['priority']: item['count'] for item in priority_stats},
        }
    
    def _get_recent_projects(self, user, limit=5):
        """Get recent projects with basic item counts"""
        recent_projects = Project.objects.filter(
            owner=user, 
            is_archived=False
        ).order_by('-updated_at')[:limit]
        
        projects_data = []
        for project in recent_projects:
            # Get item counts for each project
            total_items = project.project_items.count()
            completed_items = project.project_items.filter(status='completed').count()
            pending_items = total_items - completed_items
            
            projects_data.append({
                "id": str(project.id),
                "title": project.title,
                "description": project.description,
                "visibility": project.visibility,
                "total_items": total_items,
                "completed_items": completed_items,
                "pending_items": pending_items,
                "completion_rate": (completed_items / total_items * 100) if total_items > 0 else 0,
                "last_updated": project.updated_at,
            })
        
        return projects_data
    
    def _get_upcoming_tasks(self, user, limit=10):
        """Get upcoming tasks across all projects"""
        # Get tasks from user's own projects and shared projects
        shared_projects = SharedListAccess.objects.filter(user=user).values_list('project_id', flat=True)
        
        upcoming_tasks = ProjectItem.objects.filter(
            Q(project__owner=user) | Q(project_id__in=shared_projects),
            status__in=['pending', 'in_progress'],
            due_date__gte=timezone.now()
        ).select_related('project').order_by('due_date')[:limit]
        
        tasks_data = []
        for task in upcoming_tasks:
            tasks_data.append({
                "id": str(task.id),
                "title": task.title,
                "description": task.description,
                "due_date": task.due_date,
                "priority": task.priority,
                "status": task.status,
                "project_id": str(task.project.id),
                "project_title": task.project.title,
                "is_overdue": task.due_date < timezone.now() if task.due_date else False,
                "days_until_due": (task.due_date - timezone.now()).days if task.due_date else None,
            })
        
        return tasks_data
    
    def _get_shared_projects(self, user):
        """Get projects shared with the user"""
        shared_access = SharedListAccess.objects.filter(user=user).select_related('project', 'shared_by')
        
        shared_projects_data = []
        for access in shared_access:
            project = access.project
            total_items = project.project_items.count()
            completed_items = project.project_items.filter(status='completed').count()
            
            shared_projects_data.append({
                "project_id": str(project.id),
                "title": project.title,
                "description": project.description,
                "owner_email": project.owner.email,
                "shared_by_email": access.shared_by.email,
                "access_level": access.access_level,
                "shared_since": access.created_at,
                "total_items": total_items,
                "completed_items": completed_items,
                "visibility": project.visibility,
            })
        
        return shared_projects_data
    
    def _get_quick_stats(self, user):
        """Get quick overview statistics"""
        # User's projects and items
        user_projects = Project.objects.filter(owner=user, is_archived=False)
        user_items = ProjectItem.objects.filter(project__owner=user)
        
        # Shared projects
        shared_projects_count = SharedListAccess.objects.filter(user=user).count()
        
        # Today's tasks
        today = timezone.now().date()
        tomorrow = today + timedelta(days=1)
        todays_tasks = user_items.filter(
            due_date__date=today,
            status__in=['pending', 'in_progress']
        ).count()
        
        # Overdue tasks
        overdue_tasks = user_items.filter(
            due_date__lt=timezone.now(),
            status__in=['pending', 'in_progress']
        ).count()
        
        # Completed this week
        week_ago = timezone.now() - timedelta(days=7)
        weekly_completed = user_items.filter(
            completed_at__gte=week_ago,
            status='completed'
        ).count()
        
        return {
            "total_projects": user_projects.count(),
            "total_tasks": user_items.count(),
            "shared_projects_count": shared_projects_count,
            "todays_tasks": todays_tasks,
            "overdue_tasks": overdue_tasks,
            "completed_this_week": weekly_completed,
            "in_progress_tasks": user_items.filter(status='in_progress').count(),
        }
    
    def _get_user_settings(self, user):
        """Get user settings"""
        try:
            settings = UserSettings.objects.get(user=user)
            return {
                "theme": settings.theme,
                "language": settings.language,
                "items_per_page": settings.items_per_page,
                "default_due_date_days": settings.default_due_date_days,
                "enable_email_notifications": settings.enable_email_notifications,
                "enable_push_notifications": settings.enable_push_notifications,
                "auto_archive_completed": settings.auto_archive_completed,
            }
        except UserSettings.DoesNotExist:
            # Return default settings if not set
            return {
                "theme": "light",
                "language": "en",
                "items_per_page": 10,
                "default_due_date_days": 7,
                "enable_email_notifications": True,
                "enable_push_notifications": True,
                "auto_archive_completed": True,
            }