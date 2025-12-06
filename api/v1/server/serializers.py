from rest_framework import serializers
from server_manager.models import Server, ServerMember, ServerInvitation
from user_manager.models import CustomUser as User


class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='profile.username', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'username']


class ServerMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ServerMember
        fields = ['id', 'user', 'role', 'joined_at']


class ServerSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    is_owner = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    members = ServerMemberSerializer(many=True, read_only=True)
    
    class Meta:
        model = Server
        fields = [
            'id', 'name', 'description', 'icon', 'owner', 
            'server_type', 'created_at', 'updated_at', 
            'member_count', 'is_owner', 'user_role', 'members'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at', 'member_count']
    
    def get_is_owner(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.owner == request.user
        return False
    
    def get_user_role(self, obj):
        request = self.context.get('request')
        if request and request.user:
            membership = ServerMember.objects.filter(
                server=obj,
                user=request.user
            ).first()
            return membership.role if membership else None
        return None

class CreateServerInvitationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)

    class Meta:
        model = ServerInvitation
        fields = [
            "id",
            "server",
            "invited_user",
            "email",
            "max_uses",
            "expires_at",
            "invite_code",
            "role",
        ]
        read_only_fields = ["id", "invite_code", "server", "invited_user"]

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "No user with this email exists."
            )
        return value

    def create(self, validated_data):
        request = self.context["request"]
        email = validated_data.pop("email")

        # ✅ Prevent self-invitation
        if request.user.email == email:
            raise serializers.ValidationError(
                "You cannot invite yourself."
            )

        invited_user = User.objects.get(email=email)

        server = validated_data.get("server")

        # ✅ BLOCK ONLY IF ACTIVE OR PENDING INVITE EXISTS
        if ServerInvitation.objects.filter(
            server=server,
            invited_user=invited_user,
            status__in=["pending", "accepted"],
        ).exists():
            raise serializers.ValidationError(
                "This user already has an active invitation."
            )

        return ServerInvitation.objects.create(
            invited_by=request.user,
            invited_user=invited_user,
            **validated_data
        )


class ReceivedInvitationSerializer(serializers.ModelSerializer):
    server_name = serializers.CharField(source="server.name", read_only=True)
    invited_by = serializers.CharField(
        source="invited_by.email", read_only=True
    )

    class Meta:
        model = ServerInvitation
        fields = [
            "id",
            "server",
            "server_name",
            "invited_by",
            "status",
            "created_at",
            "expires_at",
            "invite_code",
            'role',
        ]

# class ServerInvitationSerializer(serializers.ModelSerializer):
#     server = ServerSerializer(read_only=True)
#     server_id = serializers.UUIDField(write_only=True)
#     invited_by = UserSerializer(read_only=True)
#     invited_user = UserSerializer(read_only=True)
#     invited_user_id = serializers.IntegerField(write_only=True, required=False)
#     is_valid = serializers.SerializerMethodField()
    
#     class Meta:
#         model = ServerInvitation
#         fields = [
#             'id', 'server', 'server_id', 'invited_by', 'invited_user',
#             'invited_user_id', 'invite_code', 'email', 'status',
#             'max_uses', 'uses', 'expires_at', 'created_at', 'is_valid'
#         ]
#         read_only_fields = [
#             'id', 'invite_code', 'invited_by', 'status', 
#             'uses', 'created_at'
#         ]
    
#     def get_is_valid(self, obj):
#         return obj.is_valid()
    
#     def create(self, validated_data):
#         server_id = validated_data.pop('server_id')
#         invited_user_id = validated_data.pop('invited_user_id', None)
        
#         server = Server.objects.get(id=server_id)
        
#         invitation = ServerInvitation.objects.create(
#             server=server,
#             invited_user_id=invited_user_id,
#             **validated_data
#         )
        
#         return invitation

