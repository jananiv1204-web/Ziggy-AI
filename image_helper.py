from PIL import Image


def load_image(uploaded_file):
    """
    Opens the uploaded image using Pillow.

    Returns:
        PIL.Image object
    """

    if uploaded_file is None:
        return None

    image = Image.open(uploaded_file)

    return image