# song_vocab_generator/tools/lyric_search.py
import os
import re
import requests
from bs4 import BeautifulSoup
from bs4.element import Comment # <--- ADDED THIS IMPORT!
from googleapiclient.discovery import build
from typing import Optional

def search_and_retrieve_lyrics(song_name: str, artist_name: Optional[str] = None) -> Optional[str]:
    """
    Searches the internet for song lyrics using Google Custom Search JSON API
    and retrieves them using requests and BeautifulSoup. Prioritizes known lyric sites
    and iterates through multiple results if the first fails.

    Args:
        song_name (str): The name of the song.
        artist_name (Optional[str]): The name of the artist.

    Returns:
        Optional[str]: The extracted lyrics as plain text, or None if not found or extracted.
    """
    # Retrieve API key and CSE ID from environment variables (set from Colab secrets)
    google_api_key = os.environ.get('GOOGLE_API_KEY')
    google_cse_id = os.environ.get('GOOGLE_CSE_ID')

    if not google_api_key or not google_cse_id:
        print("Error: GOOGLE_API_KEY or GOOGLE_CSE_ID not found in environment variables.")
        return None

    query = f"{song_name} lyrics"
    if artist_name:
        query += f" {artist_name}"

    # REMOVED 'genius.com' from the preferred_sites list for query construction
    preferred_sites = ['azlyrics.com', 'lyricfind.com', 'metrolyrics.com', 'songlyrics.com', 'lyrics.com']
    query += " " + " OR ".join([f"site:{site}" for site in preferred_sites])

    print(f"Searching for lyrics with query: '{query}'")

    try:
        # Build the Custom Search API service
        service = build("customsearch", "v1", developerKey=google_api_key)

        # Execute the search - get up to 10 results to iterate through
        search_results = service.cse().list(
            q=query,
            cx=google_cse_id,
            num=10 # Get up to 10 results
        ).execute()

        if 'items' in search_results and len(search_results['items']) > 0:
            print(f"Found {len(search_results['items'])} search results.")

            # Separate results by domain to prioritize different sites
            results_by_domain = {}
            for item in search_results['items']:
                url = item.get('link')
                if url:
                    domain_match = re.findall(r'https?://(?:www\.)?([^/]+)/', url) # Improved domain extraction
                    if domain_match:
                        domain = domain_match[0]
                        # Only add to results if not genius.com
                        if domain != 'genius.com':
                            if domain not in results_by_domain:
                                results_by_domain[domain] = []
                            results_by_domain[domain].append(item)

            # Prioritize domains from the preferred list, then others
            # FIXED SYNTAX ERROR HERE: 'd for d d' changed to 'd for d'
            ordered_domains = [d for d in preferred_sites if d in results_by_domain and d != 'genius.com'] + \
                              [d for d in results_by_domain if d not in preferred_sites and d != 'genius.com']


            # Iterate through domains and their results
            for domain in ordered_domains:
                print(f"Attempting to retrieve lyrics from domain: {domain}")
                for item in results_by_domain[domain]:
                    lyrics_url = item.get('link')
                    if not lyrics_url:
                        continue 

                    # Double-check that we are not attempting Genius.com URLs
                    if "genius.com" in lyrics_url:
                        print(f"  Skipping Genius.com URL: {lyrics_url}")
                        continue

                    print(f"  Attempting URL: {lyrics_url}")

                    try:
                        # Add a User-Agent header to mimic a browser
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
                        }
                        response = requests.get(lyrics_url, headers=headers, timeout=15) # Increased timeout slightly
                        response.raise_for_status() # Raise an exception for bad status codes (like 403)
                        page_content = response.text
                        print("  Page content fetched.")

                        # Parse the HTML content with BeautifulSoup
                        soup = BeautifulSoup(page_content, 'html.parser')

                        lyrics = None

                        # --- Specific Parsing for AZLyrics.com ---
                        if "azlyrics.com" in domain:
                            # AZLyrics often places lyrics within a div that follows a specific HTML comment
                            comment_text_pattern = re.compile(r'')
                            
                            # Find all comment nodes
                            comments = soup.find_all(string=comment_text_pattern)
                            
                            for comment in comments:
                                # The actual lyrics div is usually the next sibling after the comment's parent div
                                lyrics_div = comment.find_parent('div').find_next_sibling('div')
                                if lyrics_div:
                                    lyrics = lyrics_div.get_text(separator='\n', strip=True)
                                    # AZLyrics sometimes includes "Submit Corrections" etc. after lyrics
                                    # This regex looks for text that usually appears AFTER the lyrics body.
                                    # More robust split, targeting common JS/footer text
                                    lyrics = re.split(r'(?i)\(function\(\)\{var\s*az\s*=\s*\{\};az\.ad\.|Submit Corrections|AZLyrics\.com', lyrics, 1)[0].strip()
                                    if lyrics and len(lyrics) > 50: # Basic length check
                                        print(f"  Extracted lyrics using AZLyrics specific logic.")
                                        break
                            if lyrics: # If lyrics found by AZLyrics specific logic, proceed
                                print(f"Successfully retrieved and processed lyrics from {lyrics_url}")
                                return lyrics


                        # --- General Parsing Attempts (for other sites or if specific fails) ---
                        if not lyrics: # Only try general parsing if site-specific didn't yield results
                            # Attempt 1: Look for common lyric container classes/ids
                            # More specific selectors using `css_selector`
                            common_selectors = [
                                'div[class*="lyrics"]', # Matches div with "lyrics" anywhere in class name
                                'div.lyrics',
                                'p.lyrics',
                                '#lyrics',
                                '.lyrics-body',
                                '.lyrics-text',
                                'div[itemprop="description"]' # Sometimes used on other sites
                            ]
                            for selector in common_selectors:
                                container = soup.select_one(selector)
                                if container:
                                    lyrics = container.get_text(separator='\n', strip=True)
                                    print(f"  Extracted lyrics using general selector: {selector}")
                                    break

                        # Attempt 2: Look for <pre> tags (often used for preserving formatting)
                        if not lyrics:
                            pre_tags = soup.find_all('pre')
                            if pre_tags:
                                # Assuming the largest <pre> tag is likely the lyrics
                                largest_pre = max(pre_tags, key=lambda tag: len(tag.get_text()), default=None)
                                if largest_pre and len(largest_pre.get_text()) > 100: # Basic check for minimum length
                                     lyrics = largest_pre.get_text(separator='\n', strip=True)
                                     print("  Extracted lyrics from <pre> tag.")


                        if lyrics:
                            # Final general cleaning: remove excessive newlines and leading/trailing whitespace
                            lyrics = re.sub(r'\n\s*\n', '\n\n', lyrics).strip()
                            print(f"Successfully retrieved and processed lyrics from {lyrics_url}")
                            return lyrics # Return upon successful retrieval and extraction

                    except requests.exceptions.RequestException as req_e:
                        print(f"  Error fetching or parsing content from {lyrics_url}: {req_e}")
                        # Continue to the next URL on error within this domain
                    except Exception as parse_e:
                        print(f"  An unexpected error occurred during parsing {lyrics_url}: {parse_e}")
                        # Continue to the next URL on parsing error

            print("Tried multiple search results but could not retrieve lyrics.")
            return None # Return None if no lyrics were successfully retrieved from any result

        else:
            print("No search results found with a link.")
            return None

    except Exception as e:
        print(f"An error occurred during Google Custom Search: {e}")
        return None

# --- Test Script for Lyric Search & Retrieval Tool ---
# (This would typically be in a separate test file, but we'll include it here for demonstration)

def test_search_and_retrieve_lyrics():
    """
    Tests the search_and_retrieve_lyrics function with a sample song.
    Note: This test requires GOOGLE_API_KEY and GOOGLE_CSE_ID to be set as environment variables.
    """
    print("\n--- Testing Lyric Search & Retrieval Tool ---")

    # Ensure secrets are set as environment variables before running the test
    # This part would ideally be handled during agent initialization or setup
    from google.colab import userdata
    import os
    try:
        os.environ['GOOGLE_API_KEY'] = userdata.get('GOOGLE_API_KEY')
        os.environ['GOOGLE_CSE_ID'] = userdata.get('GOOGLE_CSE_ID')
        print("Environment variables for API key and CSE ID set.")
    except Exception as e:
        print(f"Could not set environment variables from secrets: {e}")
        print("Please ensure your GOOGLE_API_KEY and GOOGLE_CSE_ID are correctly set in Colab secrets.")
        return # Exit test if secrets can't be accessed


    song = "Bohemian Rhapsody"
    artist = "Queen"

    print(f"Attempting to find lyrics for '{song}' by {artist}...")

    lyrics = search_and_retrieve_lyrics(song, artist)

    if lyrics:
        print("\nSuccessfully retrieved potential lyrics. First 500 characters:")
        print(lyrics[:500] + "..." if len(lyrics) > 500 else lyrics)
    else:
        print("\nFailed to retrieve lyrics.")

# Execute the test
#test_search_and_retrieve_lyrics()