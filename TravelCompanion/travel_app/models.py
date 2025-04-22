from django.db import models

class ApiKey(models.Model):
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Destination(models.Model):
    name = models.CharField(max_length=100)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Itinerary(models.Model):
    title = models.CharField(max_length=200)
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='itineraries')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class ItineraryDay(models.Model):
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name='days')
    day_number = models.PositiveIntegerField()
    content = models.TextField()
    
    class Meta:
        ordering = ['day_number']
    
    def __str__(self):
        return f"{self.itinerary.title} - Day {self.day_number}"

class Place(models.Model):
    name = models.CharField(max_length=200)
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name='places')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name

class Message(models.Model):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('assistant', 'Assistant'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."