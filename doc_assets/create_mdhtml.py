from jinja2 import Environment, FileSystemLoader
from sys import argv
import os
import markdown2

if __name__ == "__main__":
    contents = markdown2.markdown_path(argv[1])
    this_dir = os.path.dirname(os.path.abspath(__file__))
    j2_env = Environment(loader=FileSystemLoader(os.path.join(this_dir, "docs")), trim_blocks=True)
    html = j2_env.get_template(os.path.join("md_template.html")).render(title=argv[2], body=contents)

    with open(os.path.join("docs", argv[1][:-2]+"html"), "wb") as f:
        f.write(html.encode("utf-8"))
