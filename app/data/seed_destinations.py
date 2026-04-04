"""
Seed Kuriftu Destinations and Room Types
"""
import json
from sqlalchemy.orm import Session
from app.models.destinations import Destination, DestinationRoomType


def seed_destinations(db: Session):
    """Seed 5 Kuriftu destinations with room types"""
    
    # Clear existing data
    db.query(DestinationRoomType).delete()
    db.query(Destination).delete()
    db.commit()
    
    # Define destinations
    destinations_data = [
        {
            "code": "ENTOTO",
            "name": "Kuriftu Entoto Adventure Park",
            "location": "Entoto, Addis Ababa",
            "description": "Mountain resort with adventure activities and stunning city views",
            "amenities": json.dumps(["Adventure Park", "Hiking Trails", "Mountain Biking", "Restaurant", "WiFi", "Parking"])
        },
        {
            "code": "AWASH",
            "name": "Kuriftu Resort and Spa Awash",
            "location": "Awash, Oromia",
            "description": "Luxury resort near Awash National Park with wildlife viewing",
            "amenities": json.dumps(["Spa", "Pool", "Wildlife Tours", "Restaurant", "Bar", "WiFi", "Gym"])
        },
        {
            "code": "TANA",
            "name": "Kuriftu Resort and Spa Lake Tana",
            "location": "Bahir Dar, Amhara",
            "description": "Lakeside paradise on Ethiopia's largest lake with monastery tours",
            "amenities": json.dumps(["Lake View", "Boat Tours", "Spa", "Pool", "Restaurant", "WiFi", "Cultural Tours"])
        },
        {
            "code": "BISHOFTU",
            "name": "Kuriftu Resort and Spa Bishoftu",
            "location": "Bishoftu (Debre Zeit), Oromia",
            "description": "Crater lake resort with water sports and relaxation",
            "amenities": json.dumps(["Crater Lake", "Water Sports", "Spa", "Pool", "Restaurant", "WiFi", "Gym"])
        },
        {
            "code": "AFRICAN_VILLAGE",
            "name": "Kuriftu Resort and Spa African Village",
            "location": "Ziway, Oromia",
            "description": "Cultural village experience with traditional Ethiopian hospitality",
            "amenities": json.dumps(["Cultural Village", "Traditional Dining", "Spa", "Pool", "Coffee Ceremony", "WiFi"])
        }
    ]
    
    # Insert destinations
    for dest_data in destinations_data:
        destination = Destination(**dest_data)
        db.add(destination)
    
    db.commit()
    
    # Define room types for each destination
    room_types_data = [
        # ENTOTO
        {"destination_code": "ENTOTO", "room_type": "STANDARD", "room_type_name": "Standard Room", 
         "total_rooms": 23, "base_rate_etb": 3500, "base_rate_usd": 65, "max_occupancy": 2, "size_sqm": 30,
         "description": "Comfortable room with mountain views",
         "amenities": json.dumps(["WiFi", "TV", "Mini Bar", "Mountain View"]),
         "services_included": json.dumps(["WiFi", "Breakfast", "Parking"])},
        
        {"destination_code": "ENTOTO", "room_type": "DELUXE", "room_type_name": "Deluxe Room", 
         "total_rooms": 15, "base_rate_etb": 5500, "base_rate_usd": 100, "max_occupancy": 3, "size_sqm": 45,
         "description": "Spacious room with premium amenities",
         "amenities": json.dumps(["WiFi", "Smart TV", "Mini Bar", "Balcony", "Mountain View"]),
         "services_included": json.dumps(["WiFi", "Breakfast", "Parking", "Welcome Drink"])},
        
        {"destination_code": "ENTOTO", "room_type": "SUITE", "room_type_name": "Executive Suite", 
         "total_rooms": 8, "base_rate_etb": 8500, "base_rate_usd": 155, "max_occupancy": 4, "size_sqm": 70,
         "description": "Luxury suite with living area and panoramic views",
         "amenities": json.dumps(["WiFi", "Smart TV", "Mini Bar", "Living Room", "Balcony", "Jacuzzi"]),
         "services_included": json.dumps(["WiFi", "Breakfast", "Parking", "Welcome Drink", "Spa Access"])},
        
        # AWASH
        {"destination_code": "AWASH", "room_type": "STANDARD", "room_type_name": "Standard Room", 
         "total_rooms": 20, "base_rate_etb": 4000, "base_rate_usd": 75, "max_occupancy": 2, "size_sqm": 32,
         "description": "Comfortable room with garden views",
         "amenities": json.dumps(["WiFi", "TV", "Mini Bar", "Garden View"]),
         "services_included": json.dumps(["WiFi", "Breakfast", "Pool Access"])},
        
        {"destination_code": "AWASH", "room_type": "DELUXE", "room_type_name": "Deluxe Room", 
         "total_rooms": 18, "base_rate_etb": 6000, "base_rate_usd": 110, "max_occupancy": 3, "size_sqm": 48,
         "description": "Spacious room with wildlife viewing deck",
         "amenities": json.dumps(["WiFi", "Smart TV", "Mini Bar", "Balcony", "Wildlife View"]),
         "services_included": json.dumps(["WiFi", "Breakfast", "Pool Access", "Wildlife Tour"])},
        
        {"destination_code": "AWASH", "room_type": "SUITE", "room_type_name": "Safari Suite", 
         "total_rooms": 10, "base_rate_etb": 9500, "base_rate_usd": 175, "max_occupancy": 4, "size_sqm": 75,
         "description": "Luxury suite with private deck and wildlife views",
         "amenities": json.dumps(["WiFi", "Smart TV", "Mini Bar", "Living Room", "Private Deck", "Jacuzzi"]),
         "services_included": json.dumps(["WiFi", "Breakfast", "Pool Access", "Spa Access", "Private Wildlife Tour"])},
        
        # TANA
        {"destination_code": "TANA", "room_type": "STANDARD", "room_type_name": "Standard Room", 
         "total_rooms": 25, "base_rate_etb": 4500, "base_rate_usd": 85, "max_occupancy": 2, "size_sqm": 35,
         "description": "Comfortable room with lake glimpses",
         "amenities": json.dumps(["WiFi", "TV", "Mini Bar", "Lake Glimpse"]),
         "services_included": json.dumps(["WiFi", "Breakfast", "Pool Access"])},
        
        {"destination_code": "TANA", "room_type": "DELUXE", "room_type_name": "Lake View Deluxe", 
         "total_rooms": 20, "base_rate_etb": 6500, "base_rate_usd": 120, "max_occupancy": 3, "size_sqm": 50,
         "description": "Spacious room with direct lake views",
         "amenities": json.dumps(["WiFi", "Smart TV", "Mini Bar", "Balcony", "Lake View"]),
         "services_included": json.dumps(["WiFi", "Breakfast", "Pool Access", "Boat Tour"])},
        
        {"destination_code": "TANA", "room_type": "SUITE", "room_type_name": "Lakeside Suite", 
         "total_rooms": 12, "base_rate_etb": 10000, "base_rate_usd": 185, "max_occupancy": 4, "size_sqm": 80,
         "description": "Luxury suite with panoramic lake views",
         "amenities": json.dumps(["WiFi", "Smart TV", "Mini Bar", "Living Room", "Balcony", "Jacuzzi", "Lake View"]),
         "services_included": json.dumps(["WiFi", "Breakfast", "Pool Access", "Spa Access", "Private Boat Tour", "Monastery Tour"])},
        
        # BISHOFTU
        {"destination_code": "BISHOFTU", "room_type": "STANDARD", "room_type_name": "Standard Room", 
         "total_rooms": 28, "base_rate_etb": 3800, "base_rate_usd": 70, "max_occupancy": 2, "size_sqm": 33,
         "description": "Comfortable room near crater lake",
         "amenities": json.dumps(["WiFi", "TV", "Mini Bar", "Lake Access"]),
         "services_included": json.dumps(["WiFi", "Breakfast", "Pool Access"])},
        
        {"destination_code": "BISHOFTU", "room_type": "DELUXE", "room_type_name": "Crater View Deluxe", 
         "total_rooms": 22, "base_rate_etb": 5800, "base_rate_usd": 105, "max_occupancy": 3, "size_sqm": 47,
         "description": "Spacious room with crater lake views",
         "amenities": json.dumps(["WiFi", "Smart TV", "Mini Bar", "Balcony", "Crater View"]),
         "services_included": json.dumps(["WiFi", "Breakfast", "Pool Access", "Water Sports"])},
        
        {"destination_code": "BISHOFTU", "room_type": "SUITE", "room_type_name": "Lakeside Suite", 
         "total_rooms": 10, "base_rate_etb": 9000, "base_rate_usd": 165, "max_occupancy": 4, "size_sqm": 72,
         "description": "Luxury suite with direct lake access",
         "amenities": json.dumps(["WiFi", "Smart TV", "Mini Bar", "Living Room", "Private Terrace", "Jacuzzi"]),
         "services_included": json.dumps(["WiFi", "Breakfast", "Pool Access", "Spa Access", "Private Water Sports"])},
        
        # AFRICAN_VILLAGE
        {"destination_code": "AFRICAN_VILLAGE", "room_type": "STANDARD", "room_type_name": "Village Room", 
         "total_rooms": 30, "base_rate_etb": 3200, "base_rate_usd": 60, "max_occupancy": 2, "size_sqm": 28,
         "description": "Traditional Ethiopian style room",
         "amenities": json.dumps(["WiFi", "TV", "Traditional Decor"]),
         "services_included": json.dumps(["WiFi", "Breakfast", "Coffee Ceremony"])},
        
        {"destination_code": "AFRICAN_VILLAGE", "room_type": "DELUXE", "room_type_name": "Cultural Deluxe", 
         "total_rooms": 18, "base_rate_etb": 5200, "base_rate_usd": 95, "max_occupancy": 3, "size_sqm": 42,
         "description": "Spacious room with cultural elements",
         "amenities": json.dumps(["WiFi", "Smart TV", "Mini Bar", "Traditional Decor", "Garden View"]),
         "services_included": json.dumps(["WiFi", "Breakfast", "Pool Access", "Coffee Ceremony", "Cultural Show"])},
        
        {"destination_code": "AFRICAN_VILLAGE", "room_type": "SUITE", "room_type_name": "Royal Suite", 
         "total_rooms": 8, "base_rate_etb": 8000, "base_rate_usd": 145, "max_occupancy": 4, "size_sqm": 65,
         "description": "Luxury suite with royal Ethiopian design",
         "amenities": json.dumps(["WiFi", "Smart TV", "Mini Bar", "Living Room", "Private Garden", "Traditional Decor"]),
         "services_included": json.dumps(["WiFi", "Breakfast", "Pool Access", "Spa Access", "Private Coffee Ceremony", "Cultural Experience"])},
    ]
    
    # Insert room types
    for room_data in room_types_data:
        room_type = DestinationRoomType(**room_data)
        db.add(room_type)
    
    db.commit()
    
    print(f"✅ Seeded {len(destinations_data)} destinations with {len(room_types_data)} room types")


if __name__ == "__main__":
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        seed_destinations(db)
    finally:
        db.close()
