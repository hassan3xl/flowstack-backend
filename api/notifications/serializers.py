# # serializers.py
from rest_framework import serializers
from api.users.serializers import UserProfileSerializer
from notifications.models import Notification, NotificationTemplate, UserNotificationPreference, NotificationChannel, NotificationPriority

class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'name', 'subject', 'message', 'html_message', 
            'channels', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class NotificationListSerializer(serializers.ModelSerializer):
    # user = UserProfileSerializer(read_only=True)
    template = NotificationTemplateSerializer(read_only=True)
    
    # Computed fields
    channels_list = serializers.SerializerMethodField()
    time_since = serializers.SerializerMethodField()
    is_urgent = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'template', 'title', 'message', 'html_message',
            'channels', 'channels_list', 'priority', 'is_read', 'is_sent',
            'category', 'action_url', 'time_since', 'is_urgent',
            'created_at'
        ]
        read_only_fields = ['created_at', ]
    
    def get_channels_list(self, obj):
        """Convert comma-separated channels to list"""
        return obj.channels.split(',') if obj.channels else []
    
    def get_time_since(self, obj):
        """Human-readable time since creation"""
        from django.utils import timezone
        from django.utils.timesince import timesince
        
        if obj.created_at:
            return timesince(obj.created_at)
        return None
    
    def get_is_urgent(self, obj):
        """Check if notification is urgent"""
        return obj.priority == NotificationPriority.URGENT

# class NotificationCreateSerializer(serializers.ModelSerializer):
#     user_id = serializers.IntegerField(write_only=True)
#     template_id = serializers.IntegerField(required=False, allow_null=True)
#     channels = serializers.ListField(
#         child=serializers.ChoiceField(choices=NotificationChannel.choices),
#         default=[NotificationChannel.IN_APP]
#     )
    
#     class Meta:
#         model = Notification
#         fields = [
#             'user_id', 'template_id', 'title', 'message', 'html_message',
#             'channels', 'priority', 'category', 'action_url', 
#             , 'extra_data'
#         ]
    
#     def validate_user_id(self, value):
#         """Validate that user exists"""
#         try:
#             User.objects.get(id=value)
#         except User.DoesNotExist:
#             raise serializers.ValidationError("User does not exist")
#         return value
    
#     def validate_template_id(self, value):
#         """Validate that template exists if provided"""
#         if value is not None:
#             try:
#                 NotificationTemplate.objects.get(id=value, is_active=True)
#             except NotificationTemplate.DoesNotExist:
#                 raise serializers.ValidationError("Template does not exist or is not active")
#         return value
    
#     def validate_channels(self, value):
#         """Validate channels"""
#         if not value:
#             raise serializers.ValidationError("At least one channel is required")
#         return ','.join(value)
    
#     def create(self, validated_data):
#         """Create notification instance"""
#         user_id = validated_data.pop('user_id')
#         template_id = validated_data.pop('template_id', None)
        
#         user = User.objects.get(id=user_id)
#         template = None
#         if template_id:
#             template = NotificationTemplate.objects.get(id=template_id)
        
#         return Notification.objects.create(
#             user=user,
#             template=template,
#             **validated_data
#         )

# class NotificationUpdateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Notification
#         fields = ['is_read']
    
#     def update(self, instance, validated_data):
#         """Update notification instance"""
#         instance.is_read = validated_data.get('is_read', instance.is_read)
#         instance.save()
#         return instance

# class NotificationDetailSerializer(NotificationListSerializer):
#     """Extended serializer for detailed notification view"""
#     extra_data = serializers.SerializerMethodField()
    
#     class Meta(NotificationListSerializer.Meta):
#         fields = NotificationListSerializer.Meta.fields + ['extra_data']
    
#     def get_extra_data(self, obj):
#         """Safely return extra_data"""
#         return obj.extra_data or {}

# class BulkNotificationUpdateSerializer(serializers.Serializer):
#     """Serializer for bulk operations"""
#     notification_ids = serializers.ListField(
#         child=serializers.IntegerField(),
#         min_length=1
#     )
#     action = serializers.ChoiceField(choices=['mark_read', 'mark_unread', 'delete'])
    
#     def validate_notification_ids(self, value):
#         """Validate that all notification IDs belong to the current user"""
#         request = self.context.get('request')
#         if request and request.user:
#             valid_notifications = Notification.objects.filter(
#                 id__in=value, 
#                 user=request.user
#             ).values_list('id', flat=True)
            
#             invalid_ids = set(value) - set(valid_notifications)
#             if invalid_ids:
#                 raise serializers.ValidationError(
#                     f"Notifications not found or access denied: {invalid_ids}"
#                 )
        
#         return value

# class NotificationStatsSerializer(serializers.Serializer):
#     """Serializer for notification statistics"""
#     total = serializers.IntegerField()
#     unread = serializers.IntegerField()
#     read = serializers.IntegerField()
#     by_category = serializers.DictField(child=serializers.IntegerField())
#     by_priority = serializers.DictField(child=serializers.IntegerField())
#     recent_count = serializers.IntegerField(help_text="Notifications from last 7 days")


# # serializers.py (continued)
# class UserNotificationPreferenceSerializer(serializers.ModelSerializer):
#     user = UserProfileSerializer(read_only=True)
#     channel_status = serializers.SerializerMethodField()
    
#     class Meta:
#         model = UserNotificationPreference
#         fields = [
#             'id', 'user', 'email_enabled', 'push_enabled', 
#             'sms_enabled', 'in_app_enabled', 'preferences', 
#             'channel_status', 'updated_at'
#         ]
#         read_only_fields = ['user', 'updated_at']
    
#     def get_channel_status(self, obj):
#         """Get channel status in a structured format"""
#         return {
#             'email': obj.email_enabled,
#             'push': obj.push_enabled,
#             'sms': obj.sms_enabled,
#             'in_app': obj.in_app_enabled
#         }
    
#     def validate_preferences(self, value):
#         """Validate preferences JSON field"""
#         if not isinstance(value, dict):
#             raise serializers.ValidationError("Preferences must be a JSON object")
#         return value
    
#     def update(self, instance, validated_data):
#         """Update user preferences"""
#         # Handle category-specific preferences
#         preferences = validated_data.get('preferences', {})
#         if preferences:
#             # Merge with existing preferences
#             current_preferences = instance.preferences or {}
#             current_preferences.update(preferences)
#             instance.preferences = current_preferences
        
#         # Update channel preferences
#         instance.email_enabled = validated_data.get('email_enabled', instance.email_enabled)
#         instance.push_enabled = validated_data.get('push_enabled', instance.push_enabled)
#         instance.sms_enabled = validated_data.get('sms_enabled', instance.sms_enabled)
#         instance.in_app_enabled = validated_data.get('in_app_enabled', instance.in_app_enabled)
        
#         instance.save()
#         return instance

# class UserNotificationPreferenceCreateSerializer(serializers.ModelSerializer):
#     user_id = serializers.IntegerField(write_only=True)
    
#     class Meta:
#         model = UserNotificationPreference
#         fields = [
#             'user_id', 'email_enabled', 'push_enabled', 
#             'sms_enabled', 'in_app_enabled', 'preferences'
#         ]
    
#     def validate_user_id(self, value):
#         """Validate user exists and doesn't already have preferences"""
#         try:
#             user = User.objects.get(id=value)
#         except User.DoesNotExist:
#             raise serializers.ValidationError("User does not exist")
        
#         if UserNotificationPreference.objects.filter(user=user).exists():
#             raise serializers.ValidationError("User already has notification preferences")
        
#         return value
    
#     def create(self, validated_data):
#         user_id = validated_data.pop('user_id')
#         user = User.objects.get(id=user_id)
#         return UserNotificationPreference.objects.create(user=user, **validated_data)



# # serializers.py (continued)
# class NotificationTemplateCreateSerializer(serializers.ModelSerializer):
#     channels = serializers.ListField(
#         child=serializers.ChoiceField(choices=NotificationChannel.choices),
#         default=[NotificationChannel.IN_APP]
#     )
    
#     class Meta:
#         model = NotificationTemplate
#         fields = [
#             'name', 'subject', 'message', 'html_message', 
#             'channels', 'is_active'
#         ]
    
#     def validate_name(self, value):
#         """Ensure template name is unique"""
#         if NotificationTemplate.objects.filter(name=value).exists():
#             raise serializers.ValidationError("A template with this name already exists")
#         return value
    
#     def validate_channels(self, value):
#         """Convert list to comma-separated string"""
#         return ','.join(value)
    
#     def create(self, validated_data):
#         return NotificationTemplate.objects.create(**validated_data)

# class NotificationTemplateUpdateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = NotificationTemplate
#         fields = [
#             'subject', 'message', 'html_message', 'channels', 'is_active'
#         ]
    
#     def update(self, instance, validated_data):
#         instance.subject = validated_data.get('subject', instance.subject)
#         instance.message = validated_data.get('message', instance.message)
#         instance.html_message = validated_data.get('html_message', instance.html_message)
#         instance.channels = validated_data.get('channels', instance.channels)
#         instance.is_active = validated_data.get('is_active', instance.is_active)
#         instance.save()
#         return instance

# class TemplateTestSerializer(serializers.Serializer):
#     """Serializer for testing templates"""
#     template_id = serializers.IntegerField()
#     test_context = serializers.DictField(
#         child=serializers.CharField(),
#         required=False,
#         default=dict
#     )
#     user_id = serializers.IntegerField(required=False)
    
#     def validate_template_id(self, value):
#         try:
#             template = NotificationTemplate.objects.get(id=value)
#         except NotificationTemplate.DoesNotExist:
#             raise serializers.ValidationError("Template does not exist")
#         return value
    
#     def validate_user_id(self, value):
#         if value is not None:
#             try:
#                 User.objects.get(id=value)
#             except User.DoesNotExist:
#                 raise serializers.ValidationError("User does not exist")
#         return value


# # serializers.py (continued)
# class NotificationResponseSerializer(serializers.Serializer):
#     """Generic response serializer for notification operations"""
#     success = serializers.BooleanField()
#     message = serializers.CharField()
#     notification_id = serializers.IntegerField(required=False)
#     notifications_affected = serializers.IntegerField(required=False)

# class PaginatedNotificationSerializer(serializers.Serializer):
#     """Serializer for paginated notification responses"""
#     count = serializers.IntegerField()
#     next = serializers.URLField(allow_null=True)
#     previous = serializers.URLField(allow_null=True)
#     results = NotificationListSerializer(many=True)

# class UnreadCountSerializer(serializers.Serializer):
#     """Serializer for unread notification count"""
#     unread_count = serializers.IntegerField()
#     total_count = serializers.IntegerField()
#     unread_urgent = serializers.IntegerField()