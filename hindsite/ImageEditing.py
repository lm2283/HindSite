import fitz, io, gc, os, zipfile
from PIL import Image, ImageDraw, ImageFont
from PIL.ExifTags import TAGS

def get_exif_data(img: Image.Image):
    """Return a dictionary of EXIF data from an image."""
    img.verify()
    exif_data = {}
    info = img.getexif()
    if info is not None:
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            exif_data[decoded] = value
    return exif_data

def get_date_time_from_exif(exif_data):
    """Extract date and time from EXIF data."""
    if 'DateTimeOriginal' in exif_data:
        date_time = exif_data['DateTimeOriginal']
        date, time = date_time.split(' ')
        return date, time
    elif 'DateTime' in exif_data:
        date_time = exif_data['DateTime']
        date, time = date_time.split(' ')
        return date, time
    return None, None

def get_time_from_img(img: Image.Image):
    exif_data = get_exif_data(img)
    _, time = get_date_time_from_exif(exif_data)
    return time

def process_file(z, filename, operation, new_z=None, rename_start=None):
    original_info = z.getinfo(filename)  # Get the info before renaming
    with z.open(filename) as file:
        with Image.open(file) as img:  # Use the file directly without reading it into memory
            img.load()
            exif_data = img.getexif()
            img, additional_data = operation(img, filename)  # Apply the passed operation to the image
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='JPEG', exif=exif_data, quality=95)
            img_bytes.seek(0)
            # Set the filename extension to .jpg since we're saving in JPEG format
            filename_base = filename.rsplit('.', 1)[0]
            filename = filename_base + '.jpg'
            # Rename the file if rename_start is provided
            if rename_start is not None:
                ext = filename.split('.')[-1]  # Get the file extension
                filename = f"{rename_start}.{ext}"
                rename_start += 1
            zip_info = zipfile.ZipInfo(filename)
            zip_info.date_time = original_info.date_time  # Use the original date_time
            zip_info.external_attr = original_info.external_attr  # Use the original external_attr
            if new_z:
                new_z.writestr(zip_info, img_bytes.getvalue())
    gc.collect()  # Manually invoke garbage collector
    return img_bytes.getvalue(), additional_data

def convert_pdf_to_jpg(pdf_file):
    # Load the PDF from the bytes
    pdf_document = fitz.open(stream=pdf_file.file.read(), filetype="pdf")
    base_filename = os.path.splitext(pdf_file.filename)[0]
    images = []
    # Convert each page to an image
    for page_number in range(pdf_document.page_count):
        page = pdf_document.load_page(page_number)
        image = page.get_pixmap()
        img_bytes = image.tobytes(output='jpg', jpg_quality=95)
        output_filename = f"{base_filename}_page_{page_number + 1}.jpg"
        images.append((output_filename, img_bytes))
    pdf_document.close()
    return images

def resize_image(img: Image.Image, filename: str, width_cm=7.0, dpi=220) -> Image.Image:
    width_px = int((width_cm / 2.54) * dpi)
    aspect_ratio = img.height / img.width
    new_height = int(width_px * aspect_ratio)
    return img.resize((width_px, new_height), resample=Image.BICUBIC)

def watermark_image(img: Image.Image, filename, factor=0.03) -> Image.Image:
    # Set the font size as a factor of the larger image dimension
    size = int(img.width * factor)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("arial.ttf", size)
    # Use the image's mode as the watermark text
    stamp_text = filename.upper()
    # Calculate text position
    x, y = 0, 0
    # Calculate the bounding box of the text using the font object
    left, upper, right, lower = font.getbbox(stamp_text)
    # Adjust the bounding box coordinates by the text position
    left += x
    upper += y
    right += x
    lower += y
    # Draw a black rectangle using the bounding box
    padding = 5  # Adjust as needed
    draw.rectangle([left - padding, upper - padding, right + padding, lower + padding], fill="black")
    # Add watermark
    draw.text((x, y), stamp_text, (255, 255, 0), font=font)
    return img