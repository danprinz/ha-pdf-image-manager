#!/usr/bin/env python3
"""
PDF to PNG Converter
Converts a PDF file to a single PNG image with all pages arranged side by side.
Pure Python implementation using pypdfium2.
"""

import argparse
import io
from pathlib import Path
from PIL import Image

try:
    import pypdfium2 as pdfium

    PYPDFIUM2_AVAILABLE = True
except ImportError:
    PYPDFIUM2_AVAILABLE = False


def pdf_to_png(
    pdf_path: str, output_path: str, target_width: int = 3840, target_height: int = 2160
):
    """
    Convert PDF to PNG with all pages side by side.

    Args:
        pdf_path: Path to input PDF file
        output_path: Path for output PNG file
        target_width: Target width of output PNG (default: 3840)
        target_height: Target height of output PNG (default: 2160)
    """
    if not PYPDFIUM2_AVAILABLE:
        raise ImportError(
            "pypdfium2 is required for PDF processing. Please install it."
        )

    try:
        # Open PDF document
        pdf = pdfium.PdfDocument(pdf_path)
        num_pages = len(pdf)

        if num_pages == 0:
            raise ValueError("PDF has no pages")

        # Render each page to PIL Image (from last to first for right-to-left sequence)
        page_images = []
        for page_index in range(num_pages - 1, -1, -1):  # Reverse order: last to first
            page = pdf.get_page(page_index)

            # Calculate scale to get high quality rendering
            # Start with a reasonable DPI (150-300)
            scale = 2.0  # This gives roughly 144 DPI for typical PDFs

            # Render page to bitmap
            bitmap = page.render(scale=scale, rotation=0)

            # Convert bitmap to PIL Image
            pil_image = bitmap.to_pil()
            page_images.append(pil_image)

            # Clean up
            page.close()

        pdf.close()

        # Create combined image
        _create_combined_image(page_images, output_path, target_width, target_height)

    except Exception as e:
        raise ValueError(f"Failed to process PDF: {e}")


def _create_combined_image(
    page_images, output_path: str, target_width: int, target_height: int
):
    """Create a combined image from multiple page images."""
    num_pages = len(page_images)

    if num_pages == 1:
        # Single page - just resize to fit target dimensions
        page_img = page_images[0]

        # Calculate scale to fit within target dimensions while maintaining aspect ratio
        scale_width = target_width / page_img.width
        scale_height = target_height / page_img.height
        scale = min(scale_width, scale_height)

        new_width = int(page_img.width * scale)
        new_height = int(page_img.height * scale)

        # Resize the image
        resized_img = page_img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Create output canvas and center the image
        output_img = Image.new("RGB", (target_width, target_height), "white")
        x_offset = (target_width - new_width) // 2
        y_offset = (target_height - new_height) // 2
        output_img.paste(resized_img, (x_offset, y_offset))

    else:
        # Multiple pages - arrange side by side
        # Calculate equal spacing distribution
        margin_spaces = num_pages + 1  # Left, between pages, and right margins
        available_width_for_pages = target_width  # Use 100% for pages, 0% for margins
        margin_width = (target_width - available_width_for_pages) / margin_spaces
        page_area_width = available_width_for_pages / num_pages

        # Find the maximum page dimensions for scaling reference
        max_page_height = max(img.height for img in page_images)
        max_page_width = max(img.width for img in page_images)

        # Calculate scale to fit pages within allocated space and target height
        scale_width = page_area_width / max_page_width
        scale_height = target_height / max_page_height
        scale = min(scale_width, scale_height)  # * 0.9  # Leave some padding

        # Resize pages maintaining aspect ratio
        scaled_images = []
        scaled_max_height = 0

        for img in page_images:
            new_width = int(img.width * scale)
            new_height = int(img.height * scale)
            scaled_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            scaled_images.append(scaled_img)
            scaled_max_height = max(scaled_max_height, new_height)

        # Create output canvas
        output_img = Image.new("RGB", (target_width, target_height), "white")

        # Calculate vertical centering offset
        v_offset = (target_height - scaled_max_height) // 2

        # Paste pages with equal distribution across width
        for i, scaled_img in enumerate(scaled_images):
            # Calculate x position: left margin + (page_index * (page_area + margin))
            page_center_x = (
                margin_width
                + (i * (page_area_width + margin_width))
                + (page_area_width / 2)
            )
            page_x = int(page_center_x - (scaled_img.width / 2))

            # Center each page vertically
            page_v_offset = v_offset + (scaled_max_height - scaled_img.height) // 2
            output_img.paste(scaled_img, (page_x, page_v_offset))

    # Save with high quality
    output_img.save(output_path, "PNG", optimize=False, compress_level=1)
    print(f"Successfully converted PDF to {output_path}")
    print(f"Output dimensions: {target_width}x{target_height}")
    print(f"Pages processed: {num_pages}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert PDF to PNG")
    parser.add_argument("pdf_path", help="Path to input PDF file")
    parser.add_argument("output_path", help="Path for output PNG file")
    parser.add_argument(
        "--width", type=int, default=3840, help="Target width (default: 3840)"
    )
    parser.add_argument(
        "--height", type=int, default=2160, help="Target height (default: 2160)"
    )

    args = parser.parse_args()
    pdf_to_png(args.pdf_path, args.output_path, args.width, args.height)
