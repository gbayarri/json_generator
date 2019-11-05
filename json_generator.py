import os
import glob
import argparse
from importlib import import_module
from difflib import SequenceMatcher
from ast import literal_eval
import re

regex_default = '\((\"*([a-zA-Z0-9_\-\^]*|\-*\d*\.*\d*)\"*)\)'
regex_default_array = '\((\[.*?\])\)'
regex_float = '\-*\d*\.\d*'
regex_prop_name = '\*\*(.*?)\*\*'
regex_type = '\(\*(.*?)\*\)'

class JSONSchemaGenerator():

    def __init__(self, input_package, **kwargs):
       self.input_package = input_package
       # TODO!!! GET output_path WITH MODULE FOLDER FOR SAVING JSON FILES

    def similar_string(self, a, b):
        """ check similarity between two strings """
        return SequenceMatcher(None, a, b).ratio()

    def getType(self, type):

        if type == 'str': return 'string'
        if type == 'int': return 'number'
        if type == 'float': return 'float'
        if type == 'bool': return 'boolean'
        if type == 'dic': return 'object'

        return type 

    def getDefault(self, default, i):

        # take second from the tuple (because of regex groups!)
        if(i == 0): return literal_eval(default)
        else: val = default[i]

        if val == 'True': return True
        if val == 'False': return False
        if val == 'None': return None
        if val.isdigit(): 
            return int(val)
        if re.match(regex_float, val) is not None:
            return float(val)
        # TODO: fix for arrays: ["Potential"]
        if isinstance(val, str): return val.strip('\"')
        
        return val


    def parseDocs(self, doclines):

        # get title
        title = doclines[0]
        # parse documentation
        args = False
        required = []
        json_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": "http://bioexcel.eu/biobb_analysis/json_schemas/0.1/cluster",
            "title": title,
            "type": "object",
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
                    if('properties' not in chunks1[0] and '[Optional]' not in row): required.append(prop_id)

                    # get I/O properties
                    if 'properties' not in chunks1[0]:

                        chunks2 = chunks1[1].split(')')
                        if '[Optional]' not in row: chunks3 = row.split('):')
                        else: chunks3 = row.split(')[Optional]:')

                        chunks4 = chunks3[1].split('Accepted formats:')

                        #if 'Accepted formats:' in chunks3[1]: chunks4 = chunks3[1].split('Accepted formats:')

                        # check if property has "Accepted formats:"
                        if len(chunks4) > 1: 

                            values = chunks4[1].replace(' ','').replace('.','').split(',')

                            p = {
                                "type": self.getType(chunks2[0].strip()),
                                "description": chunks4[0].strip(),
                                "enum": values
                                }

                        else:

                            p = {
                                "type": self.getType(chunks2[0].strip()),
                                "description": chunks3[1].strip()
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

                        values = chunks5[1].replace(' ','').replace('.','').split(',')

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

                        values = chunks6[1].replace(' ','').replace('.','').split(',')

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

        json_schema["required"] = required
        json_schema["properties"] = properties

        json_schema["additionalProperties"] = False

        print(json_schema)

    def launch(self):
        """ launch function for JSONSchemaGenerator """
        # import package
        packages = import_module(self.input_package)

        for package in packages.__all__:
            # for every package import all modules
            modules = import_module(self.input_package + '.' + package)
            #print(package + ": " + ', '.join(modules.__all__))
            for module in modules.__all__:
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

                # get class documentation
                klass = getattr(mod, sel_class)
                print(klass.__doc__)
                doclines = klass.__doc__.splitlines()

                self.parseDocs(doclines)
                

                ##############
                #break
                ##############

            ##############
            #break
            ##############
        

def main():
    parser = argparse.ArgumentParser(description="Creates json_schemas for given Biobb package.", formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=99999))
    parser.add_argument('--package', required=False, help='Biobb package to be parsed')

    args = parser.parse_args()

    JSONSchemaGenerator(input_package=args.package).launch()


if __name__ == '__main__':
    main()
