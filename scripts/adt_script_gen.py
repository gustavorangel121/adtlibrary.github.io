#!/usr/bin/env python3
"""
Gigahertz FM Links Library Generator
Generates a static HTML website for GitHub Pages displaying episode links from Gigahertz FM podcasts
"""

import json
import os
import re
import requests
from datetime import datetime
from typing import List, Dict, Any
from html.parser import HTMLParser

# API Base URL
API_BASE = "https://gigahertz.fm/api"

class LinkExtractor(HTMLParser):
    """Extract links from HTML content"""
    def __init__(self):
        super().__init__()
        self.links = []
        self.current_text = ""
        self.in_link = False
        
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.in_link = True
            self.current_text = ""
            for attr, value in attrs:
                if attr == 'href':
                    self.current_url = value
                    
    def handle_endtag(self, tag):
        if tag == 'a' and self.in_link:
            self.links.append({
                'text': self.current_text.strip(),
                'url': self.current_url
            })
            self.in_link = False
            
    def handle_data(self, data):
        if self.in_link:
            self.current_text += data

def extract_episode_links(body_html: str) -> List[Dict[str, str]]:
    """Extract links from the episode body, specifically from 'LINKS DO EPISÓDIO' section"""
    if not body_html:
        return []
    
    # Find the "LINKS DO EPISÓDIO" section
    # Common variations: "LINKS DO EPISÓDIO", "Links do Episódio", "LINKS", etc.
    links_pattern = r'(?:LINKS DO EPISÓDIO|Links do Episódio|LINKS DO SHOW|Links do Show)(.*?)(?:<h2>|<h3>|$)'
    match = re.search(links_pattern, body_html, re.IGNORECASE | re.DOTALL)
    
    if not match:
        # If no specific section found, try to extract all links from the body
        links_section = body_html
    else:
        links_section = match.group(1)
    
    # Extract links using HTMLParser
    parser = LinkExtractor()
    parser.feed(links_section)
    
    return parser.links

def fetch_podcasts() -> List[Dict[str, Any]]:
    """Fetch all podcasts from Gigahertz API"""
    print("Fetching podcasts list...")
    response = requests.get(f"{API_BASE}/podcasts.json")
    response.raise_for_status()
    data = response.json()
    return data.get('podcasts', [])

def fetch_podcast_details(slug: str) -> Dict[str, Any]:
    """Fetch detailed information about a specific podcast including episodes"""
    print(f"Fetching details for podcast: {slug}")
    response = requests.get(f"{API_BASE}/podcasts/{slug}/index.json")
    response.raise_for_status()
    return response.json()

def fetch_episode_details(slug: str, episode_number: int) -> Dict[str, Any]:
    """Fetch detailed information about a specific episode"""
    print(f"Fetching episode {episode_number} of {slug}")
    response = requests.get(f"{API_BASE}/podcasts/{slug}/{episode_number}.json")
    response.raise_for_status()
    return response.json()

def collect_all_episodes() -> List[Dict[str, Any]]:
    """Collect all episodes from all podcasts with their links"""
    all_episodes = []
    
    podcasts = fetch_podcasts()
    
    for podcast in podcasts:
        slug = podcast.get('slug')
        podcast_title = podcast.get('title', 'Unknown Podcast')
        
        if not slug:
            continue
            
        try:
            # Fetch podcast details to get episode list
            podcast_details = fetch_podcast_details(slug)
            episodes = podcast_details.get('episodes', [])
            
            # Fetch detailed information for each episode
            for episode_info in episodes:
                episode_number = episode_info.get('episodeNumber')
                
                if episode_number is None:
                    continue
                
                try:
                    episode_details = fetch_episode_details(slug, episode_number)
                    
                    # Extract links from episode body
                    body = episode_details.get('body', '')
                    links = extract_episode_links(body)
                    
                    # Only include episodes that have links
                    if links:
                        episode_data = {
                            'id': episode_details.get('id'),
                            'episodeNumber': episode_number,
                            'title': episode_details.get('title', ''),
                            'date': episode_details.get('date', ''),
                            'permalink': episode_details.get('permalink', ''),
                            'podcastTitle': podcast_title,
                            'podcastSlug': slug,
                            'links': links
                        }
                        
                        all_episodes.append(episode_data)
                    
                except Exception as e:
                    print(f"Error fetching episode {episode_number} of {slug}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error fetching podcast {slug}: {e}")
            continue
    
    # Sort episodes by date (newest first)
    all_episodes.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    return all_episodes

def generate_html(episodes: List[Dict[str, Any]], generation_date: str) -> str:
    """Generate the HTML page with all episode links"""
    
    # Convert episodes to JSON for JavaScript
    episodes_json = json.dumps(episodes, ensure_ascii=False)
    
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gigahertz FM - Biblioteca de Links</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        header {{
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }}
        
        h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .subtitle {{
            font-size: 1.2rem;
            opacity: 0.9;
            margin-bottom: 5px;
        }}
        
        .last-update {{
            font-size: 0.9rem;
            opacity: 0.8;
            margin-top: 10px;
            padding: 8px 16px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 20px;
            display: inline-block;
        }}
        
        .search-container {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        
        .search-box {{
            width: 100%;
            padding: 15px;
            font-size: 1rem;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            outline: none;
            transition: border-color 0.3s;
        }}
        
        .search-box:focus {{
            border-color: #667eea;
        }}
        
        .stats {{
            text-align: center;
            color: #666;
            margin-top: 10px;
            font-size: 0.9rem;
        }}
        
        .episodes-list {{
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        
        .episode {{
            border-bottom: 1px solid #e0e0e0;
            padding: 20px;
        }}
        
        .episode:last-child {{
            border-bottom: none;
        }}
        
        .episode-header {{
            margin-bottom: 15px;
        }}
        
        .episode-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            align-items: center;
            margin-bottom: 8px;
        }}
        
        .podcast-badge {{
            background: #764ba2;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 500;
        }}
        
        .episode-number {{
            background: #667eea;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: bold;
        }}
        
        .episode-date {{
            color: #666;
            font-size: 0.85rem;
        }}
        
        .episode-title {{
            font-size: 1.1rem;
            font-weight: 600;
            color: #333;
            margin: 8px 0;
        }}
        
        .episode-title a {{
            color: #333;
            text-decoration: none;
            transition: color 0.2s;
        }}
        
        .episode-title a:hover {{
            color: #667eea;
        }}
        
        .links-section {{
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        
        .link-item {{
            display: flex;
            align-items: center;
            padding: 10px 15px;
            background: #f8f9fa;
            border-radius: 8px;
            text-decoration: none;
            color: #333;
            transition: all 0.2s;
            border-left: 3px solid #667eea;
        }}
        
        .link-item:hover {{
            background: #e9ecef;
            transform: translateX(5px);
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
        }}
        
        .link-icon {{
            margin-right: 10px;
            font-size: 1.2rem;
        }}
        
        .link-text {{
            flex: 1;
            font-size: 0.95rem;
        }}
        
        .external-icon {{
            opacity: 0.5;
            font-size: 0.8rem;
        }}
        
        .no-results {{
            text-align: center;
            padding: 60px 20px;
            color: #666;
        }}
        
        .no-results-icon {{
            font-size: 4rem;
            margin-bottom: 20px;
        }}
        
        .loading {{
            text-align: center;
            padding: 40px;
            color: #666;
            font-size: 1.2rem;
        }}
        
        footer {{
            text-align: center;
            color: white;
            margin-top: 40px;
            padding: 20px;
            opacity: 0.8;
        }}
        
        footer a {{
            color: white;
            text-decoration: underline;
        }}
        
        @media (max-width: 768px) {{
            h1 {{
                font-size: 1.8rem;
            }}
            
            .episode-meta {{
                flex-direction: column;
                align-items: flex-start;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎙️ Gigahertz FM</h1>
            <p class="subtitle">Biblioteca de Links dos Episódios</p>
            <div class="last-update">
                📅 Atualizado em: {generation_date}
            </div>
        </header>
        
        <div class="search-container">
            <input 
                type="text" 
                id="searchBox" 
                class="search-box" 
                placeholder="Buscar por episódio, título ou link..."
            >
            <div class="stats">
                <span id="statsText">Carregando episódios...</span>
            </div>
        </div>
        
        <div id="episodesList" class="episodes-list">
            <div class="loading">Carregando episódios...</div>
        </div>
        
        <footer>
            <p>Gerado a partir da <a href="https://github.com/gigahertzfm/api" target="_blank">API Gigahertz FM</a></p>
        </footer>
    </div>
    
    <script>
        // Episodes data
        const allEpisodes = {episodes_json};
        let filteredEpisodes = [...allEpisodes];
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {{
            renderEpisodes(filteredEpisodes);
            updateStats();
            
            // Search functionality
            const searchBox = document.getElementById('searchBox');
            searchBox.addEventListener('input', function(e) {{
                const searchTerm = e.target.value.toLowerCase().trim();
                
                if (searchTerm === '') {{
                    filteredEpisodes = [...allEpisodes];
                }} else {{
                    filteredEpisodes = allEpisodes.filter(episode => {{
                        const episodeNumber = String(episode.episodeNumber || '');
                        const title = (episode.title || '').toLowerCase();
                        const podcastTitle = (episode.podcastTitle || '').toLowerCase();
                        
                        // Check if search term matches episode info
                        const matchesEpisodeInfo = episodeNumber.includes(searchTerm) || 
                                                   title.includes(searchTerm) || 
                                                   podcastTitle.includes(searchTerm);
                        
                        // Check if search term matches any link text or URL
                        const matchesLinks = episode.links.some(link => 
                            link.text.toLowerCase().includes(searchTerm) || 
                            link.url.toLowerCase().includes(searchTerm)
                        );
                        
                        return matchesEpisodeInfo || matchesLinks;
                    }});
                }}
                
                renderEpisodes(filteredEpisodes);
                updateStats();
            }});
        }});
        
        function renderEpisodes(episodes) {{
            const container = document.getElementById('episodesList');
            
            if (episodes.length === 0) {{
                container.innerHTML = `
                    <div class="no-results">
                        <div class="no-results-icon">🔍</div>
                        <h2>Nenhum episódio encontrado</h2>
                        <p>Tente buscar por outro termo</p>
                    </div>
                `;
                return;
            }}
            
            container.innerHTML = episodes.map(episode => {{
                const date = new Date(episode.date);
                const formattedDate = date.toLocaleDateString('pt-BR', {{
                    day: '2-digit',
                    month: 'long',
                    year: 'numeric'
                }});
                
                const linksHTML = episode.links.map(link => `
                    <a href="${{link.url}}" target="_blank" class="link-item">
                        <span class="link-icon">🔗</span>
                        <span class="link-text">${{link.text}}</span>
                        <span class="external-icon">↗</span>
                    </a>
                `).join('');
                
                return `
                    <div class="episode">
                        <div class="episode-header">
                            <div class="episode-meta">
                                <span class="podcast-badge">${{episode.podcastTitle}}</span>
                                <span class="episode-number">#${{episode.episodeNumber}}</span>
                                <span class="episode-date">${{formattedDate}}</span>
                            </div>
                            <h2 class="episode-title">
                                <a href="${{episode.permalink}}" target="_blank">${{episode.title}}</a>
                            </h2>
                        </div>
                        <div class="links-section">
                            ${{linksHTML}}
                        </div>
                    </div>
                `;
            }}).join('');
        }}
        
        function updateStats() {{
            const statsText = document.getElementById('statsText');
            const total = allEpisodes.length;
            const showing = filteredEpisodes.length;
            
            const totalLinks = allEpisodes.reduce((sum, ep) => sum + ep.links.length, 0);
            const showingLinks = filteredEpisodes.reduce((sum, ep) => sum + ep.links.length, 0);
            
            if (showing === total) {{
                statsText.textContent = `${{total}} episódio${{total !== 1 ? 's' : ''}} • ${{totalLinks}} links disponíveis`;
            }} else {{
                statsText.textContent = `Mostrando ${{showing}} de ${{total}} episódios • ${{showingLinks}} links`;
            }}
        }}
    </script>
</body>
</html>"""
    
    return html

def main():
    """Main function to generate the static site"""
    print("=" * 60)
    print("Gigahertz FM Links Library Generator")
    print("=" * 60)
    print()
    
    # Record generation date
    generation_date = datetime.now().strftime('%d/%m/%Y às %H:%M')
    
    try:
        # Collect all episodes
        print("Starting to collect episodes and extract links...")
        episodes = collect_all_episodes()
        print(f"\nTotal episodes with links: {len(episodes)}")
        
        total_links = sum(len(ep['links']) for ep in episodes)
        print(f"Total links extracted: {total_links}")
        
        # Generate HTML
        print("\nGenerating HTML...")
        html = generate_html(episodes, generation_date)
        
        # Save to file
        output_file = "index.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\n✅ Successfully generated {output_file}")
        print(f"📊 Statistics:")
        print(f"   - Episodes with links: {len(episodes)}")
        print(f"   - Total links: {total_links}")
        print(f"   - Generated on: {generation_date}")
        print("\n" + "=" * 60)
        print("Next steps:")
        print("1. Upload index.html to your GitHub repository")
        print("2. Enable GitHub Pages in repository settings")
        print("3. Set source to main branch / root")
        print("4. Your site will be available at: https://USERNAME.github.io/REPO-NAME/")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise

if __name__ == "__main__":
    main()