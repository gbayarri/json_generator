import glob
import argparse
import re
import json
import yaml
from importlib import import_module
from difflib import SequenceMatcher
from ast import literal_eval
from pathlib import Path, PurePath
from os import walk

regex_default = '\((\"*([a-zA-Z0-9_ \-\^\:\.\/\']*|\-*\d*\.*\d*)\"*)\)'
regex_default_array = '\((\[.*?\])\)'
regex_float = '\-*\d*\.\d*'
regex_prop_name = '\*\*(.*?)\*\*'
regex_type = '\(\*(.*?)\*\)'

class JSONSchemaGenerator():

    def __init__(self, input_package, output_path, **kwargs):
        self.input_package = input_package

        # check if output_path exists
        if not Path(output_path).exists():
            raise SystemExit('Unexisting output path')

        # check if output_path has correct structure
        if not input_package in output_path:
            raise SystemExit('Incorrect output path. The structure must be: path/biobb_package/biobb_package')

        self.output_path = PurePath(output_path).joinpath('json_schemas')
        self.output_path_test = PurePath(output_path).joinpath('test')
        self.output_path_config = PurePath(output_path).joinpath('test/data/config')

        if not Path(self.output_path).exists():
            raise SystemExit('Incorrect output path. The structure must be: path/biobb_package/biobb_package')
       

    def similar_string(self, a, b):
        """ check similarity between two strings """
        return SequenceMatcher(None, a, b).ratio()

    def getType(self, type):
        """ return JSON friendly type """
        if type == 'str': return 'string'
        if type == 'int': return 'number'
        if type == 'float': return 'float'
        if type == 'bool': return 'boolean'
        if type == 'dic': return 'object'

        return type 

    def getDefault(self, default, i):
        """ return defaults """ 
        
        if(i == 0): return literal_eval(default)
        else: val = default[i]

        if val == 'True': return True
        if val == 'False': return False
        if val == 'None': return None
        if val.lstrip('-+').isdigit(): 
            return int(val)
        if re.match(regex_float, val) is not None:
            return float(val)

        if isinstance(val, str): return val.strip('\"')
        
        return val


    def parseDocs(self, doclines, module):
        """ parse python docs to object / JSON format """

        # get title
        title = doclines[0]
        # parse documentation
        args = False
        required = []
        object_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": "http://bioexcel.eu/" + self.input_package + "/json_schemas/1.0/" + module,
            "title": title,
            "type": "object",
            "required": [],
            "properties": {}
        }
        properties = {}
        for row in doclines:
            leading = len(row) - len(row.lstrip())
            # check if arguments
            if 'Args:' in row:
                args = True

            if args:
                # first level: I/O & properties dictionary
                if leading == 8: 
                    # get required array
                    chunks1 = row.split(' (')
                    prop_id = chunks1[0].strip()
                    if('properties' not in chunks1[0] and '(Optional)' not in row): required.append(prop_id)

                    # get I/O properties
                    if 'properties' not in chunks1[0]:

                        chunks2 = chunks1[1].split(')')
                        if '(Optional)' not in row: chunks3 = row.split('):')
                        else: chunks3 = row.split(') (Optional):')

                        #chunks3[1] contains description, file type and accepted formats

                        if 'File type:' in chunks3[1]: filetype = re.search('(?<=File type:\s)(\w+)', chunks3[1]).group(1)
                        else: filetype = None

                        if 'Sample file' in chunks3[1]: sample = re.search('<(.*)>', chunks3[1]).group(1)
                        else: sample = None

                        chunks4 = chunks3[1].split('Accepted formats:')

                        # check if property has "Accepted formats:"
                        if len(chunks4) > 1: 

                            values = chunks4[1].replace('.','').split(',')
                            values = [item.strip() for item in values]
                            values = ['.*\.{0}$'.format(item) for item in values]

                            p = {
                                "type": self.getType(chunks2[0].strip()),
                                #"description": chunks4[0].strip(),
                                "description": re.search('^(.*?)(?=\.)', chunks3[1]).group(1).strip(),
                                "filetype": filetype,
                                "sample": sample,
                                "enum": values
                                }

                        else:

                            p = {
                                "type": self.getType(chunks2[0].strip()),
                                #"description": chunks3[1].strip(),
                                "description": re.search('^(.*?)(?=\.)', chunks3[1]).group(1).strip(),
                                "filetype": filetype,
                                "sample": sample
                                }

                        properties[prop_id] = p

                # second level: properties
                if leading == 12 and not row.isspace():

                    if not "properties" in properties: 
                        properties["properties"] = { "type": "object", "properties": {} }

                    prop_level1 = re.findall(regex_prop_name, row)[0]

                    chunks5 = row.split('Values:')

                    

                    if '["' and '"]' in row: 
                        regex_def = regex_default_array
                        index_def = 0
                    else: 
                        regex_def = regex_default
                        index_def = 1

                    if len(chunks5) > 1: 

                        values = chunks5[1].replace('.','').split(',')
                        values = [item.strip() for item in values]

                        p = {
                            "type": self.getType(re.findall(regex_type, row)[0]),
                            "default": self.getDefault(re.findall(regex_def, row)[0], index_def),
                            "description": chunks5[0].strip().split(') ')[-1],
                            "enum": values
                            }

                    else:

                        p = {
                            "type": self.getType(re.findall(regex_type, row)[0]),
                            "default": self.getDefault(re.findall(regex_def, row)[0], index_def),
                            "description": chunks5[0].strip().split(') ')[-1],
                            }

                    properties["properties"]["properties"][prop_level1] = p

                # third level: parameters
                if(leading == 16):

                    if not "parameters" in properties["properties"]["properties"][prop_level1]: 
                        properties["properties"]["properties"][prop_level1] = { "type": "object", "parameters": {} }

                    prop_level2 = re.findall(regex_prop_name, row)[0]

                    chunks6 = row.split('Values:')

                    if '["' and '"]' in row: 
                        regex_def = regex_default_array
                        index_def = 0
                    else: 
                        regex_def = regex_default
                        index_def = 1

                    if len(chunks6) > 1: 

                        values = chunks6[1].replace('.','').split(',')
                        values = [item.strip() for item in values]

                        p = {
                            "type": self.getType(re.findall(regex_type, row)[0]),
                            "default": self.getDefault(re.findall(regex_def, row)[0], index_def),
                            "description": chunks6[0].strip().split(') ')[-1],
                            "enum": values
                            }

                    else:
                        
                        p = {
                            "type": self.getType(re.findall(regex_type, row)[0]),
                            "default": self.getDefault(re.findall(regex_def, row)[0], index_def),
                            "description": chunks6[0].strip().split(') ')[-1],
                            }

                    properties["properties"]["properties"][prop_level1]["parameters"][prop_level2] = p

        object_schema["required"] = required
        object_schema["properties"] = properties

        object_schema["additionalProperties"] = False

        return object_schema

    def cleanOutputPath(self):
        """ removes all JSON files from the output path (except the biobb_package.json file) and all the config files """

        # get all files in json_schemas folder
        files = []
        for (dirpath, dirnames, filenames) in walk(self.output_path):
            files.extend(filenames)
            break

        # remove biobb_package.json file from array of files
        if(self.input_package + '.json' in files): files.remove(self.input_package + '.json')

        # remove files from array of files
        for f in files:
            path = PurePath(self.output_path).joinpath(f)
            Path(path).unlink()

        # get all files in config folder
        files = []
        for (dirpath, dirnames, filenames) in walk(self.output_path_config):
            files.extend(filenames)
            break

        # remove files from array of files
        for f in files:
            path = PurePath(self.output_path_config).joinpath(f)
            Path(path).unlink()

    def saveJSONFile(self, module, object_schema):
        """ save JSON file for each module """

        path = PurePath(self.output_path).joinpath(module + '.json')

        with open(path, 'w') as file:
            json.dump(object_schema, file, indent=4)

        print(str(path) + " file saved")

    def saveConfigJSONFile(self, properties, module, ):
        """ save config JSON file for each module """

        # pmx hardcoding
        if module.endswith('_docker'):
            module = module.replace('_docker', '')

        conf_json = {
            'properties': properties
        }
        path = PurePath(self.output_path_config).joinpath('config_'+ module + '.json')
        with open(path, 'w') as file:
            json.dump(conf_json, file, indent=4)

        print(str(path) + " file saved")

    def launch(self):
        """ launch function for JSONSchemaGenerator """

        # import package
        packages = import_module(self.input_package)

        # remove old JSON files
        self.cleanOutputPath()

        # get config properties
        with open(PurePath(self.output_path_test).joinpath('conf.yml')) as f:
            try:
                conf = yaml.safe_load(f)
            except yaml.YAMLError as exc:
                print(exc)                

        # get documentation of python files
        for package in packages.__all__:
            # for every package import all modules
            modules = import_module(self.input_package + '.' + package)
            for module in modules.__all__:

                # config files
                # biobb_analysis hardcoding for bfactor, rms and rmsf
                mdl = module
                if(self.input_package == 'biobb_analysis' and not module in conf):
                    mdl = module + '_first'

                # biobb_analysis hardcoding forcing to take docker cofiguration
                if(self.input_package == 'biobb_pmx'):
                    mdl = module + '_docker'

                if('properties' in conf[mdl] and conf[mdl]['properties'] is not None): 
                    self.saveConfigJSONFile(conf[mdl]['properties'], mdl)

                # json schemas
                # import single module
                mod = import_module(self.input_package + '.' + package + '.' + module)

                # get class name through similarity with module name
                sel_class = ''
                similarity = 0;
                for item in dir(mod):
                    if ( item[0].isupper() and 
                    not item.startswith('Path') and 
                    not item.startswith('Pure') and
                    not item.startswith('check_') ):
                        s = self.similar_string(item, module)
                        if s > similarity:
                            sel_class = item
                            similarity = s

                # exceptions:
                if sel_class == "KMeans" and module == "k_means": 
                    sel_class = "KMeansClustering"
                if sel_class == "KMeans" and module == "dbscan": 
                    sel_class = "DBSCANClustering"
                if sel_class == "AgglomerativeClustering": 
                    sel_class = "AgglClustering"
                if sel_class == "SpectralClustering": 
                    sel_class = "SpecClustering"

                # get class documentation
                klass = getattr(mod, sel_class)
                doclines = klass.__doc__.splitlines()

                object_schema = self.parseDocs(doclines, module)

                self.saveJSONFile(module, object_schema)


def main():
    parser = argparse.ArgumentParser(description="Creates json_schemas for given BioBB package.", 
                                     formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=99999),
                                     epilog='''Examples: \njson_generator.py -p biobb_package -o path/to/biobb_package/biobb_package\njson_generator.py --package biobb_package --output path/to/biobb_package/biobb_package''')
    required_args = parser.add_argument_group('required arguments')
    required_args.add_argument('--package', '-p', required=True, help='BioBB package to be parsed.')
    required_args.add_argument('--output', '-o', required=True, help='Output path to the biobb_package/biobb_package folder.')

    args = parser.parse_args()

    JSONSchemaGenerator(input_package=args.package, output_path=args.output).launch()


if __name__ == '__main__':
    main()
