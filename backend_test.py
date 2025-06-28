#!/usr/bin/env python3
import requests
import json
import time
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://634c5745-151a-49f7-b585-b1f89de70098.preview.emergentagent.com"
API_BASE_URL = f"{BACKEND_URL}/api"

# Test user ID for favorites
TEST_USER_ID = "test_user_" + datetime.now().strftime("%Y%m%d%H%M%S")

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def print_success(message):
    print(f"{GREEN}✓ {message}{RESET}")

def print_error(message):
    print(f"{RED}✗ {message}{RESET}")

def print_info(message):
    print(f"{YELLOW}ℹ {message}{RESET}")

def test_root_endpoint():
    """Test the root endpoint to ensure server is running"""
    print_info("Testing root endpoint...")
    try:
        # The root endpoint is at the base URL with no /api prefix
        response = requests.get(f"{BACKEND_URL}/")
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "Worldwide Radio Station API" in data["message"]:
                print_success("Root endpoint is working correctly")
                return True
            else:
                print_error(f"Root endpoint returned unexpected data: {data}")
                return False
        else:
            print_error(f"Root endpoint returned status code {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error testing root endpoint: {str(e)}")
        return False

def test_stations_endpoint():
    """Test the /api/stations endpoint with different region filters"""
    print_info("Testing stations endpoint...")
    
    regions = ["all", "american", "african"]
    success = True
    
    for region in regions:
        try:
            print_info(f"  Testing region: {region}")
            response = requests.get(f"{API_BASE_URL}/stations", params={"region": region, "limit": 10})
            
            if response.status_code == 200:
                stations = response.json()
                if isinstance(stations, list) and len(stations) > 0:
                    # Verify station data structure
                    sample_station = stations[0]
                    required_fields = ["stationuuid", "name", "url", "url_resolved", "country"]
                    missing_fields = [field for field in required_fields if field not in sample_station]
                    
                    if not missing_fields:
                        print_success(f"  Region '{region}' returned {len(stations)} stations with valid data structure")
                    else:
                        print_error(f"  Region '{region}' returned stations with missing fields: {missing_fields}")
                        success = False
                else:
                    print_error(f"  Region '{region}' returned no stations or invalid data: {stations}")
                    success = False
            else:
                print_error(f"  Region '{region}' request failed with status code {response.status_code}")
                success = False
        except Exception as e:
            print_error(f"  Error testing region '{region}': {str(e)}")
            success = False
    
    return success

def test_search_endpoint():
    """Test the /api/search endpoint with sample queries"""
    print_info("Testing search endpoint...")
    
    search_queries = ["music", "news", "jazz", "talk"]
    regions = ["all", "american", "african"]
    success = True
    
    for query in search_queries:
        for region in regions:
            try:
                print_info(f"  Testing search query: '{query}' in region: '{region}'")
                response = requests.get(
                    f"{API_BASE_URL}/search", 
                    params={"q": query, "region": region, "limit": 5}
                )
                
                if response.status_code == 200:
                    stations = response.json()
                    if isinstance(stations, list):
                        print_success(f"  Search for '{query}' in '{region}' returned {len(stations)} results")
                    else:
                        print_error(f"  Search for '{query}' in '{region}' returned invalid data: {stations}")
                        success = False
                else:
                    print_error(f"  Search for '{query}' in '{region}' failed with status code {response.status_code}")
                    success = False
            except Exception as e:
                print_error(f"  Error testing search for '{query}' in '{region}': {str(e)}")
                success = False
    
    return success

def test_favorites_system():
    """Test adding, retrieving, and removing favorite stations"""
    print_info("Testing favorites system...")
    
    # Create a test station to add to favorites
    test_station = {
        "user_id": TEST_USER_ID,
        "station_uuid": f"test-station-{int(time.time())}",
        "station_name": "Test Radio Station",
        "country": "Test Country"
    }
    
    try:
        # 1. Add station to favorites
        print_info("  Adding station to favorites...")
        add_response = requests.post(f"{API_BASE_URL}/favorites", json=test_station)
        
        if add_response.status_code != 200:
            print_error(f"  Failed to add station to favorites: {add_response.status_code} - {add_response.text}")
            return False
        
        add_data = add_response.json()
        if "message" in add_data and "added to favorites" in add_data["message"]:
            print_success("  Successfully added station to favorites")
        else:
            print_error(f"  Unexpected response when adding to favorites: {add_data}")
            return False
        
        # 2. Get user favorites
        print_info("  Retrieving user favorites...")
        get_response = requests.get(f"{API_BASE_URL}/favorites", params={"user_id": TEST_USER_ID})
        
        if get_response.status_code != 200:
            print_error(f"  Failed to get favorites: {get_response.status_code} - {get_response.text}")
            return False
        
        favorites = get_response.json()
        if isinstance(favorites, list):
            # Find our test station
            found = False
            for fav in favorites:
                if fav.get("station_uuid") == test_station["station_uuid"]:
                    found = True
                    break
            
            if found:
                print_success(f"  Successfully retrieved favorites, found test station")
            else:
                print_error(f"  Test station not found in favorites: {favorites}")
                return False
        else:
            print_error(f"  Invalid favorites data: {favorites}")
            return False
        
        # 3. Remove station from favorites
        print_info("  Removing station from favorites...")
        delete_response = requests.delete(
            f"{API_BASE_URL}/favorites/{test_station['station_uuid']}",
            params={"user_id": TEST_USER_ID}
        )
        
        if delete_response.status_code != 200:
            print_error(f"  Failed to remove favorite: {delete_response.status_code} - {delete_response.text}")
            return False
        
        delete_data = delete_response.json()
        if "message" in delete_data and "removed from favorites" in delete_data["message"]:
            print_success("  Successfully removed station from favorites")
        else:
            print_error(f"  Unexpected response when removing favorite: {delete_data}")
            return False
        
        # 4. Verify station was removed
        print_info("  Verifying station was removed...")
        verify_response = requests.get(f"{API_BASE_URL}/favorites", params={"user_id": TEST_USER_ID})
        
        if verify_response.status_code != 200:
            print_error(f"  Failed to verify favorites: {verify_response.status_code} - {verify_response.text}")
            return False
        
        verify_favorites = verify_response.json()
        for fav in verify_favorites:
            if fav.get("station_uuid") == test_station["station_uuid"]:
                print_error("  Test station still found in favorites after deletion")
                return False
        
        print_success("  Successfully verified station was removed from favorites")
        return True
        
    except Exception as e:
        print_error(f"  Error testing favorites system: {str(e)}")
        return False

def test_region_specific_endpoints():
    """Test region-specific endpoints"""
    print_info("Testing region-specific endpoints...")
    
    regions = ["american", "african"]
    success = True
    
    for region in regions:
        try:
            print_info(f"  Testing region: {region}")
            response = requests.get(f"{API_BASE_URL}/stations/by-region/{region}", params={"limit": 10})
            
            if response.status_code == 200:
                stations = response.json()
                if isinstance(stations, list) and len(stations) > 0:
                    print_success(f"  Region '{region}' endpoint returned {len(stations)} stations")
                else:
                    print_error(f"  Region '{region}' endpoint returned no stations or invalid data: {stations}")
                    success = False
            else:
                print_error(f"  Region '{region}' endpoint failed with status code {response.status_code}")
                success = False
        except Exception as e:
            print_error(f"  Error testing region '{region}' endpoint: {str(e)}")
            success = False
    
    return success

def test_countries_endpoint():
    """Test the /api/countries endpoint"""
    print_info("Testing countries endpoint...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/countries")
        
        if response.status_code == 200:
            countries_data = response.json()
            
            if not isinstance(countries_data, dict):
                print_error(f"Countries endpoint returned non-dictionary data: {countries_data}")
                return False
            
            required_regions = ["american", "african"]
            missing_regions = [region for region in required_regions if region not in countries_data]
            
            if missing_regions:
                print_error(f"Countries endpoint missing required regions: {missing_regions}")
                return False
            
            # Check if each region has countries
            for region in required_regions:
                countries = countries_data.get(region, [])
                if not countries or not isinstance(countries, list) or len(countries) == 0:
                    print_error(f"Region '{region}' has no countries or invalid data: {countries}")
                    return False
                print_success(f"  Region '{region}' has {len(countries)} countries")
            
            print_success("Countries endpoint is working correctly")
            return True
        else:
            print_error(f"Countries endpoint failed with status code {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error testing countries endpoint: {str(e)}")
        return False

def run_all_tests():
    """Run all API tests and return results"""
    print_info("Starting backend API tests...")
    print_info(f"Backend URL: {BACKEND_URL}")
    print_info(f"API Base URL: {API_BASE_URL}")
    print()
    
    test_results = {
        "root_endpoint": test_root_endpoint(),
        "stations_endpoint": test_stations_endpoint(),
        "search_endpoint": test_search_endpoint(),
        "favorites_system": test_favorites_system(),
        "region_specific_endpoints": test_region_specific_endpoints(),
        "countries_endpoint": test_countries_endpoint()
    }
    
    print()
    print_info("Test Results Summary:")
    all_passed = True
    
    for test_name, result in test_results.items():
        if result:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")
            all_passed = False
    
    if all_passed:
        print()
        print_success("All tests PASSED!")
    else:
        print()
        print_error("Some tests FAILED!")
    
    return test_results

if __name__ == "__main__":
    run_all_tests()