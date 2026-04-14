import os
import markdown
from weasyprint import HTML


def convert_md2html(md_file):
    """
    The convert_md2html function takes a markdown file as input and converts it to html.
    It uses the Python Markdown library, which is a pure-Python implementation of John Gruber's Markdown.
    It supports the full syntax of Markdown (including tables) and extensions such as codehilite for syntax highlighting.

    :param md_file: Specify the markdown file to be converted
    :return: None
    """
    html_file = '.'.join([md_file.rsplit('.', 1)[0], 'html'])

    md_extensions_config = {
        "tables": {
            "use_align_attribute": True
        }
    }
    with open(md_file, "r") as f:
        text = f.read()
        html = markdown.markdown(text,
                                 extensions=["md_in_html",
                                             "tables",
                                             "fenced_code",
                                             "codehilite"],
                                 extension_configs=md_extensions_config)

    with open(html_file, "w") as f:
        f.write(html)


def write_html2pdf(file, theme=None):
    """
    The write_html2pdf function takes a file name as input and writes the corresponding HTML file to PDF.

    :param file: Specify the file to be converted
    :param theme: Specify the css file to use for styling the pdf
    :return: None
    """
    input = '.'.join([file.rsplit('.', 1)[0], 'html'])
    output = '.'.join([file.rsplit('.', 1)[0], 'pdf'])

    with open(input, "r") as f:
        html = f.read()

    base_url = os.path.dirname(os.path.realpath(__file__))

    if theme is not None:
        BASE_DIR = os.path.abspath(os.path.dirname(__file__))
        css_file = theme
        if not os.path.exists(css_file):
            css_file = os.path.join(BASE_DIR, 'themes/' + theme + '.css')

        print(css_file)
        # weasyprint.DEFAULT_OPTIONS.update({"attachments": ["./images/Aumovio.jpg"]})
        HTML(string=html, base_url=base_url).write_pdf(output, presentational_hints=True, stylesheets=[css_file])
    else:
        HTML(string=html, base_url=base_url).write_pdf(output, presentational_hints=True)
