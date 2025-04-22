from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .api import views as api_views

# Setup the API router
router = DefaultRouter()
router.register(r'api-keys', api_views.ApiKeyViewSet)
router.register(r'destinations', api_views.DestinationViewSet)
router.register(r'itineraries', api_views.ItineraryViewSet)
router.register(r'places', api_views.PlaceViewSet)
router.register(r'messages', api_views.MessageViewSet)

urlpatterns = [
    # Frontend views
    path('', views.home, name='home'),
    path('api-keys/', views.api_keys, name='api_keys'),
    path('api-keys/delete/<int:pk>/', views.delete_api_key, name='delete_api_key'),
    
    # API endpoints
    path('api/', include(router.urls)),
    path('api/chat/', views.chat_message, name='chat_message'),
    path('api/chat-message/', views.chat_message, name='chat_message_alt'),  # Alias for compatibility
    path('api/chat-history/', views.get_chat_history, name='chat_history'),
    path('api/generate-itinerary/', api_views.generate_itinerary, name='generate_itinerary'),
    path('api/get-itineraries/', views.get_itineraries, name='get_itineraries'),
    path('api/get-itinerary/<int:pk>/', views.get_itinerary, name='get_itinerary'),
    path('api/map-data/', views.get_map_data, name='map_data'),
    path('api/map-data/<int:itinerary_id>/', views.get_map_data, name='map_data_with_id'),
    path('api/api-keys/', api_views.check_api_keys, name='check_api_keys'),
]