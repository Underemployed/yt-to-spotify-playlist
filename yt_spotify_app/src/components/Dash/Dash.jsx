import  { useEffect, useState } from 'react';
import './Dash.css';

const Dash = () => {
  // State variables to manage user input, fetched data, and UI status
  const [channelId, setChannelId] = useState(''); // Stores the current YouTube Channel ID input
  const [channels, setChannels] = useState([]); // List of previously stored channel IDs
  const [playlists, setPlaylists] = useState([]); // Playlists fetched from the API
  const [loading, setLoading] = useState(false); // Indicates if data is being loaded
  const [importInProgress, setImportInProgress] = useState(false); // Tracks if import is ongoing
  const [progressLog, setProgressLog] = useState([]); // Logs progress messages during import

  // Load stored channels from localStorage on component mount
  useEffect(() => {
    const storedChannels = JSON.parse(localStorage.getItem('channels')) || []; // Retrieve saved channels from localStorage
    setChannels(storedChannels); // Update the channels state with stored data
  }, []);

  // Store new channel IDs in localStorage to maintain history
  const storeChannelId = (id) => {
    if (!channels.includes(id)) { // Avoid duplicate entries
      const updatedChannels = [...channels, id]; // Add new channel ID to the list
      localStorage.setItem('channels', JSON.stringify(updatedChannels)); // Save updated list to localStorage
      setChannels(updatedChannels); // Update state with new channel list
    }
  };

  // Fetch playlists from the backend API using the provided channel ID
  const fetchPlaylists = async () => {
    setLoading(true); // Set loading state to true to indicate API call in progress
    try {
      const response = await fetch('/api/fetch-playlists', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }, // Specify JSON content type
        body: JSON.stringify({ channelId }) // Send channelId in the request body
      });
      const data = await response.json(); // Parse JSON response
      storeChannelId(channelId); // Store the channel ID after successful fetch
      setPlaylists(Object.entries(data)); // Convert object data to array for easier mapping
    } finally {
      setLoading(false); // Reset loading state regardless of success or failure
    }
  };

  // Import selected playlists to Spotify
  const importSelectedPlaylists = () => {
    // Filter playlists based on user-selected checkboxes
    const selected = playlists.filter(([id]) => document.getElementById(id).checked)
      .map(([name, id]) => ({ playlistId: id, playlistName: name })); // Map selected items to an object with ID and name

    if (selected.length === 0) { // Alert if no playlists are selected
      alert('Please select at least one playlist');
      return;
    }

    setImportInProgress(true); // Set import progress state to true

    // Establish a connection with the server to receive real-time progress updates
    const eventSource = new EventSource(`/api/import-playlists?playlists=${encodeURIComponent(JSON.stringify(selected))}`);

    eventSource.onmessage = (event) => {
      setProgressLog(prev => [...prev, event.data]); // Append new progress messages to the log

      if (event.data === 'All imports completed') { // Check if import is complete
        setImportInProgress(false); // Reset import progress state
        eventSource.close(); // Close EventSource connection
      }
    };
  };

  return (
    <div className="dash-wrapper">
    <div className="dashboard-container">
      <h1 className="dashboard-title">YouTube to Spotify Playlist Porter</h1>

      <div className="input-section">
        {/* Input field for YouTube Channel ID with autocomplete support */}
        <input 
          type="text" 
          value={channelId} 
          onChange={(e) => setChannelId(e.target.value)} // Update channelId state on input change
          placeholder="Enter YouTube Channel ID" 
          className="channel-input" 
          list="channelsList" // Provide autocomplete suggestions from stored channels
        />
        <datalist id="channelsList">
          {channels.map((id, index) => <option key={index} value={id} />)} 
          
        </datalist>
        <button 
          onClick={fetchPlaylists} // Trigger playlist fetch on click
          className="fetch-button" 
          disabled={loading} // Disable button while loading data
        >
          {loading ? 'Loading...' : 'Fetch Playlists'} 
        </button>
      </div>

      {/* Display playlists if any are fetched */}
      {playlists.length > 0 && (
        <div className="playlists-section">
          <h2 className="section-title">Available Playlists</h2>
          <div className="playlists-list">
            {playlists.map(([name, id]) => (
              <div key={id} className="playlist-item">
                <input type="checkbox" id={id} className="playlist-checkbox" /> 
                <label htmlFor={id}>{name}</label> 
              </div>
            ))}
          </div>
          <button 
            onClick={importSelectedPlaylists} // Trigger import on click
            className="import-button" 
            disabled={importInProgress} // Disable button during import
          >
            Import Selected Playlists
          </button>
        </div>
      )}

      {/* Display real-time import progress */}
      {progressLog.length > 0 && (
        <div className="progress-section">
          <h2 className="section-title">Import Progress</h2>
          <div className="progress-log">
            {progressLog.map((log, index) => (
              <p key={index} className={
                log.includes('error:') ? 'error-log' : // Apply error styling
                log.includes('warning:') ? 'warning-log' : // Apply warning styling
                'success-log' // Apply success styling for all other messages
              }>
                {log} 
              </p>
            ))}
          </div>
        </div>
      )}
    </div>
    </div>
  );
};

export default Dash;
