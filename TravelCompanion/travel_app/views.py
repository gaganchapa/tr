from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets
from rest_framework.response import Response

from .models import Destination, Itinerary, ItineraryDay, Place, Message, ApiKey
from .api.serializers import (
    DestinationSerializer, ItinerarySerializer, 
    ItineraryDaySerializer, PlaceSerializer, 
    MessageSerializer, ApiKeySerializer
)

from travel_agent import TravelAgent
import utils
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def home(request):
    """Home page view"""
    # Get API keys for configuration
    api_keys = ApiKey.objects.all()
    return render(request, 'travel_app/index.html', {'api_keys': api_keys})

def api_keys(request):
    """API keys management page"""
    if request.method == 'POST':
        name = request.POST.get('name')
        key = request.POST.get('key')
        
        # If a key with this name already exists, update it instead of creating
        existing_key = ApiKey.objects.filter(name=name).first()
        if existing_key:
            existing_key.key = key
            existing_key.save()
        else:
            ApiKey.objects.create(name=name, key=key)
        
        return redirect('api_keys')
    
    api_keys = ApiKey.objects.all()
    return render(request, 'travel_app/api_keys.html', {'api_keys': api_keys})

def delete_api_key(request, pk):
    """Delete an API key"""
    if request.method == 'POST':
        api_key = get_object_or_404(ApiKey, pk=pk)
        api_key.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

# ===== API endpoints =====

class DestinationViewSet(viewsets.ModelViewSet):
    """API endpoint for destinations"""
    queryset = Destination.objects.all()
    serializer_class = DestinationSerializer

class ItineraryViewSet(viewsets.ModelViewSet):
    """API endpoint for itineraries"""
    queryset = Itinerary.objects.all()
    serializer_class = ItinerarySerializer

class ItineraryDayViewSet(viewsets.ModelViewSet):
    """API endpoint for itinerary days"""
    queryset = ItineraryDay.objects.all()
    serializer_class = ItineraryDaySerializer

class PlaceViewSet(viewsets.ModelViewSet):
    """API endpoint for places"""
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer

class MessageViewSet(viewsets.ModelViewSet):
    """API endpoint for messages"""
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

def chat_message(request):
    """Handle chat messages and generate responses"""
    if request.method == 'POST':
        data = json.loads(request.body)
        user_message = data.get('message', '')
        
        # Save the user message
        Message.objects.create(role='user', content=user_message)
        
        # Initialize the travel agent
        serper_api_key = None
        google_api_key = None
        
        # Get API keys from database
        try:
            serper_key = ApiKey.objects.filter(name='serper').first()
            if serper_key:
                serper_api_key = serper_key.key
                
            google_key = ApiKey.objects.filter(name='google').first()
            if google_key:
                google_api_key = google_key.key
        except:
            pass
            
        # Fall back to environment variables if not found in database
        if not serper_api_key:
            serper_api_key = os.getenv('SERPER_API_KEY')
        if not google_api_key:
            google_api_key = os.getenv('GOOGLE_API_KEY')
            
        travel_agent = TravelAgent(
            serper_api_key=serper_api_key,
            google_api_key=google_api_key
        )
        
        # Check if it's a command to add a location to the itinerary
        if user_message.startswith('/add'):
            content = user_message[4:].strip()
            try:
                # Generate an itinerary
                response = travel_agent.generate_itinerary(content)
                
                # Extract destination
                destination_name = utils.extract_destination(content)
                if not destination_name:
                    # If no destination found, use a generic name based on the content
                    words = content.split()
                    destination_name = ' '.join(words[:2]) + " Trip" if len(words) >= 2 else "Travel Plan"
                
                destination, created = Destination.objects.get_or_create(
                    name=destination_name
                )
                
                # Get coordinates for the destination
                if created and not (destination.latitude and destination.longitude):
                    coords = utils.get_coordinates(destination_name)
                    if coords:
                        destination.latitude = coords[0]
                        destination.longitude = coords[1]
                        destination.save()
                
                # Create the itinerary
                itinerary = Itinerary.objects.create(
                    title=f"{destination_name} Itinerary",
                    destination=destination,
                    content=response
                )
                
                # Parse days and places
                days = utils.parse_itinerary_to_days(response)
                
                # Create a dictionary to store places by day
                places_by_day = {}
                
                # Process each day
                for day_num, content in days.items():
                    # Create the itinerary day
                    itinerary_day = ItineraryDay.objects.create(
                        itinerary=itinerary,
                        day_number=day_num,
                        content=content
                    )
                    
                    # Extract places for this specific day
                    day_places = utils.extract_places_from_itinerary(content)
                    places_by_day[day_num] = day_places
                    
                    # Create places with day association
                    for place_name in day_places:
                        try:
                            # Create the place with day number in description
                            place = Place.objects.create(
                                name=place_name,
                                itinerary=itinerary,
                                description=f"Day {day_num}"
                            )
                            
                            # Then try to get coordinates
                            try:
                                coords = utils.get_coordinates(f"{place_name}, {destination_name}")
                                if coords:
                                    place.latitude = coords[0]
                                    place.longitude = coords[1]
                                    place.save()
                            except Exception as coord_error:
                                print(f"Warning: Failed to get coordinates for {place_name}: {coord_error}")
                        except Exception as place_error:
                            print(f"Warning: Failed to save place {place_name}: {place_error}")
                
                # Save the assistant's response
                response_message = f"I've created an itinerary for {destination_name}. You can see it in the itinerary panel."
                Message.objects.create(role='assistant', content=response_message)
                
                return JsonResponse({
                    'message': response_message,
                    'itinerary_id': itinerary.id
                })
                
            except Exception as e:
                error_message = f"Sorry, I couldn't create an itinerary: {str(e)}"
                Message.objects.create(role='assistant', content=error_message)
                return JsonResponse({'message': error_message}, status=500)
        else:
            # Regular travel question
            try:
                response = travel_agent.answer_travel_question(user_message)
                
                # Save the assistant's response
                Message.objects.create(role='assistant', content=response)
                
                return JsonResponse({'message': response})
            except Exception as e:
                error_message = f"Sorry, I couldn't answer that: {str(e)}"
                Message.objects.create(role='assistant', content=error_message)
                return JsonResponse({'message': error_message}, status=500)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

def get_chat_history(request):
    """Get the chat history"""
    messages = Message.objects.all().order_by('timestamp')
    serializer = MessageSerializer(messages, many=True)
    return JsonResponse(serializer.data, safe=False)

def get_itineraries(request):
    """Get all itineraries"""
    itineraries = Itinerary.objects.all().order_by('-created_at')
    serializer = ItinerarySerializer(itineraries, many=True)
    return JsonResponse(serializer.data, safe=False)

def get_itinerary(request, pk):
    """Get a specific itinerary with all its details"""
    itinerary = get_object_or_404(Itinerary, pk=pk)
    serializer = ItinerarySerializer(itinerary)
    return JsonResponse(serializer.data)

def get_map_data(request, itinerary_id=None):
    """Get map data for places in an itinerary"""
    if itinerary_id:
        itinerary = get_object_or_404(Itinerary, pk=itinerary_id)
        places = Place.objects.filter(itinerary=itinerary)
        destination = itinerary.destination
    else:
        # Get the most recent itinerary
        itinerary = Itinerary.objects.order_by('-created_at').first()
        if itinerary:
            places = Place.objects.filter(itinerary=itinerary)
            destination = itinerary.destination
        else:
            places = []
            destination = None
    
    result = {
        'destination': DestinationSerializer(destination).data if destination else None,
        'places': PlaceSerializer(places, many=True).data
    }
    
    return JsonResponse(result)