"""
Jackett Client Module

Provides a Python client for interacting with a Jackett API, primarily for 
searching releases via its Torznab (RSS) interface. This client is designed 
for integration into applications that need to query Jackett for available 
releases, such as media automation tools or notification bots.

The main class provided is `JackettClient`, which handles the construction
of API requests, submission to Jackett, and parsing of the Torznab responses.
"""

import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Union

# Custom Exceptions
class JackettError(Exception):
    """Base exception class for errors originating from the Jackett client."""
    pass

class JackettConnectionError(JackettError):
    """
    Indicates an error related to network connectivity with the Jackett instance.
    This can include DNS failures, connection refusals, timeouts, or HTTP error codes
    (4xx, 5xx) from Jackett.
    """
    pass

class JackettAPIError(JackettError):
    """
    Represents an error explicitly reported by the Jackett API.
    This typically means the request was received, but Jackett could not process it
    correctly (e.g., invalid API key, or an <error> tag in the Torznab XML response).
    """
    pass

class JackettParseError(JackettError):
    """
    Signifies an error encountered while parsing the XML response from Jackett's
    Torznab feed. This usually indicates an unexpected response format or corrupted data.
    """
    pass

class JackettSearchError(JackettError):
    """
    Raised when a search operation initiated by the client fails to return any results
    from any of the attempted indexers, often due to repeated individual indexer failures.
    This indicates a general failure of the search rather than an issue with a single indexer.
    """
    pass


class JackettClient:
    """
    A client to perform searches against a Jackett instance using its Torznab API.

    This client handles forming the API requests, sending them to Jackett,
    and parsing the XML (Torznab) responses into a more usable Python format.
    It also defines a set of custom exceptions for specific error conditions.
    """
    _TORZNAB_NAMESPACE = {'torznab': 'http://torznab.com/schemas/servarr/2014/01/16/torznab'}

    def __init__(self, jackett_url: str, api_key: str):
        """
        Initializes the Jackett client with the necessary connection details.

        :param jackett_url: The base URL of the Jackett instance (e.g., "http://localhost:9117").
                            This URL should point to the root of your Jackett installation.
        :type jackett_url: str
        :param api_key: The API key obtained from your Jackett instance, used for authentication.
        :type api_key: str
        :raises ValueError: If `jackett_url` or `api_key` are empty or None.
        :raises JackettConnectionError: Although less common during `__init__`, future versions
                                       might add a connection test here. Currently, connection
                                       errors are primarily raised during operations like `search`.
        """
        if not jackett_url:
            raise ValueError("Jackett URL cannot be empty.")
        if not api_key:
            raise ValueError("Jackett API key cannot be empty.")

        self.jackett_url = jackett_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()

    def _parse_torznab_response(self, xml_response_text: str, indexer_name_for_item: str) -> List[Dict[str, Union[str, int]]]:
        """
        Parses the XML response text from a Jackett Torznab feed.

        This is a protected helper method used internally by the client to process
        the raw XML data returned by Jackett for a specific indexer query.

        :param xml_response_text: The XML content as a string.
        :type xml_response_text: str
        :param indexer_name_for_item: The identifier of the indexer from which this response originated.
                                      This is used to tag each parsed release with its source indexer.
        :type indexer_name_for_item: str
        :return: A list of dictionaries, where each dictionary represents a parsed release item.
                 Each item includes keys like 'title', 'link', 'size', 'seeders', 'leechers',
                 'pub_date', and 'indexer'.
        :rtype: list[dict]
        :raises JackettAPIError: If the XML response contains an <error> tag from Jackett.
        :raises JackettParseError: If the XML is malformed or an unexpected error occurs during parsing.
        """
        results = []
        try:
            root = ET.fromstring(xml_response_text)
            # Check for <error> tag immediately after parsing
            error_tag = root.find("error") # Torznab errors are usually at the root if the whole request is bad
            if error_tag is not None: # Check ET.Element object, not root.tag
                code = error_tag.get("code")
                description = error_tag.get("description", "No description provided.")
                raise JackettAPIError(f"Jackett API error for indexer '{indexer_name_for_item}': Code {code} - {description}")

            channel = root.find("channel")
            if channel is None:
                 # If there's no <channel> tag, it might be an empty valid response or an unexpected format.
                 # If it was an error, the <error> tag should have been caught.
                 # For now, treat as no items found if no <error> tag.
                return results


            for item in channel.findall('item'):
                title = item.findtext('title')
                link = None
                # Prioritize magnet links from enclosure
                enclosure = item.find('enclosure[@type="application/x-bittorrent"][@url]')
                if enclosure is not None and enclosure.get('url', '').startswith('magnet:'):
                    link = enclosure.get('url')
                
                # Fallback to link tag if no magnet enclosure, or if it wasn't a magnet
                if not link:
                    link_tag = item.findtext('link')
                    if link_tag and (link_tag.startswith('http') or link_tag.startswith('magnet:')):
                         link = link_tag
                
                # If still no link, skip item as it's not downloadable
                if not link:
                    continue

                size_str = None
                seeders_str = None
                leechers_str = None # Peers from Torznab often means total (seeders + leechers)

                for attr in item.findall('torznab:attr', self._TORZNAB_NAMESPACE):
                    name = attr.get('name')
                    value = attr.get('value')
                    if name == 'size':
                        size_str = value
                    elif name == 'seeders':
                        seeders_str = value
                    elif name == 'leechers': # Some indexers might use leechers directly
                        leechers_str = value
                    elif name == 'peers' and leechers_str is None: # If peers is present and leechers not yet set
                        # Assuming peers = seeders + leechers. We need seeders to calculate leechers.
                        # This part is tricky as "peers" can be ambiguous.
                        # If seeders_str is available, leechers = peers - seeders.
                        # For now, we'll prefer explicit "leechers" if available.
                        # If only peers and seeders are available, leechers = peers - seeders.
                        # If only peers is available, it's hard to determine leechers.
                        # Let's assume for now 'peers' is not directly 'leechers' unless 'leechers' is absent.
                        # This might need refinement based on typical Jackett outputs.
                        # For simplicity, we'll prioritize 'leechers' over calculating from 'peers'.
                        pass


                # If 'leechers' attribute wasn't found, try to get 'peers' and calculate if 'seeders' is also there
                if leechers_str is None:
                    peers_attr = item.find('torznab:attr[@name="peers"]', self._TORZNAB_NAMESPACE)
                    if peers_attr is not None and seeders_str is not None:
                        try:
                            leechers_val = int(peers_attr.get('value')) - int(seeders_str)
                            leechers_str = str(max(0, leechers_val)) # Ensure non-negative
                        except (ValueError, TypeError):
                            leechers_str = "0" # Default if calculation fails

                pub_date = item.findtext('pubDate')
                
                # Indexer name is passed to this function, as it's per-request
                # Some Torznab feeds might have <jackettindexer> but it's more reliable from the request context.
                
                release = {
                    'title': title,
                    'link': link,
                    'size': int(size_str) if size_str and size_str.isdigit() else 0,
                    'seeders': int(seeders_str) if seeders_str and seeders_str.isdigit() else 0,
                    'leechers': int(leechers_str) if leechers_str and leechers_str.isdigit() else 0,
                    'pub_date': pub_date,
                    'indexer': indexer_name_for_item 
                }
                results.append(release)
        except ET.ParseError as e:
            raise JackettParseError(f"Error parsing XML for indexer '{indexer_name_for_item}': {e}. Response: {xml_response_text[:500]}") from e
        except JackettAPIError: # Re-raise API errors from within the XML
            raise
        except Exception as e: # Catch any other unexpected error during parsing of an item
            # Log this or handle more gracefully, for now, reraise as parse error
            raise JackettParseError(f"Unexpected error parsing item for indexer '{indexer_name_for_item}': {e}") from e
        return results

    def search(self, query: str, indexers: Optional[List[str]] = None, categories: Optional[List[int]] = None) -> List[Dict[str, Union[str, int]]]:
        """
        Searches for releases on Jackett using the specified query and filters.

        :param query: The search query string.
        :type query: str
        :param indexers: Optional. A list of specific indexer IDs to query (e.g., ['prowlarr', 'torrentdb']).
                         If None or empty, Jackett's 'all' aggregate indexer is used.
        :type indexers: list[str], optional
        :param categories: Optional. A list of Torznab category IDs to filter the search 
                            (e.g., [2000, 5000]). Defaults to None (no category filter).
        :type categories: list[int], optional
        :return: A list of dictionaries, where each dictionary represents a found release.
                 The structure of each dictionary includes keys: 'title' (str), 'link' (str, URL),
                 'size' (int, bytes), 'seeders' (int), 'leechers' (int), 'pub_date' (str, RFC 822 format),
                 and 'indexer' (str, the ID of the indexer that found the release).
                 Returns an empty list if no results are found after querying all specified/default indexers.
        :rtype: list[dict]
        :raises ValueError: If the `query` argument is empty.
        :raises JackettConnectionError: If there's a network-level error (DNS, connection refused, timeout, HTTP error)
                                        when querying the 'all' indexer, or if such an error occurs for all
                                        specified individual indexers.
        :raises JackettAPIError: If the Jackett API reports an error for the 'all' indexer (e.g., via an <error> tag),
                                 or if such an error occurs for all specified individual indexers.
        :raises JackettParseError: If the response from the 'all' indexer is unparseable, or if responses from
                                   all specified individual indexers are unparseable.
        :raises JackettSearchError: If all attempted indexers (whether 'all' or a list of specific ones)
                                    fail to yield any results due to repeated errors (connection, API, or parse).
        """
        if not query:
            raise ValueError("Search query cannot be empty.")

        if not indexers:
            effective_indexers = ['all']
        else:
            effective_indexers = indexers
        
        all_results = []
        successful_indexer_queries = 0
        processed_indexers_count = 0
        
        for indexer_id in effective_indexers:
            processed_indexers_count +=1
            api_url = f"{self.jackett_url}/api/v2.0/indexers/{indexer_id}/results/torznab/"
            
            params = {
                'apikey': self.api_key,
                't': 'search',
                'q': query,
            }
            if categories:
                params['cat'] = ",".join(map(str, categories))

            try:
                # print(f"DEBUG: Querying Jackett: URL={api_url}, Params={params}")
                response = self.session.get(api_url, params=params, timeout=15)
                response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
                
                indexer_name = indexer_id 
                
                parsed_data = self._parse_torznab_response(response.text, indexer_name)
                all_results.extend(parsed_data)
                successful_indexer_queries += 1

            except requests.exceptions.HTTPError as e:
                http_error_msg = f"HTTP error {e.response.status_code} for indexer '{indexer_id}' ({api_url}): {e.response.text[:200] if e.response else 'N/A'}"
                print(f"Warning: {http_error_msg}")
                if indexer_id == 'all' and len(effective_indexers) == 1:
                    raise JackettConnectionError(f"Failed to query Jackett (indexer: all): {http_error_msg}") from e
            except requests.exceptions.Timeout as e:
                timeout_msg = f"Timeout occurred while querying indexer '{indexer_id}' ({api_url})."
                print(f"Warning: {timeout_msg}")
                if indexer_id == 'all' and len(effective_indexers) == 1:
                    raise JackettConnectionError(f"Failed to query Jackett (indexer: all): {timeout_msg}") from e
            except requests.exceptions.RequestException as e: # Other network errors (DNS, ConnectionRefused)
                req_error_msg = f"Request exception for indexer '{indexer_id}' ({api_url}): {e}"
                print(f"Warning: {req_error_msg}")
                if indexer_id == 'all' and len(effective_indexers) == 1:
                    raise JackettConnectionError(f"Failed to query Jackett (indexer: all): {req_error_msg}") from e
            except JackettParseError as e: 
                print(f"Warning: Could not parse response for indexer '{indexer_id}': {e}")
                # If 'all' indexer's response is unparseable, it's a significant failure.
                if indexer_id == 'all' and len(effective_indexers) == 1:
                    raise # Re-raise JackettParseError
            except JackettAPIError as e: # Errors from within the XML (e.g. <error> tag) for a specific indexer
                 print(f"Warning: API error reported by Jackett for indexer '{indexer_id}': {e}")
                 # If 'all' indexer itself reports an API error (e.g. wrong API key), it's a general failure.
                 if indexer_id == 'all' and len(effective_indexers) == 1:
                    raise # Re-raise JackettAPIError
        
        if processed_indexers_count > 0 and successful_indexer_queries == 0:
            # This means all attempted indexers failed for one reason or another.
            raise JackettSearchError(f"Search for '{query}' failed across all {processed_indexers_count} attempted indexer(s). Check warnings for details.")

        return all_results


if __name__ == '__main__':
    # --- Configuration Placeholders ---
    # IMPORTANT: Replace these with your actual Jackett URL and API key.
    JACKETT_URL = "http://localhost:9117"  # Example: "http://your-jackett-domain.com:9117"
    JACKETT_API_KEY = "YOUR_JACKETT_API_KEY"  # Replace with your actual API key from Jackett

    # Check if placeholders have been changed
    if JACKETT_API_KEY == "YOUR_JACKETT_API_KEY" or JACKETT_URL == "http://localhost:9117":
        print("----------------------------------------------------------------------")
        print("IMPORTANT: Please update JACKETT_URL and JACKETT_API_KEY in this script")
        print("           with your actual Jackett instance details to run the example.")
        print("----------------------------------------------------------------------")
        # exit() # Uncomment to prevent running with default/dummy values

    print(f"Attempting to connect to Jackett at: {JACKETT_URL}")

    try:
        # --- Instantiate JackettClient ---
        # This creates an instance of the client using your URL and API key.
        print("Instantiating JackettClient...")
        client = JackettClient(jackett_url=JACKETT_URL, api_key=JACKETT_API_KEY)
        print("JackettClient instantiated successfully.")

        # --- Perform a Search ---
        # Define a sample search query.
        search_query = "ubuntu desktop"
        # Torznab categories (examples):
        # Movies: 2000, TV: 5000, PC/ISO: 4020, Audio: 3000
        # Using PC/ISO category for "ubuntu desktop"
        categories_to_search = [4020] 
        
        print(f"\nPerforming search for: '{search_query}' (Categories: {categories_to_search if categories_to_search else 'Any'})")
        
        # Call the search method. This will query all configured and enabled indexers in Jackett
        # unless specific indexers are provided.
        results = client.search(query=search_query, categories=categories_to_search)
        # To search specific indexers:
        # results = client.search(query=search_query, indexers=['yourindexer1', 'yourindexer2'])

        # --- Process and Display Results ---
        if results:
            print(f"\nFound {len(results)} results for '{search_query}':")
            # Iterate through the results and print them in a structured format.
            # This is similar to how a bot might format information for a message.
            for i, release in enumerate(results[:10], 1):  # Display top 10 results
                size_gb = release['size'] / (1024**3) if release['size'] else 0
                print(f"\n  Result {i}:")
                print(f"    Title: {release['title']}")
                print(f"    Size: {size_gb:.2f} GB")
                print(f"    Seeders: {release['seeders']}, Leechers: {release['leechers']}")
                print(f"    Link: {release['link']}")
                print(f"    Indexer: {release['indexer']}")
                print(f"    Published: {release['pub_date']}")
        else:
            print(f"\nNo results found for '{search_query}'.")

        # --- Example of another search (e.g., a movie) ---
        # search_query_movie = "Big Buck Bunny"
        # categories_movie = [2000] # Movies category
        # print(f"\nPerforming search for: '{search_query_movie}' (Categories: {categories_movie})")
        # movie_results = client.search(query=search_query_movie, categories=categories_movie)
        # if movie_results:
        #     print(f"\nFound {len(movie_results)} movie results for '{search_query_movie}':")
        #     for release in movie_results[:5]: # Display top 5
        #         print(f"    - {release['title']} (S:{release['seeders']}/L:{release['leechers']}) [{release['indexer']}]")
        # else:
        #     print(f"\nNo movie results found for '{search_query_movie}'.")


    # --- Error Handling Demonstration ---
    # Catch specific custom exceptions from the JackettClient.
    except ValueError as ve:
        # Raised if JACKETT_URL or JACKETT_API_KEY are empty during client instantiation.
        print(f"\n--- Configuration Error ---")
        print(f"Details: {ve}")
        print("Please ensure JACKETT_URL and JACKETT_API_KEY are correctly set.")
    except JackettConnectionError as jce:
        # Raised for network issues (DNS, connection refused, timeout, HTTP 4xx/5xx errors).
        print(f"\n--- Jackett Connection Error ---")
        print(f"Could not connect to Jackett at {JACKETT_URL}.")
        print(f"Details: {jce}")
        print("Please check if Jackett is running, accessible, and the URL is correct.")
    except JackettAPIError as jae:
        # Raised for errors reported by Jackett's API (e.g., invalid API key, <error> tag in response).
        print(f"\n--- Jackett API Error ---")
        print(f"Jackett reported an API error.")
        print(f"Details: {jae}")
        print("This might be due to an invalid API key or an issue with Jackett itself.")
    except JackettParseError as jpe:
        # Raised if the XML response from Jackett is malformed or cannot be parsed.
        print(f"\n--- Jackett Response Parse Error ---")
        print(f"Could not parse the response from Jackett.")
        print(f"Details: {jpe}")
        print("This might indicate an issue with the Jackett instance or an unexpected response format.")
    except JackettSearchError as jse:
        # Raised if the search fails across all attempted indexers.
        print(f"\n--- Jackett Search Failure ---")
        print(f"The search operation failed for all attempted indexers.")
        print(f"Details: {jse}")
        print("This could be due to issues with all configured indexers or a problem reaching them.")
    except Exception as e:
        # Catch any other unexpected exceptions.
        print(f"\n--- An Unexpected Error Occurred ---")
        print(f"Error Type: {type(e).__name__}")
        print(f"Details: {e}")

    print("\n--- Jackett client example finished ---")
