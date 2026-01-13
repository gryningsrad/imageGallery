import os
import shutil
import math
import sys
from enum import Enum
from PIL import Image, ExifTags

class Headers(Enum):
    """
    Define ENUM for statistics Headers 
    """
    LANDSCAPE_HIGH_DPI = "Landscape High DPI (>250)"
    LANDSCAPE_LOW_DPI = "Landscape Low DPI (<250)"
    LANDSCAPE_OTHER_DPI = "Landscape Other DPI"
    PORTRAIT_HIGH_DPI = "Portrait High DPI (>250)"
    PORTRAIT_LOW_DPI = "Portrait Low DPI (<250)"
    PORTRAIT_OTHER_DPI = "Portrait Other DPI"

# Pixel threshold
HIGH_RESOLUTION = 1000
GALLERY_FOLDER_NAME = "gallery"
TUMBNAIL_WIDTH = 600

def get_image_info(image_path) -> tuple:
    """Get image information including width, height, and DPI.

    Args:
        image_path (str): Path to the image file.

    Returns:
        tuple: Width, height, and DPI of the image.
    """
    with Image.open(image_path) as img:
        width, height = img.size
        dpi = img.info.get('dpi', (72, 72))[0]  # Default to 72 if DPI info is not available
    return width, height, dpi

def reset_orientation(image):
    """_summary_

    Args:
        image (_type_): _description_

    Returns:
        _type_: _description_
    """
    # Adjust image orientation based on EXIF
    for orientation in ExifTags.TAGS.keys():
        if ExifTags.TAGS[orientation] == 'Orientation':
            break
    exif = image._getexif()

    if exif is not None:

        print(f"Orientation: {exif.get(orientation)}")

        orientation_value = exif.get(orientation)
        if orientation_value == 3:
            image = image.rotate(180, expand=True)
            print("Rotated 180 degrees")
        elif orientation_value == 6:
            print("Rotated 90 degrees")
            image = image.rotate(270, expand=True)
        elif orientation_value == 8:
            print("Rotated 270 degrees")
            image = image.rotate(90, expand=True)
    else:
        print("No EXIF data found. Image orientation will not be adjusted.")
    return image

def create_thumbnail(file_path, width) -> Image:
    """Create a thumbnail of the image.

    Args:
        file_path (str): Path to the image file.
        width (int, optional): Width of the thumbnail.
        height will be calculated based on the aspect ratio.
        
        
    Returns:
        Image: Thumbnail image.
    """

    height=0

    with Image.open(file_path) as img:

        # Calculate the new size maintaining the aspect ratio
        # width is given, calculate height
        original_width, original_height = img.size

        if original_height < original_width:
            # portrait image
            aspect_ratio = original_width / original_height
            height = int(width * aspect_ratio)
        else:
            # Landscape image or square image
            aspect_ratio = original_height / original_width
            height = int(width * aspect_ratio)

        # Create the thumbnail
        img = reset_orientation(img)
        img.thumbnail((width, height))
        return img.copy()

def copy_and_rename_images_in_subfolders(base_folder, target_folder) -> None:
    """Copy and rename images in subfolders, creating thumbnails instead of copying the original files.

    Args:
        base_folder (str): Path to the base folder.
        target_folder (str): Path to the target folder.
    """
    image_serial_number = 1

    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    for root, dirs, files in os.walk(base_folder):
        if GALLERY_FOLDER_NAME in dirs:
            dirs.remove(GALLERY_FOLDER_NAME)  # Exclude the gallery folder from the search

        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg')):
                file_path = os.path.join(root, file)
                width, height, dpi = get_image_info(file_path)
                subfolder_name = os.path.basename(root)
                new_file_name = f"{image_serial_number:03}-{subfolder_name}-{file} - {width}x{height}@{math.trunc(dpi)}.jpg"
                new_file_path = os.path.join(target_folder, new_file_name)

                # Create and save the thumbnail
                thumbnail = create_thumbnail(file_path, width=TUMBNAIL_WIDTH)  # Example thumbnail width
                thumbnail.save(new_file_path)

                print(f"Created thumbnail for {file_path} and saved to {new_file_path}")
                image_serial_number += 1

def count_images_by_category(base_folder) -> dict:
    """Counts the number of images in the base folder by category.

    Args:
        base_folder (str): Path to the base folder.

    Returns:
        dict: Dictionary with counts of images by category.
    """
    landscape_high_dpi = 0
    landscape_low_dpi = 0
    landscape_other_dpi = 0
    portrait_high_dpi = 0
    portrait_low_dpi = 0
    portrait_other_dpi = 0

    for root, dirs, files in os.walk(base_folder):
        if GALLERY_FOLDER_NAME in dirs:
            dirs.remove(GALLERY_FOLDER_NAME)  # Exclude the gallery folder from the search

        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg')):
                file_path = os.path.join(root, file)
                width, height, dpi = get_image_info(file_path)

                if width > height:  # Landscape orientation
                    if dpi > 250:
                        landscape_high_dpi += 1
                    elif dpi < 100:
                        landscape_low_dpi += 1
                    else:
                        landscape_other_dpi += 1
                else:  # Portrait orientation
                    if dpi > 250:
                        portrait_high_dpi += 1
                    elif dpi < 250:
                        portrait_low_dpi += 1
                    else:
                        portrait_other_dpi += 1

    return {
        "landscape_high_dpi": landscape_high_dpi,
        "landscape_low_dpi": landscape_low_dpi,
        "landscape_other_dpi": landscape_other_dpi,
        "portrait_high_dpi": portrait_high_dpi,
        "portrait_low_dpi": portrait_low_dpi,
        "portrait_other_dpi": portrait_other_dpi
    }

def create_image_gallery(target_folder):
    """Create an HTML file with an image gallery from the images in the target folder.

    Args:
        target_folder (str): Path to the target folder.
    """

    print_vote_box = input("Do you want to create an Image Gallery? (y/N): ").strip().upper()

    if print_vote_box == "":
        print_vote_box = False

    if print_vote_box == "Y":
        print_vote_box = True

    # Else
    printVoteBox = False

    images = [f for f in os.listdir(target_folder) if f.lower().endswith(('.jpg', '.jpeg'))]
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Image Gallery</title>
        <link rel="stylesheet" href="../styles.css">
    </head>
    <body>
    """

    low_html_content = """
        <h1>Low-res pictures</h1><div class="gallery">
    """
    high_html_content = """
        <h1>High-res pictures</h1><div class="gallery">
    """
    images = [f for f in os.listdir(target_folder) if f.lower().endswith(('72.jpg', '72.jpeg'))]

    for image in images:    
        # Split up images in big or smaller photos
        low_html_content += f'''
            <div class="image">
            <img src="{os.path.join(target_folder, image)}" alt="{image}" title="{image}">
            <p>Image nr # {image[:image.find('-')] if '-' in image else image}</p>
        '''
        if print_vote_box:
            low_html_content += '<div class="rectangle"><div class="rectangletext">VOTE HERE</div></div></div>'
        else:
            low_html_content += '<p></p></div>'

    images = [f for f in os.listdir(target_folder) if f.lower().endswith(('96.jpg', '96.jpeg'))]

    for image in images:    
        # Split up images in big or smaller photos
        low_html_content += f'''
            <div class="image">
            <img src="{os.path.join(target_folder, image)}" alt="{image}" title="{image}">
            <p>Image nr # {image[:image.find('-')] if '-' in image else image}</p>
        '''

        if print_vote_box:
            low_html_content += '<div class="rectangle"><div class="rectangletext">VOTE HERE</div></div></div>'
        else:
            low_html_content += '<p></p></div>'

    images = [f for f in os.listdir(target_folder) if f.lower().endswith(('300.jpg', '300.jpeg'))]
    for image in images:    
        # Split up images in big or smaller photos
        high_html_content += f'''
            <div class="image">
            <img src="{os.path.join(target_folder, image)}" alt="{image}" title="{image}">
            <p>Image nr # {image[:image.find('-')] if '-' in image else image}</p>
            <p></p>
            </div>
        '''
        if print_vote_box:
            high_html_content += '<div class="rectangle"><div class="rectangletext">VOTE HERE</div></div></div>'
        else:
            high_html_content += '<p></p></div>'

    html_content += high_html_content + "</div>"
    html_content += low_html_content + "</div>"
    html_content += """
    </body>
    </html>
    """

    with open(os.path.join(target_folder, "ImageGallery.html"), "w") as html_file:
        html_file.write(html_content)

def main():
    """Main function to run the program."""
    base_folder = os.path.dirname(os.path.abspath(__file__))
    target_folder = os.path.join(base_folder, GALLERY_FOLDER_NAME)

    statistics = count_images_by_category(base_folder)
    print("Images have been counted by category")

    for key, value in statistics.items():
        header = Headers[key.upper()].value if key.upper() in Headers.__members__ else key
        print(f"{header}: {value}")

    response = input("Do you want to create an Image Gallery? (y/N): ").strip().upper()

    if response == "":
        response = "N"

    if response == "Y":
        print("Thumbnails and Image Gallery HTML will be created")
        copy_and_rename_images_in_subfolders(base_folder, target_folder)
        create_image_gallery(target_folder)
        print("Image copying, renaming, and gallery creation completed.")
    elif response == "N":
        print("You chose to exit!")
    else:
        print("Invalid input. Please try again. Program will exit")
        sys.exit()

if __name__ == "__main__":
    main()