## Will Schema

Within the DASS framework, we need to maintain multiple representations of will content along different stages of the processing pipeline. The DASS Wills data model manages this represenetation as a set of (currently 2) schema that specify the data model. The data model schema are implemented under the `schemas` directory:

```
<root>/schemas/
```

The data model schemas are specified using the [Swagger](https://swagger.io/) framework implementing the [OpenAPI](https://www.openapis.org/) specification.

Each DASS Will data model schema specification is implemented in a single `.yaml` file. There are currently two data models used within the DASS Wills schema, both within the `schemas` directory:

- `text_extractions_schema_v0.1.0.yaml`: Specifies the data model representing the interface between NLP-based extractions from reading and the process to translate those extractions into the Will Model schema.
- `will_model_schema_v0.1.0.yaml`: Specifies the data model representing the internal Will Model that results from having translated NLP extractions. This Will Model is intended to contain all of the extracted will semantic content and used to generate the executable will representation.

There are three aspects DASS Will data model development

- Editing the schema (the `.yaml` files).
- Using swagger-codgen to generate/update the python implementation of the schemas.
- Using the data models programmitcally to implement DASS functionality.

### Editing the schema

We recommend the [online swagger editor](https://editor-next.swagger.io/) to view and edit the schema `.yaml` files. Open the editor window and copy and paste the `.yaml` content into the left-side editor window. Make edits; the editor will provide live updates to the structure and alert the author to bugs. When satisfied, copy the contant back into the source `.yaml` file.

### Swagger Codegen

Swagger provides functionality to generate python (and other language) classes based on the specification in the Swagger `.yaml` files using the [swagger-codegen](https://swagger.io/tools/swagger-codegen/) framework.

The swagger-codegen script should be run after an update to a data model schema specification has been "accepted" by the DASS Wills developers. When this is the case, the following steps are taken:

- Run the `codegen_swagger_model.py` script (see below).
- Manually verify that the generated python code is what was expected (i.e., represents the updates made to the corresponding data model `.yaml` specification).
- Add, commit and push the new generated 
- Once satisfied, delete the copy of the previous data model code

#### Installing swagger-codegen

In order to use the swagger-codegen framework, you must first install it on your local machine. Install via the method described for your operating system [here](https://github.com/swagger-api/swagger-codegen#Prerequisites). Make sure to install a version after 3.0 that will support OpenAPI 3.

#### Running the `codegen_swagger_model.py` script

The following script orchestrates running swagger-codegen and using either of the current DASS Wills data model schemas to generate the python class code.

```
<root>/schemas/codegen_swagger_model.py
```

The script currently supports generating one or both of the following schema, each generating files in the corresponding subdirectory:

- **Text Extraction**: `<root>/schemas/model/te`
- **Will Model**: `<root>/schemas/model/wm`

Which of these directories is generated is currently controlled within the `main()` function (which in turn is called within the top-level `__main__` block of the script). TODO: provide a command-line interface.

The script orchestrates the following actions:

1. Preserves the original version of the directory under `<root>/schemas/model/` to `<root>/schemas/model/<base_name>_orig_<date>`.
2. Runs `swagger-codegen` from the shell to generate the new code.

### Using the data models: Will Model example

The following python file provides a simple example of how to create an instance Will Model using the python classes that were generated based on the `will_model_schema_v0.1.0.yaml` specification.

```
<root>/WILL_JSON/bequeath_01_specific_to_specific/will_model.py
```

The file has this structure:

- Import relevant data model objects (`from schemas.model.wm import` ...) from the swagger-codegen schema python class implementation (located under `<root>/schemas/model/`)
- Note the naming convention: All Will Model classes start with `WM`; Text Extraction classes (not used in this example) start with `TE`.
- Function `make_instance()` implements the incremental construction of the Will Model objects for the example. This culminates in the top-level object `WMWillModel`.
- The top-level `__main__` script demonstrates printing the model using `to_str()` and `to_dict()`.

### TODO

- [ ] Finish implementation of model-to-JSON export. This will use the codegen-generated `to_dict()` functionality and json-to-dict to export a JSON file.
- [ ] For each schema, write an ingestion function to read a JSON file in to a python object.
- [ ] Write the translator from the Text Extraction data model object to Will Model object.

# Older Documentation

## Creating and manipulating smart wills

The files in this directory are a first attempt at code for creating and manipulating smart wills.

### Creating a will
To create a will, use the command

    ./create_will -j <input_json_file>

### Asset Distribution Chart
The Distribution_Scenarios_DASS.pdf is a chart of distribution scenarios for Issue, Living Issue, and Per Stirpes. The top two scenarios assume that Living Issue and Issue mean the same thing and the bottom two scenarios assume they mean different distributions. Per stirpes does not show in the third or fourth scenario but would be the same distribution as the first two. It is omitted for ease of reading. The first and third scenarios show one set of living and deceased (in red letters) children and grandchildren. The second and fourth scenarios show another set of living and deceased children. Note that in the first third section of scenarios 1 and 2, it is not labeled issue, living issue or per stirpes. This scenario happens with a set of explicit conditions stated in the will itself.

### The JSON representation of a will
The JSON representation of a will currently contains the following top-level items:

- `"text"` : the original natural-language text of the will;
- `"testator"` : the name, ID, and possibly other information about the testator;
- `"witnesses"` : the name, ID, and information about the witnesses;
- `"directives"` : the directives of the will.  This is a mapping from assets to the beneficiary and any conditions governing the transfer.

Example: the file `will01.json` encodes the following simple will:

```
{
    "text" : "I, John Doe, bequeath my red car to Tom Doe and my vacuum cleaner to Mary Hoover",
    "testator" : {
	"name" : "John Doe",
	"id" : "0x1234",
	"info" : "address: 12 Magnolia Lane, Bisbee; phone: 123-456-7890"
    },
    "witnesses" : [
	{
	    "name" : "Jack Doe",
	    "id" : "0x2345",
	    "info" : ""
	},
	{
	    "name" : "Jane Doe",
	    "id" : "0x3456",
	    "info" : ""
	}
    ],
    "directives" : {
	"red car" : {
	    "if" : "True",
	    "then" : {
		"beneficiary" : {
		    "name" : "Tom Doe",
		    "id" : "0x4567",
		    "info" : ""
		}
	    }
	},
	"vacuum cleaner" : {
	    "if" : "True",
	    "then" : {
		"beneficiary" : {
		    "name" : "Mary Hoover",
		    "id" : "0x5678",
		    "info" : ""
		}
	    }
	}
    }
}
```
