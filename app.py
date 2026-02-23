import streamlit as st
import os
import json
from crewai import Agent, Task, Crew, Process, LLM

# --- Streamlit UI Config ---
st.set_page_config(page_title="AI Presentation Builder", page_icon="⚡", layout="wide")

st.title("⚡ Autonomous HTML Presentation Factory")
st.write("Paste your raw notes, outline, or description below. The AI will structure it into a 10-12 slide presentation.")

# --- Streamlit UI: Sidebar for Gemini API Key ---
with st.sidebar:
    st.header("⚙️ Configuration")
    gemini_api_key = st.text_input("Enter Google Gemini API Key", type="password")

# --- Streamlit UI: Main Input ---
user_description = st.text_area("Paste presentation details here:", height=200, placeholder="Paste your raw thoughts, business plan, or research here...")

# --- Trigger the Agentic Workflow ---
if st.button("Generate HTML Presentation", type="primary"):
    
    if not gemini_api_key:
        st.error("Enter your Gemini API Key in the sidebar.")
    elif len(user_description) < 20:
        st.error("Provide a longer description so the AI has enough context to build 10 slides.")
    else:
        with st.spinner("Agents are structuring your 10-12 slide deck..."):
            
            os.environ["GEMINI_API_KEY"] = gemini_api_key

            llm = LLM(
                model="gemini/gemini-2.5-flash"
            )

            # --- Define Agents ---
            strategist = Agent(
                role='Content Strategist',
                goal='Analyze the user input and outline a logical progression of exactly 10 to 12 presentation slides.',
                backstory='You are a ruthless editor. You take unstructured thoughts and organize them into a powerful, multi-slide narrative arc.',
                allow_delegation=False,
                llm=llm
            )

            copywriter = Agent(
                role='Executive Copywriter',
                goal='Draft the specific bullet points for the 10-12 slides outlined by the strategist.',
                backstory='You write punchy, minimalist slide copy. No long paragraphs. Only high-impact bullet points.',
                allow_delegation=False,
                llm=llm
            )

            art_director = Agent(
                role='Creative Art Director',
                goal='Select a dark-mode CSS color palette based on the tone of the content.',
                backstory='You output exact CSS hex values. Always use dark backgrounds (e.g., #111111) with vibrant accent colors.',
                allow_delegation=False,
                llm=llm
            )

            developer = Agent(
                role='Front-End Data Engineer',
                goal='Compile the content and design into a strict, nested JSON format.',
                backstory='You only output raw JSON. You must ensure the slides array contains exactly 10 to 12 slide objects.',
                allow_delegation=False,
                llm=llm
            )

            # --- Define Tasks ---
            strategy_task = Task(
                description=f'Analyze this user input: "{user_description}". Create an outline for exactly 10 to 12 slides.',
                expected_output='A numbered outline of 10-12 slides with a core concept for each.',
                agent=strategist
            )

            writing_task = Task(
                description='Take the outline and write the final title and 3-4 bullet points for each of the 10-12 slides.',
                expected_output='Text document containing the final copy for all slides.',
                agent=copywriter
            )

            art_task = Task(
                description='Analyze the subject matter and define the CSS color variables: bg_color (dark), text_main_color (light), accent_color (vibrant), grid_color (faint overlay), animation_theme, transition_style.',
                expected_output='A list of CSS values.',
                agent=art_director
            )

            coding_task = Task(
                description='''Map all content and design choices into this EXACT JSON schema. Return ONLY valid JSON.
                {
                    "design": {
                        "bg_color": "#...",
                        "text_main_color": "#...",
                        "accent_color": "#...",
                        "grid_color": "rgba(..., 0.1)",
                        "animation_theme": "theme-grid",
                        "transition_style": "transition-fade"
                    },
                    "slides": [
                        {
                            "title": "Slide 1 Title",
                            "content": ["Point 1", "Point 2", "Point 3"]
                        },
                        {
                            "title": "Slide 2 Title",
                            "content": ["Point 1", "Point 2"]
                        }
                    ]
                }
                Make absolutely sure the "slides" array has 10 to 12 objects.
                ''',
                expected_output='A valid JSON string matching the exact schema.',
                agent=developer
            )

            # --- Run the Crew ---
            presentation_crew = Crew(
                agents=[strategist, copywriter, art_director, developer],
                tasks=[strategy_task, writing_task, art_task, coding_task],
                process=Process.sequential 
            )

            # --- Execution Block ---
            try:
                result = presentation_crew.kickoff()

                clean_json_str = str(result.raw).strip()
                if clean_json_str.startswith('```json'):
                    clean_json_str = clean_json_str[7:-3]
                elif clean_json_str.startswith('```'):
                    clean_json_str = clean_json_str[3:-3]
                    
                presentation_data = json.loads(clean_json_str)
                
                # Build the dynamic HTML for the slides
                slides_html = ""
                for slide in presentation_data.get("slides", []):
                    points_html = "".join([f"<li>{pt}</li>" for pt in slide.get("content", [])])
                    slides_html += f"""
                    <div class="slide">
                        <div class="content-box">
                            <h2>{slide.get('title', 'Untitled')}</h2>
                            <ul>{points_html}</ul>
                        </div>
                    </div>
                    """
                
                # Load template
                with open("master_template.html", "r", encoding="utf-8") as file:
                    html_template = file.read()
                    
                # Inject Data
                final_html = html_template
                for key, value in presentation_data.get("design", {}).items():
                    final_html = final_html.replace(f"{{{key}}}", str(value))
                    
                final_html = final_html.replace("{presentation_slides}", slides_html)
                
                st.success(f"✅ Presentation built successfully! Generated {len(presentation_data.get('slides', []))} slides.")
                
                st.download_button(
                    label="⬇️ Download HTML Presentation",
                    data=final_html,
                    file_name="Generated_Presentation.html",
                    mime="text/html",
                    type="primary"
                )

            except Exception as e:
                st.error("Execution failed. Read the exact failure below:")
                st.code(str(e))
