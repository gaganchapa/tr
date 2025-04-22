import re
import os
import requests
from datetime import datetime, timedelta
from dateutil.parser import parse
from geopy.geocoders import Nominatim
import time
import folium
from folium.plugins import MarkerCluster

def parse_natural_date(text):
    """Parse natural language date references from text."""
    text = text.lower()
    today = datetime.today()
    if "tomorrow" in text:
        return today + timedelta(days=1)
    elif "day after tomorrow" in text:
        return today + timedelta(days=2)
    elif "yesterday" in text:
        return today - timedelta(days=1)
    elif "day before yesterday" in text:
        return today - timedelta(days=2)
    else:
        try:
            return parse(text, fuzzy=True)
        except:
            return None

def detect_personality_prefs(user_input):
    """Detect travel personality preferences from user input."""
    personalities = [
        "Adventurous", "Relaxed", "Foodie", "Cultural Explorer",
        "Party Animal", "Solo Traveler", "Family-Oriented"
    ]
    found = [p for p in personalities if p.lower() in user_input.lower()]
    return found or ["Relaxed"]  # default

def extract_destination(user_input):
    """Extract destination from user input.
    
    This function uses multiple patterns and heuristics to identify
    the travel destination in a user query.
    """
    if not user_input:
        return None
        
    # Common patterns for destination mentions
    patterns = [
        r'(?:trip to|visit|going to|travel to|in|at|destination|vacation in) ([a-zA-Z\s\',]+?)(?:\s+(?:for|on|in|with|and|to)|[.,?!]|$)',
        r'(?:plan|planning|create|designing) (?:a|an|my) (?:trip|vacation|visit|itinerary) (?:to|for|in) ([a-zA-Z\s\',]+?)(?:\s+(?:for|on|in|with|and|to)|[.,?!]|$)',
        r'/add .+? (?:in|to|at) ([a-zA-Z\s\',]+)(?:\s+|$|[.,?!])',
        r'([a-zA-Z\s\',]+?) (?:itinerary|vacation|trip|travel plan)'
    ]
    
    # Try all patterns
    for pattern in patterns:
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            # Clean up the extracted destination
            destination = match.group(1).strip()
            # Remove leading articles or prepositions
            destination = re.sub(r'^(?:the|a|an) ', '', destination, flags=re.IGNORECASE)
            return destination.strip()
    
    # If no match with patterns, try to identify known destinations
    words = user_input.split()
    for i in range(len(words) - 1):
        # Check for potential compound city names
        if i < len(words) - 1:
            potential_location = words[i].capitalize()
            if potential_location in ["New", "Los", "San", "Las", "Hong", "Tel", "Rio"]:
                potential_location += " " + words[i+1].capitalize()
                
                # Check if it's in our extended city list
                known_cities = [
                    "New York", "Los Angeles", "San Francisco", "Las Vegas", 
                    "Hong Kong", "Tel Aviv", "Rio Janeiro", "New Orleans",
                    "New Delhi", "San Diego", "San Jose", "San Antonio"
                ]
                if potential_location in known_cities:
                    return potential_location

        # Check single-word major cities
        known_cities = [
            "Paris", "London", "Tokyo", "Rome", "Dubai", "Berlin", "Madrid",
            "Barcelona", "Vienna", "Amsterdam", "Prague", "Singapore", "Sydney",
            "Istanbul", "Bangkok", "Seoul", "Cairo", "Vancouver", "Toronto",
            "Chicago", "Boston", "Miami", "Seattle", "Denver", "Austin"
        ]
        if words[i].capitalize() in known_cities:
            return words[i].capitalize()
            
    # No destination found
    return None

def get_coordinates(location_name):
    """Get latitude and longitude for a location using Geopy.
    
    This function attempts to geocode a location name with increased reliability
    by using several strategies if initial geocoding fails.
    """
    if not location_name:
        return None
        
    # Clean up the location name - remove any non-alphanumeric characters except spaces, commas and basic punctuation
    clean_location = ''.join(c for c in location_name if c.isalnum() or c.isspace() or c in ',-.')
    
    try:
        # Add a delay to avoid hitting rate limits
        time.sleep(0.5)
        geolocator = Nominatim(user_agent="travel_planner_app")
        
        # First attempt with original name
        location = geolocator.geocode(location_name, exactly_one=True, timeout=10)
        
        # If that fails, try with cleaned name
        if not location and clean_location != location_name:
            time.sleep(0.5)
            location = geolocator.geocode(clean_location, exactly_one=True, timeout=10)
            
        # If that fails and there are commas in the name, try the first part
        if not location and ',' in clean_location:
            primary_location = clean_location.split(',')[0].strip()
            time.sleep(0.5)
            location = geolocator.geocode(primary_location, exactly_one=True, timeout=10)
        
        if location:
            return (location.latitude, location.longitude)
        else:
            print(f"Warning: Could not geocode location '{location_name}'")
    except Exception as e:
        print(f"Error getting coordinates for '{location_name}': {e}")
    
    return None

def extract_places_from_itinerary(itinerary_text):
    """Extract place names from the itinerary text."""
    places = []
    
    # Common words that aren't places
    non_place_words = ["the", "your", "this", "that", "these", "those", 
                       "then", "there", "here", "where", "what", "when", 
                       "breakfast", "lunch", "dinner", "brunch", "day",
                       "morning", "afternoon", "evening", "night", "noon"]
    
    # Look for patterns indicating places
    patterns = [
        # Places after action verbs
        r"(?:Visit|Explore|Check out|Go to|See|Head to|Stop by|Enjoy|Experience) ([\w\s',-&]+?)(?:\.|\,|\s|$)",
        
        # Places with ratings
        r"([\w\s',-&]+?) \([\d\.]+\/[\d\.]+\)",
        
        # Landmark pattern
        r"([\w\s',-&]+? (?:Museum|Temple|Cathedral|Church|Palace|Castle|Park|Garden|Monument|Square|Tower|Bridge|Market|Restaurant|Café|Bistro|Hotel|Resort))",
        
        # Places after time
        r"\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm):\s*([\w\s',-&]+?)(?:\.|\,|\s|$)",
        
        # Quoted places
        r'"([\w\s\',-&]+?)"',
        
        # Bold places in markdown
        r'\*\*([\w\s\',-&]+?)\*\*',
        
        # Places after "at" or "to" or "in"
        r"(?:at|to|in) the ([\w\s',-&]+?)(?:\.|\,|\s|$)"
    ]
    
    for pattern in patterns:
        try:
            matches = re.finditer(pattern, itinerary_text)
            for match in matches:
                place = match.group(1).strip()
                # Filter out short words and non-place words
                if len(place) > 3 and not any(word.lower() == place.lower() for word in non_place_words):
                    # Remove any ending punctuation
                    place = place.rstrip('.,;:')
                    places.append(place)
        except Exception as e:
            print(f"Error in pattern matching: {e}")
    
    # Extract locations that are in quotes or marked in some way
    quote_patterns = [r'"([^"]+)"', r"'([^']+)'", r"\*\*([^*]+)\*\*", r"\*([^*]+)\*"]
    for pattern in quote_patterns:
        try:
            matches = re.finditer(pattern, itinerary_text)
            for match in matches:
                place = match.group(1).strip()
                if len(place) > 3 and not any(word.lower() == place.lower() for word in non_place_words):
                    place = place.rstrip('.,;:')
                    places.append(place)
        except Exception as e:
            print(f"Error in quote pattern matching: {e}")
    
    # Find locations with ratings pattern
    ratings_pattern = r'([\w\s\']+)(?:\s*-\s*|\s*\(\s*)(?:\d(?:\.\d)?\s*\/\s*\d|\d(?:\.\d)?\s*stars?|\d(?:\.\d)?★)'
    try:
        ratings_matches = re.finditer(ratings_pattern, itinerary_text)
        for match in ratings_matches:
            place = match.group(1).strip()
            if len(place) > 3 and not any(word.lower() == place.lower() for word in non_place_words):
                place = place.rstrip('.,;:')
                places.append(place)
    except Exception as e:
        print(f"Error in ratings pattern matching: {e}")
    
    # Look for locations that might be hotels or restaurants
    hotel_patterns = [r"([\w\s',\-&]+? (?:Hotel|Resort|Inn|Suites|B&B))", r"Stay at ([\w\s',\-&]+?)(?:\.|\,|\s|$)"]
    restaurant_patterns = [r"([\w\s',\-&]+? (?:Restaurant|Café|Bistro|Eatery|Diner))", r"Eat at ([\w\s',\-&]+?)(?:\.|\,|\s|$)"]
    
    for pattern in hotel_patterns + restaurant_patterns:
        try:
            matches = re.finditer(pattern, itinerary_text)
            for match in matches:
                place = match.group(1).strip()
                if len(place) > 3 and not any(word.lower() == place.lower() for word in non_place_words):
                    place = place.rstrip('.,;:')
                    places.append(place)
        except Exception as e:
            print(f"Error in hotel/restaurant pattern matching: {e}")
    
    # Remove duplicates while preserving order
    unique_places = []
    for place in places:
        if place not in unique_places:
            unique_places.append(place)
    
    return unique_places

def parse_itinerary_to_days(itinerary_text):
    """Parse the itinerary text into days with activities."""
    days = {}
    
    # Split by markdown day headers or "Day X" patterns
    day_pattern = r'(?:#{1,3}\s*)?Day\s*(\d+)'
    day_matches = re.finditer(day_pattern, itinerary_text)
    
    day_positions = []
    for match in day_matches:
        day_number = int(match.group(1))
        start_pos = match.start()
        day_positions.append((day_number, start_pos))
    
    # Sort by position in text
    day_positions.sort(key=lambda x: x[1])
    
    if day_positions:
        # Extract content for each day
        for i, (day_number, start_pos) in enumerate(day_positions):
            # Get end position (start of next day or end of text)
            end_pos = day_positions[i+1][1] if i+1 < len(day_positions) else len(itinerary_text)
            
            # Extract day content
            day_text = itinerary_text[start_pos:end_pos].strip()
            days[day_number] = day_text
    else:
        # If no days found, treat entire text as day 1
        days[1] = itinerary_text
    
    return days

def create_map_with_markers(places, destination):
    """Create a folium map with markers for all places."""
    # Try to get coordinates for the destination
    destination_coords = get_coordinates(destination)
    
    # Default to a general location if destination coordinates not found
    if not destination_coords:
        destination_coords = (40.7128, -74.0060)  # New York by default
    
    # Create map centered on destination
    travel_map = folium.Map(location=destination_coords, zoom_start=12)
    
    # Create marker clusters for each day
    day_clusters = {}
    
    # Add a marker for the destination
    folium.Marker(
        location=destination_coords,
        popup=f"<b>{destination}</b>",
        icon=folium.Icon(color="red", icon="info-sign"),
    ).add_to(travel_map)
    
    # Group places by day
    places_by_day = {}
    for place in places:
        # Extract day from description if available
        day = place.description if hasattr(place, 'description') and place.description else "Other"
        if day not in places_by_day:
            places_by_day[day] = []
        places_by_day[day].append(place)
    
    # Define colors for each day
    day_colors = {
        "Day 1": "blue",
        "Day 2": "green",
        "Day 3": "purple",
        "Other": "orange"
    }
    
    # Create a cluster for each day
    for day, day_places in places_by_day.items():
        day_cluster = MarkerCluster(name=day).add_to(travel_map)
        day_clusters[day] = day_cluster
        
        color = day_colors.get(day, "blue")
        
        # Add markers for each place in this day
        for place in day_places:
            place_name = place.name if hasattr(place, 'name') else place
            
            # Get coordinates
            if hasattr(place, 'latitude') and hasattr(place, 'longitude') and place.latitude and place.longitude:
                coords = (place.latitude, place.longitude)
            else:
                # Get coordinates for the place, appending the destination for better accuracy
                place_with_city = f"{place_name}, {destination}"
                coords = get_coordinates(place_with_city)
            
            if coords:
                popup_content = f"<b>{place_name}</b><br>{day}"
                folium.Marker(
                    location=coords,
                    popup=popup_content,
                    icon=folium.Icon(color=color, icon="info-sign"),
                ).add_to(day_cluster)
    
    # Add layer control
    folium.LayerControl().add_to(travel_map)
    
    return travel_map
