import markdown
from xhtml2pdf import pisa

def convert_md_to_pdf(md_file, pdf_file):
    # Read markdown content
    with open(md_file, 'r', encoding='utf-8') as f:
        md_text = f.read()

    # Convert markdown to html
    # Use extensions for tables and fenced code blocks
    html_content = markdown.markdown(md_text, extensions=['tables', 'fenced_code'])

    # Add some basic CSS for better rendering in xhtml2pdf
    html_template = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Helvetica, Arial, sans-serif; font-size: 12px; line-height: 1.5; color: #333; }}
            h1, h2, h3, h4 {{ color: #2c3e50; }}
            pre {{ background-color: #f8f9fa; padding: 10px; border: 1px solid #e9ecef; border-radius: 4px; font-family: Courier, monospace; font-size: 10px; }}
            code {{ font-family: Courier, monospace; background-color: #f8f9fa; padding: 2px 4px; border-radius: 3px; font-size: 10px; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #dee2e6; padding: 8px; text-align: left; }}
            th {{ background-color: #f8f9fa; font-weight: bold; }}
            blockquote {{ border-left: 4px solid #ced4da; margin-left: 0; padding-left: 15px; color: #6c757d; }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    # Generate PDF
    with open(pdf_file, 'wb') as f:
        pisa_status = pisa.CreatePDF(html_template, dest=f)

    if pisa_status.err:
        print(f"Error creating PDF: {pisa_status.err}")
    else:
        print(f"Successfully created {pdf_file}")

if __name__ == "__main__":
    convert_md_to_pdf("TrendPulse_Project_Documentation.md", "TrendPulse_Project_Documentation.pdf")
