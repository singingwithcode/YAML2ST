import re
import ast
import io
import os
import urllib
import yaml
import json
import copy
import pandas as pd

from decimal import Decimal
from dateutil import parser
from datetime import datetime

try: 
    from streamlit.uploaded_file_manager import UploadedFile, UploadedFileRec # type: ignore
except:
    from streamlit.runtime.uploaded_file_manager import UploadedFile, UploadedFileRec


PERSISTDECIMAL = True # e.g. if YAML value 0.01 and user wants the value to be 0.001. Keep True for now. 


class YAML2ST:


    # Integer check
    ## Should be called prior to __representsDecimal
    def __representsInt(s):
        try:
            float(s)
        except ValueError:
            return False
        else:
            return float(s).is_integer() and ('.' not in str(s))


    # List check
    def __representsList(s):
        try: 
            if s.startswith('['):
                ast.literal_eval(s)
                return True
            else:
                return False
        except ValueError:
            return False


    # Decimal check 
    def __representsDecimal(s):
        try: 
            float(s)
            return True
        except ValueError:
            return False


    # Datetime check
    def __representsDatetime(s):
        try: 
            parser.isoparse(str(s))
            return True
        except ValueError:
            return False


    # Hex check
    def __representsHex(s):
        if not s.startswith('#'):
            return False
        valid = re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', s)
        if valid is None:
            return False
        else:
            return True


    # Calculate the streamlit widget Step by the lowest decimal position
    def __calcPrecision(s):
        d = Decimal(s)
        decFormat = "%.{}f".format(abs(d.as_tuple().exponent))
        decStep = float("1e-{}".format(abs(d.as_tuple().exponent)))
        return decFormat, decStep


    # Safely gets the last crumbs via index
    def checkCrumbs(lastBreadcrumbs, index):
        try: 
            lastcrumb = lastBreadcrumbs[index]
            return lastcrumb
        except:
            return ""


    # Recursively checks and returns any line comments
    def lineCheck(line_to_comment, line, newFile):
        if ('~'+str(line)) in line_to_comment:
            newFile.write(' ' + line_to_comment.get('~'+str(line)))
        if str(line) in line_to_comment:
            newFile.write(('' if line == 0 else '\n') + line_to_comment.get(str(line)))
            line = YAML2ST.lineCheck(line_to_comment, line + 1, newFile)
        return line


    # Preps the comments to be used for export
    def prepComments(upload):
        line_to_comment = {}
        if upload: 
            for index, line in enumerate(upload):
                line2 = str(line.decode('utf-8')).strip() # strip() removes the /n

                # Store the lines
                if line2.lstrip(' ').startswith("#") or line2.lstrip(' ').startswith("---"): # Regular comment or beginning of YAML
                    line_to_comment[str(index)] = line2
                elif line2.find('#') != -1: # locates the comment and stores the comment
                    sindex = line2.find('#')
                    if not YAML2ST.__representsHex(line2[sindex:0]):
                        line_to_comment['~' + str(index+1)] = line2[sindex:len(line2)]
        
        return line_to_comment


    # Recursively parses each YAML line ('/n') seperating any YAML comments 
    def __forceConfig(dataString):
        forceVal = "" 
        lIndex = dataString.find("\n")
        if lIndex == -1:
            lIndex = len(dataString)
        data_string_line = dataString[:lIndex]
        dataString = dataString[lIndex+1:]
        if data_string_line.lstrip(' ').startswith("#") or data_string_line.lstrip(' ').startswith("---"):
            return YAML2ST.__forceConfig(dataString)
        elif data_string_line.find('#FORCE:') != -1:
            sIndex = data_string_line.find('#FORCE:')
            forceVal = data_string_line[int(sIndex+7):]
        return dataString, forceVal


    # Builds a file from the data 
    def recursiveExport(df, lastBreadcrumbs, newFile, line_to_comment, line):
        if not df.empty:
            row = df.iloc[0]
            breadcrumbs = str(row['breadcrumb']).split(" > ")[:-1]
            for index, crumb in enumerate(breadcrumbs):
                if YAML2ST.checkCrumbs(lastBreadcrumbs, index) != crumb:
                    newFile.write(('' if line == 0 else '\n') + ('  ' * index) + crumb + ':')
                    line = YAML2ST.lineCheck(line_to_comment, line + 1, newFile)
            
            st_value = str(row['st_value'])
            if (YAML2ST.__representsInt(st_value) or YAML2ST.__representsList(st_value) or YAML2ST.__representsDecimal(st_value) or 
                YAML2ST.__representsDatetime(st_value) or st_value == 'True' or st_value == 'False' or st_value == 'true' or st_value == 'false'):
                newFile.write(('' if line == 0 else '\n') + ('  ' * len(breadcrumbs)) + str(row['key']) + ': ' + st_value)
                line = YAML2ST.lineCheck(line_to_comment, line + 1, newFile)
            else:
                newFile.write(('' if line == 0 else '\n') + ('  ' * len(breadcrumbs)) + str(row['key']) + ': \"' + st_value + '\"')
                line = YAML2ST.lineCheck(line_to_comment, line + 1, newFile)

            YAML2ST.recursiveExport(df[1:], breadcrumbs, newFile, line_to_comment, line)


    # Strips the spaces in a line except if within ""
    def __stripSpace(text):
        lst = text.split('"')
        for i, item in enumerate(lst):
            if not i % 2:
                lst[i] = re.sub("\s+", "", item)
        return '"'.join(lst)

    
    # Input a YAML via Streamlit's UploadedFile and this outputs string for sharing
    def urlEncode(upload): 
        stringio = upload.getvalue()
        params = urllib.parse.quote_plus(stringio)
        return str(params)


    # Dev helper to convert a streamlit uploaded file to a dataString
    # Use a deep copy of the uploaded file to avoid issues
    def uploadToDataString(upload):
        stringio = io.StringIO(upload.getvalue().decode("utf-8"))
        return stringio.read()


    # The defualt configuration of the CSS style for 4 levels of headers
    # Can override to use your own configHeaderFormat() via "class child(YAML2ST): def configHeaderFormat(stObject)"
    def configHeaderFormat(stObject):
        stObject.markdown("""
        <style>
        .h1 {
            font-size:18px;
            text-decoration: underline;
            font-weight: 600;
        }
        .h1::after {
            content: "*";
        }
        .h2 {
            font-size:16px;
            text-decoration: underline;
            font-weight: 600;
        }
        .h2::after {
            content: "**";
        }
        .h3 {
            font-size:14px;
            text-decoration: underline;
            font-weight: 600;
        }
        .h3::after {
            content: "***";
        }
        .h4 {
            font-size:12px;
            text-decoration: underline;
            font-weight: 600;
        }
        .h4::after {
            content: "****";
        }
        </style>
        """, unsafe_allow_html=True)


    # Helper
    # The logic for parameter formation and then its creation 
    def __paramLogic(literalParam, key, value, breadcrumb, df, stObject):
        
        label=""
        if 'label' in literalParam: 
            label = literalParam["label"]
            del literalParam["label"]
        else:
            label = key
        
        index = 0

        if 'options' in literalParam: 
            __paramOptions = ast.literal_eval(literalParam["options"])
            if YAML2ST.__representsList(str(value)):
                try: 
                    index = __paramOptions.index(next(__element for __element in ast.literal_eval(str(value)) if __element in __paramOptions))
                except: 
                    pass
            elif str(value) in __paramOptions:
                index = __paramOptions.index(str(__paramOptions[__paramOptions.index(str(value))]))
            value = __paramOptions
            del literalParam["options"]
        elif 'value' in literalParam: 
            value = literalParam["value"]
            del literalParam["value"]

        if 'index' in literalParam:
            index = int(literalParam["index"])
            del literalParam["index"]

        if 'key' in literalParam: 
            breadcrumb = literalParam["key"]
            del literalParam["key"]
        
        # For number values, we need to ensure we provide the correct number's type to the input widget
        decFormat = ""
        if literalParam['w'] == 'number_input' and YAML2ST.__representsInt(value):
            if 'type' not in literalParam:
                literalParam['type'] = "int"
        elif literalParam['w'] == 'number_input' and YAML2ST.__representsDecimal(value):
            decFormat, decStep = YAML2ST.__calcPrecision(str(value))
            if 'format' not in literalParam and PERSISTDECIMAL:
                literalParam['format'] = "'"+str(decFormat)+"'"
            if 'step' not in literalParam:
                literalParam['step'] = decStep
            if 'type' not in literalParam:
                literalParam['type'] = "float"
        
        # YAML2ST param: Persist the type [int, string, float, etc.] of the data
        ## Based on the statement that "All numerical arguments must be of the same type" in streamlit
        if "type" in literalParam:

            dataType = literalParam["type"]
            del literalParam["type"]

            for param in literalParam:
                try: 
                    literalParam[param] = eval(str(dataType+'(\"'+str(literalParam[param])+'\")'))
                except:
                    pass
        
        # For all params but w, form a code command statement
        wParameters = "" 
        for ___k, ___v in literalParam.items():
            if ___k != 'w':
                wParameters = wParameters + str(___k) + "=" + str(___v) + ", "
        
        # Code command statement build 
        if literalParam['w'] == 'datetime_input': # A custom input widget. Doesn't use literals
            date = value
            col1, col2 = stObject.columns(2)
            value = datetime.combine(col1.date_input(key + ' > date', value=date, key=(breadcrumb + ' > date')), col2.time_input(key + ' > time', value=date, key=(breadcrumb + ' > time')))
        elif literalParam['w'] == 'selectbox' or literalParam['w'] == 'radio':
            __literalCommand = str('stObject.' + literalParam['w'] + '(label=label, options=value, ' + wParameters + 'index=index, key=breadcrumb)')
        elif literalParam['w'] == 'select_slider' or literalParam['w'] == 'multiselect': #has no index param but has options param
            __literalCommand = str('stObject.' + literalParam['w'] + '(label=label, options=value, ' + wParameters + 'key=breadcrumb)')
        elif literalParam['w'] == 'checkbox':
            __literalCommand = str('stObject.' + literalParam['w'] + '(label=label, value=eval(value), ' + wParameters + 'key=breadcrumb)')
        else:
            __literalCommand = str('stObject.' + literalParam['w'] + '(label=label, value=value, ' + wParameters + 'key=breadcrumb)')
        
        # Launch and storage
        if literalParam['w'] != 'datetime_input': 
            try:
                print ("Y2S EXECUTING COMMAND: " + __literalCommand + "\n   WHERE: " + "label=" + str(label) + " value=" + str(value) + " key=" + str(breadcrumb) + " index=" + str(index))
                df.loc[len(df)+1] = key, eval(__literalCommand), breadcrumb
            except: 
                stObject.error("YAML2ST: Couldn't execute the literal command: \n\n" + __literalCommand + "\n\n Check your YAML and the Streamlit API for errors.")

            # Will enforce the decimal format in the df since floats
            if decFormat:
                df.loc[len(df)] = key, decFormat % (df.iloc[len(df)-1, 1]), breadcrumb

        else:
            
            df.loc[len(df)+1] = key, value, breadcrumb
    

    # Recursively, manually, and/or dynamically builds a YAML or JSON file's params to streamlit input widgets.
    ## dict: a dictionary of the data, less comments
    ## df: a pandas dataframe for where the streamlit input wiget value updates are sent
    ## breadcrumbs: used to track the hierarchy. Typically start with a blank []
    ## stObject: a streamlit object on where to write the input widgets to
    ## data_string: a string of all the data in the YAML file for #FORCE. To ignore, use ""
    def recursiveBuild(dataDict, df, breadcrumbs, stObject, dataString):

        for key, value in dataDict.items():
            
            # Get the force values to see if the nearby lines have any '#FORCE's
            dataString, forceVal = YAML2ST.__forceConfig(dataString) 

            # Check to see if is a dictionary within this dataDict
            if str(value)[0] == '{':
                breadcrumbs.append(key)

                if forceVal.find('hide') == -1:
                    
                    # Deduce the proper header style for output
                    if len(breadcrumbs)<2 :
                        stObject.markdown('<p class="h1">' + key + '</p>', unsafe_allow_html=True)
                    elif len(breadcrumbs)==2:
                        stObject.markdown('<p class="h2">' + key + '</p>', unsafe_allow_html=True)
                    elif len(breadcrumbs)==3:
                        stObject.markdown('<p class="h3">' + key + '</p>', unsafe_allow_html=True)
                    else:
                        stObject.markdown('<p class="h4">' + key + '</p>', unsafe_allow_html=True)
                
                # Repeat process within next dict
                dataString = YAML2ST.recursiveBuild(value, df, breadcrumbs, stObject, dataString)[1]
                breadcrumbs.pop(len(breadcrumbs)-1)

            else:  # Is a key value pair (if correct YAML)
                
                # Breadcrumb tracking
                if len(breadcrumbs) == 0: breadcrumb = "".join(("".join(breadcrumbs),key))
                else: breadcrumb = " > ".join((" > ".join(breadcrumbs),key))
                
                # Pre-Process params: Split the params into key value pairs so we can parse the keys 
                literalParam = {}
                if forceVal != "":
                    force_arr = YAML2ST.__stripSpace(forceVal).split("|")
                    for fitem in force_arr:
                        if fitem != "":
                            fkey, fvalue = fitem.split("=")
                            literalParam[fkey] = fvalue

                # YAML2ST param: If we are hiding the param
                if 'hide' in literalParam:
                    df.loc[len(df)+1] = key, value, breadcrumb

                # YAML2ST param: If an input widget w is specified via #FORCE: 
                elif 'w' in literalParam: 
                    YAML2ST.__paramLogic(literalParam, key, value, breadcrumb, df, stObject)
                    
                # Dynamics: Deduce streamlit input widget by its value. Chronological integrity is necessary.  
                else: 

                    value = str(value) # Housekeeping
                    
                    # Boolean
                    if value == 'True' or value == 'true':
                        literalParam['w'] = 'checkbox'
                        #literalParam['type'] = "bool"
                    elif value == 'False' or value == 'false':
                        literalParam['w'] = 'checkbox'
                        #literalParam['type'] = "bool"

                    # Integer
                    elif YAML2ST.__representsInt(value):
                        literalParam['w'] = 'number_input'
                        literalParam['type'] = "int"
                        literalParam['value'] = int(value)
                        
                    # Decimal
                    elif YAML2ST.__representsDecimal(value):
                        decFormat, decStep = YAML2ST.__calcPrecision(value)
                        literalParam['w'] = 'number_input'
                        literalParam['type'] = "float"
                        literalParam['value'] = float(value)
                        if "format" not in literalParam:
                            literalParam['format'] = '"' + str(decFormat) + '"'
                        if "step" not in literalParam:
                            literalParam['step'] = decStep

                    # Datetime
                    elif YAML2ST.__representsDatetime(value):
                        date = parser.isoparse(value)
                        if date.strftime("%H:%M:%S") == '00:00:00': # Date only
                            literalParam['w'] = 'date_input'
                            literalParam['value'] = date
                        else: 
                            literalParam['w'] = 'datetime_input' # A custom input widget for date and time together
                            literalParam['value'] = date
                    
                    # Hex
                    elif YAML2ST.__representsHex(value):
                        literalParam['w'] = 'color_picker' 

                    # Text with new lines
                    elif ('\n' in value):
                        literalParam['w'] = 'text_area' 

                    # Text with commas 
                    elif YAML2ST.__representsList(value):
                        literalParam['w'] = 'multiselect' 
                        literalParam['options'] = value
                        literalParam['default'] = value
                    
                    # Text 
                    else: 
                        literalParam['w'] = 'text_input' 
                        literalParam['value'] = value

                    YAML2ST.__paramLogic(literalParam, key, value, breadcrumb, df, stObject)

        return df, dataString


##  ##   ## ##     ## ##   
##  ##   ##  ##   ##   ##  
##  ##       ##   ####     
 ## ##      ##     #####   
  ##       ##         ###  
  ##      #   ##  ##   ##  
  ##     ######    ## ##   
                        

# Input URL params via dict and this outputs a formatted YAML file; namely, Streamlit's UploadedFile
def urlDecode(urlParamDict):
    uploadedFileRec = UploadedFileRec(int(999), str("config.yaml"), str("application/x-yaml"), bytes(urlParamDict.get("YAML2URL")[0],'ascii'))
    return UploadedFile(uploadedFileRec)


# YAML file to Streamlit's UploadedFile
def YAML2UploadedFile(filePath):
    uploadedFileRec = UploadedFileRec(int(999), str("config.yaml"), str("application/x-yaml"), open(filePath, "rb").read())
    return UploadedFile(uploadedFileRec)


# A raw export method that returns an unclosed file, the fileName, and a string URL to be shared. 
## upload: the origional uploadedFile used to create df
## df: the changed values of the uploaded file
## URL: the domain to append a parameter to e.g. https://pg.com/
## exportFilePath: the path to export the data inclusive of the file name e.g. /users/user/config.yaml. 
def exportRaw(upload, df, URL, exportFilePath):

    upload = copy.deepcopy(upload)

    # Get the file details
    file_details = {"Filename":upload.name,"FileType":upload.type,"FileSize":upload.size}
    fname = file_details['Filename'].split(".", 1)[0] + ".yaml"

    newFile = open(exportFilePath, "w")
    line_to_comment = YAML2ST.prepComments(upload)
    YAML2ST.recursiveExport(df, [""], newFile, line_to_comment, YAML2ST.lineCheck(line_to_comment, 0, newFile))
    newFile.close()

    return str(URL + "?YAML2URL=" + YAML2ST.urlEncode(YAML2UploadedFile(exportFilePath)))


# Is a pre-formatted export method that posts a Button Input Widget and Code Input Widget for
# file download and link sharing. 
def export(upload, df, stObject, URL):

    upload = copy.deepcopy(upload)

    # Get the file details
    file_details = {"Filename":upload.name,"FileType":upload.type,"FileSize":upload.size}

    # Create a downloaded file with the contents
    fname = file_details['Filename'].split(".", 1)[0] + "_new.yaml"
    newFile = open(fname, "w")
    line_to_comment = YAML2ST.prepComments(upload)
    YAML2ST.recursiveExport(df, [""], newFile, line_to_comment, YAML2ST.lineCheck(line_to_comment, 0, newFile))
    newFile.close()

    # Display the button for download
    stObject.subheader("Export YAML File")
    with open(fname, "r") as f:
        stObject.download_button('Download', f, file_name=fname)

    stObject.subheader("Share With Link")
    stObject.code(URL + "?YAML2URL=" + YAML2ST.urlEncode(YAML2UploadedFile(fname)))

    os.remove(fname)


# Uses an upload file and builds the input parameters to the steamlit object 
def build(upload, stObject):

    # Configure appearance
    YAML2ST.configHeaderFormat(stObject)

    # Generate string of file for possible comments
    data_string = YAML2ST.uploadToDataString(copy.deepcopy(upload))

    # Generate dataDict of file 
    try: # YAML
        dataDict = dict(yaml.load(copy.deepcopy(upload), yaml.SafeLoader))
    except: # Maybe it's JSON
        try:
            dataDict = dict(json.load(copy.deepcopy(upload)))
        except:
            stObject.error("Read Error: Not a valid YAML or JSON file.")
            return pd.DataFrame()

    if bool(dataDict):

        # Build parameters to streamlit
        return YAML2ST.recursiveBuild(dataDict, pd.DataFrame(columns=['key','st_value','breadcrumb']), [], stObject, data_string)[0]                

    else: 
        stObject.error("Build Error: Could be due to bad share link and/or wrong YAML formatting. Remove share link if present.")