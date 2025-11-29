# utils/image_processing.py
"""
Centralized image processing utilities.
Handles thumbnail generation and WebP conversion for all photo models.
"""
import os
from io import BytesIO
from PIL import Image, ImageOps
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


def create_thumbnail(image_path, base_height=300):
    """
    Creates a thumbnail from an image file.

    Args:
        image_path: Path to the source image
        base_height: Target height for thumbnail (maintains aspect ratio)

    Returns:
        Path to the created thumbnail, or None if failed
    """
    if not os.path.exists(image_path):
        return None

    try:
        img = Image.open(image_path)

        # Handle EXIF orientation
        img = ImageOps.exif_transpose(img)

        # Calculate new dimensions
        height_percent = base_height / float(img.size[1])
        width_size = int(float(img.size[0]) * height_percent)
        img = img.resize((width_size, base_height), Image.Resampling.LANCZOS)

        # Convert RGBA to RGB if necessary
        if img.mode == 'RGBA':
            img = img.convert('RGB')

        # Generate thumbnail filename
        base_name = os.path.basename(image_path)
        name, ext = os.path.splitext(base_name)
        thumbnail_name = f'{name}_thumbnail.webp'

        # Determine thumbnail directory
        dir_path = os.path.dirname(image_path)
        thumbnail_dir = os.path.join(dir_path, 'thumbnails')
        os.makedirs(thumbnail_dir, exist_ok=True)

        thumbnail_path = os.path.join(thumbnail_dir, thumbnail_name)

        # Save as WebP
        img.save(thumbnail_path, format='WEBP', quality=85, optimize=True)

        # Return relative path from media root
        media_root = default_storage.location
        return os.path.relpath(thumbnail_path, media_root)

    except Exception as e:
        print(f"Error creating thumbnail: {e}")
        return None


def convert_to_webp(image_path, media_subfolder, delete_original=True):
    """
    Converts an image to WebP format.

    Args:
        image_path: Path to the source image
        media_subfolder: Subfolder within media directory (e.g., 'Homepage', 'Portfolio')
        delete_original: Whether to delete the original file after conversion

    Returns:
        Path to the WebP image, or empty string if already WebP or failed
    """
    if not os.path.exists(image_path):
        return ""

    # Already WebP, nothing to do
    if image_path.lower().endswith('.webp'):
        return ""

    try:
        img = Image.open(image_path)

        # Convert RGBA to RGB if necessary
        if img.mode == 'RGBA':
            img = img.convert('RGB')

        # Generate new filename
        base_name = os.path.basename(image_path)
        name, _ = os.path.splitext(base_name)
        webp_name = f'{name}.webp'

        # Build output path
        dir_path = os.path.dirname(image_path)
        webp_path = os.path.join(dir_path, webp_name)

        # Save as WebP
        img.save(webp_path, format='WEBP', quality=90, optimize=True)

        # Delete original if requested
        if delete_original and image_path != webp_path:
            os.remove(image_path)

        # Return relative path from media root
        media_root = default_storage.location
        return os.path.relpath(webp_path, media_root)

    except Exception as e:
        print(f"Error converting to WebP: {e}")
        return ""
