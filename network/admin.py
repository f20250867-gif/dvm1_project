from django.contrib import admin
from .models import Node, Edge,ServiceStatus
from django.db import models

@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display  = ('id', 'name', 'latitude', 'longitude')
    search_fields = ('name',)


@admin.register(Edge)
class EdgeAdmin(admin.ModelAdmin):
    list_display  = ('id', 'from_node', 'to_node', 'distance')
    list_filter   = ('from_node', 'to_node')
    search_fields = ('from_node__name', 'to_node__name')

admin.site.register(ServiceStatus)