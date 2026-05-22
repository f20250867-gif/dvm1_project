from django.db import models

# Create your models here.
class Node(models.Model):
    name      = models.CharField(max_length=100, unique=True)
    latitude  = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.name


class Edge(models.Model):
    from_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='outgoing_edges')
    to_node   = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='incoming_edges')
    distance  = models.FloatField(default=1.0)

    class Meta:
        unique_together = ('from_node', 'to_node')

    def __str__(self):
        return f"{self.from_node} → {self.to_node}"