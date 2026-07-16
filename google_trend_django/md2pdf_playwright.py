import os
import markdown
import asyncio
from playwright.async_api import async_playwright

async def convert_md_to_pdf(md_file, pdf_file):
    with open(md_file, 'r', encoding='utf-8') as f:
        md_text = f.read()

    # Convert markdown to html
    html_content = markdown.markdown(md_text, extensions=['tables', 'fenced_code', 'toc'])

    # Add html wrapper with a premium, academic report style
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <link href="https://fonts.googleapis.com/css2?family=Merriweather:wght@300;400;700&family=Open+Sans:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            @page {{
                margin: 25mm 20mm;
            }}
            body {{
                font-family: 'Open Sans', sans-serif;
                font-size: 11pt;
                line-height: 1.6;
                color: #2b2b2b;
                max-width: 100%;
                margin: 0 auto;
            }}
            
            /* Cover Page styling for the first H1 */
            h1:first-of-type {{
                font-family: 'Merriweather', serif;
                font-size: 28pt;
                text-align: center;
                margin-top: 20%;
                color: #1a365d;
                border-bottom: none;
                page-break-after: always;
            }}

            h1 {{ 
                font-family: 'Merriweather', serif;
                font-size: 20pt;
                color: #1a365d; 
                border-bottom: 2px solid #e2e8f0; 
                padding-bottom: 8px; 
                margin-top: 0;
                page-break-before: always;
            }}
            
            /* Don't page break the first H1 (handled above) or if it's right after another page break */
            h1:first-child {{
                page-break-before: auto;
            }}

            h2 {{ 
                font-family: 'Merriweather', serif;
                font-size: 16pt;
                color: #2d3748; 
                border-bottom: 1px solid #edf2f7; 
                padding-bottom: 4px; 
                margin-top: 24pt; 
            }}
            
            h3 {{
                font-family: 'Merriweather', serif;
                font-size: 13pt;
                color: #4a5568;
                margin-top: 16pt;
            }}
            
            p {{
                margin-bottom: 12pt;
                text-align: justify;
            }}

            pre {{ 
                background-color: #f8fafc; 
                padding: 12pt; 
                border-radius: 6px; 
                border: 1px solid #e2e8f0;
                overflow-x: auto; 
                page-break-inside: avoid;
            }}
            
            code {{ 
                font-family: 'Consolas', 'Monaco', monospace; 
                background-color: #f8fafc; 
                padding: 2px 4px; 
                border-radius: 3px; 
                font-size: 9.5pt; 
                color: #e53e3e;
            }}
            
            pre code {{ 
                background-color: transparent; 
                padding: 0; 
                color: #2d3748;
            }}
            
            table {{ 
                border-collapse: collapse; 
                width: 100%; 
                margin: 16pt 0; 
                page-break-inside: avoid;
            }}
            
            th, td {{ 
                border: 1px solid #cbd5e0; 
                padding: 10pt; 
                text-align: left; 
            }}
            
            th {{ 
                background-color: #edf2f7; 
                font-weight: 700; 
                color: #2d3748;
            }}
            
            tr:nth-child(even) {{
                background-color: #f8fafc;
            }}
            
            blockquote {{ 
                border-left: 4px solid #718096; 
                background-color: #f7fafc;
                margin: 12pt 0; 
                padding: 10pt 16pt; 
                color: #4a5568; 
                font-style: italic; 
                page-break-inside: avoid;
            }}
            
            .mermaid {{ 
                display: flex; 
                justify-content: center; 
                margin: 20pt 0; 
                page-break-inside: avoid;
            }}
            
            ul, ol {{
                margin-bottom: 12pt;
            }}
            
            li {{
                margin-bottom: 4pt;
            }}
        </style>
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
    </head>
    <body>
        {html_content}
        
        <script>
            mermaid.initialize({{ startOnLoad: false, theme: 'default' }});
            
            async function renderMermaid() {{
                const codeBlocks = document.querySelectorAll('code.language-mermaid');
                for (let block of codeBlocks) {{
                    const pre = block.parentElement;
                    const div = document.createElement('div');
                    div.className = 'mermaid';
                    div.textContent = block.textContent;
                    pre.parentElement.replaceChild(div, pre);
                }}
                
                try {{
                    await mermaid.run();
                }} catch (e) {{
                    console.error("Mermaid error:", e);
                }}
                
                const doneDiv = document.createElement('div');
                doneDiv.id = 'mermaid-done';
                document.body.appendChild(doneDiv);
            }}
            
            renderMermaid();
        </script>
    </body>
    </html>
    """

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        page.on("console", lambda msg: print(f"Browser console: {{msg.text}}"))
        
        await page.set_content(html_template, wait_until="networkidle")
        
        try:
            await page.wait_for_selector('#mermaid-done', timeout=15000)
        except Exception as e:
            print("Warning: Timeout waiting for #mermaid-done")
            
        await page.pdf(
            path=pdf_file, 
            format="A4", 
            print_background=True,
            display_header_footer=True,
            header_template="<div style='font-size:8px; color:#a0aec0; width:100%; text-align:right; padding-right:20px;'>TrendPulse Project Documentation</div>",
            footer_template="<div style='font-size:8px; color:#a0aec0; width:100%; text-align:center;'>Page <span class='pageNumber'></span> of <span class='totalPages'></span></div>",
            margin={'top': '20mm', 'right': '20mm', 'bottom': '20mm', 'left': '20mm'}
        )
        await browser.close()
        print(f"Successfully created {{pdf_file}}")

if __name__ == "__main__":
    asyncio.run(convert_md_to_pdf("TrendPulse_Project_Documentation.md", "TrendPulse_Project_Documentation_V2.pdf"))
