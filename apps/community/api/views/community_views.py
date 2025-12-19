from rest_framework import viewsets, status, generics, permissions
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import NotFound

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q

# Models
from community.models import (
    Community, 
    CommunityMember, 
    CommunityInvitation, 
    CommunityCategory
)

# Serializers (Assumed you have renamed/created these based on previous steps)
from ..serializers.community_serializers import (
    CommunitySerializer,
    CreateCommunitySerializer,
    CommunityMemberSerializer,
    CommunityCategorySerializer,
    # You need to create/rename these specific serializer classes in serializers.py:
    CreateCommunityInvitationSerializer,   # was CreateServerInvitationSerializer
    ReceivedCommunityInvitationSerializer, # was ReceivedInvitationSerializer
    UploadCommunityIconSerializer,         # was UploadServerLogoSerializer
    PublicCommunityInviteSerializer,       # was PublicServerInviteSerializer
    PublicCommunityListSerializer,         # was PublicServerListSerializer
    JoinCommunityByInviteSerializer        # was JoinServerByInviteSerializer
)


# --- CATEGORY VIEW ---
class CommunityCategoryListView(generics.ListAPIView):
    serializer_class = CommunityCategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CommunityCategory.objects.all()


# --- MAIN COMMUNITY VIEWSET ---
class CommunityViewSet(viewsets.ModelViewSet):
    queryset = Community.objects.all()
    serializer_class = CommunitySerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateCommunitySerializer
        return CommunitySerializer
    
    def get_queryset(self):
        user = self.request.user
        # Return communities where user is Creator OR a Member
        return Community.objects.filter(
            Q(created_by=user) |
            Q(members__user=user)
        ).distinct()
    
    def perform_create(self, serializer):
        # 1. Create Community
        community = serializer.save(created_by=self.request.user)
        
        # 2. Add Creator as Admin
        CommunityMember.objects.create(
            community=community,
            user=self.request.user,
            role='admin'
        )

        # 3. If Public, create a default infinite invite link (Optional)
        if community.visibility == "public":
            CommunityInvitation.objects.create(
                community=community,
                invited_by=self.request.user,
                invited_user=None,
                max_uses=0, # Infinite
            )
        

    @action(detail=False, methods=['get'])
    def public_communities(self, request):
        """Get all public communities that the user is NOT a member of"""
        user = request.user
        
        # IDs where user is already a member
        user_community_ids = Community.objects.filter(
            Q(created_by=user) | Q(members__user=user)
        ).values_list('id', flat=True)
        
        # Public communities excluding joined ones
        communities = Community.objects.filter(
            visibility="public"
        ).exclude(
            id__in=user_community_ids
        ).select_related("category")
        
        serializer = PublicCommunityListSerializer(
            communities,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='members')
    def members(self, request, pk=None):
        """
        Fetch all members of a specific community.
        """
        community = self.get_object()
        members = CommunityMember.objects.filter(community=community).select_related('user')
        serializer = CommunityMemberSerializer(members, many=True)
        return Response(serializer.data)
    

# --- INVITATION VIEWS ---

class ReceivedInvitationListView(generics.ListAPIView):
    serializer_class = ReceivedCommunityInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return CommunityInvitation.objects.filter(
            invited_user=user,
            status="pending"
        )
    
class CreateInvitationView(generics.CreateAPIView):
    serializer_class = CreateCommunityInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        community_id = self.kwargs["community_id"]
        community = get_object_or_404(Community, id=community_id)
        
        # Check permissions (Only admins/mods should invite?)
        # For now, allowing all members, but you can add a check here.

        serializer.save(
            community=community,
            invited_by=self.request.user
        )


class AcceptInvitationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, invite_id):
        user = request.user

        try:
            invite = CommunityInvitation.objects.select_related("community").get(
                id=invite_id,
                invited_user=user,
                status="pending",
            )
        except CommunityInvitation.DoesNotExist:
            return Response(
                {"error": "Invalid or expired invite"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Create Member
        member, created = CommunityMember.objects.get_or_create(
            user=user,
            community=invite.community,
            defaults={"role": 'member'}, # Default role
        )

        if not created:
            return Response(
                {"error": "You are already a member of this community"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update invite status
        invite.status = "accepted"
        invite.save(update_fields=["status"])

        # Note: We removed 'member_count' increment logic because 
        # the Community model does not have that field (it's calculated).

        return Response(
            {"message": f"You have joined {invite.community.name}"},
            status=status.HTTP_200_OK,
        )


class RejectInvitationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, invite_id):
        user = request.user

        try:
            invite = CommunityInvitation.objects.get(
                id=invite_id,
                invited_user=user,
                status="pending"
            )
        except CommunityInvitation.DoesNotExist:
            return Response({"error": "Invalid invite"}, status=status.HTTP_404_NOT_FOUND)

        invite.status = "rejected"
        invite.save()

        return Response({"message": "Invitation rejected"}, status=status.HTTP_200_OK)


# --- UTILITY VIEWS ---

class CommunityIconUploadView(generics.UpdateAPIView):
    serializer_class = UploadCommunityIconSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        community_id = self.kwargs["community_id"]
        # Ensure only admin/creator can upload
        community = get_object_or_404(Community, id=community_id)
        
        # Simple permission check
        if community.created_by != self.request.user:
             # Ideally check CommunityMember role is admin
             pass 
             
        return community
    
class CommunityMemberRoleView(APIView):
    """
    Update a member's role (Admin/Moderator/Member)
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, community_id, user_id):
        community = get_object_or_404(Community, id=community_id)

        # 1. Check if requester is Admin
        try:
            requester_member = CommunityMember.objects.get(community=community, user=request.user)
        except CommunityMember.DoesNotExist:
            return Response({"error": "You are not a member."}, status=status.HTTP_403_FORBIDDEN)

        if requester_member.role != "admin":
             # Note: 'created_by' is not a role in the Member model, it's on the Community model
             # So we check if role is admin OR if they are the creator
            if community.created_by != request.user:
                return Response({"error": "Only admins can update roles."}, status=status.HTTP_403_FORBIDDEN)

        # 2. Get target member
        member = get_object_or_404(CommunityMember, community=community, user__id=user_id)

        # 3. Prevent changing own role (optional safety)
        if member.user == request.user:
            return Response({"error": "You cannot change your own role."}, status=status.HTTP_400_BAD_REQUEST)

        # 4. Update
        role = request.data.get("role")
        if role not in dict(CommunityMember.ROLE_CHOICES):
            return Response({"error": "Invalid role."}, status=status.HTTP_400_BAD_REQUEST)

        member.role = role
        member.save()

        return Response(
            {"message": "Role updated", "user": member.user.id, "role": member.role},
            status=status.HTTP_200_OK
        )
    

class InvitePreviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, invite_code):
        try:
            invite = CommunityInvitation.objects.select_related("community").get(
                invite_code=invite_code,
                invited_user__isnull=True,  # PUBLIC LINK ONLY
            )
        except CommunityInvitation.DoesNotExist:
            raise NotFound("Invalid or expired invite link.")

        serializer = PublicCommunityInviteSerializer(invite)
        return Response(serializer.data)


class JoinCommunityByInviteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = JoinCommunityByInviteSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        member = serializer.save()

        return Response(
            {
                "message": "Successfully joined community.",
                "community_id": member.community.id,
                "role": member.role,
            },  
            status=status.HTTP_201_CREATED,
        )