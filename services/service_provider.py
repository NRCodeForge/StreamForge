# services/service_provider.py

"""
Stellt globale Singleton-Instanzen der Services bereit.
Dies stellt sicher, dass die API und die GUI-Komponenten
dieselben Daten und dieselben Hintergrund-Threads (z.B. für den Tikfinity-Client) teilen.
"""

from services.like_challenge_service import LikeChallengeService
from services.subathon_service import SubathonService
from services.wish_service import WishService
from services.audio_service import AudioService

# Globale Singleton-Instanzen
like_service_instance = LikeChallengeService()
subathon_service_instance = SubathonService()
wish_service_instance = WishService()
audio_service_instance = AudioService()