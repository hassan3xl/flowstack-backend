from rest_framework import viewsets, status, generics, permissions
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from server_manager.models import Server, ServerMember, ServerInvitation
from .serializers import (
    ServerSerializer,
    CreateServerInvitationSerializer,
    ServerSerializer,
    ReceivedInvitationSerializer

)
from django.db.models import Q

class ServerViewSet(viewsets.ModelViewSet):
    queryset = Server.objects.all()
    serializer_class = ServerSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return Server.objects.filter(
            Q(owner=user) |
            Q(members__user=user)
        ).distinct()
    
    def perform_create(self, serializer):
        server = serializer.save(owner=self.request.user)
        ServerMember.objects.create(
            server=server,
            user=self.request.user,
            role='owner'
        )

    @action(detail=False, methods=['get'])
    def public_servers(self, request):
        """Get all public servers for discovery"""
        public_servers = Server.objects.filter(
            server_type='public'
        ).exclude(
            members__user=request.user
        )
        serializer = self.get_serializer(public_servers, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def join_public(self, request, pk=None):
        """Join a public server directly"""
        server = self.get_object()
        
        if server.server_type != 'public':
            return Response(
                {'error': 'This server is private'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if already a member
        if ServerMember.objects.filter(server=server, user=request.user).exists():
            return Response(
                {'error': 'Already a member'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add user as member
        ServerMember.objects.create(
            server=server,
            user=request.user,
            role='member'
        )
        
        server.member_count += 1
        server.save()
        
        return Response({'message': 'Successfully joined server'})

class ReceivedInvitationListView(generics.ListAPIView):
    serializer_class = ReceivedInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return ServerInvitation.objects.filter(
            invited_user=user,
            status="pending"
        )
    
class CreateServerInvitationView(generics.CreateAPIView):
    serializer_class = CreateServerInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        server_id = self.kwargs["server_id"]
        server = get_object_or_404(Server, id=server_id)

        serializer.save(
            server=server,
            # invited_by=self.request.user
        )


class AcceptInvitationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, invite_id):
        user = request.user

        try:
            invite = ServerInvitation.objects.get(
                id=invite_id,
                invited_user=user,
                status="pending",
            )
        except ServerInvitation.DoesNotExist:
            return Response(
                {"error": "Invalid or expired invite"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        ServerMember.objects.get_or_create(
            user=user,
            server=invite.server,
            role=invite.role
        )

        # Update invite
        invite.status = "accepted"
        invite.save()


        return Response(
            {"message": f"You have joined {invite.server.name}"},
            status=status.HTTP_200_OK
        )


class RejectInvitationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, invite_id):
        user = request.user

        try:
            invite = ServerInvitation.objects.get(
                id=invite_id,
                invited_user=user,
                status="pending"
            )
        except ServerInvitation.DoesNotExist:
            return Response(
                {"error": "Invalid invite"},
                status=status.HTTP_404_NOT_FOUND
            )

        invite.status = "rejected"
        invite.save()

        return Response(
            {"message": "you rejected the invite"},
            status=status.HTTP_200_OK
        )
    
    # @action(detail=True, methods=['post'])
    # def leave(self, request, pk=None):
    #     """Leave a server"""
    #     server = self.get_object()
        
    #     if server.owner == request.user:
    #         return Response(
    #             {'error': 'Owner cannot leave the server'},
    #             status=status.HTTP_403_FORBIDDEN
    #         )
        
    #     membership = ServerMember.objects.filter(
    #         server=server,
    #         user=request.user
    #     ).first()
        
    #     if membership:
    #         membership.delete()
    #         server.member_count -= 1
    #         server.save()
    #         return Response({'message': 'Successfully left server'})
        
    #     return Response(
    #         {'error': 'Not a member'},
    #         status=status.HTTP_400_BAD_REQUEST
    #     )
    
    # @action(detail=True, methods=['get'])
    # def members(self, request, pk=None):
    #     """Get all members of a server"""
    #     server = self.get_object()
    #     members = server.members.all()
    #     serializer = ServerMemberSerializer(members, many=True)
    #     return Response(serializer.data)


# class ServerInvitationViewSet(viewsets.ModelViewSet):
#     serializer_class = ServerInvitationSerializer
#     permission_classes = [IsAuthenticated]
    
#     def get_queryset(self):
#         # Get invitations for servers user is part of or invitations sent to user
#         return ServerInvitation.objects.filter(
#             models.Q(server__members__user=self.request.user) |
#             models.Q(invited_user=self.request.user)
#         ).distinct()
    
#     def perform_create(self, serializer):
#         """Create a new invitation"""
#         server_id = self.request.data.get('server')
#         server = get_object_or_404(Server, id=server_id)
        
#         # Check if user has permission to invite
#         membership = ServerMember.objects.filter(
#             server=server,
#             user=self.request.user,
#             role__in=['owner', 'admin', 'moderator']
#         ).first()
        
#         if not membership:
#             return Response(
#                 {'error': 'No permission to invite'},
#                 status=status.HTTP_403_FORBIDDEN
#             )
        
#         # Set expiration (7 days default)
#         expires_at = timezone.now() + timedelta(days=7)
        
#         serializer.save(
#             invited_by=self.request.user,
#             expires_at=expires_at
#         )
    
#     @action(detail=False, methods=['get'])
#     def my_invitations(self, request):
#         """Get all pending invitations for current user"""
#         invitations = ServerInvitation.objects.filter(
#             invited_user=request.user,
#             status='pending'
#         )
#         serializer = self.get_serializer(invitations, many=True)
#         return Response(serializer.data)
    
#     @action(detail=True, methods=['post'])
#     def accept(self, request, pk=None):
#         """Accept an invitation"""
#         invitation = self.get_object()
        
#         if invitation.invited_user != request.user:
#             return Response(
#                 {'error': 'This invitation is not for you'},
#                 status=status.HTTP_403_FORBIDDEN
#             )
        
#         if not invitation.is_valid():
#             return Response(
#                 {'error': 'Invitation is no longer valid'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
        
#         # Check if already a member
#         if ServerMember.objects.filter(
#             server=invitation.server,
#             user=request.user
#         ).exists():
#             invitation.status = 'accepted'
#             invitation.save()
#             return Response({'message': 'Already a member'})
        
#         # Add user to server
#         ServerMember.objects.create(
#             server=invitation.server,
#             user=request.user,
#             role='member'
#         )
        
#         # Update invitation
#         invitation.status = 'accepted'
#         invitation.uses += 1
#         invitation.save()
        
#         # Update member count
#         invitation.server.member_count += 1
#         invitation.server.save()
        
#         return Response({
#             'message': 'Successfully joined server',
#             'server': ServerSerializer(invitation.server).data
#         })
    
#     @action(detail=True, methods=['post'])
#     def decline(self, request, pk=None):
#         """Decline an invitation"""
#         invitation = self.get_object()
        
#         if invitation.invited_user != request.user:
#             return Response(
#                 {'error': 'This invitation is not for you'},
#                 status=status.HTTP_403_FORBIDDEN
#             )
        
#         invitation.status = 'declined'
#         invitation.save()
        
#         return Response({'message': 'Invitation declined'})
    
#     @action(detail=False, methods=['post'])
#     def join_by_code(self, request):
#         """Join server using invite code"""
#         invite_code = request.data.get('invite_code')
        
#         if not invite_code:
#             return Response(
#                 {'error': 'Invite code required'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
        
#         invitation = ServerInvitation.objects.filter(
#             invite_code=invite_code
#         ).first()
        
#         if not invitation or not invitation.is_valid():
#             return Response(
#                 {'error': 'Invalid or expired invite code'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
        
#         # Check if already a member
#         if ServerMember.objects.filter(
#             server=invitation.server,
#             user=request.user
#         ).exists():
#             return Response({'message': 'Already a member'})
        
#         # Add user to server
#         ServerMember.objects.create(
#             server=invitation.server,
#             user=request.user,
#             role='member'
#         )
        
#         # Update invitation
#         invitation.uses += 1
#         invitation.save()
        
#         # Update member count
#         invitation.server.member_count += 1
#         invitation.server.save()
        
#         return Response({
#             'message': 'Successfully joined server',
#             'server': ServerSerializer(invitation.server).data
#         })