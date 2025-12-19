from rest_framework import serializers
from community.models import Community, CommunityMember, CommunityCategory, CommunityChannel, CommunityInvitation
from users.models import User
from users.api import UserSerializer

class CommunityCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityCategory
        fields = ['id', 'name', 'description']

class CommunityChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityChannel
        fields = ['id', 'name', 'channel_type', 'is_read_only', 'position']

class CommunityMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = CommunityMember
        fields = ['id', 'user', 'role', 'joined_at']

class CommunitySerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    is_owner = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    member_count = serializers.IntegerField(source='members.count', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    channels = CommunityChannelSerializer(many=True, read_only=True)

    class Meta:
        model = Community
        fields = [
            'id', 'name', 'description', 'icon', 'visibility', 
            'category', 'category_name', 'created_by', 'created_at', 
            'member_count', 'is_owner', 'user_role', 'channels'
        ]
        read_only_fields = ['id', 'created_by', 'created_at']

    def get_is_owner(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.created_by == request.user
        return False

    def get_user_role(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            membership = CommunityMember.objects.filter(
                community=obj, # Fixed from 'server'
                user=request.user
            ).first()
            return membership.role if membership else None
        return None

class CreateCommunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Community
        fields = ['id', 'name', 'description', 'visibility', 'category', 'icon']

    def create(self, validated_data):
        request = self.context.get('request')
        # Automatically assign the creator and add them as an Admin member
        community = Community.objects.create(created_by=request.user, **validated_data)
        CommunityMember.objects.create(
            community=community,
            user=request.user,
            role='admin'

        )
        return community
    

class CreateCommunityInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityInvitation
        fields = ['id', 'community', 'invited_by', 'invited_user', 'max_uses']




# ... keep your existing imports and classes (CommunitySerializer, etc.) ...

# --- INVITATION SERIALIZERS ---

class CreateCommunityInvitationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)

    class Meta:
        model = CommunityInvitation
        fields = [
            "id",
            "community",
            "invited_user",
            "email",
            "max_uses",
            "expires_at",
            "invite_code",
        ]
        read_only_fields = ["id", "invite_code", "community", "invited_user"]

    def validate_email(self, value):
        try:
            # Check if user exists
            User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("No user with this email exists.")
        return value

    def create(self, validated_data):
        request = self.context.get("request")
        email = validated_data.pop("email")
        invited_user = User.objects.get(email=email)

        # 1. Prevent self-invitation
        if request.user.email == email:
            raise serializers.ValidationError("You cannot invite yourself.")

        community = validated_data.get("community")

        # 2. Block if already a member
        if CommunityMember.objects.filter(community=community, user=invited_user).exists():
            raise serializers.ValidationError("User is already a member of this community.")

        # 3. Block if active/pending invite exists
        if CommunityInvitation.objects.filter(
            community=community,
            invited_user=invited_user,
            status__in=["pending", "accepted"],
        ).exists():
            raise serializers.ValidationError("This user already has an active invitation.")

        return CommunityInvitation.objects.create(
            invited_by=request.user,
            invited_user=invited_user,
            **validated_data
        )


class ReceivedCommunityInvitationSerializer(serializers.ModelSerializer):
    community_name = serializers.CharField(source="community.name", read_only=True)
    community_icon = serializers.ImageField(source="community.icon", read_only=True)
    invited_by = serializers.CharField(source="invited_by.email", read_only=True)

    class Meta:
        model = CommunityInvitation
        fields = [
            "id",
            "community",
            "community_name",
            "community_icon",
            "invited_by",
            "status",
            "created_at",
            "expires_at",
            "invite_code",
        ]


# --- PUBLIC & DISCOVERY SERIALIZERS ---

class PublicCommunityListSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.name", read_only=True)
    invite_code = serializers.SerializerMethodField()
    member_count = serializers.IntegerField(source='members.count', read_only=True)

    class Meta:
        model = Community
        fields = [
            "id",
            "name",
            "description",
            "category",
            "icon",
            "member_count",
            "invite_code",
        ]

    def get_invite_code(self, obj):
        # Find the first valid public invite code for this community
        invite = obj.invitations.filter(
            invited_user__isnull=True, # Public link
            max_uses=0 # Infinite uses
        ).first()
        return invite.invite_code if invite else None


class PublicCommunityInviteSerializer(serializers.ModelSerializer):
    """
    Used when a user clicks a link (e.g., /invite/abc) to preview the community
    before joining.
    """
    community_name = serializers.CharField(source="community.name", read_only=True)
    community_icon = serializers.ImageField(source="community.icon", read_only=True)
    community_id = serializers.UUIDField(source="community.id", read_only=True)
    member_count = serializers.IntegerField(source="community.members.count", read_only=True)
    
    class Meta:
        model = CommunityInvitation
        fields = [
            "invite_code",
            "community_id",
            "community_name",
            "community_icon",
            "member_count",
            "expires_at",
            "max_uses",
            "uses",
        ]


class JoinCommunityByInviteSerializer(serializers.Serializer):
    invite_code = serializers.CharField()

    def validate(self, attrs):
        request = self.context["request"]
        code = attrs["invite_code"]

        # 1. Find Invite
        try:
            invite = CommunityInvitation.objects.select_related("community").get(
                invite_code=code,
                invited_user__isnull=True, # Must be a public link
            )
        except CommunityInvitation.DoesNotExist:
            raise serializers.ValidationError("Invalid invite code.")

        # 2. Check Expiry
        if invite.is_expired:
            raise serializers.ValidationError("Invite link has expired.")

        # 3. Check Usage Limits
        if invite.max_uses != 0 and invite.uses >= invite.max_uses:
            raise serializers.ValidationError("Invite link usage limit reached.")

        # 4. Check Visibility (Optional safety check)
        if invite.community.visibility != "public":
             # Sometimes private communities have one-time links, so you might remove this
             # depending on your logic.
            pass

        # 5. Check if already a member
        if CommunityMember.objects.filter(
            community=invite.community,
            user=request.user
        ).exists():
            raise serializers.ValidationError("You are already a member.")

        attrs["invite"] = invite
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        invite = validated_data["invite"]
        community = invite.community

        # Create Member
        member = CommunityMember.objects.create(
            community=community,
            user=request.user,
            role='member' 
        )

        # Increment Usage
        invite.uses += 1
        invite.save(update_fields=["uses"])

        return member


class UploadCommunityIconSerializer(serializers.ModelSerializer):
    icon = serializers.ImageField(required=True)

    class Meta:
        model = Community
        fields = ['icon']

    def update(self, instance, validated_data):
        instance.icon = validated_data.get('icon', instance.icon)
        instance.save()
        return instance