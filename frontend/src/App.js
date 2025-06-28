import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const App = () => {
  const [stations, setStations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedRegion, setSelectedRegion] = useState('all');
  const [currentStation, setCurrentStation] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [favorites, setFavorites] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [showFavorites, setShowFavorites] = useState(false);
  const [volume, setVolume] = useState(0.7);
  const audioRef = useRef(null);

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    fetchStations();
    fetchFavorites();
  }, [selectedRegion]);

  const fetchStations = async () => {
    try {
      setLoading(true);
      const endpoint = searchQuery 
        ? `/api/search?q=${encodeURIComponent(searchQuery)}&region=${selectedRegion}&limit=50`
        : `/api/stations?region=${selectedRegion}&limit=50`;
      
      const response = await fetch(`${backendUrl}${endpoint}`);
      const data = await response.json();
      setStations(data);
    } catch (error) {
      console.error('Error fetching stations:', error);
      setStations([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchFavorites = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/favorites?user_id=demo_user`);
      const data = await response.json();
      setFavorites(data);
    } catch (error) {
      console.error('Error fetching favorites:', error);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    fetchStations();
  };

  const playStation = (station) => {
    if (currentStation?.stationuuid === station.stationuuid && isPlaying) {
      pauseStation();
      return;
    }

    setCurrentStation(station);
    if (audioRef.current) {
      audioRef.current.src = station.url_resolved || station.url;
      audioRef.current.volume = volume;
      audioRef.current.play()
        .then(() => setIsPlaying(true))
        .catch(error => {
          console.error('Error playing station:', error);
          alert('Unable to play this station. It might be offline or have connection issues.');
        });
    }
  };

  const pauseStation = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
    }
  };

  const addToFavorites = async (station) => {
    try {
      const response = await fetch(`${backendUrl}/api/favorites`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: 'demo_user',
          station_uuid: station.stationuuid,
          station_name: station.name,
          country: station.country
        })
      });
      
      const result = await response.json();
      if (!result.already_exists) {
        fetchFavorites();
        alert('Station added to favorites!');
      } else {
        alert('Station is already in your favorites!');
      }
    } catch (error) {
      console.error('Error adding to favorites:', error);
      alert('Error adding to favorites');
    }
  };

  const removeFromFavorites = async (stationUuid) => {
    try {
      await fetch(`${backendUrl}/api/favorites/${stationUuid}?user_id=demo_user`, {
        method: 'DELETE'
      });
      fetchFavorites();
      alert('Station removed from favorites!');
    } catch (error) {
      console.error('Error removing from favorites:', error);
    }
  };

  const handleVolumeChange = (e) => {
    const newVolume = e.target.value;
    setVolume(newVolume);
    if (audioRef.current) {
      audioRef.current.volume = newVolume;
    }
  };

  const isFavorite = (stationUuid) => {
    return favorites.some(fav => fav.station_uuid === stationUuid);
  };

  const displayStations = showFavorites 
    ? stations.filter(station => isFavorite(station.stationuuid))
    : stations;

  return (
    <div className="app">
      {/* Hero Section */}
      <div className="hero-section">
        <div className="hero-overlay">
          <div className="hero-content">
            <h1 className="hero-title">
              <span className="gradient-text">Worldwide Radio</span>
            </h1>
            <p className="hero-subtitle">
              Discover the sounds of America & Africa - Stream live radio from two vibrant continents
            </p>
          </div>
        </div>
      </div>

      <div className="main-content">
        {/* Controls Section */}
        <div className="controls-section">
          <div className="controls-container">
            {/* Search */}
            <form onSubmit={handleSearch} className="search-form">
              <input
                type="text"
                placeholder="Search stations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="search-input"
              />
              <button type="submit" className="search-btn">
                🔍 Search
              </button>
            </form>

            {/* Region Filter */}
            <div className="region-filter">
              <button 
                className={`filter-btn ${selectedRegion === 'all' ? 'active' : ''}`}
                onClick={() => setSelectedRegion('all')}
              >
                🌍 All Regions
              </button>
              <button 
                className={`filter-btn ${selectedRegion === 'american' ? 'active' : ''}`}
                onClick={() => setSelectedRegion('american')}
              >
                🇺🇸 American
              </button>
              <button 
                className={`filter-btn ${selectedRegion === 'african' ? 'active' : ''}`}
                onClick={() => setSelectedRegion('african')}
              >
                🌍 African
              </button>
            </div>

            {/* Favorites Toggle */}
            <button 
              className={`favorites-toggle ${showFavorites ? 'active' : ''}`}
              onClick={() => setShowFavorites(!showFavorites)}
            >
              ❤️ {showFavorites ? 'Show All' : `Favorites (${favorites.length})`}
            </button>
          </div>
        </div>

        {/* Current Playing Station */}
        {currentStation && (
          <div className="now-playing">
            <div className="now-playing-content">
              <div className="station-info">
                <h3>🎵 Now Playing</h3>
                <h2>{currentStation.name}</h2>
                <p>{currentStation.country} • {currentStation.tags}</p>
              </div>
              <div className="player-controls">
                <button 
                  className={`play-btn ${isPlaying ? 'playing' : ''}`}
                  onClick={() => isPlaying ? pauseStation() : playStation(currentStation)}
                >
                  {isPlaying ? '⏸️' : '▶️'}
                </button>
                <div className="volume-control">
                  <span>🔊</span>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={volume}
                    onChange={handleVolumeChange}
                    className="volume-slider"
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Stations Grid */}
        <div className="stations-section">
          <div className="section-header">
            <h2>
              {showFavorites ? '❤️ Your Favorites' : 
               selectedRegion === 'american' ? '🇺🇸 American Radio Stations' :
               selectedRegion === 'african' ? '🌍 African Radio Stations' :
               '🌍 American & African Radio Stations'}
            </h2>
            <p className="station-count">
              {loading ? 'Loading...' : `${displayStations.length} stations found`}
            </p>
          </div>

          {loading ? (
            <div className="loading">
              <div className="loading-spinner"></div>
              <p>Loading radio stations...</p>
            </div>
          ) : (
            <div className="stations-grid">
              {displayStations.map((station) => (
                <div key={station.stationuuid} className="station-card">
                  <div className="station-header">
                    <div className="station-favicon">
                      {station.favicon ? (
                        <img src={station.favicon} alt="" onError={(e) => e.target.style.display = 'none'} />
                      ) : (
                        <div className="default-icon">📻</div>
                      )}
                    </div>
                    <div className="station-info">
                      <h3>{station.name}</h3>
                      <p className="station-country">📍 {station.country}</p>
                      {station.tags && (
                        <p className="station-tags">🎵 {station.tags.split(',').slice(0, 3).join(', ')}</p>
                      )}
                    </div>
                  </div>
                  
                  <div className="station-meta">
                    {station.bitrate > 0 && (
                      <span className="bitrate">{station.bitrate} kbps</span>
                    )}
                    {station.codec && (
                      <span className="codec">{station.codec.toUpperCase()}</span>
                    )}
                  </div>

                  <div className="station-controls">
                    <button 
                      className={`play-station-btn ${
                        currentStation?.stationuuid === station.stationuuid && isPlaying ? 'playing' : ''
                      }`}
                      onClick={() => playStation(station)}
                    >
                      {currentStation?.stationuuid === station.stationuuid && isPlaying ? '⏸️ Pause' : '▶️ Play'}
                    </button>
                    
                    {isFavorite(station.stationuuid) ? (
                      <button 
                        className="favorite-btn favorited"
                        onClick={() => removeFromFavorites(station.stationuuid)}
                        title="Remove from favorites"
                      >
                        ❤️
                      </button>
                    ) : (
                      <button 
                        className="favorite-btn"
                        onClick={() => addToFavorites(station)}
                        title="Add to favorites"
                      >
                        🤍
                      </button>
                    )}
                  </div>
                </div>
              ))}
              
              {displayStations.length === 0 && !loading && (
                <div className="no-results">
                  <h3>No stations found</h3>
                  <p>Try adjusting your search or region filter</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Hidden Audio Element */}
      <audio
        ref={audioRef}
        onError={() => {
          setIsPlaying(false);
          alert('Unable to play this station. It might be offline.');
        }}
        onEnded={() => setIsPlaying(false)}
        crossOrigin="anonymous"
      />
    </div>
  );
};

export default App;