import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import httpx
from pydantic import BaseModel
from typing import List, Optional
import asyncio
from datetime import datetime

app = FastAPI(title="Worldwide Radio Station API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/radio_db')

@app.on_event("startup")
async def startup_db_client():
    app.mongodb_client = AsyncIOMotorClient(MONGO_URL)
    app.mongodb = app.mongodb_client.get_database("radio_db")
    print(f"Connected to MongoDB at {MONGO_URL}")

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()

# Data models
class RadioStation(BaseModel):
    stationuuid: str
    name: str
    url: str
    url_resolved: str
    country: str
    tags: str
    favicon: Optional[str] = ""
    bitrate: Optional[int] = 0
    codec: Optional[str] = ""

class FavoriteStation(BaseModel):
    user_id: str = "demo_user"
    station_uuid: str
    station_name: str
    country: str
    added_at: Optional[datetime] = None

# API endpoints
@app.get("/")
async def root():
    return {"message": "Worldwide Radio Station API - American & African Stations"}

@app.get("/api/stations")
async def get_radio_stations(
    region: str = "all", 
    limit: int = 50,
    search: Optional[str] = None
):
    """Fetch radio stations from Radio-Browser API focusing on American and African stations"""
    try:
        # Define American and African countries
        american_countries = ["United States", "Canada", "Mexico", "Brazil", "Argentina", "Chile"]
        african_countries = ["South Africa", "Nigeria", "Kenya", "Ghana", "Egypt", "Morocco", "Ethiopia", "Tanzania", "Uganda", "Zimbabwe"]
        
        if region == "american":
            countries = american_countries
        elif region == "african":
            countries = african_countries
        else:
            countries = american_countries + african_countries
        
        all_stations = []
        
        # Fetch stations for each country
        async with httpx.AsyncClient(timeout=30.0) as client:
            for country in countries[:6]:  # Limit to avoid timeout
                try:
                    params = {
                        "country": country,
                        "limit": max(5, limit // len(countries)),
                        "order": "clickcount",
                        "reverse": "true"
                    }
                    if search:
                        params["name"] = search
                    
                    response = await client.get(
                        "https://de1.api.radio-browser.info/json/stations/search",
                        params=params
                    )
                    if response.status_code == 200:
                        stations = response.json()
                        # Filter out stations with empty URLs
                        valid_stations = [s for s in stations if s.get('url_resolved') and s.get('name')]
                        all_stations.extend(valid_stations[:10])  # Take top 10 from each country
                except Exception as e:
                    print(f"Error fetching stations for {country}: {e}")
                    continue
        
        # Sort by click count and limit results
        all_stations.sort(key=lambda x: x.get('clickcount', 0), reverse=True)
        return all_stations[:limit]
        
    except Exception as e:
        print(f"Error in get_radio_stations: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching stations: {str(e)}")

@app.get("/api/stations/by-region/{region}")
async def get_stations_by_region(region: str, limit: int = 30):
    """Get stations filtered by region (american or african)"""
    return await get_radio_stations(region=region, limit=limit)

@app.get("/api/search")
async def search_stations(q: str, region: str = "all", limit: int = 20):
    """Search for radio stations by name or tags"""
    return await get_radio_stations(region=region, limit=limit, search=q)

@app.post("/api/favorites")
async def add_favorite_station(favorite: FavoriteStation):
    """Add station to user favorites"""
    try:
        favorite.added_at = datetime.utcnow()
        existing = await app.mongodb.favorites.find_one({
            "user_id": favorite.user_id,
            "station_uuid": favorite.station_uuid
        })
        
        if existing:
            return {"message": "Station already in favorites", "already_exists": True}
        
        result = await app.mongodb.favorites.insert_one(favorite.dict())
        return {"message": "Station added to favorites", "id": str(result.inserted_id), "already_exists": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/favorites")
async def get_user_favorites(user_id: str = "demo_user"):
    """Get user's favorite stations"""
    try:
        favorites = await app.mongodb.favorites.find({"user_id": user_id}).to_list(100)
        # Convert ObjectId to string for JSON serialization
        for fav in favorites:
            fav["_id"] = str(fav["_id"])
        return favorites
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/favorites/{station_uuid}")
async def remove_favorite(station_uuid: str, user_id: str = "demo_user"):
    """Remove station from favorites"""
    try:
        result = await app.mongodb.favorites.delete_one({
            "user_id": user_id,
            "station_uuid": station_uuid
        })
        if result.deleted_count:
            return {"message": "Station removed from favorites"}
        else:
            raise HTTPException(status_code=404, detail="Favorite not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/countries")
async def get_available_countries():
    """Get list of available countries"""
    return {
        "american": ["United States", "Canada", "Mexico", "Brazil", "Argentina", "Chile"],
        "african": ["South Africa", "Nigeria", "Kenya", "Ghana", "Egypt", "Morocco", "Ethiopia", "Tanzania", "Uganda", "Zimbabwe"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)