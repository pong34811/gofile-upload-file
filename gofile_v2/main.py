import os
import asyncio
from pygofile import Gofile
from tkinter import Tk, filedialog
import time
from typing import Dict, List
from tqdm import tqdm

# Configurations
TOKEN = "ugYhNVomilmWIR0Soak1qHtDBKVtuphG"
FOLDER_ID = "947f79af-7f7b-45aa-80c7-de8884faeea7"
MAX_RETRIES = 3
MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1GB in bytes
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.mp4', '.zip', '.rar', '.txt', '.pdf'}

class UploadStats:
    def __init__(self):
        self.successful: List[str] = []
        self.failed: Dict[str, str] = {}
        self.total_size: int = 0
        self.uploaded_size: int = 0

def is_valid_file(file_path: str) -> bool:
    """Check if file is valid and has allowed extension"""
    if not os.path.exists(file_path):
        return False
    _, ext = os.path.splitext(file_path)
    return ext.lower() in ALLOWED_EXTENSIONS

async def upload_file(file_path: str, folder_id: str, token: str, stats: UploadStats, pbar: tqdm) -> None:
    """Upload a single file with retry mechanism"""
    if not is_valid_file(file_path):
        stats.failed[file_path] = "Invalid file type or file doesn't exist"
        return

    file_size = os.path.getsize(file_path)
    if file_size > MAX_FILE_SIZE:
        stats.failed[file_path] = "File too large (max 1GB)"
        return

    for attempt in range(MAX_RETRIES):
        try:
            gofile = Gofile(token=token)
            response = await gofile.upload(
                file=file_path,
                folder_id=folder_id
            )
            
            if response.get('downloadPage'):
                stats.successful.append(file_path)
                stats.uploaded_size += file_size
                pbar.update(1)
                print(f"\n✓ Successfully uploaded: {os.path.basename(file_path)}")
                print(f"  Download link: {response['downloadPage']}")
                return
            
            print(f"\nAttempt {attempt + 1}/{MAX_RETRIES} failed. Retrying...")
            await asyncio.sleep(2)  # Non-blocking sleep
            
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                stats.failed[file_path] = str(e)
                print(f"\n✗ Failed to upload {os.path.basename(file_path)}: {e}")

async def upload_folder(folder_path: str, folder_id: str, token: str) -> None:
    """Upload all files in a folder with statistics"""
    stats = UploadStats()
    
    # Count valid files and total size
    valid_files = []
    for root, _, files in os.walk(folder_path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            if is_valid_file(file_path):
                valid_files.append(file_path)
                stats.total_size += os.path.getsize(file_path)

    if not valid_files:
        print("No valid files found to upload!")
        return

    print(f"\nFound {len(valid_files)} valid files to upload")
    print(f"Total size: {stats.total_size / (1024*1024):.2f} MB")

    with tqdm(total=len(valid_files), desc="Uploading", unit="file") as pbar:
        # Create tasks for all files
        tasks = [
            upload_file(file_path, folder_id, token, stats, pbar)
            for file_path in valid_files
        ]
        
        # Execute all uploads concurrently
        await asyncio.gather(*tasks)

    # Print summary
    print("\n=== Upload Summary ===")
    print(f"Total files processed: {len(valid_files)}")
    print(f"Successfully uploaded: {len(stats.successful)}")
    print(f"Failed uploads: {len(stats.failed)}")
    print(f"Total data uploaded: {stats.uploaded_size / (1024*1024):.2f} MB")
    
    if stats.failed:
        print("\nFailed uploads details:")
        for file_path, error in stats.failed.items():
            print(f"- {os.path.basename(file_path)}: {error}")

def select_file_or_folder(is_folder: bool = False) -> str:
    """Unified selection method for both files and folders"""
    root = Tk()
    root.withdraw()
    path = filedialog.askdirectory() if is_folder else filedialog.askopenfilename(
        filetypes=[("Supported files", " ".join(f"*{ext}" for ext in ALLOWED_EXTENSIONS))]
    )
    root.destroy()
    return path

async def main():
    """Main async function"""
    print("GoFile Uploader")
    print("1. Single file")
    print("2. Folder")
    
    try:
        choice = input("Enter your choice (1/2): ").strip()
        
        if choice == "1":
            file_path = select_file_or_folder()
            if file_path and os.path.isfile(file_path):
                stats = UploadStats()
                with tqdm(total=1, desc="Uploading", unit="file") as pbar:
                    await upload_file(file_path, FOLDER_ID, TOKEN, stats, pbar)
            else:
                print("No file selected or invalid file.")
                
        elif choice == "2":
            folder_path = select_file_or_folder(is_folder=True)
            if folder_path and os.path.isdir(folder_path):
                await upload_folder(folder_path, FOLDER_ID, TOKEN)
            else:
                print("No folder selected or invalid folder.")
                
        else:
            print("Invalid choice. Please select 1 or 2.")
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())