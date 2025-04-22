import os
import json
import requests
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from utils import parse_natural_date, detect_personality_prefs, extract_destination

# OpenAI integration
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Load environment variables
load_dotenv()

class SerperSearch:
    def __init__(self, api_key):
        self.api_key = api_key
        self.url = "https://google.serper.dev/search"

    def search(self, query):
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "q": query
        }
        try:
            response = requests.post(self.url, headers=headers, json=payload)
            results = response.json()
            return results.get("organic", [])
        except Exception as e:
            print(f"Error in search: {e}")
            return []

class TravelAgent:
    def __init__(self, serper_api_key=None, google_api_key=None, openai_api_key=None):
        # API keys
        self.serper_api_key = serper_api_key or os.getenv("SERPER_API_KEY")
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
        # Model configurations
        self.gemini_model = "gemini-1.5-flash"
        self.openai_model = "gpt-4o"  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        
        # Setup LLM clients - ALWAYS prioritize Gemini as requested
        self.llm_provider = "gemini"  # Default and preferred LLM provider
        
        # Initialize Gemini
        if self.google_api_key:
            self.llm_gemini = ChatGoogleGenerativeAI(
                model=self.gemini_model,
                verbose=True,
                temperature=0.6,
                google_api_key=self.google_api_key
            )
        
        # Initialize OpenAI if available (only as fallback)
        if OPENAI_AVAILABLE and self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
        
        # Initialize search
        if self.serper_api_key:
            self.search = SerperSearch(self.serper_api_key)
    
    def validate_configuration(self):
        """Check if the required API keys are available."""
        # First check for search API which is always required
        if not self.serper_api_key:
            return False, "Serper API key is not configured."
            
        # Then check for LLM APIs based on provider preference
        if self.llm_provider == "openai":
            if not self.openai_api_key:
                # Fall back to Gemini if OpenAI key is missing
                if self.google_api_key:
                    self.llm_provider = "gemini"
                    return True, "Using Gemini as fallback (OpenAI API key not found)."
                else:
                    return False, "No LLM API keys configured (need either OpenAI or Google API key)."
        else:  # gemini is default
            if not self.google_api_key:
                # Try to use OpenAI if available
                if OPENAI_AVAILABLE and self.openai_api_key:
                    self.llm_provider = "openai"
                    return True, "Using OpenAI as fallback (Google API key not found)."
                else:
                    return False, "No LLM API keys configured (need either OpenAI or Google API key)."
        
        return True, "Configuration is valid."
    
    def _generate_with_openai(self, prompt):
        """Generate response using OpenAI."""
        try:
            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI error: {e}")
            raise e
            
    def _generate_with_gemini(self, prompt):
        """Generate response using Gemini."""
        try:
            response = self.llm_gemini.invoke(prompt)
            return response.content
        except Exception as e:
            print(f"Gemini error: {e}")
            raise e
            
    def generate_text(self, prompt):
        """Generate text using the selected LLM provider."""
        if self.llm_provider == "openai" and self.openai_api_key:
            return self._generate_with_openai(prompt)
        else:
            return self._generate_with_gemini(prompt)
    
    def generate_itinerary(self, user_input):
        """Generate a travel itinerary based on user input."""
        # Validate configuration
        is_valid, message = self.validate_configuration()
        if not is_valid:
            return message
        
        # Extract information from user input
        destination = extract_destination(user_input)
        if not destination:
            return "I couldn't identify a destination in your request. Please specify where you want to travel."
        
        personalities = detect_personality_prefs(user_input)
        date_obj = parse_natural_date(user_input) or None
        date_str = date_obj.strftime('%B %d, %Y') if date_obj else "flexible dates"
        
        # Perform search to gather context
        query = f"{destination} travel guide best attractions, activities, restaurants for {', '.join(personalities)} travelers"
        results = self.search.search(query)
        
        if not results:
            return f"I couldn't find travel information for {destination}. Please try another destination or check your internet connection."
        
        # Format context from search results
        context = "\n".join([
            f"Title: {r.get('title', '')}\nLink: {r.get('link', '')}\nSnippet: {r.get('snippet', '')}"
            for r in results[:5]
        ])
        
        # Generate itinerary with LLM
        prompt = f"""
        Based on the user's personality {personalities} and their travel destination {destination} on {date_str},
        generate a concise 3-day travel itinerary.

        Use this context:
        {context}

        The itinerary MUST follow this format:
        
        # Day 1
        - Morning: [Brief activity description] at [EXACT PLACE NAME]
        - Afternoon: [Brief activity description] at [EXACT PLACE NAME]  
        - Evening: [Brief activity description] at [EXACT PLACE NAME]
        
        # Day 2
        - Morning: [Brief activity description] at [EXACT PLACE NAME]
        - Afternoon: [Brief activity description] at [EXACT PLACE NAME]
        - Evening: [Brief activity description] at [EXACT PLACE NAME]
        
        # Day 3
        - Morning: [Brief activity description] at [EXACT PLACE NAME]
        - Afternoon: [Brief activity description] at [EXACT PLACE NAME]
        - Evening: [Brief activity description] at [EXACT PLACE NAME]

        IMPORTANT RULES:
        1. Each activity MUST include a specific, mappable place name (museum, landmark, restaurant, etc.)
        2. Keep activities short and concise
        3. Include ratings for restaurants (e.g., 4.5/5)
        4. Day numbers must be numerical (1, 2, 3) and not written as text
        5. Make sure to highlight the main attractions of {destination}
        6. Include at least one local secret or hidden gem
        7. Align with the user's {personalities} interests
        8. Use proper Markdown formatting with # for day headers
        """
        
        try:
            return self.generate_text(prompt)
        except Exception as e:
            return f"Error generating itinerary: {str(e)}"
    
    def answer_travel_question(self, user_input):
        """Answer travel-related questions using the LLM."""
        # Validate configuration
        is_valid, message = self.validate_configuration()
        if not is_valid:
            return message
        
        # Generate response with LLM
        prompt = f"""
        You are a helpful travel assistant. Answer the following travel-related question:
        
        {user_input}
        
        Only answer if this is related to travel, tourism, vacation planning, or destinations.
        If the question is not related to travel, politely explain that you can only help with travel topics.
        Keep your answer concise but informative.
        """
        
        try:
            return self.generate_text(prompt)
        except Exception as e:
            return f"Error answering question: {str(e)}"
