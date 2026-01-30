// JavaScript utilities for Spotify Scraper

document.addEventListener('DOMContentLoaded', function() {
    // Add any interactive features here
});

// Fetch and search function
async function search(query) {
    try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Search error:', error);
        return null;
    }
}

// Fetch playlists from API
async function fetchPlaylists(page = 1, perPage = 20, sortBy = 'followers') {
    try {
        const response = await fetch(`/api/playlists?page=${page}&per_page=${perPage}&sort_by=${sortBy}`);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Fetch playlists error:', error);
        return null;
    }
}

// Fetch tracks from API
async function fetchTracks(page = 1, perPage = 50, sortBy = 'popularity') {
    try {
        const response = await fetch(`/api/tracks?page=${page}&per_page=${perPage}&sort_by=${sortBy}`);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Fetch tracks error:', error);
        return null;
    }
}

// Fetch database statistics
async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Fetch stats error:', error);
        return null;
    }
}

// Format numbers with commas
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Format date
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

// Copy to clipboard utility
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        console.log('Copied to clipboard: ' + text);
    });
}
