# Creating and manipulating smart wills

The files in this directory are a first attempt at code for creating and manipulating smart wills.

## Creating a will
To create a will, use the command

    ./create_will -j <input_json_file>

## The JSON representation of a will
The JSON representation of a will currently contains the following top-level items:

- `"text"` : the original natural-language text of the will;
- `"testator"` : the name, ID, and possibly other information about the testator;
- `"witnesses"` : the name, ID, and information about the witnesses;
- `"directives"` : the directives of the will.  This is a mapping mapping assets to the beneficiary and any conditions governing the transfer.

Example: the file `in01.json` encodes the following simple will:

```
{
    "text" : "I, John Doe, bequeath my red car to Tom Doe and my vacuum cleaner to Mary Hoover",
    "testator" : {
	"name" : "John Doe",
	"id" : "0x1234"
    },
    "witnesses" : {
	"1" : {
	    "name" : "Jack Doe",
	    "id" : "0x2345"
	},
	"2" : {
	    "name" : "Jane Doe",
	    "id" : "0x3456"
	}
    },
    "directives" : {
	"red car" : {
	    "beneficiary" : {
		"name" : "Tom Doe",
		"id" : "0x4567"
	    },
	    "condition" : "True"
	},
	"vacuum cleaner" : {
	    "beneficiary" : {
		"name" : "Mary Hoover",
		"id" : "0x5678"
	    },
	    "condition" : "True"
	}
    }
}
```
