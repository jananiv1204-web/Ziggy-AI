from pypdf import PdfReader


def load_pdf(uploaded_file):
    """
    Reads an uploaded PDF and returns cleaned text.
    """

    reader = PdfReader(uploaded_file)

    pages = []

    for page in reader.pages:

        text = page.extract_text()

        if text:

            text = text.replace("\n", " ")

            text = text.strip()

            pages.append(text)

    return "\n".join(pages)