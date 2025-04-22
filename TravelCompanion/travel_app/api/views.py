from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, action
from django.http import JsonResponse
from travel_app.models import ApiKey, Destination, Itinerary, ItineraryDay, Place, Message
from .serializers import (
    ApiKeySerializer, DestinationSerializer, ItinerarySerializer, 
    ItineraryDaySerializer, PlaceSerializer, MessageSerializer
)
from travel_agent import TravelAgent
from utils import extract_places_from_itinerary, get_coordinates, parse_itinerary_to_days, extract_destination

class ApiKeyViewSet(viewsets.ModelViewSet):
    queryset = ApiKey.objects.all()
    serializer_class = ApiKeySerializer

class DestinationViewSet(viewsets.ModelViewSet):
    queryset = Destination.objects.all()
    serializer_class = DestinationSerializer

class ItineraryViewSet(viewsets.ModelViewSet):
    queryset = Itinerary.objects.all()
    serializer_class = ItinerarySerializer

class PlaceViewSet(viewsets.ModelViewSet):
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

@api_view(['POST'])
def generate_itinerary(request):
    """
    Generate a travel itinerary using the travel agent.
    """
    # Get API keys from database
    serper_api_key = ApiKey.objects.filter(name='serper').first()
    google_api_key = ApiKey.objects.filter(name='google').first()
    
    if not serper_api_key or not google_api_key:
        return Response(
            {"error": "API keys not configured"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Process the query
    query = request.data.get('query', '')
    if not query:
        return Response(
            {"error": "No query provided"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Initialize travel agent
    travel_agent = TravelAgent(
        serper_api_key=serper_api_key.key,
        google_api_key=google_api_key.key
    )
    
    # Process the destination
    destination_name = extract_destination(query)
    if not destination_name:
        return Response(
            {"error": "Could not identify a destination in your request"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get or create destination
    destination_coords = get_coordinates(destination_name)
    if destination_coords:
        latitude, longitude = destination_coords
        destination, created = Destination.objects.get_or_create(
            name=destination_name,
            defaults={
                'latitude': latitude,
                'longitude': longitude
            }
        )
    else:
        destination, created = Destination.objects.get_or_create(name=destination_name)
    
    # Generate itinerary
    itinerary_content = travel_agent.generate_itinerary(query)
    
    # Check for errors
    if itinerary_content.startswith("Error") or itinerary_content.startswith("I couldn't"):
        return Response(
            {"error": itinerary_content}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Create itinerary
    itinerary = Itinerary.objects.create(
        title=f"Trip to {destination_name}",
        destination=destination,
        content=itinerary_content
    )
    
    # Parse itinerary days
    days_dict = parse_itinerary_to_days(itinerary_content)
    for day_num, content in days_dict.items():
        day_number = int(day_num.replace('Day ', ''))
        ItineraryDay.objects.create(
            itinerary=itinerary,
            day_number=day_number,
            content=content
        )
    
    # Extract and create places
    places = extract_places_from_itinerary(itinerary_content)
    for place_name in places:
        # Get coordinates for the place
        place_coords = get_coordinates(f"{place_name}, {destination_name}")
        if place_coords:
            latitude, longitude = place_coords
            Place.objects.create(
                name=place_name,
                itinerary=itinerary,
                latitude=latitude,
                longitude=longitude
            )
        else:
            Place.objects.create(
                name=place_name,
                itinerary=itinerary
            )
    
    # Return the created itinerary
    serializer = ItinerarySerializer(itinerary)
    return Response(serializer.data)

@api_view(['GET'])
def check_api_keys(request):
    """
    Check if API keys are configured.
    """
    serper_key = ApiKey.objects.filter(name='serper').first()
    google_key = ApiKey.objects.filter(name='google').first()
    
    keys = []
    if serper_key:
        keys.append({"name": "serper", "id": serper_key.id})
    if google_key:
        keys.append({"name": "google", "id": google_key.id})
    
    return JsonResponse(keys, safe=False)

@api_view(['POST'])
def chat_message(request):
    """
    Process a chat message using the travel agent.
    """
    # Get API keys from database
    serper_api_key = ApiKey.objects.filter(name='serper').first()
    google_api_key = ApiKey.objects.filter(name='google').first()
    
    if not serper_api_key or not google_api_key:
        return Response(
            {"error": "API keys not configured"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Process the message
    content = request.data.get('content', '')
    if not content:
        return Response(
            {"error": "No message content provided"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Save user message
    user_message = Message.objects.create(
        role='user',
        content=content
    )
    
    # Initialize travel agent
    travel_agent = TravelAgent(
        serper_api_key=serper_api_key.key,
        google_api_key=google_api_key.key
    )
    
    # Generate response
    response_content = travel_agent.answer_travel_question(content)
    
    # Save assistant message
    assistant_message = Message.objects.create(
        role='assistant',
        content=response_content
    )
    
    # Return both messages
    serializer = MessageSerializer([user_message, assistant_message], many=True)
    return Response(serializer.data)