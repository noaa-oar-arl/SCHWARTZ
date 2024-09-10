import argparse
import configparser

def read_toml_file(filename):
    """Reads a TOML file and returns its contents as a dictionary."""
    config = configparser.ConfigParser()
    config.read(filename)
    return dict(config)

def main():
    parser = argparse.ArgumentParser(description="Reads a TOML file and prints its contents.")
    parser.add_argument("filename", help="The path to the TOML file")
    args = parser.parse_args()

    data = read_toml_file(args.filename)
    print(data)

if __name__ == "__main__":
    main()
