import streamlit as st
import pandas as pd
import datetime
import os

# ============================================================
# STREAMLIT BASICS
# ============================================================
# Streamlit reruns this entire file from top to bottom every
# time you interact with anything (click a button, fill a form).
# That's how it stays up to date — no loop needed.
#
# 'st.something()' is how you put things on the page:
#   st.title()       -> big heading
#   st.write()       -> text or data
#   st.text_input()  -> a text box
#   st.button()      -> a clickable button
#   st.bar_chart()   -> a chart
# ============================================================


# ============================================================
# SECTION 1: PAGE SETUP
# ============================================================
# st.set_page_config() must always be the very first Streamlit
# call in your file. It sets the browser tab title and layout.
# layout='wide' makes it use the full screen width — better on
# phones and larger monitors.

st.set_page_config(page_title='IBS Tracker', layout='wide')

st.title('IBS Symptom Tracker')
st.write('Track your food, symptoms, and triggers in one place.')


# ============================================================
# SECTION 2: DATA HELPERS
# ============================================================
# Instead of opening a .txt file manually every time, we use
# two helper functions. A 'function' is a reusable block of
# code you can call by name whenever you need it.
#
# 'def' means "define a new function".
# Everything indented underneath it is part of that function.
# ============================================================

# The name of our data file. Using a variable here means if
# you ever want to rename it, you only change it in one place.
DATA_FILE = 'symptoms.csv'

def load_data():
    """Load all entries from the CSV file into a pandas DataFrame.

    A DataFrame is like a spreadsheet in memory — rows and columns.
    'df' is the standard short name programmers use for DataFrames.
    """
    # If the file doesn't exist yet, return an empty DataFrame
    # with the correct column names already set up.
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(columns=['date', 'food', 'symptoms', 'severity'])

    # pd.read_csv() reads a CSV file into a DataFrame automatically.
    return pd.read_csv(DATA_FILE)


def save_entry(date, food, symptoms, severity):
    """Add a new entry to the CSV file.

    We load the existing data, add a new row, then save it back.
    'pd.concat' joins two DataFrames together (like stacking rows).
    """
    df = load_data()

    # Build the new row as a small one-row DataFrame.
    # 'index=[0]' is required by pandas when creating a single-row DataFrame.
    new_row = pd.DataFrame([{
        'date': date,
        'food': food,
        'symptoms': symptoms,
        'severity': severity
    }])

    # Stack the new row onto the existing data.
    # ignore_index=True renumbers the rows cleanly (0, 1, 2, 3...).
    df = pd.concat([df, new_row], ignore_index=True)

    # Save back to the CSV file. index=False means don't write
    # the row numbers (0, 1, 2...) into the file itself.
    df.to_csv(DATA_FILE, index=False)


# ============================================================
# SECTION 3: SIDEBAR NAVIGATION
# ============================================================
# st.sidebar puts content in a slide-out panel on the left.
# On mobile, it collapses into a hamburger menu automatically.
# st.sidebar.radio() creates a list of options to choose from —
# this replaces your old numbered menu.
# ============================================================

st.sidebar.title('Menu')
page = st.sidebar.radio(
    'Go to',
    ['Add Entry', 'View Entries', 'Analyze Data', 'Trigger Detection']
)


# ============================================================
# SECTION 4: ADD ENTRY PAGE
# ============================================================
# 'if page ==' checks which menu option the user selected.
# Only the matching block runs — the others are skipped.
# This replaces your old 'if choice == 1' menu logic.
# ============================================================

if page == 'Add Entry':
    st.header('Add a new entry')

    # st.text_input() creates a text box and returns whatever
    # the user typed as a string. We store it in a variable.
    food = st.text_input('What did you eat?')
    symptoms = st.text_input('What symptoms did you have?')

    # st.slider() creates a draggable slider — much easier on
    # a phone than typing a number. Returns the chosen value.
    severity = st.slider('Severity', min_value=1, max_value=10, value=5)

    # Show a live severity label so it feels responsive.
    # We use a simple if/elif chain to pick a label.
    if severity <= 3:
        st.write(f'Severity {severity} — mild')
    elif severity <= 6:
        st.write(f'Severity {severity} — moderate')
    else:
        st.write(f'Severity {severity} — severe')

    # st.button() shows a button. The code inside 'if st.button()'
    # only runs when the user actually clicks it.
    if st.button('Save Entry'):

        # Basic validation — make sure the user filled in both fields.
        if not food or not symptoms:
            # st.warning() shows a yellow warning message.
            st.warning('Please fill in both fields before saving.')
        else:
            save_entry(
                date=datetime.date.today(),
                food=food,
                symptoms=symptoms,
                severity=severity
            )
            # st.success() shows a green success message.
            st.success('Entry saved!')


# ============================================================
# SECTION 5: VIEW ENTRIES PAGE
# ============================================================

elif page == 'View Entries':
    st.header('Your symptom history')

    df = load_data()

    # len(df) counts the number of rows in the DataFrame.
    if len(df) == 0:
        st.info('No entries yet. Add your first entry from the menu.')
    else:
        # st.dataframe() renders the DataFrame as an interactive
        # table — sortable columns, scrollable, works great on mobile.
        # use_container_width=True makes it fill the screen width.
        st.dataframe(df, use_container_width=True, hide_index=True)

        # --- Search by food ---
        # This is the "search by food" feature from your roadmap,
        # included here for free since we're already showing the table.
        st.subheader('Search by food')
        search = st.text_input('Type a food to filter (e.g. pizza)')

        if search:
            # .str.contains() checks if the food column contains
            # the search term. case=False means it ignores upper/lowercase.
            # na=False means ignore any blank cells instead of crashing.
            filtered = df[df['food'].str.contains(search, case=False, na=False)]

            if len(filtered) == 0:
                st.write(f'No entries found for "{search}".')
            else:
                st.write(f'{len(filtered)} entries found for "{search}":')
                st.dataframe(filtered, use_container_width=True, hide_index=True)

        # --- CSV Export ---
        # st.download_button() creates a button that downloads a file.
        # df.to_csv(index=False) converts the DataFrame back to CSV text.
        # .encode() converts that text to bytes, which the download needs.
        st.subheader('Export your data')
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label='Download as CSV',
            data=csv_data,
            file_name='my_ibs_data.csv',
            mime='text/csv'
        )


# ============================================================
# SECTION 6: ANALYZE DATA PAGE
# ============================================================

elif page == 'Analyze Data':
    st.header('Data analysis')

    df = load_data()

    if len(df) == 0:
        st.info('No entries yet. Add your first entry from the menu.')
    else:
        # Make sure severity is treated as a number, not text.
        # 'errors=coerce' turns any non-number into NaN (empty).
        df['severity'] = pd.to_numeric(df['severity'], errors='coerce')

        # .dropna() removes any rows where severity is NaN/empty.
        df = df.dropna(subset=['severity'])

        # --- Summary stats ---
        # st.columns() splits the page into side-by-side columns.
        # On mobile these stack vertically automatically.
        col1, col2, col3 = st.columns(3)

        # st.metric() shows a big number with a label — looks great
        # on a dashboard. Perfect for at-a-glance health stats.
        with col1:
            st.metric('Total entries', len(df))
        with col2:
            st.metric('Average severity', round(df['severity'].mean(), 1))
        with col3:
            st.metric('Highest severity', int(df['severity'].max()))

        # Most common symptom.
        # .value_counts() counts how many times each symptom appears.
        # .idxmax() returns the one with the highest count.
        most_common = df['symptoms'].value_counts().idxmax()
        st.write(f'Most common symptom: **{most_common}**')

        # --- Average severity by food ---
        # This is the "smartest next step" from your roadmap.
        # .groupby('food') groups rows that share the same food together.
        # ['severity'].mean() then calculates the average severity for each group.
        # .sort_values() sorts from highest to lowest average severity.
        st.subheader('Average severity by food')
        food_avg = (
            df.groupby('food')['severity']
            .mean()
            .round(1)
            .sort_values(ascending=False)
            .reset_index()
        )
        food_avg.columns = ['food', 'avg severity']
        st.dataframe(food_avg, use_container_width=True, hide_index=True)
        # --- Safe foods ---
        # Safe foods = any food with average severity below 4.
        # The number 4 is a reasonable threshold — you can adjust it.
        st.subheader('Safe foods (avg severity below 4)')
        safe = food_avg[food_avg['avg severity'] < 4]

        if len(safe) == 0:
            st.write('No consistently safe foods identified yet. Keep logging!')
        else:
            st.dataframe(safe, use_container_width=True, hide_index=True)

        # --- Severity over time chart ---
        # st.line_chart() draws a line chart directly from a DataFrame.
        # We set 'date' as the x-axis and 'severity' as the y-axis.
        st.subheader('Severity over time')
        chart_data = df[['date', 'severity']].set_index('date')
        st.line_chart(chart_data)


# ============================================================
# SECTION 7: TRIGGER DETECTION PAGE
# ============================================================

elif page == 'Trigger Detection':
    st.header('Trigger detection')

    df = load_data()

    if len(df) == 0:
        st.info('No entries yet. Add your first entry from the menu.')
    else:
        df['severity'] = pd.to_numeric(df['severity'], errors='coerce')
        df = df.dropna(subset=['severity'])

        # --- Frequency count (your original trigger detection logic) ---
        # .groupby(['food', 'symptoms']) groups by both columns together,
        # so each unique food+symptom pair gets its own row.
        # .size() counts how many times each pair appears.
        st.subheader('Most frequent food + symptom combinations')
        trigger_counts = (
            df.groupby(['food', 'symptoms'])
            .size()
            .reset_index(name='count')
            .sort_values('count', ascending=False)
        )
        st.dataframe(trigger_counts, use_container_width=True, hide_index=True)

        # --- Severity-weighted triggers (smarter ranking) ---
        # This ranks triggers by average severity instead of just count.
        # A food that appeared twice with severity 9 is more important
        # than a food that appeared 5 times with severity 2.
        st.subheader('Triggers ranked by average severity')
        trigger_severity = (
            df.groupby(['food', 'symptoms'])['severity']
            .mean()
            .round(1)
            .reset_index(name='avg severity')
            .sort_values('avg severity', ascending=False)
        )
        st.dataframe(trigger_severity, use_container_width=True, hide_index=True)

        # --- Bar chart of worst trigger foods ---
        # This is the matplotlib chart from your roadmap — Streamlit
        # gives you this for free with st.bar_chart(). No extra install needed.
        st.subheader('Worst trigger foods (by avg severity)')
        food_severity = (
            df.groupby('food')['severity']
            .mean()
            .round(1)
            .sort_values(ascending=False)
        )
        st.bar_chart(food_severity)
