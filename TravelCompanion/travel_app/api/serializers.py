from rest_framework import serializers
from travel_app.models import Destination, Itinerary, ItineraryDay, Place, Message, ApiKey

class ApiKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiKey
        fields = ['id', 'name', 'key']

class DestinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = ['id', 'name', 'latitude', 'longitude']

class PlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = ['id', 'name', 'latitude', 'longitude', 'description']

class ItineraryDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = ItineraryDay
        fields = ['id', 'day_number', 'content']

class ItinerarySerializer(serializers.ModelSerializer):
    days = ItineraryDaySerializer(many=True, read_only=True)
    places = PlaceSerializer(many=True, read_only=True)
    destination = DestinationSerializer(read_only=True)
    
    class Meta:
        model = Itinerary
        fields = ['id', 'title', 'destination', 'content', 'days', 'places', 'created_at']

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'role', 'content', 'timestamp']