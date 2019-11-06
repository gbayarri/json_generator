# JSON generator

Script for generating BioBB JSON Schemas for every package. Passing the name of the package and the absolute route to it, all the JSON files will be automatically generated from the documentation of every package's module.

## Execution steps

### Step 1: activate environment

Activate the environment where the BioBB package is loaded:

```Shell
conda activate biobb_env
```

### Step 2: execute script

Run the python script passing the BioBB package to be parsed and the folder where the JSON files will be saved:

```Shell
python3 json_generator.py -p biobb_package -o path/to/biobb/package/json_schemas
```

```Shell
python3 json_generator.py --package biobb_package --output path/to/biobb/package/json_schemas
```

## Files structure

The structure of a biobb package must be:

* biobb_package
	* biobb_package
		* **\_\_init\_\_.py**
		* block
			* **\_\_init\_\_.py**
			* module 1
			* module 2
		* docs
		* **json_schemas**
		* test
	* .gitignore
	* Dockerfile
	* LICENSE
	* README.md
	* setup.py
	* Singularity.latest

### \_\_init\_\_.py files

The *\_\_init\_\_.py* file in the first level must have the following structure:

```Python
name = "biobb_package"
__all__ = ["block1", "block2", ..., "blockn"]
```

The *\_\_init\_\_.py* file in the second level must have the following structure:

```Python
name = "block1"
__all__ = ["module1", "module2", ..., "modulen"]
```

In the *\_\_all\_\_* list we have to put all the modules for which we want to generate a JSON schema.

### json_schemas folder

The *json_schemas* folder must exist before executing the script. The file *biobb_package.json* won't be affected by the script's execution.

## Docs specifications

All the docs must be written in correct markdown language and they must be properly indented. Example of documentation:

```Markdown
Description of the module.

Args:
    arg_name1 (arg_type): Description for argument 1. Accepted formats: format1, format2, format3.
    arg_name2 (arg_type)[Optional]: Description for argument 2. Accepted formats: format1, format2.
    properties (dic):
        * **property1** (*prop_type*) - (property1_default) Property 1 description.
        * **property2** (*prop_type*) - (property2_default) Property 2 description. Values: value1, value2, value3.
        * **property3** (*dic*) - (None) Property 3 description.
            * **parameter1** (*param_type*) - (parameter1_default) Parameter 1 description. Values: value1, value2, value3.
```

### Arguments

The arguments must have the next format:

```Markdown
arg_name (arg_type)[Optional]: Description. Accepted formats: format1, format2, format3.
```

The *argument type* must be between parenthesis. Argument types: *str* (string), *dic* (dictionary).

If the argument is optional, the **[Optional]** expression must be right next the *argument type*.

If there are formats they must be a list preceded by the **Accepted formats:** expression.

### Properties

The properties must have the next format:

```Markdown
* **property** (*prop_type*) - (property_default) Property description. Values: value1, value2, value3.
```

The *property name* must be a list item in markdown bold (between double asterisk).

The *property type* must be between parenthesis. Property types: *str* (string), *dic* (dictionary), *int* (integer), *float*, *bool* (boolean).

The *property default* must be between parenthesis.

If there are values they must be a list preceded by the **Values:** expression.

### Parameters

The parameters must have the next format:

```Markdown
* **parameter** (*param_type*) - (parameter_default) Parameter description. Values: value1, value2, value3.
```

The *parameter name* must be a list item in markdown bold (between double asterisk).

The *parameter type* must be between parenthesis. Parameter types: *str* (string), *dic* (dictionary), *int* (integer), *float*, *bool* (boolean).

The *parameter default* must be between parenthesis.

If there are values they must be a list preceded by the **Values:** expression.

## Credits

Genís Bayarri, Pau Andrio, Josep Lluis Gelpí.

Molecular Modeling and Bioinformatics Group. IRB Barcelona.