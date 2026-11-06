import os
import pandas as pd
import streamlit as st
from src.database import initialize
from src.security import execute_readonly
from src.assistant import EXAMPLES, llm_sql, explain_result

st.set_page_config(page_title='InsightIQ | Conversational AI for BI', page_icon='📊', layout='wide')
st.title('📊 InsightIQ — Conversational AI for Business Intelligence')
st.caption('Portfolio demonstration • synthetic healthcare operations data • read-only SQL')
db = initialize()
with st.sidebar:
    st.header('Settings')
    key = st.text_input('OpenAI API key (optional)', type='password', value=os.getenv('OPENAI_API_KEY',''), help='For custom natural-language questions. Sample queries require no key.')
    model = st.text_input('OpenAI model', value='gpt-4o-mini')
    st.info('For a public demo, avoid entering secrets on shared devices. No real patient or organizational data is included.')
st.subheader('Ask a business question')
selected = st.selectbox('Try a verified example', ['Custom question'] + list(EXAMPLES))
question = st.text_input('Question', value='' if selected == 'Custom question' else selected, placeholder='e.g., Which facility had the most visits?')
if st.button('Analyze', type='primary'):
    try:
        if selected != 'Custom question' and question.strip() == selected:
            sql = EXAMPLES[selected]
        else:
            sql = llm_sql(question, key, model)
        columns, rows = execute_readonly(db, sql)
        st.session_state['result'] = (question, sql, pd.DataFrame(rows, columns=columns))
    except Exception as exc:
        st.error(f'Could not complete query: {exc}')
if 'result' in st.session_state:
    question, sql, df = st.session_state['result']
    st.subheader('Generated SQL')
    st.code(sql, language='sql')
    st.subheader('Results')
    st.write(explain_result(question, list(df.columns), df.values.tolist()))
    st.dataframe(df, use_container_width=True, hide_index=True)
    if not df.empty:
        numeric = list(df.select_dtypes(include='number').columns)
        categories = [c for c in df.columns if c not in numeric]
        if numeric and categories:
            x = st.selectbox('Category / time axis', categories)
            y = st.selectbox('Metric', numeric)
            chart_type = st.radio('Chart type', ['Bar', 'Line'], horizontal=True)
            chart_df = df.set_index(x)[[y]]
            if chart_type == 'Line': st.line_chart(chart_df)
            else: st.bar_chart(chart_df)
        st.download_button('Export results as CSV', df.to_csv(index=False), file_name='insightiq_results.csv', mime='text/csv')
st.divider()
st.markdown('**Architecture:** Streamlit → curated sample SQL or OpenAI Text-to-SQL → SQLGlot allowlist validation → read-only SQLite → Pandas → chart / CSV.')
