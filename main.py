from fastapi import FastAPI, Query
import requests
from bs4 import BeautifulSoup
import os
from zipfile import ZipFile
from io import BytesIO
from fastapi.responses import FileResponse
import shutil

app = FastAPI()

def download_images(chapter_url):
    response = requests.get(chapter_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    img_tags = soup.select('img.reader-img')
    image_urls = [img['src'] for img in img_tags]
    return image_urls

def save_chapter_cbz(image_urls, chapter_name):
    os.makedirs(chapter_name, exist_ok=True)
    for i, url in enumerate(image_urls):
        img_data = requests.get(url).content
        with open(f"{chapter_name}/{i:03}.jpg", "wb") as f:
            f.write(img_data)

def generate_next_chapter_url(current_url):
    parts = current_url.rstrip('/').split('/')
    try:
        current_ch_num = int(parts[-1])
        parts[-1] = str(current_ch_num + 1)
        return '/'.join(parts)
    except:
        return None

@app.get("/")
def root():
    return {"message": "SnowMTL Multi-chapter Downloader is ready!"}

@app.get("/download-multi")
def download_multiple_chapters(
    base_url: str = Query(..., description="Starting chapter URL from snowmtl.ru"),
    count: int = Query(3, description="Number of chapters to download")
):
    try:
        folder_name = "multi_chapter_download"
        os.makedirs(folder_name, exist_ok=True)
        current_url = base_url

        for i in range(count):
            image_urls = download_images(current_url)
            if not image_urls:
                break
            chapter_folder = f"{folder_name}/chapter_{i+1}"
            save_chapter_cbz(image_urls, chapter_folder)
            current_url = generate_next_chapter_url(current_url)
            if not current_url:
                break

        zip_filename = "multi_chapters.zip"
        with ZipFile(zip_filename, 'w') as zipf:
            for root, _, files in os.walk(folder_name):
                for file in files:
                    filepath = os.path.join(root, file)
                    zipf.write(filepath, arcname=os.path.relpath(filepath, folder_name))

        shutil.rmtree(folder_name)
        return FileResponse(zip_filename, media_type='application/zip', filename=zip_filename)

    except Exception as e:
        return {"error": str(e)}