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
    def __init__(self, host: str = 'localhost', port: int = 9091, username: str = None, password: str = None):
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
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client = None

        try:
            self.client = transmission_rpc.Client(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=10 
            )
            self.client.server_version # Test connection by fetching server version
            # Consider removing this print or making it optional for library use
            # print(f"Successfully connected to Transmission daemon at {self.host}:{self.port}")
        except OriginalTransmissionError as e:
            err_msg = f"Could not connect to Transmission daemon at {self.host}:{self.port}. Details: {e}"
            # print(f"Error: {err_msg}") # Caller should handle logging based on exception
            raise TransmissionConnectionError(err_msg) from e
        except Exception as e: 
            err_msg = f"An unexpected error occurred during Transmission client initialization: {e}"
            # print(f"Error: {err_msg}")
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


if __name__ == '__main__':
    # This is a basic example of how to use the client. Updated for new exception handling.
    print("Attempting to initialize TransmissionClient (ensure daemon is running and accessible)...")
    test_torrent_id_to_query = None 
    client = None # Ensure client is defined in the outer scope for cleanup

    try:
        # Replace with your actual connection details if not using defaults or if auth is needed
        # client = TransmissionClient(host='your_host', port=9091, username='user', password='pass')
        client = TransmissionClient() 

        print("\n--- Session Stats ---")
        stats = client.get_session_stats()
        print(f"  Active torrent count: {stats.active_torrent_count}")
        print(f"  Download speed: {stats.download_speed / 1024:.2f} KB/s")
        print(f"  Upload speed: {stats.upload_speed / 1024:.2f} KB/s")

        print("\n--- Listing Torrents ---")
        torrents = client.list_torrents()
        if torrents:
            for torrent in torrents:
                print(f"  ID: {torrent.id}, Name: {torrent.name}, Status: {torrent.status}, Progress: {torrent.progress:.2f}%")
                if test_torrent_id_to_query is None:
                    test_torrent_id_to_query = torrent.id
        else:
            print("  No torrents currently active.")

        sample_torrent_url = "https://releases.ubuntu.com/22.04/ubuntu-22.04.4-desktop-amd64.iso.torrent"
        print(f"\n--- Adding Torrent: {sample_torrent_url} ---")
        try:
            added_torrent = client.add_torrent(sample_torrent_url)
            print(f"  Attempted to add torrent: '{added_torrent.name}', ID: {added_torrent.id}")
            test_torrent_id_to_query = added_torrent.id 
            import time
            time.sleep(2) # Give Transmission time
        except OperationFailureError as ofe:
            print(f"  Could not add torrent: {ofe}")
            # If adding failed because it's a duplicate, try to find it to continue tests
            if "already exists" in str(ofe).lower() or "duplicate" in str(ofe).lower() :
                all_torrents = client.list_torrents()
                for t in all_torrents:
                    # This check is simplistic, assumes URL matches if it's a duplicate by URL
                    if hasattr(t, 'torrent_file') and sample_torrent_url in t.torrent_file or \
                       t.magnet_link == sample_torrent_url : # Check magnet link if it was one
                        test_torrent_id_to_query = t.id
                        print(f"  Found existing torrent with ID {test_torrent_id_to_query} to use for further tests.")
                        break


        if test_torrent_id_to_query is not None:
            print(f"\n--- Get Torrent Info (ID: {test_torrent_id_to_query}) ---")
            try:
                info = client.get_torrent_info(test_torrent_id_to_query)
                print(f"  Name: {info.name}, Status: {info.status}, Downloaded: {info.downloaded_ever / (1024*1024):.2f} MB")
            except TorrentNotFoundError:
                print(f"  Torrent with ID {test_torrent_id_to_query} not found for info.")
            except OperationFailureError as ofe:
                 print(f"  Operation failure while getting info for torrent {test_torrent_id_to_query}: {ofe}")


            print(f"\n--- Stop Torrent (ID: {test_torrent_id_to_query}) ---")
            try:
                client.stop_torrent([test_torrent_id_to_query])
                print(f"  Stop command sent for torrent ID {test_torrent_id_to_query}.")
                time.sleep(1)
                info_after_stop = client.get_torrent_info(test_torrent_id_to_query)
                print(f"  Status after stop: {info_after_stop.status}")
            except TorrentNotFoundError:
                print(f"  Torrent {test_torrent_id_to_query} not found for stop operation.")
            except OperationFailureError as ofe:
                print(f"  Failed to stop torrent {test_torrent_id_to_query}: {ofe}")

            print(f"\n--- Start Torrent (ID: {test_torrent_id_to_query}) ---")
            try:
                client.start_torrent([test_torrent_id_to_query])
                print(f"  Start command sent for torrent ID {test_torrent_id_to_query}.")
                time.sleep(1)
                info_after_start = client.get_torrent_info(test_torrent_id_to_query)
                print(f"  Status after start: {info_after_start.status}")
            except TorrentNotFoundError:
                print(f"  Torrent {test_torrent_id_to_query} not found for start operation.")
            except OperationFailureError as ofe:
                print(f"  Failed to start torrent {test_torrent_id_to_query}: {ofe}")
        else:
            print("\nSkipping single torrent operations as no torrent ID was identified/added for testing.")

        print("\n--- Session Configuration ---")
        session_config = client.get_session_config()
        print(f"  Current download directory: {session_config.download_dir}")
        original_alt_speed_enabled = session_config.alt_speed_enabled
        print(f"  Original alt_speed_enabled: {original_alt_speed_enabled}")

        print("\n--- Setting Session Configuration (toggle alt-speed) ---")
        try:
            client.set_session_config(alt_speed_enabled=not original_alt_speed_enabled)
            updated_config = client.get_session_config()
            print(f"  New alt_speed_enabled: {updated_config.alt_speed_enabled}")
            # Revert
            client.set_session_config(alt_speed_enabled=original_alt_speed_enabled)
            final_config = client.get_session_config()
            print(f"  Reverted alt_speed_enabled to: {final_config.alt_speed_enabled}")
        except OperationFailureError as ofe:
            print(f"  Failed to set session config: {ofe}")


    except TransmissionConnectionError as tce:
        print(f"CONNECTION ERROR: {tce}")
    except TorrentNotFoundError as tnfe: # Should ideally be caught closer to operation
        print(f"TORRENT NOT FOUND ERROR: {tnfe}")
    except OperationFailureError as ofe: # General operational errors
        print(f"OPERATION FAILURE ERROR: {ofe}")
    except Exception as e: # Catch-all for unexpected errors in the main block
        print(f"AN UNEXPECTED ERROR OCCURRED IN EXAMPLE USAGE: {type(e).__name__} - {e}")
    finally:
        # Cleanup: Remove the test torrent if it was added and an ID is known
        if client and client.client and test_torrent_id_to_query is not None:
            try:
                print(f"\n--- Cleanup: Attempting to remove torrent ID {test_torrent_id_to_query} ---")
                client.remove_torrent([test_torrent_id_to_query], delete_data=False) # Set delete_data=True to remove files
                print(f"  Cleanup: Remove command sent for torrent ID {test_torrent_id_to_query}.")
            except TorrentNotFoundError:
                print(f"  Cleanup: Torrent ID {test_torrent_id_to_query} not found for removal.")
            except OperationFailureError as ofe:
                print(f"  Cleanup: Failed to remove torrent ID {test_torrent_id_to_query}: {ofe}")
            except Exception as e:
                print(f"  Cleanup: An unexpected error during torrent removal: {e}")
        
        print("\nTransmission client example finished.")
