import os
import time
import mimetypes
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv
load_dotenv()
from unstructured_agent import ingest_document_file, store
import threading

WATCH_DIRECTORY = os.path.join(os.path.dirname(__file__), "gst_docs")

def get_mime_type(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or "application/octet-stream"

class GSTFolderHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            self.process_file(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self.process_file(event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            doc_id = os.path.basename(event.src_path)
            print(f"File deleted: {doc_id}. Removing from vector store...")
            try:
                store.delete(ids=[doc_id])
                print(f"Successfully removed {doc_id} from Vector Store.")
            except Exception as e:
                print(f"Error removing {doc_id} from Vector Store: {e}")

    def process_file(self, file_path):
        filename = os.path.basename(file_path)
        # Skip temporary files or system files
        if filename.startswith('.') or filename.startswith('~'):
            return
            
        print(f"Processing file: {filename}")
        try:
            with open(file_path, "rb") as f:
                file_bytes = f.read()
            
            mime_type = get_mime_type(file_path)
            success = ingest_document_file(filename, file_bytes, mime_type)
            if success:
                print(f"Successfully ingested {filename}")
            else:
                print(f"Failed to ingest {filename}")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

def run_initial_scan():
    print(f"Starting initial scan of {WATCH_DIRECTORY}...")
    if not os.path.exists(WATCH_DIRECTORY):
        os.makedirs(WATCH_DIRECTORY)
        print(f"Created directory: {WATCH_DIRECTORY}")
        return

    for filename in os.listdir(WATCH_DIRECTORY):
        file_path = os.path.join(WATCH_DIRECTORY, filename)
        if os.path.isfile(file_path):
            # Check if already in collection if possible, or just upsert
            # For simplicity, we just upsert everything on startup
            handler = GSTFolderHandler()
            handler.process_file(file_path)

def start_watchdog():
    # Run initial scan in a separate thread to not block the main process
    run_initial_scan()
    
    event_handler = GSTFolderHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIRECTORY, recursive=False)
    observer.start()
    print(f"Watchdog started on {WATCH_DIRECTORY}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def start_watchdog_background():
    daemon_thread = threading.Thread(target=start_watchdog, daemon=True)
    daemon_thread.start()
    return daemon_thread

if __name__ == "__main__":
    # If run directly, run in foreground
    start_watchdog()
