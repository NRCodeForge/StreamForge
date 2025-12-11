# services/service_provider.py

"""
Stellt globale Singleton-Instanzen der Services bereit.
"""

from services.like_challenge_service import LikeChallengeService
from services.subathon_service import SubathonService
from services.wish_service import WishService
from services.audio_service import AudioService
from services.command_service import CommandService
from services.twitch_service import TwitchService
from services.currency_service import CurrencyService

# Globale Singleton-Instanzen
like_service_instance = LikeChallengeService()
subathon_service_instance = SubathonService()
wish_service_instance = WishService()
audio_service_instance = AudioService()
command_service_instance = CommandService()
twitch_service_instance = TwitchService()
currency_service_instance = CurrencyService()