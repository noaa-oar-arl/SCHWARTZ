#!/usr/bin/env python3
import argparse
import configparser
import re
from typing import Any
import os 


def render_template(template_path: str, context: dict[str, Any]) -> str:
    """Renders a template file using the given context.

    Args:
        template_path (str): The path to the template file.
        context (dict): A dictionary containing variable names and their corresponding values.

    Returns:
        str: The rendered template.
    """
    if not context:
        raise ValueError("Context dictionary cannot be empty")

    with open(template_path, 'r') as f:
        template_content = f.read()

    def replace_variables(template_content, context):
        for key, value in context.items():
            if isinstance(value, dict):
                for nested_key, nested_value in value.items():
                    if not isinstance(nested_key, str):
                        raise ValueError("Nested key in context dictionary must be a string")
                    if not isinstance(nested_value, (int, float, str, bool)):
                        raise ValueError("Nested value in context dictionary must be a string, integer, float, or boolean")
                    template_content = template_content.replace('{{{{ {0}.{1} }}}}'.format(key, nested_key), str(nested_value))
            else:
                if not isinstance(key, str):
                    raise ValueError("Key in context dictionary must be a string")
                if not isinstance(value, (int, float, str, bool)):
                    raise ValueError("Value in context dictionary must be a string, integer, float, or boolean")
                template_content = template_content.replace('{{{{ {0} }}}}'.format(key), str(value))
        return template_content

    template_content = replace_variables(template_content, context)

    # Handle if statements
    while True:
        match = re.search(r'{% if (.*?) %}(.*?){% endif %}', template_content, re.DOTALL)
        if not match:
            break
        condition, block = match.groups()
        if not isinstance(condition, str):
            raise ValueError("Condition in if statement must be a string")
        if not isinstance(block, str):
            raise ValueError("Block in if statement must be a string")

    return template_content

def read_toml_file(filename: str) -> dict:
    """Reads a TOML file and returns its contents as a dictionary."""
    config = configparser.ConfigParser()
    config.read(filename)
    return {section: dict(config.items(section)) for section in config.sections()}


def main() -> None:
    """
    Reads a TOML file and prints its contents.

    Args:
        filename (str): The path to the TOML file.
        machine (str): The machine in which use the template from.
    """
    parser = argparse.ArgumentParser(description="Reads a TOML file and prints its contents.")
    parser.add_argument("-f", "--filename", help="The path to the TOML file", default="config.toml")
    parser.add_argument("-m", "--machine", help="The machine in which use the template from", required=False)
    args = parser.parse_args()

    config = read_toml_file(filename=args.filename)
    
    # get home directory 
    home = os.environ("HOME")

    # Change bash aliases 
    #====================
    alias = render_template(template_path="bash/bash_aliases", context=config)

    # write bash aliases to $home/.bash_aliases
    with open(file=f"{home}/.bash_aliases", mode="a") as f:
        f.write(alias)

    # Change bash functions
    #======================
    functions = render_template(template_path="bash/bash_functions", context=config)

    # write bash functions to $home/.bash_functions
    with open(file=f"{home}/.bash_functions", mode="a") as f:
        f.write(functions)

    # Change bash profile
    #====================
    profile = render_template(template_path="bash/bash_profile", context=config)

    # write bash profile to $home/.bash_profile
    with open(file=f"{home}/.bash_profile", mode="a") as f:
        f.write(profile)

    # Change .gitconfig
    #==================
    gitconfig = render_template(template_path="git/gitconfig", context=config)

    # write .gitconfig to $home/.gitconfig
    with open(file=f"{home}/.gitconfig", mode="a") as f:
        f.write(gitconfig)

    # Change github_profile 
    #======================
    github_profile = render_template(template_path="git/github_profile", context=config)

    # write github_profile to $home/.gitconfig
    with open(file=f"{home}/.github_profile", mode="a") as f:
        f.write(github_profile)
    if args.machine == "hera": 
        





if __name__ == "__main__":
    main()
