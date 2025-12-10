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
    ReceivedInvitationSerializer,
    ServerMemberSerializer
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
    
    @action(detail=True, methods=['get'], url_path='members')
    def server_members(self, request, pk=None):
        """
        Fetch all members of a specific server.
        Endpoint: GET /api/servers/{id}/members/
        """
        server = self.get_object()

        # 2. Filter members belonging to this server
        members = ServerMember.objects.filter(server=server).select_related('user')
        serializer = ServerMemberSerializer(members, many=True)
        
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


