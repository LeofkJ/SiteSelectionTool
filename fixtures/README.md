You should be able to modify this tool to fit your needs without touching any code.

You're going to need to provide a set of instructions. These instructions will be used by the code to build the website and to know how to interact with the geographical data.

# Step 1: Split the procedure into steps

At each step, the user will have choices to make and will able to see what the results of those choices are.

At each step, you should determine which data is accessed. This could be:
- The currently stored data (computed from previous steps)
- A specific file
- A file to be determined by the user's input

In every case, you will need to specify what operations are done on this data, and in all but the first case, you need to specify how to combine the previous data with the newly computed one.

Additional steps available are:
- area computation (typically used to remove polygons that are too small)
- buffer calculation (typically used to include or exclude parts of polygons close to a geographical feature, such as roads or rivers)
- site optimisation

There are two types of user inputs: dropdowns and sliders.

Dropdowns allow the user to select options (usually text), while sliders allow the user to select a number.

# Step 2: Modify readableTemplate.json

Once you've established what the steps are, you can edit [readableTemplate.json](readableTemplate.json) using the following syntax:

## Operation types:
The options are `fileSelection`, `attributeSelection`, `buffer`, `areaComputation` and `selectSites`

### fileSelection:

This step's data will be the entirety of the file specified by the user's selection.

See [How To Specify The File path](README.md/#how-to-specify-the-file-path)).

### attributeSelection:

This step's data will be the polygons of the specified file with attributes corresponding to the user input.

See [How To Specify The File path](README.md/#how-to-specify-the-file-path) and [Example steps](README.md/#example-steps)

### buffer:
This step's data will be a buffer around a file's plygons, with a buffer size specified by the user. 

See [Example steps](README.md/#example-steps)

### areaComputation:
This step's data will be the area of the previous step's polygons. The user can specify which polygons to keep using the same operations as [attributeSelection](README.md/#attributeselection)

See [Example steps](README.md/#example-steps)

### selectSites
**This is typically the last step before downloading the data.**
This step will select a user-specified amount of sites to keep. The sites chosen will be optimized to minimize the euclidean distance between sites.

## Between step operations:
The options are `null`, `intersection`, `difference` and `clip`.

### null:
Use this if it is the first step, or when no files are accessed (specifically for `areaComputation` and `selectSites` operations)

### intersection:
Use this to get the intersection between the previous step's data and the current step's data.

### difference:
Use this to keep from the previous step's data the polygons that are NOT IN the current step's data.

### clip:
Use this to keep from the previous step's data the polygons that are IN the current step's data.

## Step template:

```json
{
    "stepTitle": "Put a descriptive title for the step. Shown to the user.",
    "operationType": "what operation is being done at this step? Options are fileSelection, attributeSelection, buffer, areaComputation, selectSites",
    "betweenStepOperation": "How will the data computed at this step be combined with the data computed at the previous step? Options are null (for the first step, or when the operation is done on the data of the previous step), intersection, difference, clip",
    "options":[

    ]
}
```

The options array will regroup all the user inputs of the current step. There are two formats, depending on the option type (slider or dropdown).

## Dropdown:

### If operationType is `fileSelection`:
```json
    {
        "description": "Put a descriptive description for this input. Shown to the user.",
        "type": "Dropdown",
        "file": "Put the root of the path to the file to be accessed. Can be empty.",
        "choices": [
            
        ]
    },
```

### If operationType is `attributeSelection`:
```json
    {
        "description": "Put a descriptive description for this input. Shown to the user.",
        "type": "Dropdown",
        "file": "Put the root of the path to the file to be accessed. Can be empty.",
        "attribute": "attribute to be selected",
        "choices": [
            
        ]
    },
```
### Choices array

The choices array will be all the choices available to the user. It can either be an array of choices like so:

```json
    ["Choice 1", "Choice 2", "Choice 3"]
```

Or it can be an array of arrays, where each array has the human readable text the user will select and the corresponding code (either for the file path or the attribute) like so:

```json
    [
        ["Choice 1", "c_1"],
        ["Choice 2", "c2"], 
        ["Choice 3", "choice3"]
    ]
```

## Slider

### If operationType is `fileSelection`:
```json
    {
        "description": "Put a descriptive description for this input. Shown to the user.",
        "type": "Slider",
        "file": "Put the root of the path to the file to be accessed. Can be empty.",
        "minimum": "Integer or float. Minimum value the user can select",
        "maximum": "Integer or float. Maximum value the user can select",
        "step": "Integer or float. How far apart are the possible values? For example, the second available number will be minimum+step, the third will be minimum + 2*step, etc..."
    },
```

### If operationType is `attributeSelection`:
```json
    {
        "description": "Put a descriptive description for this input. Shown to the user.",
        "type": "Slider",
        "file": "Put the root of the path to the file to be accessed. Can be empty.",
        "attribute": "attribute to be selected",
        "operation": "What operation to do when selecting values. Options are =, >=, <=, >, <; Default is =",
        "minimum": "Integer or float. Minimum value the user can select",
        "maximum": "Integer or float. Maximum value the user can select",
        "step": "Integer or float. How far apart are the possible values? For example, the second available number will be minimum+step, the third will be minimum + 2*step, etc..."
    },
```

# How to specify the file path

Your geojson file and the path to them must be properly defined. 

Here are how the code determines which file to access:

## If operationType is `attributeSelection`:

The first option will determine which file to access.

The path to the file accessed will be the first option's `file` + the first option's number (if option type is Slider) or the first option's choice (if the option type is Dropdown) + `.geojson`

## If operationType is `fileSelection`:

All the options will determine which file to access.

The file path is a concatenation of first option's `file` + first option's number or choice + second option's `file` + second option's number or choice + ... + `.geojson`

## If operationType is `buffer`:

Every option will point to a different file as follows:

The file path is the option's `file`.

The buffer size is the option's number or choice.

## If operationType is `areaComputation` or `selectSites`:

The currently stored data will be accessed. No files are looked for.

# Example steps:

```json
 {
        "stepTitle": "Aerial Survey Data",
        "operationType": "attributeSelection",
        "betweenStepOperation": null,
        "options":[
            {
                "description": "Choose an insect: ",
                "type": "Dropdown",
                "file": "insect_",
                "choices": [["Spruce Budworm", "sb"], ["Jack Pine Budworm", "jpb"]]
            },
            {
                "description": "Choose damage type: ",
                "type": "Dropdown",
                "attribute": "RANKING",
                "choices": ["Light", "Moderate-Severe", "Mortality"]
            },
            {
                "description": "Select year: ",
                "type": "Slider",
                "attribute": "EVENT_YEAR",
                "operation": "=",
                "minimum": 2009,
                "maximum": 2020,
                "step": 1
            }
        ]
    }
```

This step will pick the data from file `insect_sb` if `Spruce Budworm` is selected, or `insect_jpb` if `Jack Pine Budworm` is selected. If the damage type selected is `Light` and the year selected is `2013`, the data that it will take is all the polygons in the file with `RANKING = Light` and `EVENT_YEAR = 2013` 

```json
{
        "stepTitle": "Species Abundance",
        "operationType": "fileSelection",
        "betweenStepOperation": "intersection",
        "options":[
            {
                "description": "Host species: ",
                "type": "Dropdown",
                "file": "",
                "choices": [["Jack Pine", "jack_pine"],
                ["Balsam Fir", "balsam_fir"], 
                ["White Spruce", "white_spruce"], 
                ["Black Spruce", "black_spruce"],
                ["All SBW Host Species", "all_host"]]
            },
            {
                "description": "Host species threshold (>= % basal area): ",
                "type": "Slider",
                "file": "/spec_",
                "minimum": 10,
                "maximum": 100,
                "step": 10
            }
        ]
    }
```

If the user selects `Balsam Fir` host specy with `50` threshold, the file selected will be `balsam_fir/spec_50`. The output of this step will be the intersection between the last step's data and the data from the selected file.

```json
{
    "stepTitle": "Exclude Fires",
    "operationType": "attributeSelection",
    "betweenStepOperation": "difference",
    "options":[
        {
            "description": "Starting year of fires to exclude: ",
            "type": "Slider",
            "file": "fires_flat",
            "attribute": "YEAR",
            "operation": ">=",
            "minimum": 1996,
            "maximum": 2020,
            "step": 1
        },
        {
            "description": "Ending year of fires to exclude: ",
            "type": "Slider",
            "attribute": "YEAR",
            "operation": "<=",
            "minimum": 1996,
            "maximum": 2020,
            "step": 1
        }
    ]
}
```

The file used for this step is `fires_flat`.

If the user selects a starting year `1998` and an ending year `2013`, the data will be all polygons in `fires_flat` with `YEAR >= 1998` and `YEAR <= 2013`.

The output of this step will be the previous step's data where the current step's data removed.

```json
{
    "stepTitle": "Maximum distance to road",
    "operationType": "buffer",
    "betweenStepOperation": "clip",
    "options":[
        {
            "description": "Enter maximum distance to road (m): ",
            "type": "Slider",
            "file": "mroads_simple",
            "minimum": 500,
            "maximum": 3000,
            "step": 50
        }
    ]
}
```

The file used for this step is `mroads_simple`. 

The output of this step will be polygons in the previous step's whose location are also within the buffer around the data in `mroads_simple`.

```json
{
        "stepTitle": "Minimum area of polygon to consider",
        "operationType": "areaComputation",
        "betweenStepOperation": null,
        "options":[
            {
                "description": "Enter minimum area of site (km2): ",
                "type": "Slider",
                "operation": ">=",
                "minimum": 0,
                "maximum": 5,
                "step": 0.1
            }
        ]
    }
```

If the user selects a minimum area of 0.4, the output of this step will be the previous step's polygons with an area greater than 0.4 kilometre squared,

```json
{
        "stepTitle": "Optimize",
        "operationType": "selectSites",
        "betweenStepOperation": null,
        "options":[
            {
                "description": "Number of sites to export (optimized for Euclidean distance): ",
                "type": "Slider",
                "minimum": 2,
                "maximum": 10,
                "step": 1
            }
        ]
    }
```

 If the user selects 7 sites, the output of this step will be 7 polygon from the previous step's data that are the closest to each other (measured with euclidean distance).