// Main JavaScript for Travel Planner Application

// Global variables
let map;
let markers = [];
let markerCluster;
let currentItineraryId = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the map
    initMap();
    
    // Check API keys
    checkApiKeys();
    
    // Load itineraries
    loadItineraries();
    
    // Load chat history
    loadChatHistory();
    
    // Set up event listeners
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // Chat input
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
    
    // Send button
    const sendButton = document.getElementById('send-button');
    if (sendButton) {
        sendButton.addEventListener('click', sendMessage);
    }
}

// Initialize the map
function initMap() {
    // Create a map centered on a default location
    map = L.map('map').setView([40.7128, -74.0060], 10);
    
    // Add the OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    
    // Create a marker cluster group
    markerCluster = L.markerClusterGroup();
    map.addLayer(markerCluster);
    
    // Load default map data
    loadMapData();
}

// Check if API keys are configured
function checkApiKeys() {
    fetch('/api/api-keys/')
        .then(response => response.json())
        .then(data => {
            const hasSerperKey = data.some(key => key.name === 'serper');
            const hasGoogleKey = data.some(key => key.name === 'google');
            
            const apiWarning = document.getElementById('api-warning');
            if (apiWarning) {
                if (!hasSerperKey || !hasGoogleKey) {
                    apiWarning.style.display = 'block';
                } else {
                    apiWarning.style.display = 'none';
                }
            }
        })
        .catch(error => {
            console.error('Error checking API keys:', error);
            const apiWarning = document.getElementById('api-warning');
            if (apiWarning) {
                apiWarning.style.display = 'block';
            }
        });
}

// Load all itineraries
function loadItineraries() {
    fetch('/api/get-itineraries/')
        .then(response => response.json())
        .then(data => {
            const itinerariesList = document.getElementById('itineraries-list');
            if (!itinerariesList) return;
            
            itinerariesList.innerHTML = '';
            
            if (data.length === 0) {
                itinerariesList.innerHTML = '<p class="text-muted">No itineraries yet. Use the chat to create one!</p>';
                return;
            }
            
            data.forEach(itinerary => {
                const item = document.createElement('a');
                item.href = '#';
                item.className = 'list-group-item list-group-item-action';
                item.textContent = itinerary.title;
                item.dataset.id = itinerary.id;
                
                item.addEventListener('click', function(e) {
                    e.preventDefault();
                    loadItinerary(itinerary.id);
                });
                
                itinerariesList.appendChild(item);
            });
            
            // Load the first itinerary by default
            if (data.length > 0) {
                loadItinerary(data[0].id);
            }
        })
        .catch(error => {
            console.error('Error loading itineraries:', error);
            const itinerariesList = document.getElementById('itineraries-list');
            if (itinerariesList) {
                itinerariesList.innerHTML = '<p class="text-danger">Error loading itineraries. Please try again later.</p>';
            }
        });
}

// Load a specific itinerary
function loadItinerary(id) {
    currentItineraryId = id;
    
    // Highlight the selected itinerary in the list
    const items = document.querySelectorAll('#itineraries-list a');
    items.forEach(item => {
        if (item.dataset.id == id) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
    
    fetch(`/api/get-itinerary/${id}/`)
        .then(response => response.json())
        .then(data => {
            // Set the itinerary title
            const itineraryTitle = document.getElementById('itinerary-title');
            if (itineraryTitle) {
                itineraryTitle.textContent = data.title;
            }
            
            // Clear the current days
            const daysContainer = document.getElementById('itinerary-days');
            if (!daysContainer) return;
            
            daysContainer.innerHTML = '';
            
            // Add each day
            if (data.days && data.days.length > 0) {
                data.days.sort((a, b) => a.day_number - b.day_number);
                
                data.days.forEach(day => {
                    const dayElement = document.createElement('div');
                    dayElement.className = 'day-accordion mb-3';
                    
                    const dayHeader = document.createElement('div');
                    dayHeader.className = 'day-header';
                    dayHeader.innerHTML = `
                        <h6 class="mb-0">Day ${day.day_number}</h6>
                        <i class="fas fa-chevron-down"></i>
                    `;
                    
                    const dayContent = document.createElement('div');
                    dayContent.className = 'day-content';
                    dayContent.innerHTML = formatItineraryContent(day.content);
                    
                    // Toggle content when clicking the header
                    dayHeader.addEventListener('click', function() {
                        dayContent.style.display = 
                            dayContent.style.display === 'none' ? 'block' : 'none';
                        
                        // Toggle arrow direction
                        const arrow = this.querySelector('i');
                        arrow.classList.toggle('fa-chevron-down');
                        arrow.classList.toggle('fa-chevron-up');
                    });
                    
                    dayElement.appendChild(dayHeader);
                    dayElement.appendChild(dayContent);
                    daysContainer.appendChild(dayElement);
                });
            } else {
                // If no days, just display the content
                const contentElement = document.createElement('div');
                contentElement.innerHTML = formatItineraryContent(data.content);
                daysContainer.appendChild(contentElement);
            }
            
            // Update the map
            loadMapData(id);
        })
        .catch(error => {
            console.error('Error loading itinerary:', error);
            const itineraryTitle = document.getElementById('itinerary-title');
            const daysContainer = document.getElementById('itinerary-days');
            
            if (itineraryTitle) {
                itineraryTitle.textContent = 'Error loading itinerary';
            }
            
            if (daysContainer) {
                daysContainer.innerHTML = '<p class="text-danger">Could not load the itinerary. Please try again later.</p>';
            }
        });
}

// Format itinerary content with clickable place tags
function formatItineraryContent(content) {
    if (!content) return '';
    
    // Convert markdown headings
    content = content.replace(/### (.*)/g, '<h5>$1</h5>');
    content = content.replace(/## (.*)/g, '<h4>$1</h4>');
    content = content.replace(/# (.*)/g, '<h3>$1</h3>');
    
    // Convert markdown lists
    content = content.replace(/^\s*[\*\-]\s+(.*)$/gm, '<li>$1</li>');
    content = content.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
    
    // Convert markdown bold
    content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Convert markdown italic
    content = content.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Convert new lines
    content = content.replace(/\n/g, '<br>');
    
    return content;
}

// Load map data
function loadMapData(itineraryId = null) {
    const url = itineraryId ? 
        `/api/map-data/${itineraryId}/` : 
        '/api/map-data/';
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            // Clear existing markers
            clearMapMarkers();
            
            // If there's a destination, center the map on it
            if (data.destination && data.destination.latitude && data.destination.longitude) {
                const lat = data.destination.latitude;
                const lng = data.destination.longitude;
                
                map.setView([lat, lng], 11);
                
                // Add a marker for the destination
                const destinationMarker = L.marker([lat, lng], {
                    icon: L.divIcon({
                        className: 'custom-div-icon',
                        html: `<div class="custom-map-pin"></div>`,
                        iconSize: [30, 30],
                        iconAnchor: [15, 15]
                    })
                }).bindPopup(`<strong>${data.destination.name}</strong><br>Destination`);
                
                markers.push(destinationMarker);
                map.addLayer(destinationMarker);
            }
            
            // Add markers for each place
            if (data.places && data.places.length > 0) {
                const validPlaces = data.places.filter(place => place.latitude && place.longitude);
                
                validPlaces.forEach(place => {
                    const placeMarker = L.marker([place.latitude, place.longitude])
                        .bindPopup(`<strong>${place.name}</strong>${place.description ? '<br>' + place.description : ''}`);
                    
                    markers.push(placeMarker);
                    markerCluster.addLayer(placeMarker);
                });
                
                // Fit map to markers if there are any
                if (markers.length > 0) {
                    const group = L.featureGroup(markers);
                    map.fitBounds(group.getBounds().pad(0.1));
                }
            }
        })
        .catch(error => {
            console.error('Error loading map data:', error);
        });
}

// Clear all markers from the map
function clearMapMarkers() {
    markers.forEach(marker => {
        if (map.hasLayer(marker)) {
            map.removeLayer(marker);
        }
    });
    markerCluster.clearLayers();
    markers = [];
}

// Load chat history
function loadChatHistory() {
    fetch('/api/chat-history/')
        .then(response => response.json())
        .then(data => {
            const chatMessages = document.getElementById('chat-messages');
            if (!chatMessages) return;
            
            chatMessages.innerHTML = '';
            
            if (data.length === 0) {
                // Add welcome message
                addMessageToChat('assistant', "Hi! I'm your travel assistant. I can help you plan trips and answer travel-related questions. Try asking me about destinations or type \"/add\" followed by a destination to create a new itinerary!");
                return;
            }
            
            data.forEach(message => {
                addMessageToChat(message.role, message.content);
            });
            
            // Scroll to the bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;
        })
        .catch(error => {
            console.error('Error loading chat history:', error);
            
            // Add error message
            const chatMessages = document.getElementById('chat-messages');
            if (chatMessages) {
                chatMessages.innerHTML = '';
                addMessageToChat('assistant', "Sorry, I couldn't load your chat history. Please try refreshing the page.");
            }
        });
}

// Add a message to the chat
function addMessageToChat(role, content) {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;
    
    const messageElement = document.createElement('div');
    messageElement.className = role === 'user' ? 'message message-user' : 'message message-assistant';
    messageElement.textContent = content;
    
    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Send a message to the chat
function sendMessage() {
    const input = document.getElementById('chat-input');
    if (!input) return;
    
    const message = input.value.trim();
    if (message === '') return;
    
    // Add the message to the chat
    addMessageToChat('user', message);
    
    // Clear the input
    input.value = '';
    
    // Add a typing indicator
    const chatMessages = document.getElementById('chat-messages');
    const typingIndicator = document.createElement('div');
    typingIndicator.className = 'message message-assistant typing-indicator';
    typingIndicator.innerHTML = '<span>Thinking</span><span class="dot">.</span><span class="dot">.</span><span class="dot">.</span>';
    chatMessages.appendChild(typingIndicator);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Send the message to the server
    fetch('/api/chat-message/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'Accept': 'application/json'
        },
        credentials: 'same-origin',
        body: JSON.stringify({ message: message }),
    })
    .then(response => response.json())
    .then(data => {
        // Remove the typing indicator
        chatMessages.removeChild(typingIndicator);
        
        // Add the response to the chat
        addMessageToChat('assistant', data.message);
        
        // If an itinerary was created, reload the itineraries
        if (data.itinerary_id) {
            loadItineraries();
            loadItinerary(data.itinerary_id);
        }
    })
    .catch(error => {
        console.error('Error sending message:', error);
        
        // Remove the typing indicator
        chatMessages.removeChild(typingIndicator);
        
        // Add an error message
        addMessageToChat('assistant', 'Sorry, something went wrong. Please try again.');
    });
}

// Get CSRF Token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}