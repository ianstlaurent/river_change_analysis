# Purpose: Download binary river masks from Google Drive folder when used outside of Google Colab
# Author: Ian St. Laurent

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
import io

def download_files_from_drive(secret_path, FilePattern, OutputDir):

    # Define the scopes for Google Drive API
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

    if not SecretsFile:
        SecretsFile = input("Enter path to client secrets file: ")
        secret_path = '/Users/ian/Desktop/School/Fall 2023/CSC 497/Python_Library/River_Analysis/client_secret_61071723423-qdtatourf8qp1s40hai3m0i9jb893752.apps.googleusercontent.com.json'
    if not FolderName:
        FolderName = input("Enter folder name: ")
    if not FilePattern:
        FilePattern = input("Enter file pattern: ")
    if not OutputDir:
        OutputDir = input("Enter output directory: ")
        OutputDir= '/Users/ian/Desktop/School/Fall 2023/CSC 497/Python_Library/River_Analysis/binary_river_masks/'

    # Example Path Json file

    # Run the OAuth 2.0 flow to get an access token
    flow = InstalledAppFlow.from_client_secrets_file(secret_path, SCOPES)
    creds = flow.run_local_server(port=0)

    # Build the Drive service
    drive_service = build('drive', 'v3', credentials=creds)

    # Query to find the files in Google Drive
    query = f"name contains '{FilePattern}' and mimeType='image/tiff'"

    # Get the list of files that match the query
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get('files', [])

    # Download each file
    for item in items:
        print('Downloading file {0} ({1})'.format(item['name'], item['id']))
        request = drive_service.files().get_media(fileId=item['id'])
        fh = io.FileIO(OutputDir + item['name'], 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print("Download %d%%." % int(status.progress() * 100))
