import argparse
import configparser
import re

def render_template(template_path, context):
    """Renders a template file using the given context.

    Args:
        template_path (str): The path to the template file.
        context (dict): A dictionary containing variable names and their corresponding values.

    Returns:
        str: The rendered template.
    """

    with open(template_path, 'r') as f:
        template_content = f.read()

    # Replace variables with their corresponding values
    for var_name, var_value in context.items():
        template_content = template_content.replace('{{ ' + var_name + ' }}', str(var_value))

    # Handle if statements
    while True:
        match = re.search(r'{% if (.*?) %}(.*?){% endif %}', template_content)
        if not match:
            break
        condition, if_block = match.groups()
        if eval(condition, context):
            template_content = template_content.replace(match.group(0), if_block)
        else:
            template_content = template_content.replace(match.group(0), '')

    return template_content


def read_toml_file(filename):
    """Reads a TOML file and returns its contents as a dictionary."""
    config = configparser.ConfigParser()
    config.read(filename)
    return dict(config)

def main():
    parser = argparse.ArgumentParser(description="Reads a TOML file and prints its contents.")
    parser.add_argument("filename", help="The path to the TOML file")
    parser.add_argument("machine", help="The machine in which use the template from"
    args = parser.parse_args()

    data = read_toml_file(args.filename)
    print(data)

if __name__ == "__main__":
    main()
