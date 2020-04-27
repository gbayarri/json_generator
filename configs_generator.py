#!/usr/bin/env python3

import argparse
import yaml
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Creates config_biobb.json and config_biobb.yml files.",
                                     formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=99999),
                                     epilog="Examples: \nconfigs_generator.py -i path/to/testconffile/conf.yml -o path/to/outputdir")
    required_args = parser.add_argument_group('required arguments')
    required_args.add_argument('--input_conf_yaml', '-i', required=True, help='conf.yml file from tests configuration')
    required_args.add_argument('--output', '-o', required=True, help='Output path to the biobb_package/biobb_package/test/data/config folder.')

    args = parser.parse_args()

    config = yaml.safe_load(open(args.input_conf_yaml))
    print(config)
    for module, module_properties in config.items():
        if isinstance(module_properties, dict) and module_properties.get('properties'):
            del module_properties['paths']
            for extension in ['yml', 'json']:
                file_out_path = Path(args.output).joinpath('config_'+module+'.'+extension)
                if not file_out_path.exists():
                    print(f'Writting: {file_out_path}')
                    with open(file_out_path, 'w') as file_out:
                        if extension == 'yml':
                            yaml.safe_dump(module_properties, file_out)
                        else:
                            json.dump(module_properties, file_out, indent=2)


if __name__ == '__main__':
    main()
