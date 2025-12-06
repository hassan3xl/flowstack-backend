# # serializers.py
# from rest_framework import serializers
# from ..users.serializers import CustomUserSerializer
# from project_manager.models import Project, ProjectItem, SharedListAccess, Comment
# from django.utils import timezone
# import uuid
# from user_manager.models import UserProfile, CustomUser




# class SharedListAccessSerializer(serializers.ModelSerializer):
#     user_email = serializers.EmailField(source='user.email', read_only=True)
#     shared_by_email = serializers.EmailField(source='shared_by.email', read_only=True)
#     project_title = serializers.CharField(source='project.title', read_only=True)
    
#     class Meta:
#         model = SharedListAccess
#         fields = '__all__'
#         read_only_fields = ('id', 'shared_by', 'created_at')


# class UserProfileSerializer(serializers.ModelSerializer):
#     role = serializers.CharField(read_only=True)
#     fullname = serializers.SerializerMethodField()
#     email = serializers.SerializerMethodField()

#     class Meta:
#         model = UserProfile
#         fields = ["id", "avatar", "user", "role", "fullname", "email"]
#         read_only_fields = ('user', 'created_at', 'updated_at')

#     def get_fullname(self, obj):
#         return f"{obj.first_name} {obj.last_name}".strip()
    
#     def get_email(self, obj):
#         return obj.user.email if obj.user else None




# class ProjectItemSerializer(serializers.ModelSerializer):
#     is_overdue = serializers.SerializerMethodField()
#     started_by = CustomUserSerializer(read_only=True)
#     comments = CommentSerializer(many=True, read_only=True)  # Fix: add many=True and correct usage
    
#     class Meta:
#         model = ProjectItem
#         fields = '__all__'
#         read_only_fields = (
#             'id', 'created_at', 'updated_at', "project", 
#             'completed_at', 'started_by'
#         )
            
#     def get_is_overdue(self, obj):
#         if obj.due_date and obj.status != ProjectItem.StatusChoices.COMPLETED:
#             return obj.due_date < timezone.now()
#         return False


# class ProjectSerializer(serializers.ModelSerializer):
#     project_items = ProjectItemSerializer(many=True, read_only=True)
#     item_count = serializers.SerializerMethodField()
#     completed_count = serializers.SerializerMethodField()
#     owner_email = serializers.EmailField(source="owner.email", read_only=True)
#     is_shared = serializers.SerializerMethodField()
#     shared_users = serializers.SerializerMethodField()  # NEW

#     class Meta:
#         model = Project
#         fields = "__all__"
#         read_only_fields = ("id", "owner", "created_at", "updated_at")

#     def get_item_count(self, obj):
#         return obj.project_items.count()

#     def get_completed_count(self, obj):
#         return obj.project_items.filter(status=ProjectItem.StatusChoices.COMPLETED).count()

#     def get_is_shared(self, obj):
#         request = self.context.get("request")
#         if request and request.user:
#             return obj.owner != request.user
#         return False

#     def get_shared_users(self, obj):
#         shared_accesses = obj.shared_access.all().select_related("user__profile")
#         users_data = []
#         for access in shared_accesses:
#             profile_serializer = UserProfileSerializer(access.user.profile, context=self.context)
#             data = profile_serializer.data
#             data["role"] = access.access_level
#             data["user_id"] = access.user.id  # Add user ID explicitly
#             users_data.append(data)
#         return users_data



# class ProjectSettingsSerializer(serializers.ModelSerializer):
#     project_items = ProjectItemSerializer(many=True, read_only=True)
#     item_count = serializers.SerializerMethodField()
#     completed_count = serializers.SerializerMethodField()
#     owner_email = serializers.EmailField(source="owner.email", read_only=True)
#     is_shared = serializers.SerializerMethodField()
#     shared_users = serializers.SerializerMethodField()
#     shared_list = SharedListAccessSerializer(many=True, source="shared_access", read_only=True)

#     class Meta:
#         model = Project
#         fields = ["title", "description", "visibility", "created_at", "id", "shared_list", "project_items", "item_count", "completed_count", "owner_email", "is_shared", "shared_users", ]
#         read_only_fields = ("id", "owner", "created_at", "updated_at")

#     def get_item_count(self, obj):
#         return obj.project_items.count()

#     def get_completed_count(self, obj):
#         return obj.project_items.filter(status=ProjectItem.StatusChoices.COMPLETED).count()

#     def get_is_shared(self, obj):
#         request = self.context.get("request")
#         if request and request.user:
#             return obj.owner != request.user
#         return False

#     def get_shared_users(self, obj):
#         shared_accesses = obj.shared_access.all().select_related("user__profile")
#         users_data = []
#         for access in shared_accesses:
#             profile_serializer = UserProfileSerializer(access.user.profile, context=self.context)
#             data = profile_serializer.data
#             data["role"] = access.access_level
#             data["user_id"] = access.user.id
#             users_data.append(data)
#         return users_data



# class ProjectArchiveSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Project
#         fields = ["id", "title", "is_archived"]
#         read_only_fields = ["id", "title"]




