from pypdf import PdfReader

def read_pdf(uploaded_pdf):
    """
    Reads all text from an uploaded PDF.
    Returns a single string.
    """

    reader = PdfReader(uploaded_pdf)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text