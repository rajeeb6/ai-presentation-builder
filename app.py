import streamlit as st
import os
import json
from crewai import Agent, Task, Crew, Process, LLM

# --- Streamlit UI Config ---
st.set_page_config(page_title="AI Presentation Builder", page_icon="⚡", layout="centered")

st.title("⚡ Autonomous HTML Presentation Factory")
st.write("Enter a topic below. Our Gemini-powered AI crew will research, write, design, and code a dynamic HTML presentation for you.")

# --- Streamlit UI: Sidebar for Gemini API Key ---
with st.sidebar:
    st.header("⚙️ Configuration")
    gemini_api_key = st.text_input("Enter Google Gemini API Key", type="password")

# --- Streamlit UI: Main Input ---
user_topic = st.text_input("What is the presentation about?", placeholder="e.g., AI in Stock Trading, Sustainable Agriculture...")

# --- Trigger the Agentic Workflow ---
if st.button("Generate HTML Presentation", type="primary"):
    
    if not gemini_api_key:
        st.error("Enter your Gemini API Key in the sidebar.")
    elif not user_topic:
        st.error("Enter a presentation topic.")
    else:
        with st.spinner(f"Gemini agents are building '{user_topic}'..."):
            
            # --- Force Environment Variables ---
            os.environ["GEMINI_API_KEY"] = gemini_api_key

            # --- Native CrewAI LLM Initialization ---
            # Forcing the "-latest" tag to bypass the 404 error
            llm = LLM(
                model="gemini/gemini-1.5-pro-latest"
            )

            # --- Define Agents ---
            researcher = Agent(
                role='Senior Industry Researcher',
                goal='Identify 2 real-world company case studies and hard metrics regarding: {topic}',
                backstory='You rely on your vast internal knowledge to recall real-world company examples and quantifiable data. You do not write fluff.',
                allow_delegation=False,
                llm=llm
            )

            copywriter = Agent(
                role='Executive Presentation Copywriter',
                goal='Transform research into punchy, minimalist slide copy.',
                backstory='You write short, impactful presentation bullet points based on the research provided.',
                allow_delegation=False,
                llm=llm
            )

            art_director = Agent(
                role='Creative Art Director',
                goal='Determine the psychological color palette and visual animation theme based on the topic.',
                backstory='''You analyze the topic and output exact CSS hex values. 
                Select ONE animation theme from: "theme-grid", "theme-fluid", "theme-geo".
                Select ONE transition style from: "transition-slide", "transition-fade", "transition-zoom".
                Select ONE icon from: "icon-tech", "icon-health", "icon-finance", "icon-eco", "icon-industry", "icon-logistics", "icon-analytics", "icon-security", "icon-people", "icon-idea".''',
                allow_delegation=False,
                llm=llm
            )

            developer = Agent(
                role='Front-End Data Engineer',
                goal='Format the finalized copy and design choices into strict JSON data.',
                backstory='You only output raw JSON. You take the team\'s work and map it exactly to the template schema. DO NOT wrap the output in markdown code blocks.',
                allow_delegation=False,
                llm=llm
            )

            # --- Define Tasks ---
            research_task = Task(
                description='Recall 2 distinct real-world companies applying innovations in: {topic}. Provide specific metrics.',
                expected_output='A detailed research dossier with 2 companies and numeric metrics.',
                agent=researcher
            )

            writing_task = Task(
                description='Using the research, write the content for the 5-slide presentation. Include a main title, a 2-point paradigm shift, and descriptions/metrics for the 2 companies.',
                expected_output='Refined text document containing the presentation copy.',
                agent=copywriter
            )

            art_task = Task(
                description='Based on the topic {topic}, select the appropriate CSS colors (bg_color, text_main_color, accent_color, grid_color), animation theme, transition style, and SVG icon class.',
                expected_output='A list of CSS values and class names.',
                agent=art_director
            )

            coding_task = Task(
                description='''Map all content and design choices into this EXACT JSON format. Return ONLY valid JSON.
                {
                    "bg_color": "#...",
                    "text_main_color": "#...",
                    "accent_color": "#...",
                    "grid_color": "rgba(..., 0.2)",
                    "animation_theme": "...",
                    "transition_style": "...",
                    "topic_icon": "...",
                    "main_title": "...",
                    "author_1": "Ameya P",
                    "author_2": "Rajeeb Mohammed",
                    "slide_2_title": "...",
                    "slide_2_point_1": "...",
                    "slide_2_point_2": "...",
                    "company_1_name": "...",
                    "company_1_desc": "...",
                    "company_1_metric_1": "...",
                    "company_1_metric_2": "...",
                    "company_2_name": "...",
                    "company_2_desc": "...",
                    "company_2_metric_1": "...",
                    "company_2_metric_2": "...",
                    "conclusion_title": "...",
                    "conclusion_text": "..."
                }
                ''',
                expected_output='A valid JSON string matching the exact schema provided.',
                agent=developer
            )

            # --- Run the Crew ---
            presentation_crew = Crew(
                agents=[researcher, copywriter, art_director, developer],
                tasks=[research_task, writing_task, art_task, coding_task],
                process=Process.sequential 
            )

            # --- Execution Block ---
            try:
                result = presentation_crew.kickoff(inputs={'topic': user_topic})

                clean_json_str = str(result.raw).strip()
                if clean_json_str.startswith('```json'):
                    clean_json_str = clean_json_str[7:-3]
                elif clean_json_str.startswith('```'):
                    clean_json_str = clean_json_str[3:-3]
                    
                presentation_data = json.loads(clean_json_str)
                
                with open("master_template.html", "r", encoding="utf-8") as file:
                    html_template = file.read()
                    
                final_html = html_template.format(**presentation_data)
                
                st.success("✅ Presentation built successfully!")
                
                st.download_button(
                    label="⬇️ Download HTML Presentation",
                    data=final_html,
                    file_name=f"Generated_{user_topic.replace(' ', '_').lower()}.html",
                    mime="text/html",
                    type="primary"
                )

            except Exception as e:
                st.error("Google's API hard-rejected the request. Read the exact failure below:")
                st.code(str(e))
                st.warning("Check the logs above.")
