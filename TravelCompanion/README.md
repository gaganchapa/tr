# Travel Planner Assistant

A comprehensive travel planning application with interactive map visualization, day-wise itinerary display, and an LLM-powered chatbot.

## Features

- **Interactive Map**: Visualize destinations and points of interest with dynamic markers
- **Itinerary Management**: View day-by-day travel plans with expandable sections
- **AI Travel Assistant**: Chat with an AI assistant to answer travel questions and create itineraries
- **API Integration**: Uses Google Generative AI (Gemini) and Serper for up-to-date travel information

## Required API Keys

This application requires two API keys to function fully:

1. **Google AI API Key** (Gemini): For LLM-powered travel recommendations and chat functionality
2. **Serper API Key**: For gathering up-to-date information about travel destinations

## Getting Started

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory with the following:
   ```
   SERPER_API_KEY=your_serper_api_key
   GOOGLE_API_KEY=your_google_api_key
   ```
4. Run the application:
   ```
   python app.py
   ```
5. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```
6. Configure your API keys in the application interface (API Keys section)

## Usage

### Creating an Itinerary

To create a new travel itinerary, use the chat interface with the `/add` command:

```
/add 3 days in Paris with my family
```

### Asking Travel Questions

Simply type your travel-related questions in the chat interface:

```
What are the best months to visit Tokyo?
```

### Viewing Itineraries

Select any itinerary from the sidebar to view:
- Day-by-day breakdown
- Places to visit
- Interactive map with all locations marked

## Technologies Used

- Django (Backend)
- JavaScript (Frontend)
- Leaflet.js (Maps)
- Google Generative AI (LLM)
- Serper API (Search)

## License

MIT