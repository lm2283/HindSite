from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from pillow_heif import register_heif_opener
from collections import defaultdict
import io, zipfile

from hindsite import ImageEditing, KdeAnalysis

register_heif_opener()

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_root():
    return FileResponse('static/index.html')

@app.post("/converter")
def heic_converter(zip_file: UploadFile = File(...), width_cm: float = 7.0):
    file_contents = zip_file.file.read()
    output = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(file_contents), 'r') as z:
        with zipfile.ZipFile(output, 'a', zipfile.ZIP_DEFLATED) as new_z:
            for filename in z.namelist():
                ImageEditing.process_file(z, filename, new_z, lambda img, fname: (ImageEditing.resize_image(img, fname, width_cm=width_cm), None))
    output.seek(0)
    return StreamingResponse(output, media_type="application/zip", headers={"Content-Disposition": "attachment; filename=converted_resized_output.zip"})

@app.post("/resizer")
def resizer(zip_file: UploadFile = File(...), width_cm: float = 7.0):
    file_contents = zip_file.file.read()
    output = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(file_contents), 'r') as z:
        with zipfile.ZipFile(output, 'a', zipfile.ZIP_DEFLATED) as new_z:
            for filename in z.namelist():
                ImageEditing.process_file(z, filename, lambda img, fname: (ImageEditing.resize_image(img, fname, width_cm=width_cm), None), new_z)
    output.seek(0)
    return StreamingResponse(output, media_type="application/zip", headers={"Content-Disposition": "attachment; filename=resized_output.zip"})

@app.post("/renamer")
def renamer(zip_file: UploadFile = File(...), start_number: int = 1):
    file_contents = zip_file.file.read()
    output = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(file_contents), 'r') as z:
        with zipfile.ZipFile(output, 'a', zipfile.ZIP_DEFLATED) as new_z:
            for filename in sorted(z.namelist()):
                _, start_number = ImageEditing.process_file(z, filename, new_z, lambda img, fname: (img, start_number))
    output.seek(0)
    return StreamingResponse(output, media_type="application/zip", headers={"Content-Disposition": "attachment; filename=renamed_output.zip"})

@app.post("/watermarker")
def watermarker(zip_file: UploadFile = File(...)):
    file_contents = zip_file.file.read()
    output = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(file_contents), 'r') as z:
        with zipfile.ZipFile(output, 'a', zipfile.ZIP_DEFLATED) as new_z:
            for filename in z.namelist():
                ImageEditing.process_file(z, filename, lambda img, fname: (ImageEditing.watermark_image(img, fname), None), new_z)
    output.seek(0)
    return StreamingResponse(output, media_type="application/zip", headers={"Content-Disposition": "attachment; filename=watermarked_output.zip"})

@app.post("/pdf-to-images")
def pdf_to_images(pdf_file: UploadFile = File(...)): 
    images = ImageEditing.convert_pdf_to_jpg(pdf_file)
    # Create a ZIP file with the images
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'a', zipfile.ZIP_DEFLATED) as z:
        for img_name, img_bytes in images:
            z.writestr(img_name, img_bytes)
    output.seek(0)
    return StreamingResponse(output, media_type="application/zip", headers={"Content-Disposition": "attachment; filename=pages.zip"})

@app.post("/grouper")
def grouper(zip_file: UploadFile = File(...)):
    file_contents = zip_file.file.read()
    times = []
    images = {}  # Store the images in memory for now
    with zipfile.ZipFile(io.BytesIO(file_contents), 'r') as z:
        for filename in z.namelist():
            img_data, time_taken = ImageEditing.process_file(z, filename, lambda img, fname: (img, KdeAnalysis.time_to_fraction_of_day(ImageEditing.get_time_from_img(img))))
            times.append(time_taken)
            images[filename] = img_data  # Store the image data
    cluster_assignments = KdeAnalysis.adaptive(times)
    # Group images by their cluster
    clustered_images = defaultdict(list)
    for filename, cluster in zip(images.keys(), cluster_assignments):
        clustered_images[cluster].append(filename)
    # Create a new ZIP file with the nested file structure
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'a', zipfile.ZIP_DEFLATED) as new_z:
        for cluster, filenames in clustered_images.items():
            for filename in filenames:
                # Add the image to the subfolder corresponding to its cluster
                new_z.writestr(f"G{cluster}/{filename}", images[filename])
    output.seek(0)
    return StreamingResponse(output, media_type="application/zip", headers={"Content-Disposition": "attachment; filename=grouped_images.zip"})

@app.post("/reorganize")
def reorganize(zip_file: UploadFile = File(...)):
    file_contents = zip_file.file.read()
    # Dictionary to store filenames by subfolder
    subfolder_files = defaultdict(list)
    with zipfile.ZipFile(io.BytesIO(file_contents), 'r') as z:
        for filename in z.namelist():
            # Split the path to get the subfolder and the file name
            parts = filename.split('/')
            if len(parts) > 1:
                subfolder, file_name = parts
                subfolder_files[subfolder].append(file_name)
        # Sort subfolders based on the image names inside them
        sorted_subfolders = sorted(subfolder_files.keys(), key=lambda x: sorted(subfolder_files[x])[0] if subfolder_files[x] else "")
        # Create a new ZIP file with the reorganized structure
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'a', zipfile.ZIP_DEFLATED) as new_z:
            for index, subfolder in enumerate(sorted_subfolders):
                for file_name in subfolder_files[subfolder]:
                    # Rename the subfolder based on its index
                    new_subfolder_name = f"G{index + 1}"
                    new_z.writestr(f"{new_subfolder_name}/{file_name}", z.read(f"{subfolder}/{file_name}"))
    output.seek(0)
    return StreamingResponse(output, media_type="application/zip", headers={"Content-Disposition": "attachment; filename=reorganized_images.zip"})