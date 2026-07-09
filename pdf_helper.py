from pypdf import PdfReader


def read_pdf(uploaded_pdf):
    """
    Reads a PDF file and returns all text.
    """

    reader = PdfReader(uploaded_pdf)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text