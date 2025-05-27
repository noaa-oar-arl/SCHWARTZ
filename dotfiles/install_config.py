#!/usr/bin/env python3
import argparse
import configparser
import re
import os
import shutil
import logging
import datetime
from typing import Any
from pathlib import Path
import sys

print("Starting script", file=sys.stderr)  # Direct to stderr

# Configure logging
def setup_logging(log_level=logging.INFO, log_file=None):
    """
    Set up logging configuration with specified log level and optional log file.

    Args:
        log_level: The logging level (default: INFO)
        log_file: Path to log file (default: None - logs to console only)
    """
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler with higher logging level
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)  # Ensure console gets all messages at the set level
    root_logger.addHandler(console_handler)

    # Create file handler if log file is specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Print test message to verify logging is working
    root_logger.debug("Logging initialized")

    return root_logger

def modify_ncviewrc(filename: str, cmaps: list, output_file: str) -> None:
    """
    Modify the ncviewrc file to include only the selected colormaps.

    Args:
        filename (str): Path to the ncviewrc_all file
        cmaps (list): List of colormap paths to include
        output_file (str): Path to the output file
    """
    logger = logging.getLogger()
    logger.info(f"Modifying ncviewrc file: {filename}")
    logger.info(f"Output file will be: {output_file}")

    try:
        with open(filename) as f:
            res = []
            lines = f.readlines()
            res.append(lines[0])
            res.append(lines[1])

            logger.info(f"Processing {len(cmaps)} colormaps")
            for cmap in cmaps:
                cmap_name = os.path.basename(cmap).replace('.ncmap', '')
                for line in lines[2:]:
                    if f'{cmap_name}' in line:
                        res.append(line)

            logger.info(f"Found {len(res)-2} colormap entries in ncviewrc")

            # Create a new list with the modified strings
            modified_data = []
            for index, element in enumerate(res):
                # Find the first space to determine where the number ends
                space_index = element.find(' ')
                # Replace the number with index - 1
                new_element = f"{index - 1}{element[space_index:]}"
                modified_data.append(new_element.strip('\n'))

            # output file
            with open(output_file, 'w') as f:
                f.write('\n'.join(modified_data))

            logger.info(f"Successfully wrote ncviewrc configuration to {output_file}")

    except Exception as e:
        logger.error(f"Error modifying ncviewrc file: {str(e)}")
        raise

def check_bash_profile_sourced():
    """
    Check if .bash_profile is sourced in .bashrc file
    """
    home_dir = Path.home()
    bashrc_file = home_dir / ".bashrc"
    bash_profile_file = home_dir / ".bash_profile"

    if not bashrc_file.exists():
        print(".bashrc file not found")
        return False

    with open(bashrc_file, "r", encoding='utf-8') as f:
        bashrc_contents = f.read()

    if f"source {bash_profile_file}" in bashrc_contents or f". {bash_profile_file}" in bashrc_contents:
        print(".bash_profile is sourced in .bashrc")
        return True
    else:
        print(".bash_profile is not sourced in .bashrc")
        return False


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

    # Process the configuration to strip quotes from values
    result = {}
    for section in config.sections():
        result[section] = {}
        for key, value in config.items(section):
            # Strip quotes if the value is a string
            if isinstance(value, str) and value.startswith('"') and value.endswith('"'):
                value = value[1:-1]  # Remove first and last character
            result[section][key] = value

    return result


def install_ncmaps(source_dir: str, dest_dir: str, colormap_config: dict) -> list:
    """
    Install the ncmap files from source_dir to dest_dir based on activation settings in config.toml.

    Args:
        source_dir (str): Source directory containing ncmap files
        dest_dir (str): Destination directory to install ncmap files
        colormap_config (dict): Dictionary containing colormap activation settings from config.toml

    Returns:
        list: List of installed colormap paths
    """
    logger = logging.getLogger()
    logger.info(f"Installing ncmaps from {source_dir} to {dest_dir}")

    # Create destination directory if it doesn't exist
    if not os.path.exists(dest_dir):
        logger.info(f"Creating destination directory: {dest_dir}")
        os.makedirs(dest_dir, exist_ok=True)

    # Get list of available colormaps from the source directory
    colormaps_dir = os.path.join(source_dir, 'colormaps')
    if not os.path.exists(colormaps_dir):
        logger.error(f"Colormaps directory not found: {colormaps_dir}")
        return []

    # Get list of colormaps to install from config.toml
    active_colormaps = []
    logger.info(f"Reading colormap activation settings from config.toml")

    # Get all .ncmap files in the colormaps directory
    all_colormaps = [f for f in os.listdir(colormaps_dir) if f.endswith('.ncmap')]
    logger.info(f"Found {len(all_colormaps)} total colormaps in {colormaps_dir}")

    # Filter by activation settings in config.toml
    for cmap_file in all_colormaps:
        cmap_name = cmap_file.replace('.ncmap', '')
        # Check if this colormap is activated in config
        if cmap_name in colormap_config and colormap_config[cmap_name]:
            active_colormaps.append(os.path.join('colormaps', cmap_file))

    logger.info(f"Found {len(active_colormaps)} active colormaps to install")

    # Copy each active colormap file to the destination directory
    installed_count = 0
    for cmap in active_colormaps:
        src_file = os.path.join(source_dir, cmap)
        dest_file = os.path.join(dest_dir, os.path.basename(cmap))

        try:
            shutil.copy2(src_file, dest_file)
            logger.info(f"Copied {src_file} to {dest_file}")
            installed_count += 1
        except Exception as e:
            logger.error(f"Failed to copy {src_file} to {dest_file}: {str(e)}")

    logger.info(f"Successfully installed {installed_count} out of {len(active_colormaps)} colormaps")

    # Return list of installed colormaps for ncviewrc configuration
    return active_colormaps


def install_oh_my_bash() -> bool:
    """
    Install Oh My Bash if it's not already installed

    Returns:
        bool: True if installation was successful or already exists, False otherwise
    """
    logger = logging.getLogger()
    logger.info("Installing Oh My Bash")

    home_dir = Path.home()
    oh_my_bash_dir = home_dir / ".oh-my-bash"

    # Check if Oh My Bash is already installed
    if oh_my_bash_dir.exists():
        logger.info("Oh My Bash is already installed")
        return True

    # Clone Oh My Bash repository
    try:
        command = 'bash -c "$(curl -fsSL https://raw.githubusercontent.com/ohmybash/oh-my-bash/master/tools/install.sh)" --unattended'
        logger.info(f"Running command: {command}")

        # Run the command and capture output
        import subprocess
        result = subprocess.run(command, shell=True, capture_output=True, text=True)

        # Check if successful
        if result.returncode == 0:
            logger.info("Oh My Bash installed successfully")
            return True
        else:
            logger.error(f"Failed to install Oh My Bash: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"Error installing Oh My Bash: {str(e)}")
        return False


def main() -> None:
    """
    Reads a TOML file and prints its contents.

    Args:
        filename (str): The path to the TOML file.
        machine (str): The machine in which use the template from.
    """
    print("Starting main function")
    parser = argparse.ArgumentParser(description="Reads a TOML file and prints its contents.")
    parser.add_argument("-f", "--filename", help="The path to the TOML file", default="config.toml")
    parser.add_argument("-m", "--machine", help="The machine in which use the template from", required=False)
    parser.add_argument("--install-ncmaps", help="Install ncmaps files", action="store_true")
    parser.add_argument("--log-level", help="Logging level (default: INFO)", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default='INFO')
    args = parser.parse_args()

    print(f"Arguments: {args}")

    # Setup logging
    log_level = getattr(logging, args.log_level)
    print(f"Setting up logging with level: {log_level}")
    logger = setup_logging(log_level=log_level)

    print("Logging setup complete")
    logger.info("Starting installation script")

    config = read_toml_file(filename=args.filename)
    logger.info(f"Read configuration from {args.filename}")

    # get home directory
    home = os.environ.get("HOME")
    logger.info(f"Home directory: {home}")

    # Install ncmaps if requested
    if args.install_ncmaps:
        logger.info("Installing ncmaps files")

        # Get the current script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        logger.info(f"Script directory: {script_dir}")

        # Get ncmaps configuration from config.toml
        ncmaps_config = config.get('ncmaps', {})
        colormap_config = config.get('ncmaps.colormaps', {})

        # Source and destination paths
        ncmaps_source_dir = os.path.join(script_dir, ncmaps_config.get('source_dir', 'ncmaps'))
        ncmaps_dest_dir = os.path.join(home, ncmaps_config.get('dest_dir', '.ncmaps'))
        logger.info(f"Source directory: {ncmaps_source_dir}")
        logger.info(f"Destination directory: {ncmaps_dest_dir}")

        # Install ncmap files
        installed_cmaps = install_ncmaps(ncmaps_source_dir, ncmaps_dest_dir, colormap_config)

        # Configure ncviewrc
        ncviewrc_source = os.path.join(script_dir, ncmaps_config.get('ncviewrc_source', 'ncmaps/ncviewrc_all'))
        ncviewrc_dest = os.path.join(home, ncmaps_config.get('ncviewrc_dest', '.ncviewrc'))
        logger.info(f"Configuring ncviewrc from {ncviewrc_source} to {ncviewrc_dest}")

        modify_ncviewrc(ncviewrc_source, installed_cmaps, ncviewrc_dest)

        logger.info(f"Installed ncmaps to {ncmaps_dest_dir}")
        logger.info(f"Created ncviewrc at {ncviewrc_dest}")
        return

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

    # Install Oh My Bash if enabled in config
    bash_config = config.get('bash', {})
    if bash_config.get('use_oh_my_bash', False):
        logger.info("Oh My Bash is enabled in config, installing...")
        oh_my_bash_installed = install_oh_my_bash()
        if oh_my_bash_installed:
            logger.info("Oh My Bash installed successfully")
        else:
            logger.warning("Failed to install Oh My Bash")
    else:
        logger.info("Oh My Bash is not enabled in config, skipping installation")

    # Install machine-specific configuration if a machine is specified
    if args.machine:
        logger.info(f"Installing machine-specific configuration for {args.machine}")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        bash_dir = os.path.join(script_dir, 'bash')
        install_bash_script = os.path.join(bash_dir, 'install_bash.sh')

        # Check if the specified machine configuration exists
        machine_config = os.path.join(bash_dir, 'machines', args.machine)
        if os.path.exists(machine_config):
            try:
                import subprocess
                result = subprocess.run(f"bash {install_bash_script} {args.machine}",
                                        shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info(f"Successfully installed machine-specific configuration for {args.machine}")
                else:
                    logger.error(f"Failed to install machine-specific configuration: {result.stderr}")
            except Exception as e:
                logger.error(f"Error installing machine-specific configuration: {str(e)}")
        else:
            logger.error(f"Machine configuration file for {args.machine} not found at {machine_config}")
    else:
        logger.info("No machine specified, using default configuration")
        # Check if .bash_site exists
        if not os.path.exists(os.path.join(home, '.bash_site')):
            try:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                bash_dir = os.path.join(script_dir, 'bash')
                install_bash_script = os.path.join(bash_dir, 'install_bash.sh')
                import subprocess
                result = subprocess.run(f"bash {install_bash_script} default",
                                      shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info("Successfully installed default machine configuration")
                else:
                    logger.error(f"Failed to install default machine configuration: {result.stderr}")
            except Exception as e:
                logger.error(f"Error installing default machine configuration: {str(e)}")
                logger.info("Consider specifying a machine with -m option.")

    # Get the user's current selection in the active terminal.
    if args.machine == "hera":
        pass  # Add your hera-specific code here


if __name__ == "__main__":
    main()
