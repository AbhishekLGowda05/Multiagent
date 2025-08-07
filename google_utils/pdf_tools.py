from fpdf import FPDF
import os

def create_pdf_from_text(text: str, file_path: str = "report.pdf") -> str:
    """
    Creates a PDF file from a given text string.

    Args:
        text: The content to be written to the PDF.
        file_path: The path to save the generated PDF file.

    Returns:
        The path to the created PDF file.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Add content
    pdf.multi_cell(0, 10, text)
    
    # Save the PDF
    pdf.output(file_path)
    
    return file_path
