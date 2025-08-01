"""
Configuration settings for NYC Open Data API
Keep this file out of version control

To get your API token:
1. Go to https://opendata.cityofnewyork.us/
2. Sign in or create an account
3. Go to your profile settings
4. Click on "Developer Settings"
5. Create a new application token
"""

# Your NYC Open Data API credentials for Basic Authentication
import os

# Your API Key ID (serves as the username)
API_KEY_ID = os.environ.get("API_KEY_ID", "3qdn29iqbizsqgjpvnd9d4leq")

# Your API Key Secret (serves as the password)
API_KEY_SECRET = os.environ.get("API_KEY_SECRET", "5emfx7sphlceagjmjcm1qh40l70wxaop26vi7ym7c6i9ky8omf")

# Google Maps Geocoding API
# Get your API key from: https://console.cloud.google.com/apis/credentials
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "AIzaSyA4gSJ9LDVqQ9AVxw3zVoHSQQVr_9W2V54")

# NYC Geoclient API credentials (deprecated - using Google Maps instead)
# GEOCLIENT_APP_ID = "2yex1z2mmlwqnhw6nh7cjlynq"
# GEOCLIENT_APP_KEY = "40shw20l258bpklra4ejkuz7ka4twpzt2g534lwh1enxncl6m"
