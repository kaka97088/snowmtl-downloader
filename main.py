from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from bs4 import BeautifulSoup
import requests
import os
import zipfile
from fpdf import FPDF

app = FastAPI()

def download_images_from_chapter(chapter_url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(chapter_url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    image_tags = soup.select("img.chapter-img") or soup.find_all("img")

    image_urls = []
    for img in image_tags:
        src = img.get("src")
        if src and src.startswith("http"):
            image_urls.append(src)
    return image_urls

def save_as_cbz(images, filename="chapter.cbz"):
    os.makedirs("temp", exist_ok=True)
    paths = []
    for idx, url in enumerate(images):
        img_data = requests.get(url).content
        path = f"temp/page_{idx+1}.jpg"
        with open(path, "wb") as f:
            f.write(img_data)
        paths.append(path)
    with zipfile.ZipFile(filename, 'w') as zipf:
        for path in paths:
            zipf.write(path, arcname=os.path.basename(path))
    for path in paths:
        os.remove(path)
    os.rmdir("temp")

def save_as_pdf(images, filename="chapter.pdf"):
    pdf = FPDF()
    pdf.set_auto_page_break(0)
    for url in images:
        img_path = "temp_img.jpg"
        with open(img_path, "wb") as f:
            f.write(requests.get(url).content)
        pdf.add_page()
        pdf.image(img_path, x=0, y=0, w=210, h=297)
    pdf.output(filename)

@app.get("/")
def read_root():
    return {"message": "SnowMTL Downloader API is live!"}

@app.get("/download")
def download_file(
    chapter_url: str = Query(...),
    format: str = Query("cbz"),
    count: int = Query(1)
):
    # For simplicity, only download 1 chapter
    images = download_images_from_chapter(chapter_url)
    filename = f"downloaded_chapter.{format}"

    if format == "cbz":
        save_as_cbz(images, filename)
    else:
        save_as_pdf(images, filename)

    return FileResponse(filename, filename=filename, media_type="application/octet-stream")
