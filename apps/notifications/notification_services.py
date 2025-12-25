from django.contrib.contenttypes.models import ContentType
from .models import Notification

class NotificationService:
    
    @staticmethod
    def send_notification(recipient, actor, title, message, target_obj, category='system_alert', type='info'):
        """
        Sends a single notification to one user.
        """
        # 1. Safety Check: Don't notify users of their own actions
        if recipient == actor:
            return None 

        # 2. Create the Notification
        notification = Notification.objects.create(
            recipient=recipient,
            actor=actor,
            title=title,
            message=message,
            target=target_obj, # Django handles content_type/object_id assignment automatically
            category=category,
            type=type
        )

        # --- FUTURE PROOFING ---
        # This is where you would add:
        # send_websocket_event(recipient.id, notification) 
        # send_email_alert(recipient.email, title, message)
        
        return notification

    @staticmethod
    def send_bulk_notification(recipients, actor, title, message, target_obj, category='system_alert'):
        """
        Efficiently creates notifications for multiple users (e.g. whole team).
        """
        # Filter out the actor so they don't get notified
        valid_recipients = [u for u in recipients if u != actor]
        
        if not valid_recipients:
            return []

        # Get ContentType once to save DB queries
        content_type = ContentType.objects.get_for_model(target_obj)
        
        notifications = [
            Notification(
                recipient=user,
                actor=actor,
                title=title,
                message=message,
                content_type=content_type,
                object_id=target_obj.id,
                category=category
            ) for user in valid_recipients
        ]
        
        # bulk_create is much faster than looping .create()
        return Notification.objects.bulk_create(notifications)