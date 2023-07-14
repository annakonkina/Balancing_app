import pandas as pd
import streamlit as st
from PIL import Image
import matplotlib.pyplot as plt
import string
from streamlit_extras.no_default_selectbox import selectbox


# from st_aggrid import AgGrid, GridUpdateMode,  JsCode, DataReturnMode,
# from st_aggrid.grid_options_builder import GridOptionsBuilder

st.set_page_config(page_title = 'Interactive balancing', layout="wide")
st.header('Interactive balancing')
st.markdown('The uploaded file should be a preprocessed answers dataframe, supposedly without bugs')
#uploading
uploaded_file = st.file_uploader('Drag a .csv file here', type=['csv'])
submit = st.button('Submit')

if uploaded_file  and submit:
        st.session_state.uploaded_file = uploaded_file
elif uploaded_file and not submit:
    st.text('You can upload another csv file or if you want to continue, please, press "Submit"')
elif not uploaded_file and not submit and 'uploaded_file' in st.session_state:
    st.text('You can upload another csv file or if you want to continue, please, press "Submit"')
else:
    #  inputs are not filled
    st.text('Please upload csv file and press "Submit"')

# ------------------------------------------------------------------
# by now the csv file is in the memory, we should read it

if 'uploaded_file' in st.session_state:
    #  only if input is in session we continue
    if not submit:
            # case after coming back to page withing the session
        if 'df_filtered' in st.session_state and ('refresh_filters' not in st.session_state 
                                                  or not st.session_state.refresh_filters):
            df = st.session_state.df_filtered
        elif 'df_filtered' in st.session_state and st.session_state.refresh_filters:
            df = pd.read_csv(st.session_state.uploaded_file)
            st.session_state.df  = df
        else:
            if 'df' not in st.session_state:
                df = pd.read_csv(st.session_state.uploaded_file)
                st.session_state.df  = df
            # else:
            #     st.text('smth not expected ... df_filtered should be defined anyway by now')

    elif submit:
        # means second or more input so we need to redefine our inputs and read df again
        st.session_state.uploaded_file = uploaded_file
        df = pd.read_csv(st.session_state.uploaded_file)
        st.session_state.df  = df
    else:
        #  inputs are not filled
        st.text('You can upload another excel file or press "Submit"')


    # ----------------------------------------------------------------------------------
    # by now we have the df in the memory
    # ADDING IMAGE AND DISPLAYING THE DF
    col1, col2 = st.columns(2) 
    image = Image.open('images/still-life-with-scales-justice.jpg')
    col1.image(image,
             caption='Image by Freepik',
             use_column_width=True,
            width = 400
            )
    col2.dataframe(st.session_state.df)

    # -------------------------------------------------------------
    # the table is displayed
    # # Basic input form (col 1)
    # Each time we press the button, 
    # Streamlit reruns app.py from top to bottom, and with every run, count gets initialized to None.
    # Helper function that initializes session_state variables
    def experiment_state(key, default_value=None, set_default=False):
        # Init persist dict
        if "experiments" not in st.session_state:
            st.session_state["experiments"] = dict()
        # Init key
        if key not in st.session_state["experiments"]:
            # Initialize to the saved value in session state if it's available
            if key in st.session_state:
                st.session_state["experiments"][key] = st.session_state[key]
            elif default_value is not None:
                st.session_state["experiments"][key] = default_value
                st.session_state[key] = default_value

        # Generic callback function (curry with lambda & pass)
        def __handle_change(key):
            st.session_state["experiments"][key] = st.session_state[key]

        default = st.session_state["experiments"].get(key)
        return {
            "on_change": lambda: __handle_change(key),
            "key": key,
            # only include default arg if set_default=True as some forms don't support default
            **{"default": default for x in [set_default] if set_default},
        }


    # Usage
    selected_experiments = col1.multiselect("Select experiment", [i for i in st.session_state.df.experiment_name.unique()],
        **experiment_state("selected_experiments", [], set_default=True)
    )

    col1.write(f'Selected experiments: {selected_experiments}')
    
    # --------------------------------------------------------------
    # displaying all the filters possible
    st.session_state.df['answer'] = st.session_state.df['answer'].fillna('-')
    col2.markdown(f'Nb of respondents in the data: {st.session_state.df.uid.nunique()}') 

    # lock the options in the first run
    for q in st.session_state.df.question.unique():
        if not any(' | ' in str(i) for i in st.session_state.df[
            st.session_state.df.question == q
        ].answer.unique()):
            globals()[f'{q}_options'] = st.session_state.df[
                                                st.session_state.df.question == q
                                            ].answer.unique().tolist()
        else:
            options_ = list(itertools.chain.from_iterable([a.split(' | ') 
                                for a in set([i for i in st.session_state.df[
                                                st.session_state.df.question == q
                                            ].answer.unique()])]))
            globals()[f'{q}_options'] = [*set(options_)]

        # adding MULTISELECT for the specific breakout/question:
        with st.container():
            globals()[f'{q}_selection'] = col1.multiselect(f'{q}:',
                                    globals()[f'{q}_options'],
                                    default = globals()[f'{q}_options'],
                                    )
        
    # so far we just created the multiselct objects themselves, which are not connected to the data. 
    # next we need to actually filter out dataframe and connect it to the wordcloud function
        
    # # --- FILTER DATAFRAME BASED ON SELECTION
    # mask = []
    # for col in st.session_state.df_cols:
    #     if not any(' | ' in str(i) for i in st.session_state.df[col].unique()):
    #         mask.append((st.session_state.df[col].isin(globals()[f'{col}_selection'])))
    #     else:
    #         multi_mask = []
    #         for opt in globals()[f'{col}_selection']:
    #             multi_mask.append((st.session_state.df[col].str.contains(opt, regex=False)))
                
    #         mask.append(multi_mask)

    # # ADD df_filtered to the current session state:
    # if 'df_filtered' not in st.session_state:
    #     st.session_state.df_filtered = st.session_state.df.copy() #was df_filtered.copy()
    
    # #here df_filtered is still ok
    # index_filter = st.session_state.df_filtered.index.values.tolist()
    # # st.text(len(index_filter))
    # for cond in mask:
    #     if type(cond) == list:
    #         cond_multi = pd.concat(cond, axis=1)
    #         cond_x = cond_multi.any(axis='columns')
    #         df_filtered_x = st.session_state.df_filtered[cond_x]
    #         index_filter = [i for i in index_filter if i in df_filtered_x.index.values.tolist()]
    #         # st.session_state.df_filtered = df_filtered_x
    #     else:
    #         df_filtered_x = st.session_state.df_filtered[cond]
    #         index_filter = [i for i in index_filter if i in df_filtered_x.index.values.tolist()]
    #         # st.session_state.df_filtered = df_filtered_x
    # index_filter = [*set(index_filter)]
    # # st.text(len(index_filter))

    
    # df_filtered_to_use = st.session_state.df_filtered[st.session_state.df_filtered.index.isin(index_filter)]
    # col2.markdown(f'**Available results:** {len(df_filtered_to_use)}')
    # # st.text(st.session_state.df_filtered.shape)

    # # till now al the filters are working fine. Without reloading the page we can play with them, removing and choosing 
    # # again and they are changing the available results back to the original

    
    # stop_words = set(stopwords.words(st.session_state.language))

    # if len(st.session_state.stopwords_to_add) > 0:
    #     stop_words.update(st.session_state.stopwords_to_add)

    # if len(st.session_state.stopwords_to_remove) > 0:
    #     stop_words = stop_words - st.session_state.stopwords_to_remove

    # st.session_state.stop_words = stop_words

    # # ---- ADD WORDCLOUD
    
    # corpus = df_filtered_to_use.answer.unique().tolist() #was df_filtered, change 07.07.23 16:34
    # corpus = [i.lower() for i in corpus]
    # text = ' '.join(corpus)
    # col2.markdown(f'Total nb of words: {len(text)}')

    # for i in ['-', '  ', '’', "\'"]: # drop extra symbols
    #     if i != '’':
    #         text = text.replace(i, '')
    #     else:
    #         text = text.replace(i, "'")
    # # st.text(text)
    # text = text.translate(str.maketrans('', '', string.punctuation))

    # # LEMMATIZE
    # try:
    #     text = lemmatize_sentence(text)
    # except:
    #     nltk.download('all')
    #     text = lemmatize_sentence(text)


    # # Create and generate a word cloud image:
    # if 'wordcloud' not in st.session_state:    
    #     with st.spinner('Wait for it...'):
    #         wordcloud = calculate_wordcloud(text)
    #     st.session_state.wordcloud = wordcloud
    #     with st.spinner('Wait for it...'):
    #         display_wordcloud(st.session_state.wordcloud)
            
    
    # regenerate_wordcloud = col2.button('Generate wordcloud (or regenerate to refresh)')
    # if regenerate_wordcloud:
    #     with st.spinner('Wait for it...'):
    #         wordcloud = calculate_wordcloud(text)
    #     st.session_state.wordcloud = wordcloud
    #     with st.spinner('Wait for it...'):
    #         display_wordcloud(st.session_state.wordcloud)




