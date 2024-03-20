# -*- coding: latin-1 -*-
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# Initialisieren des Geocoders
geolocator = Nominatim(user_agent="geoapiExercises")


def get_location(postal_code):
    """Gibt die geografische Breite und Länge für eine gegebene Postleitzahl zurück."""
    location = geolocator.geocode({'postalcode': postal_code}, country_codes='de')
    if location:
        return location.latitude, location.longitude
    else:
        return None


def calculate_distance(postal_code1, postal_code2):
    """Berechnet die Entfernung in Kilometern zwischen zwei Postleitzahlen."""
    loc1 = get_location(postal_code1)
    loc2 = get_location(postal_code2)

    if loc1 and loc2:
        # Berechnung der Entfernung
        distance = geodesic(loc1, loc2).kilometers
        return distance
    else:
        return "Eine oder beide Postleitzahlen konnten nicht geortet werden."
