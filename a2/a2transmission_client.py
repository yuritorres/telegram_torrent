"""
Transmission Client Module

This module provides a Python client for interacting with a Transmission 
BitTorrent client's RPC interface. It simplifies common operations such as 
adding, listing, starting, stopping, and removing torrents, as well as 
managing session configuration and statistics.

The primary class provided is `TransmissionClient`.

Example:
    >>> from transmission_client import TransmissionClient, TransmissionConnectionError
    >>> try:
    ...     client = TransmissionClient(host='localhost', port=9091)
    ...     stats = client.get_session_stats()
    ...     print(f"Total torrents: {stats.torrent_count}")
    ... except TransmissionConnectionError as e:
    ...     print(f"Connection failed: {e}")

Note:
    Requires the `transmission-rpc` library to be installed.
    A Transmission daemon must be running and accessible for the client to connect.
"""

import transmission_rpc
from transmission_rpc.error import TransmissionError as OriginalTransmissionError

# Custom Exceptions
class TransmissionClientError(Exception):
    """Base class for exceptions raised by the TransmissionClient."""
    pass

class TransmissionConnectionError(TransmissionClientError):
    """
    Raised for errors related to establishing or maintaining a connection 
    with the Transmission daemon.
    """
    pass

class TorrentNotFoundError(TransmissionClientError):
    """Raised when an operation attempts to target a torrent ID that does not exist."""
    pass

class OperationFailureError(TransmissionClientError):
    """
    Raised when a Transmission RPC operation fails for reasons other than
    a connection error or a torrent not being found (e.g., invalid arguments,
    daemon-side errors).
    """
    pass


class TransmissionClient:
    """
    A client for interacting with a Transmission BitTorrent daemon's RPC interface.

    This class wraps the `transmission-rpc` library to provide a more
    opinionated and exception-focused interface for common Transmission operations.
    """
    def __init__(self, host: str = 'localhost', port: int = 9091, username: str = None, password: str = None, timeout: int = 10):
        """
        Initializes the Transmission client and attempts to connect to the daemon.

        :param host: The hostname or IP address of the Transmission daemon.
        :type host: str
        :param port: The port number of the Transmission daemon.
        :type port: int
        :param username: Optional. The username for RPC authentication.
        :type username: str, optional
        :param password: Optional. The password for RPC authentication.
        :type password: str, optional
        :param timeout: Optional. Connection timeout in seconds. Default is 10.
        :type timeout: int, optional
        
        :raises TransmissionConnectionError: If the client cannot connect to the 
                                             Transmission daemon at the specified address 
                                             or if authentication fails.
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client = None
        self.timeout = timeout

        try:
            self.client = transmission_rpc.Client(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=self.timeout
            )
            # Test connection by fetching server version
            self.client.server_version
        except OriginalTransmissionError as e:
            err_msg = f"Could not connect to Transmission daemon at {self.host}:{self.port}. Details: {e}"
            raise TransmissionConnectionError(err_msg) from e
        except Exception as e: 
            err_msg = f"An unexpected error occurred during Transmission client initialization: {e}"
            raise TransmissionConnectionError(err_msg) from e

    def _ensure_client_initialized(self):
        """
        Ensures the client is initialized. For internal use.
        :raises TransmissionConnectionError: If the client is not initialized.
        """
        if not self.client:
            raise TransmissionConnectionError("Transmission client not initialized. Please connect first.")

    def get_session_stats(self):
        """
        Retrieves the current session statistics from the Transmission daemon.

        :return: A SessionStats object containing various statistics like upload/download speed, counts, etc.
        :rtype: transmission_rpc.lib_types.SessionStats
        :raises TransmissionConnectionError: If the client is not connected.
        :raises OperationFailureError: If the daemon fails to return session stats or another RPC error occurs.
        """
        self._ensure_client_initialized()
        try:
            return self.client.session_stats()
        except OriginalTransmissionError as e:
            raise OperationFailureError(f"Failed to get session stats: {e}") from e
        except Exception as e: # Catch other unexpected errors
            raise OperationFailureError(f"An unexpected error occurred while getting session stats: {e}") from e

    def add_torrent(self, torrent_url_or_path: str, download_dir: str = None):
        """
        Adds a new torrent to Transmission using a URL (magnet or HTTP/HTTPS to .torrent file)
        or a local file path to a .torrent file.

        If the torrent is already present in Transmission (matched by its hash string),
        this method will return the existing Torrent object.

        :param torrent_url_or_path: The URL or local file path of the torrent.
        :type torrent_url_or_path: str
        :param download_dir: Optional. The directory where the torrent data should be downloaded.
                             If None, Transmission's default download directory is used.
        :type download_dir: str, optional
        :return: A Torrent object representing the added or existing torrent.
        :rtype: transmission_rpc.lib_types.Torrent
        :raises TransmissionConnectionError: If the client is not connected.
        :raises OperationFailureError: If adding the torrent fails (e.g., invalid torrent file,
                                     unreachable URL, daemon-side error, or local file not found).
        """
        self._ensure_client_initialized()
        try:
            # The transmission-rpc library itself handles duplicates by hash and returns the existing torrent.
            # However, its add_torrent can sometimes return None or a Torrent object without an ID if it's a duplicate.
            # We ensure a valid torrent object is returned.
            torrent = self.client.add_torrent(torrent_url_or_path, download_dir=download_dir)
            
            if torrent and hasattr(torrent, 'id') and torrent.id is not None:
                # print(f"Torrent '{torrent.name}' (ID: {torrent.id}) processed successfully.") # Optional: for verbose logging
                return torrent
            else:
                # This block attempts to find the torrent if the add_torrent call didn't directly return a usable object,
                # which can happen with some versions or specific duplicate scenarios.
                current_torrents = self.client.get_torrents()
                # Attempt to match by hash string if available, or by URL/path as a fallback.
                # Note: hashString is the most reliable way to identify a torrent.
                # This is a simplified matching; real matching happens server-side by hash.
                for t in current_torrents:
                    if hasattr(torrent, 'hashString') and hasattr(t, 'hashString') and torrent.hashString == t.hashString:
                        return t # Found by hash
                    if t.magnet_link == torrent_url_or_path or \
                       (hasattr(t, 'torrent_file') and t.torrent_file == torrent_url_or_path):
                        # print(f"Torrent '{torrent_url_or_path}' already exists with ID {t.id}. Returning existing.")
                        return t
                raise OperationFailureError(f"Failed to add or find torrent '{torrent_url_or_path}'. Daemon response was inconclusive.")
        except OriginalTransmissionError as e:
            # Check if error indicates duplicate, though library usually handles this.
            if 'duplicate torrent' in str(e).lower():
                 # Try to find and return the existing torrent as a best effort
                existing_torrents = self.client.get_torrents()
                for t in existing_torrents: # Simplified matching
                    if t.magnet_link == torrent_url_or_path or \
                       (hasattr(t, 'torrent_file') and t.torrent_file == torrent_url_or_path):
                        return t
            raise OperationFailureError(f"Failed to add torrent '{torrent_url_or_path}': {e}") from e
        except FileNotFoundError: # Specifically for local .torrent file paths
            raise OperationFailureError(f"Local torrent file not found at '{torrent_url_or_path}'.") from None
        except Exception as e: # Catch other unexpected errors
            raise OperationFailureError(f"An unexpected error occurred while adding torrent '{torrent_url_or_path}': {e}") from e

    def list_torrents(self):
        """
        Retrieves a list of all torrents currently managed by the Transmission daemon.

        :return: A list of Torrent objects. Returns an empty list if no torrents are active.
        :rtype: list[transmission_rpc.lib_types.Torrent]
        :raises TransmissionConnectionError: If the client is not connected.
        :raises OperationFailureError: If the daemon fails to return the torrent list or another RPC error occurs.
        """
        self._ensure_client_initialized()
        try:
            return self.client.get_torrents()
        except OriginalTransmissionError as e:
            raise OperationFailureError(f"Failed to list torrents: {e}") from e
        except Exception as e:
            raise OperationFailureError(f"An unexpected error occurred while listing torrents: {e}") from e

    def get_torrent_info(self, torrent_id: int):
        """
        Retrieves detailed information for a specific torrent identified by its ID.

        :param torrent_id: The ID of the torrent to retrieve.
        :type torrent_id: int
        :return: A Torrent object containing details of the specified torrent.
        :rtype: transmission_rpc.lib_types.Torrent
        :raises TransmissionConnectionError: If the client is not connected.
        :raises TorrentNotFoundError: If no torrent with the given ID exists.
        :raises OperationFailureError: If any other error occurs during the RPC call.
        """
        self._ensure_client_initialized()
        try:
            torrent = self.client.get_torrent(torrent_id)
            if torrent is None: # The library returns None if torrent ID is not found
                raise TorrentNotFoundError(f"Torrent with ID {torrent_id} not found.")
            return torrent
        except OriginalTransmissionError as e:
            # Further inspect error if it's an RPC error that might also imply "not found"
            if 'not found' in str(e).lower() or 'no torrent with id' in str(e).lower():
                 raise TorrentNotFoundError(f"Torrent with ID {torrent_id} not found. Details: {e}") from e
            raise OperationFailureError(f"Failed to get torrent info for ID {torrent_id}: {e}") from e
        except Exception as e:
            raise OperationFailureError(f"An unexpected error occurred while getting torrent info for ID {torrent_id}: {e}") from e
            
    def start_torrent(self, torrent_ids: list[int]):
        """
        Starts one or more torrents identified by their IDs.

        :param torrent_ids: A list of integer torrent IDs to start.
        :type torrent_ids: list[int]
        :return: True if the start command was successfully sent to the daemon.
                 Note: This does not guarantee the torrents have fully started, only that
                 the command was accepted by the daemon.
        :rtype: bool
        :raises TransmissionConnectionError: If the client is not connected.
        :raises TorrentNotFoundError: If one or more torrent IDs in the list are invalid or not found.
        :raises OperationFailureError: If the start command fails for other reasons (e.g., daemon error).
        """
        self._ensure_client_initialized()
        if not torrent_ids: return True # No action needed for empty list
        try:
            self.client.start_torrent(torrent_ids)
            # print(f"Start command sent successfully for torrent IDs: {torrent_ids}") # Optional: for verbose logging
            return True
        except OriginalTransmissionError as e:
            if "torrent not found" in str(e).lower() or "invalid id" in str(e).lower():
                raise TorrentNotFoundError(f"Failed to start torrents. One or more IDs in {torrent_ids} may be invalid. Details: {e}") from e
            raise OperationFailureError(f"Failed to start torrents {torrent_ids}: {e}") from e
        except Exception as e:
            raise OperationFailureError(f"An unexpected error occurred while starting torrents {torrent_ids}: {e}") from e

    def stop_torrent(self, torrent_ids: list[int]):
        """
        Stops one or more torrents identified by their IDs.

        :param torrent_ids: A list of integer torrent IDs to stop.
        :type torrent_ids: list[int]
        :return: True if the stop command was successfully sent.
        :rtype: bool
        :raises TransmissionConnectionError: If the client is not connected.
        :raises TorrentNotFoundError: If one or more torrent IDs in the list are invalid or not found.
        :raises OperationFailureError: If the stop command fails for other reasons.
        """
        self._ensure_client_initialized()
        if not torrent_ids: return True
        try:
            self.client.stop_torrent(torrent_ids)
            # print(f"Stop command sent successfully for torrent IDs: {torrent_ids}") # Optional: for verbose logging
            return True
        except OriginalTransmissionError as e:
            if "torrent not found" in str(e).lower() or "invalid id" in str(e).lower():
                raise TorrentNotFoundError(f"Failed to stop torrents. One or more IDs in {torrent_ids} may be invalid. Details: {e}") from e
            raise OperationFailureError(f"Failed to stop torrents {torrent_ids}: {e}") from e
        except Exception as e:
            raise OperationFailureError(f"An unexpected error occurred while stopping torrents {torrent_ids}: {e}") from e

    def remove_torrent(self, torrent_ids: list[int], delete_data: bool = False):
        """
        Removes one or more torrents from Transmission.

        :param torrent_ids: A list of integer torrent IDs to remove.
        :type torrent_ids: list[int]
        :param delete_data: If True, the downloaded data associated with the torrents
                            will also be deleted from the disk. Defaults to False.
        :type delete_data: bool
        :return: True if the remove command was successfully sent.
        :rtype: bool
        :raises TransmissionConnectionError: If the client is not connected.
        :raises TorrentNotFoundError: If one or more torrent IDs in the list are invalid or not found.
        :raises OperationFailureError: If the remove command fails for other reasons.
        """
        self._ensure_client_initialized()
        if not torrent_ids: return True
        try:
            self.client.remove_torrent(torrent_ids, delete_data=delete_data)
            # action = "and deleted data" if delete_data else "" # Optional: for verbose logging
            # print(f"Remove command sent successfully for torrent IDs: {torrent_ids} {action}")
            return True
        except OriginalTransmissionError as e:
            if "torrent not found" in str(e).lower() or "invalid id" in str(e).lower():
                raise TorrentNotFoundError(f"Failed to remove torrents. One or more IDs in {torrent_ids} may be invalid. Details: {e}") from e
            raise OperationFailureError(f"Failed to remove torrents {torrent_ids}: {e}") from e
        except Exception as e:
            raise OperationFailureError(f"An unexpected error occurred while removing torrents {torrent_ids}: {e}") from e

    def get_session_config(self):
        """
        Retrieves the current session configuration settings from the Transmission daemon.

        :return: A Session object containing various configuration parameters of the daemon.
        :rtype: transmission_rpc.lib_types.Session
        :raises TransmissionConnectionError: If the client is not connected.
        :raises OperationFailureError: If the daemon fails to return session configuration or an RPC error occurs.
        """
        self._ensure_client_initialized()
        try:
            return self.client.get_session()
        except OriginalTransmissionError as e:
            raise OperationFailureError(f"Failed to get session config: {e}") from e
        except Exception as e:
            raise OperationFailureError(f"An unexpected error occurred while getting session config: {e}") from e

    def set_session_config(self, **kwargs):
        """
        Sets session configuration parameters on the Transmission daemon.
        Refer to the Transmission RPC specification for available parameters.

        Example:
            `client.set_session_config(speed_limit_down=100, alt_speed_enabled=True)`

        :param kwargs: Keyword arguments representing session parameters to change.
                       (e.g., `speed_limit_down=100`, `alt_speed_enabled=True`).
        :return: True if the configuration was successfully set.
        :rtype: bool
        :raises TransmissionConnectionError: If the client is not connected.
        :raises OperationFailureError: If setting the configuration fails due to invalid parameters,
                                     daemon error, or other RPC issues.
        """
        self._ensure_client_initialized()
        try:
            self.client.set_session(**kwargs)
            # print(f"Set session config command sent successfully with parameters: {kwargs}") # Optional: for verbose logging
            return True
        except OriginalTransmissionError as e: # Includes errors from bad arguments
            raise OperationFailureError(f"Failed to set session config with {kwargs}: {e}") from e
        except Exception as e:
            raise OperationFailureError(f"An unexpected error or invalid argument in set_session_config({kwargs}): {e}") from e


def main():
    """Run the Transmission client example."""
    print("=== Transmission Client Example ===")
    print("This example demonstrates basic usage of the Transmission client.")
    print("Ensure the Transmission daemon is running and accessible.\n")
    
    test_torrent_id = None 
    client = None
    
    try:
        # Initialize client with default settings (localhost:9091)
        # For custom settings, use: client = TransmissionClient(host='your_host', port=9091, username='user', password='pass')
        print("Initializing Transmission client...")
        client = TransmissionClient()
        
        # Get and display session stats
        print("\n--- Session Stats ---")
        stats = client.get_session_stats()
        print(f"  Active torrents: {stats.active_torrent_count}")
        print(f"  Download speed: {stats.download_speed / 1024:.2f} KB/s")
        print(f"  Upload speed: {stats.upload_speed / 1024:.2f} KB/s")
        print(f"  Downloaded: {stats.downloaded_bytes / (1024*1024):.2f} MB")
        print(f"  Uploaded: {stats.uploaded_bytes / (1024*1024):.2f} MB")

        # List existing torrents
        print("\n--- Current Torrents ---")
        torrents = client.list_torrents()
        if torrents:
            for idx, torrent in enumerate(torrents, 1):
                status = getattr(torrent, 'status', 'unknown')
                progress = getattr(torrent, 'progress', 0)
                name = getattr(torrent, 'name', 'Unknown')
                print(f"  {idx}. ID: {torrent.id}, Name: {name[:50]}{'...' if len(name) > 50 else ''}")
                print(f"     Status: {status}, Progress: {progress:.1f}%")
                if test_torrent_id is None:
                    test_torrent_id = torrent.id
        else:
            print("  No torrents currently active.")

        # Example: Add a test torrent
        sample_torrent_url = "https://releases.ubuntu.com/22.04/ubuntu-22.04.4-desktop-amd64.iso.torrent"
        print(f"\n--- Adding Test Torrent ---")
        print(f"URL: {sample_torrent_url}")
        
        try:
            added_torrent = client.add_torrent(sample_torrent_url)
            if added_torrent and hasattr(added_torrent, 'id'):
                print(f"  Successfully added torrent: '{added_torrent.name}'")
                print(f"  Torrent ID: {added_torrent.id}")
                test_torrent_id = added_torrent.id
                # Give Transmission time to process the new torrent
                import time
                time.sleep(2)
            else:
                print("  Warning: Received incomplete response when adding torrent")
                
        except OperationFailureError as ofe:
            print(f"  Could not add torrent: {ofe}")
            # If adding failed because it's a duplicate, try to find the existing torrent
            if any(msg in str(ofe).lower() for msg in ["already exists", "duplicate"]):
                print("  Torrent already exists. Attempting to find it...")
                try:
                    all_torrents = client.list_torrents()
                    for t in all_torrents:
                        if (hasattr(t, 'torrent_file') and sample_torrent_url in t.torrent_file) or \
                           (hasattr(t, 'magnet_link') and t.magnet_link == sample_torrent_url):
                            test_torrent_id = t.id
                            print(f"  Found existing torrent with ID: {test_torrent_id}")
                            break
                    else:
                        print("  Could not find the existing torrent in the list.")
                except Exception as e:
                    print(f"  Error while searching for existing torrent: {e}")


        # Perform operations on the test torrent if we have a valid ID
        if test_torrent_id is not None:
            # Get detailed info
            print(f"\n--- Torrent Details (ID: {test_torrent_id}) ---")
            try:
                info = client.get_torrent_info(test_torrent_id)
                print(f"  Name: {getattr(info, 'name', 'Unknown')}")
                print(f"  Status: {getattr(info, 'status', 'unknown')}")
                print(f"  Progress: {getattr(info, 'progress', 0):.1f}%")
                print(f"  Downloaded: {getattr(info, 'downloaded_ever', 0) / (1024*1024):.2f} MB")
                print(f"  Uploaded: {getattr(info, 'uploaded_ever', 0) / (1024*1024):.2f} MB")
                print(f"  Ratio: {getattr(info, 'upload_ratio', 0):.2f}")
            except TorrentNotFoundError:
                print(f"  Error: Torrent with ID {test_torrent_id} was not found.")
            except OperationFailureError as ofe:
                print(f"  Error getting torrent info: {ofe}")

            # Example: Stop the torrent
            print(f"\n--- Stopping Torrent (ID: {test_torrent_id}) ---")
            try:
                client.stop_torrent([test_torrent_id])
                print("  Stop command sent successfully.")
                # Wait a moment for the status to update
                import time
                time.sleep(1)
                
                # Verify status
                try:
                    status = client.get_torrent_info(test_torrent_id).status
                    print(f"  New status: {status}")
                except Exception as e:
                    print(f"  Warning: Could not verify status: {e}")
                    
            except TorrentNotFoundError:
                print(f"  Error: Torrent {test_torrent_id} not found for stop operation.")
            except OperationFailureError as ofe:
                print(f"  Error stopping torrent: {ofe}")
        else:
            print("\n--- No valid torrent ID available for testing operations ---")

            print(f"\n--- Start Torrent (ID: {test_torrent_id_to_query}) ---")
            try:
                client.start_torrent([test_torrent_id_to_query])
                print(f"  Start command sent for torrent ID {test_torrent_id_to_query}.")
                time.sleep(1)
                info_after_start = client.get_torrent_info(test_torrent_id_to_query)
                print(f"  Status after start: {info_after_start.status}")
            except TorrentNotFoundError:
                print(f"  Torrent {test_torrent_id_to_query} not found for start operation.")
        print("\n--- Session Configuration ---")
        try:
            session_config = client.get_session_config()
            print(f"  Download directory: {getattr(session_config, 'download_dir', 'Not available')}")
            print(f"  Incomplete directory: {getattr(session_config, 'incomplete_dir', 'Not set')}")
            print(f"  Speed limit down: {getattr(session_config, 'speed_limit_down', 0)} KB/s")
            print(f"  Speed limit up: {getattr(session_config, 'speed_limit_up', 0)} KB/s")
            print(f"  Alt speed enabled: {getattr(session_config, 'alt_speed_enabled', False)}")
            
            # Example: Toggle a setting (alt speed) to demonstrate config modification
            try:
                original_alt_speed = getattr(session_config, 'alt_speed_enabled', False)
                print(f"\n  Toggling alt speed from {original_alt_speed} to {not original_alt_speed}...")
                client.set_session_config(alt_speed_enabled=not original_alt_speed)
                
                # Verify the change
                updated_config = client.get_session_config()
                print(f"  New alt_speed_enabled: {getattr(updated_config, 'alt_speed_enabled', 'N/A')}")
                
                # Revert the change
                client.set_session_config(alt_speed_enabled=original_alt_speed)
                print(f"  Reverted alt_speed_enabled to: {original_alt_speed}")
                
            except OperationFailureError as ofe:
                print(f"  Warning: Could not modify settings: {ofe}")
                
        except OperationFailureError as ofe:
            print(f"  Error: Could not retrieve session configuration: {ofe}")
        except Exception as e:
            print(f"  Unexpected error with session configuration: {e}")

    except TransmissionConnectionError as tce:
        print(f"\nERROR: Could not connect to Transmission daemon: {tce}")
        print("Please ensure the Transmission daemon is running and accessible.")
    except TorrentNotFoundError as tnfe:
        print(f"\nERROR: Torrent not found: {tnfe}")
    except OperationFailureError as ofe:
        print(f"\nOPERATION FAILED: {ofe}")
    except Exception as e:
        import traceback
        print(f"\nUNEXPECTED ERROR: {e}")
        traceback.print_exc()
    finally:
        # Cleanup code
        print("\n--- Cleanup ---")
        if client:
            try:
                # Remove the test torrent if it was added during this session
                if 'added_torrent' in locals() and hasattr(added_torrent, 'id'):
                    print(f"Removing test torrent (ID: {added_torrent.id})...")
                    try:
                        client.remove_torrent([added_torrent.id], delete_data=False)
                        print("  Test torrent removed successfully.")
                    except Exception as e:
                        print(f"  Warning: Could not remove test torrent: {e}")
                
                print("Closing Transmission client connection...")
                # No explicit close needed for transmission_rpc client
                
            except Exception as e:
                print(f"  Error during cleanup: {e}")
        
        print("\n=== Example completed. ===")


if __name__ == '__main__':
    main()
