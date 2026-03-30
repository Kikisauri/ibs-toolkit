import streamlit as st
import pandas as pd
import datetime
import gspread
from google.oauth2.service_account import Credentials

# ============================================================
# GOOGLE SHEETS SETUP
# ============================================================
# We define the 'scopes' — these tell Google what permissions
# our app needs. We need Sheets and Drive access.

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def get_sheet():
    """Connect to Google Sheets and return the first worksheet.
    
    st.secrets reads from your secrets.toml file locally, and
    from Streamlit Cloud's secrets panel when deployed.
    """
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )
    client = gspread.authorize(creds)
    # Open the sheet by name — must match exactly
    sheet = client.open("IBS Tracker Data").sheet1
    return sheet

def load_data():
    """Load all rows from Google Sheets into a DataFrame."""
    sheet = get_sheet()
    data = sheet.get_all_records()
    # If sheet is empty (only headers), return empty DataFrame
    if not data:
        return pd.DataFrame(columns=['date', 'food', 'symptoms', 'severity'])
    return pd.DataFrame(data)

def save_entry(date, food, symptoms, severity):
    """Append a new row to the Google Sheet."""
    sheet = get_sheet()
    # .append_row() adds a new row at the bottom of the sheet.
    # We pass the values in the same order as our column headers.
    sheet.append_row([str(date), food, symptoms, severity])


# ============================================================
# PAGE SETUP
# ============================================================

st.set_page_config(page_title='IBS Tracker', layout='wide')
st.title('IBS Symptom Tracker')
st.write('Track your food, symptoms, and triggers in one place.')

st.sidebar.title('Menu')
page = st.sidebar.radio('Go to', ['Add Entry', 'View Entries', 'Analyze Data', 'Trigger Detection'])


# ============================================================
# ADD ENTRY
# ============================================================

if page == 'Add Entry':
    st.header('Add a new entry')
    food = st.text_input('What did you eat?')
    symptoms = st.text_input('What symptoms did you have?')
    severity = st.slider('Severity', min_value=1, max_value=10, value=5)

    if severity <= 3:
        st.write(f'Severity {severity} — mild')
    elif severity <= 6:
        st.write(f'Severity {severity} — moderate')
    else:
        st.write(f'Severity {severity} — severe')

    if st.button('Save Entry'):
        if not food or not symptoms:
            st.warning('Please fill in both fields before saving.')
        else:
            save_entry(
                date=datetime.date.today(),
                food=food,
                symptoms=symptoms,
                severity=severity
            )
            st.success('Entry saved!')


# ============================================================
# VIEW ENTRIES
# ============================================================

elif page == 'View Entries':
    st.header('Your symptom history')
    df = load_data()

    if len(df) == 0:
        st.info('No entries yet. Add your first entry from the menu.')
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.subheader('Search by food')
        search = st.text_input('Type a food to filter (e.g. pizza)')
        if search:
            filtered = df[df['food'].str.contains(search, case=False, na=False)]
            if len(filtered) == 0:
                st.write(f'No entries found for "{search}".')
            else:
                st.write(f'{len(filtered)} entries found for "{search}":')
                st.dataframe(filtered, use_container_width=True, hide_index=True)

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
    df = load_data()

    if len(df) == 0:
        st.info('No entries yet. Add your first entry from the menu.')
    else:
        df['severity'] = pd.to_numeric(df['severity'], errors='coerce')
        df = df.dropna(subset=['severity'])

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric('Total entries', len(df))
        with col2:
            st.metric('Average severity', round(df['severity'].mean(), 1))
        with col3:
            st.metric('Highest severity', int(df['severity'].max()))

        most_common = df['symptoms'].value_counts().idxmax()
        st.write(f'Most common symptom: **{most_common}**')

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

        st.subheader('Safe foods (avg severity below 4)')
        safe = food_avg[food_avg['avg severity'] < 4]
        if len(safe) == 0:
            st.write('No consistently safe foods identified yet. Keep logging!')
        else:
            st.dataframe(safe, use_container_width=True, hide_index=True)

        st.subheader('Severity over time')
        chart_data = df[['date', 'severity']].set_index('date')
        st.line_chart(chart_data)


# ============================================================
# TRIGGER DETECTION
# ============================================================

elif page == 'Trigger Detection':
    st.header('Trigger detection')
    df = load_data()

    if len(df) == 0:
        st.info('No entries yet. Add your first entry from the menu.')
    else:
        df['severity'] = pd.to_numeric(df['severity'], errors='coerce')
        df = df.dropna(subset=['severity'])

        st.subheader('Most frequent food + symptom combinations')
        trigger_counts = (
            df.groupby(['food', 'symptoms'])
            .size()
            .reset_index(name='count')
            .sort_values('count', ascending=False)
        )
        st.dataframe(trigger_counts, use_container_width=True, hide_index=True)

        st.subheader('Triggers ranked by average severity')
        trigger_severity = (
            df.groupby(['food', 'symptoms'])['severity']
            .mean()
            .round(1)
            .reset_index(name='avg severity')
            .sort_values('avg severity', ascending=False)
        )
        st.dataframe(trigger_severity, use_container_width=True, hide_index=True)

        st.subheader('Worst trigger foods (by avg severity)')
        food_severity = (
            df.groupby('food')['severity']
            .mean()
            .round(1)
            .sort_values(ascending=False)
        )
        st.bar_chart(food_severity)
