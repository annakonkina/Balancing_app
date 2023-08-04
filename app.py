import pandas as pd
import numpy as np
import streamlit as st
from PIL import Image
import matplotlib.pyplot as plt
from streamlit_extras.no_default_selectbox import selectbox
from itertools import chain
from basic_functions import make_flat
from calc_tables import demographics


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

    if 'exp_drop_dict' not in st.session_state:
        st.session_state.exp_drop_dict = {}

    if 'exclude_list' not in st.session_state:
        st.session_state.exclude_list = []

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
    selected_experiments = col1.multiselect("Select ONLY ONE experiment from which you would like to drop people", 
                                            [i for i in st.session_state.df.experiment_name.unique()],
        **experiment_state("selected_experiments", [], set_default=True)
    )

    col1.markdown(f'**Selected experiment**: {selected_experiments}')
    
    # # --------------------------------------------------------------
    # # displaying all the filters possible
    # lock the options in the first run
    for q in st.session_state.df.question.unique():
        if not any(' | ' in str(i) for i in st.session_state.df[
            st.session_state.df.question == q
        ].answer.unique()):
            globals()[f'{q}_options'] = st.session_state.df[
                                                st.session_state.df.question == q
                                            ].answer.unique().tolist()
        else:
            options_ = list(chain.from_iterable([a.split(' | ') 
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
    # next we need to actually filter out dataframe
    # --- FILTER DATAFRAME BASED ON SELECTION

    mask = []
    for q in st.session_state.df.question.unique():
        ### st.markdown(globals()[f'{q}_selection']) #is list of all options for the specific question selected
        mask.append((st.session_state.df.question == q)
                                            & (st.session_state.df.answer.isin(globals()[f'{q}_selection'])))

    # ADD df_filtered to the current session state:
    if 'df_filtered' not in st.session_state:
        st.session_state.df_filtered = st.session_state.df.copy()

    #here df_filtered is still ok
    uids_filter = st.session_state.df_filtered.uid.unique().tolist()

    for cond in mask:
        cond_uids = st.session_state.df_filtered[cond].uid.unique().tolist()
        uids_filter = [i for i in uids_filter if i in cond_uids]

    uids_filter = [*set(uids_filter)]

    if len(st.session_state.exclude_list) > 0:
        uids_filter = [i for i in uids_filter if i not in st.session_state.exclude_list]

    df_filtered_to_drop = st.session_state.df_filtered[st.session_state.df_filtered.uid.isin(uids_filter)]
    # finally leaving only people belonging to the selected experiment
    df_filtered_to_drop = df_filtered_to_drop[
        df_filtered_to_drop.experiment_name.isin(selected_experiments)]
    uids_filter = df_filtered_to_drop.uid.unique().tolist()

    col2.markdown(f'**Available uids to drop:** {df_filtered_to_drop.uid.nunique()}')

     # SELECTION OF NUMBER OF PEOPLE TO BE DROPPED
    droppers_number = col2.number_input('Insert a number of people you would like to exclude')
    col2.text(f'The current number is {droppers_number}')

    col2.markdown('If you are fine with the uids number to drop in the selected experiment, press "Submit" \
    and select another experiment above')
    submit_exp_drop = col2.button('Submit uids')
    if submit_exp_drop:
        np.random.seed(1234)
        st.session_state.exp_drop_dict[selected_experiments[0]] = list(
            np.random.choice(uids_filter,
            int(droppers_number), 
            replace=False))
        submit_exp_drop = False

    col2.markdown('**NB OF PEOPLE SELECTED TO DROP**:')
    for k in st.session_state.exp_drop_dict.keys():
        col2.markdown(f"{k} >> **{len(set(st.session_state.exp_drop_dict[k]))}**")

    col2.markdown('If you are ready to confirm this selection, please, press "CONFIRM" to see the balanced tables. \
                  Note, that the round will start over once u press submit and the selected ids will be stored in the background')
    confirm_round = col2.button('CONFIRM')
    if confirm_round:
        st.session_state.exclude_list += [*set(make_flat(st.session_state.exp_drop_dict.values()))]
        confirm_round = False
        col2.markdown(f"**Total nb of dropped uids from this round:** {len(set(make_flat(st.session_state.exp_drop_dict.values())))}")
        col2.markdown(f"**TOTAL nb of dropped uids:** {len(set(st.session_state.exclude_list))}")
        st.session_state.exp_drop_dict = {}

    col2.markdown('If you want to start from the beginning, press "REFRESH". \
                  The filters above will be refreshed once you select an experiment to work with.')
    clean_exclude_list = col2.button('REFRESH')
    if clean_exclude_list:
        st.session_state.exclude_list = []
        st.session_state.exp_drop_dict = {}
        clean_exclude_list = False

    col2.markdown(f'That is how the balanced dataset looks?')

    # generate_demo = col2.button('GENERATE/refresh TABLES')
    # if generate_demo:

    if 'breakouts' not in st.session_state:
        breakouts = []
        for q in st.session_state.df.question.unique():
            d_ = {
                'title': q.split('.')[0].upper(), 
                'to_be_sorted':False,
                'question': [q], 
                'answers': None,
                'position': "Screener",
                }
            breakouts.append(d_)

        available_options = [[0]*len(breakouts)]

        for breakout in breakouts:
            breakout_index = breakouts.index(breakout)
            # Fill answers
            if breakouts[breakout_index ]['answers'] is None:
                answers = list(st.session_state.df[(st.session_state.df['question'].isin(breakout['question'])) & \
                                    (st.session_state.df['position']==breakout['position'])]['answer'].unique())
                answers = [[part.strip() for part in str(answer).split("|")] for answer in answers]
                answers = list(set(chain.from_iterable(answers)))
                answers.sort()

                tmp_answers = []
                for answer in answers:
                    tmp_answers.append({'title': answer, 'include': [answer], 'exclude': [], 'uids':None})
                if len(tmp_answers) > 1:
                    tmp_answers.insert(0, {'title': "Any answer", 'include': answers, 'exclude': [], 'uids':None})
                breakouts[breakout_index]['answers'] = tmp_answers
            
            if len(breakouts[breakout_index]['answers']) > 1:
                option_index = 1
                for option in breakouts[ breakout_index ]['answers'][1:]:
                    base_combination = [0]*len(breakouts)
                    base_combination[breakout_index]= option_index

                    available_options.append(base_combination)
                    option_index += 1

            st.session_state.breakouts = breakouts

    nb_users_ = st.session_state.df[
        ~st.session_state.df.uid.isin(st.session_state.exclude_list)].uid.nunique()
    col2.markdown(f'There are {nb_users_} user ids.')
    col2.markdown(f'{len(st.session_state.exclude_list)}')
    
    @st.cache(suppress_st_warning=False)
    def build_demo():
        return demographics(df_answers = st.session_state.df[
            ~st.session_state.df.uid.isin(st.session_state.exclude_list)], 
            breakouts = st.session_state.breakouts
            )   
    
    tables = build_demo()
    for n, t in tables.items():
        col2.markdown(n)
        col2.table(t)

       
   



