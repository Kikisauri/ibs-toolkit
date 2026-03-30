import streamlit as st
import pandas as pd
import datetime
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def get_sheet(tab_name):
    """Connect to Google Sheets and return the specified tab."""
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )
    client = gspread.authorize(creds)
    # .worksheet() opens a specific tab by name
    sheet = client.open("IBS Tracker Data").worksheet(tab_name)
    return sheet

def load_data(tab_name):
    """Load all rows from a specific tab into a DataFrame."""
    sheet = get_sheet(tab_name)
    data = sheet.get_all_records()
    # If the tab is empty, return an empty DataFrame with the right columns
    if not data:
        if tab_name == 'Symptoms':
            return pd.DataFrame(columns=['date', 'food', 'symptoms', 'severity'])
        else:
            return pd.DataFrame(columns=['date', 'medication', 'time'])
    return pd.DataFrame(data)

def save_symptom_entry(date, food, symptoms, severity):
    """Append a new row to the Symptoms tab."""
    sheet = get_sheet('Symptoms')
    sheet.append_row([str(date), food, symptoms, severity])

def save_med_entry(date, medication, time):
    """Append a new row to the Medications tab."""
    sheet = get_sheet('Medications')
    sheet.append_row([str(date), medication, time])


# ============================================================
# PAGE SETUP
# ============================================================
# st.set_page_config() must always be the very first Streamlit
# call in the file. layout='wide' uses the full screen width.

st.set_page_config(page_title='IBS Tracker', layout='wide')
st.title('IBS Symptom Tracker')
st.write('Track your food, symptoms, and triggers in one place.')

# st.sidebar.radio() creates the navigation menu in the side panel.
# On mobile it collapses into a hamburger menu automatically.
st.sidebar.title('Menu')
page = st.sidebar.radio(
    'Go to',
    ['Add Entry', 'Medication Log', 'View Entries', 'Analyze Data', 'Trigger Detection']
)


# ============================================================
# ADD ENTRY
# ============================================================

if page == 'Add Entry':
    st.header('Add a new entry')

    food = st.text_input('What did you eat?')
    symptoms = st.text_input('What symptoms did you have?')

    # st.slider() is easier on a phone than typing a number
    severity = st.slider('Severity', min_value=1, max_value=10, value=5)

    # Show a live label so the severity number feels meaningful
    if severity <= 3:
        st.write(f'Severity {severity} — mild')
    elif severity <= 6:
        st.write(f'Severity {severity} — moderate')
    else:
        st.write(f'Severity {severity} — severe')

    # st.button() only runs the code inside when actually clicked
    if st.button('Save Entry'):
        if not food or not symptoms:
            st.warning('Please fill in both fields before saving.')
        else:
            save_symptom_entry(
                date=datetime.date.today(),
                food=food,
                symptoms=symptoms,
                severity=severity
            )
            st.success('Entry saved!')


# ============================================================
# MEDICATION LOG
# ============================================================

elif page == 'Medication Log':
    st.header('Medication log')

    st.subheader('Log a medication')

    medication = st.text_input('Medication name')

    # st.time_input doesn't support 12 hour format yet (open Streamlit
    # feature request), so we use a text input instead.
    # strftime('%I:%M %p') formats the current time as e.g. "02:30 PM"
    # %I = 12 hour (1-12), %M = minutes, %p = AM/PM
    default_time = datetime.datetime.now().strftime('%I:%M %p')
    time_taken = st.text_input('Time taken (e.g. 2:30 PM)', value=default_time)

    if st.button('Save Medication'):
        if not medication:
            st.warning('Please enter a medication name.')
        else:
            save_med_entry(
                date=datetime.date.today(),
                medication=medication,
                time=time_taken
            )
            st.success(f'{medication} logged at {time_taken}!')

    # --- View medication history ---
    st.subheader('Medication history')
    med_df = load_data('Medications')

    if len(med_df) == 0:
        st.info('No medications logged yet.')
    else:
        st.dataframe(med_df, use_container_width=True, hide_index=True)

        # .value_counts() counts how many times each medication appears.
        # This tells you which meds you reach for most often.
        st.subheader('Most frequently taken')
        freq = (
            med_df['medication']
            .value_counts()
            .reset_index()
        )
        freq.columns = ['medication', 'times taken']
        st.dataframe(freq, use_container_width=True, hide_index=True)

        st.subheader('Export medication log')
        csv_data = med_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label='Download as CSV',
            data=csv_data,
            file_name='my_medication_log.csv',
            mime='text/csv'
        )


# ============================================================
# VIEW ENTRIES
# ============================================================

elif page == 'View Entries':
    st.header('Your symptom history')
    df = load_data('Symptoms')

    if len(df) == 0:
        st.info('No entries yet. Add your first entry from the menu.')
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Search by food — .str.contains() checks if the food column
        # contains the search term. case=False ignores upper/lowercase.
        st.subheader('Search by food')
        search = st.text_input('Type a food to filter (e.g. pizza)')
        if search:
            filtered = df[df['food'].str.contains(search, case=False, na=False)]
            if len(filtered) == 0:
                st.write(f'No entries found for "{search}".')
            else:
                st.write(f'{len(filtered)} entries found for "{search}":')
                st.dataframe(filtered, use_container_width=True, hide_index=True)

        # .to_csv(index=False) converts the DataFrame to CSV text.
        # .encode('utf-8') converts that text to bytes for the download.
        st.subheader('Export your data')
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label='Download as CSV',
            data=csv_data,
            file_name='my_ibs_data.csv',
            mime='text/csv'
        )


# ============================================================
# ANALYZE DATA
# ============================================================

elif page == 'Analyze Data':
    st.header('Data analysis')
    df = load_data('Symptoms')

    if len(df) == 0:
        st.info('No entries yet. Add your first entry from the menu.')
    else:
        # pd.to_numeric() makes sure severity is treated as a number.
        # errors='coerce' turns any non-number into NaN (empty).
        # .dropna() then removes any rows where severity is empty.
        df['severity'] = pd.to_numeric(df['severity'], errors='coerce')
        df = df.dropna(subset=['severity'])

        # st.columns() splits the page into side-by-side panels.
        # On mobile these stack vertically automatically.
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric('Total entries', len(df))
        with col2:
            st.metric('Average severity', round(df['severity'].mean(), 1))
        with col3:
            st.metric('Highest severity', int(df['severity'].max()))

        # .value_counts() counts each symptom, .idxmax() returns
        # the one that appears most often
        most_common = df['symptoms'].value_counts().idxmax()
        st.write(f'Most common symptom: **{most_common}**')

        # .groupby('food') groups all rows with the same food together.
        # .mean() calculates the average severity for each food group.
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

        # Safe foods = any food with average severity below 4.
        # You can adjust the number 4 to whatever threshold feels right.
        st.subheader('Safe foods (avg severity below 4)')
        safe = food_avg[food_avg['avg severity'] < 4]
        if len(safe) == 0:
            st.write('No consistently safe foods identified yet. Keep logging!')
        else:
            st.dataframe(safe, use_container_width=True, hide_index=True)

        # .set_index('date') makes date the x-axis of the chart
        st.subheader('Severity over time')
        chart_data = df[['date', 'severity']].set_index('date')
        st.line_chart(chart_data)


# ============================================================
# TRIGGER DETECTION
# ============================================================

elif page == 'Trigger Detection':
    st.header('Trigger detection')
    # FIX: was incorrectly set to 'Sheet1' — corrected to 'Symptoms'
    df = load_data('Symptoms')

    if len(df) == 0:
        st.info('No entries yet. Add your first entry from the menu.')
    else:
        df['severity'] = pd.to_numeric(df['severity'], errors='coerce')
        df = df.dropna(subset=['severity'])

        # .groupby(['food', 'symptoms']) groups by both columns together
        # so each unique food+symptom pair gets counted separately.
        # .size() counts how many times each pair appears.
        st.subheader('Most frequent food + symptom combinations')
        trigger_counts = (
            df.groupby(['food', 'symptoms'])
            .size()
            .reset_index(name='count')
            .sort_values('count', ascending=False)
        )
        st.dataframe(trigger_counts, use_container_width=True, hide_index=True)

        # This ranks triggers by average severity instead of just count.
        # A food that appeared twice with severity 9 ranks higher than
        # a food that appeared 5 times with severity 2.
        st.subheader('Triggers ranked by average severity')
        trigger_severity = (
            df.groupby(['food', 'symptoms'])['severity']
            .mean()
            .round(1)
            .reset_index(name='avg severity')
            .sort_values('avg severity', ascending=False)
        )
        st.dataframe(trigger_severity, use_container_width=True, hide_index=True)

        # st.bar_chart() gives us a chart for free — no matplotlib needed
        st.subheader('Worst trigger foods (by avg severity)')
        food_severity = (
            df.groupby('food')['severity']
            .mean()
            .round(1)
            .sort_values(ascending=False)
        )
        st.bar_chart(food_severity)
