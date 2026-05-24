from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db import models
from .models import Node, Edge
from .serializers import NodeSerializer, EdgeSerializer

class NodeView(APIView):

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]   # any logged in user can view
        return [IsAdminUser()]           # only admin can add/delete


    def get(self, request):
        nodes = Node.objects.all()
        serializer = NodeSerializer(nodes, many=True)
        return Response(serializer.data)


    def post(self, request):
        serializer = NodeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)  
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#For single node operations — get by id, delete by id
class NodeDetailView(APIView):
    

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsAdminUser()]

    def get_object(self, pk):
        try:
            return Node.objects.get(pk=pk)
        except Node.DoesNotExist:
            return None

    def get(self, request, pk):
        node = self.get_object(pk)
        if not node:
            return Response({'error': 'Node not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = NodeSerializer(node)
        return Response(serializer.data)

    def delete(self, request, pk):
        node = self.get_object(pk)
        if not node:
            return Response({'error': 'Node not found'}, status=status.HTTP_404_NOT_FOUND)
        node.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EdgeView(APIView):

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsAdminUser()]

    def get(self, request):
        edges = Edge.objects.select_related('from_node', 'to_node').all()
        serializer = EdgeSerializer(edges, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = EdgeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EdgeDetailView(APIView):
    """For single edge operations — get by id, delete by id"""

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsAdminUser()]

    def get_object(self, pk):
        try:
            return Edge.objects.get(pk=pk)
        except Edge.DoesNotExist:
            return None

    def get(self, request, pk):
        edge = self.get_object(pk)
        if not edge:
            return Response({'error': 'Edge not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = EdgeSerializer(edge)
        return Response(serializer.data)

    def delete(self, request, pk):
        edge = self.get_object(pk)
        if not edge:
            return Response({'error': 'Edge not found'}, status=status.HTTP_404_NOT_FOUND)
        edge.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


    class Meta:
        verbose_name = 'Service Status'