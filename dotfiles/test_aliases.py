#!/usr/bin/env python3
import configparser

def read_toml_file(filename):
    config = configparser.ConfigParser()
    config.read(filename)
    result = {}
    for section in config.sections():
        result[section] = {}
        for key, value in config.items(section):
            if isinstance(value, str) and value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            result[section][key] = value
    return result

def process_custom_aliases(config):
    aliases_config = config.get('bash', {}).get('aliases', {})
    print(f"Found aliases config: {aliases_config}")

    if not aliases_config:
        return ""

    alias_lines = []
    alias_lines.append("# Custom aliases from config.toml")

    for alias_name, alias_command in aliases_config.items():
        escaped_command = alias_command.replace('"', '\\"')
        alias_lines.append(f'alias {alias_name}="{escaped_command}"')

    return '\n'.join(alias_lines)

if __name__ == "__main__":
    config = read_toml_file('config.toml')
    print("Full config:")
    for section, items in config.items():
        print(f"  [{section}]")
        for key, value in items.items():
            print(f"    {key} = {value}")

    print(f"\nBash section: {config.get('bash', {})}")

    aliases = process_custom_aliases(config)
    print(f"\nGenerated aliases:\n{aliases}")
