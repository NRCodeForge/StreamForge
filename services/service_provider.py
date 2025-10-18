# services/service_provider.py

"""
Stellt globale Singleton-Instanzen der Services bereit.
Dies stellt sicher, dass die API und die GUI-Komponenten
dieselben Daten und dieselben Hintergrund-Threads (z.B. für den Tikfinity-Client) teilen.
"""

from .like_challenge_service import LikeChallengeService
from .subathon_service import SubathonService
from .wish_service import WishService

# Globale Singleton-Instanzen
like_service_instance = LikeChallengeService()
subathon_service_instance = SubathonService()
wish_service_instance = WishService()