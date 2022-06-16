import streamlit as st
import src.YAML2ST as y2s # Use 'import YAML2ST' if downloaded as a package

URL = "https://mb-app-kub02.na.pg.com:32110/user/klich.mw/dash-yaml-2-streamlit/" # For the link sharing feature, set the 

def main():
    """Demp function of YAML2ST"""

    st.sidebar.title("Data")

    st.session_state.upload = None

    if "link" not in st.session_state:
        st.session_state.link = None
    
    # Import Block
    with st.sidebar.expander("Import", True):

        fileUpload = st.file_uploader('By File Upload', type=['yaml', 'json'], key='file_upload')

        # For link sharing feature
        params = st.experimental_get_query_params() # Returns a dict with value(s) as a list 
        if bool(params.get("YAML2URL")):
            st.success("Shared link found! Imported.")

            st.session_state.upload = y2s.urlDecode(params) # For this run
            st.session_state.link = y2s.urlDecode(params) # For furture run

            st.experimental_set_query_params() # Reset URL params

            if st.button('Clear Shared Link'):
                st.session_state.link = None
                st.experimental_rerun()
        
        # For file upload feature
        elif fileUpload != None:
            st.session_state.upload = fileUpload
            st.session_state.link = None
        
        # If a shared link was active
        elif st.session_state.link:
            st.session_state.upload = st.session_state.link
            if st.button('Clear Shared Link'): 
                st.session_state.link = None
                st.experimental_rerun()

    if st.session_state.upload != None:

        st.title('Output')
        st.markdown('Read From A Pandas DataFrame:')

        stObject = st.sidebar # Create a streamlit object for display in the sidebar

        # Export Block
        with stObject.expander("Export"):
            if st.button('Generate Export Data'):

                # YAML2ST export
                y2s.export(st.session_state.upload, st.session_state.df, st, URL)

        stObject.title("Parameters")

        # YAML2ST build
        st.session_state.df = y2s.build(st.session_state.upload, stObject)

        # Display df 
        st.table(st.session_state.df.astype("str"))


if __name__ == '__main__':
    main()