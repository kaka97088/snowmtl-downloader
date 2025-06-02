from fastapi import FastAPI, Query import requests from bs4 import BeautifulSoup import os from zipfile import ZipFile from fpdf import FPDF from io import BytesIO

app = FastAPI()

HEADERS = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36" }

def get_image_links(chapter_url): response = requests.get(chapter_url, headers=HEADERS) if response.status_code != 200: return []

soup = BeautifulSoup(response.text, "html.parser")

# Support both /manga/... and /reader/... formats
# Look for image containers used in both formats
image_tags = soup.select(".reading-content img, .reader-area img")
image_urls = [img.get("src") for img in image_tags if img.get("src")]

return image_urls

def download_images(image_urls): images = [] for idx, url in enumerate(image_urls): try: img_data = requests.get(url, headers=HEADERS).content images.append((f"{idx:03}.jpg", img_data)) except: continue return images

def create_cbz(images): cbz_io = BytesIO() with ZipFile(cbz_io, "w") as cbz: for filename, content in images: cbz.writestr(filename, content) cbz_io.seek(0) return cbz_io

def create_pdf(images): pdf = FPDF() for filename, content in images: img_path = f"/tmp/{filename}" with open(img_path, "wb") as f: f.write(content) pdf.add_page() pdf.image(img_path, x=10, y=10, w=190) os.remove(img_path)

pdf_output = BytesIO()
pdf.output(pdf_output)
pdf_output.seek(0)
return pdf_output

@app.get("/download") def download_chapter(chapter_url: str = Query(...), format: str = Query("cbz"), count: int = Query(1)): current_url = chapter_url all_images = []

for _ in range(count):
    image_urls = get_image_links(current_url)
    if not image_urls:
        break

    images = download_images(image_urls)
    all_images.extend(images)
    break  # For now, skip next-chapter chaining (we can implement later)

if format == "pdf":
    pdf_io = create_pdf(all_images)
    return StreamingResponse(pdf_io, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=chapter.pdf"})
else:
    cbz_io = create_cbz(all_images)
    return StreamingResponse(cbz_io, media_type="application/vnd.comicbook+zip", headers={"Content-Disposition": "attachment; filename=chapter.cbz"})

from fastapi.responses import StreamingResponse
