# YAML 2 STREAMLIT
## Description
YAML2ST automates streamlit input widgets from an uploaded YAML or JSON file. All key value pairs will be displayed as streamlit input widgets. You can then export the data changes via YAML or share a URL that contains the YAML file.

# Use: As A Package
## To Install
In a python environment:

`pip install YAML2ST`

## To Import
In a python file:

`import streamlit as st`<br>
`import YAML2ST as y2s`

## To Display YAML/JSON as Input Widgets
Use an UploadedFile type, e.g. a file from `st.file_uploader()`, and the Streamlit instance in the location you would like the input widgets displayed, e.g. `st.sidebar`, with the YAML2ST `build()` method:

`df = y2s.build(uploadedFile, st.sidebar)`<br>
build() will return a pandas DataFrame in which you can capture and display all input widget changes. 

## To Export Data: Easy
To export with ease, use: the original  UploadedFile, the changes made in the DataFrame, an instance of Streamlit for where you want the export features drawn, and the domain of the URL that we can add a parameter to.

`y2s.export(uploadedFile, df, st.sidebar, "http://localhost:9097/")`<br>
export() will draw 2 widgets at the Streamlit instance, a download button and a code box with the share link. 

## To Export Data: Raw
If you do not want these widgets drawn on Streamlit, you can use exportRaw() to capture the data:

`file, file_name, sharelink = exportRaw(uploadedFile, df, URL)`

# Use: Demo File (GitHub)
The demo file dubbed main().py is on GitHub.
## To Run
`streamlit run app/main.py --server.port 9097`  
Upload a YAML file.

# YAML & Dynamics
## YAML2ST Dynamics
The Streamlit input widgets are dynamically manifested using the following conditional order. 
| Widget | Value Input | 
| ------ | ------ |
| `checkbox` | Any value that is 'True' or 'False' |
| `number_input` (integer) | Any value that can be cast to an int. Step defaults to +1/-1.
| `number_input` (decimal) | Any value that can be cast to a float. Step defaults to the smallest digit in the value. |
| `date_input` | Any value that is ISO-8601 standard. E.g.: `"2010-02-11"`|
| `datetime_input` | A YAML2ST custom  widget to support date and time. E.g.: `"2015-06-17 14:03:40"` |
| `color_picker` | Any value that matches hexadecimal with #. E.g.: `"#0EE2D7"` |
| `text_area` | Any value that contains a new line `\n` |
| `multiselect` | Any value that is a list e.g. starts with `[` |
| `text_input` | All other data |
## Example YAML
### Example 1:
`int: 1`<br>
YAML2ST will decide that the best way to display this will be with a Streamlit "number_input" and will draw a number_input with a title of "int" and a value of 1 on the Streamit instance provided. 
### Example 2:
`string: "Dynamic"`<br>
YAML2ST will decide that the best way to display this will be with a Streamlit "text_input" and will draw a text_input with a title of "string" and a value of "Dynamic" on the Streamit instance provided. 

# YAML & YAML2ST #FORCE
Should you wish to display the value of the parameter with a specific input widget, we have made that easy with the use of ` #FORCE: ` next to the YAML parameter in the YAML file. You may also separate each #FORCE: option with ` | ` (including the space before and after the pipe). This capability extends to all of the Streamlit input widget options as your options are taken literally if not recognized by YAML2ST.
## Application Level Options 
| Option | Action | 
| ------ | ------ |
| `hide=True` | Will ignore the YAML parameter. |
| `type=int` | Will force the data type. |
## Example YAML
### Example 1:
`int: 1 #FORCE: w=number_input | min_value=0 | max_value=10`<br>
The YAML parameter "int: 1" will be read by YAML2ST as a Streamlit number_input. However, it is best practice to declare the "number_input" Streamlit input widget if there will be literal input widget options such as "min_value" and "max_value".
### Example 2:
`list1: [ "one", "two", "three", "four" ] #FORCE: w=selectbox | index=2`
### Example 3:
`block_shape5: [ "five", "three", "four"] #FORCE: w=selectbox | options=[ "six", "one", "two"] | index=2`
### Example 4:
`hidden_param: "zero" #FORCE: hide=True`


# YAML Requirements
1. The YAML key hierarchy must be unique.  
`colors:`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`color: Red`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`color: Green`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`color: Blue` # this will override the breadcrumb "colors->color" so only "color: Blue" will exist
2. No blank lines (comments are fine).
3. For now, it only supports single line data.

# Feature: Share With Link Feature
You may share a YAML file as a URL. During export() a special URL will be encoded. The domain of the URL, in the code, may need to be updated. YAML2URL uses a single URL parameter dubbed 'YAML2URL' to share all contents of a YAML, including comments and the Y2S #FORCE feature. 