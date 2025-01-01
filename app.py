import os
import logging
import streamlit as st
from cerebras.cloud.sdk import Cerebras
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize Cerebras client
def initialize_client():
    try:
        api_key = os.environ.get("CEREBRAS_API_KEY")
        if not api_key:
            raise ValueError("CEREBRAS_API_KEY is not set in the .env file.")
        return Cerebras(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to initialize Cerebras client: {e}")
        st.error("Failed to initialize the chatbot. Please check the logs for details.")
        st.stop()

# Knowledge base about Aniket Kumar
knowledge_base = {
    "Aniket Kumar": (
        "**Aniket Kumar** is a passionate developer and AI enthusiast. "
        "He believes in the power of **optimism** and strives to build tools that "
        "make the world a better place. Aniket is known for his problem-solving skills "
        "and his ability to simplify complex concepts. He is also an advocate for "
        "open-source software and continuous learning."
    )
}

# System prompts
system_prompt_complex = (
    "You are an AI assistant that uses advanced reasoning methods like Chain of Thought (CoT), "
    "Self-Consistency, and Tree of Thoughts (ToT) to provide accurate and detailed answers. "
    "Always think step-by-step, explain your reasoning, and then provide a final answer. "
    "Make sure to clearly separate your thinking process from the final answer. "
    "You were created by **Aniket Kumar**, a passionate developer and AI enthusiast who believes in the power of **optimism**."
)

system_prompt_simple = (
    "You are an AI assistant that provides concise and immediate answers to straightforward questions. "
    "Keep your responses short and to the point. You were created by **Aniket Kumar**, a passionate developer and AI enthusiast."
)

# Stream response word by word
def stream_response(stream, placeholder, is_complex=False):
    full_response = ""
    thinking_process = ""
    for chunk in stream:
        chunk_content = chunk.choices[0].delta.content or ""
        full_response += chunk_content

        if is_complex and "**Final Answer**" not in full_response:
            thinking_process += chunk_content
            with placeholder.expander("**View Thinking Process**", expanded=True):
                st.markdown(thinking_process + "▌")
        else:
            # Stream word by word
            words = full_response.split(" ")
            for i in range(len(words)):
                placeholder.markdown(" ".join(words[:i+1]) + "▌")
            if "**Final Answer**" in full_response:
                final_answer = full_response.split("**Final Answer**")[1].strip()
                placeholder.markdown(final_answer)
                return final_answer, thinking_process
    return full_response, thinking_process.strip()

# Handle special queries (like Aniket or location)
def handle_special_queries(prompt):
    # Handle specific queries (e.g., about Aniket Kumar)
    if "aniket kumar" in prompt.lower():
        return knowledge_base["Aniket Kumar"]
    
    # Handle location-based queries
    if "location" in prompt.lower():
        return "I can provide location-based responses. Please enable location access in your browser settings."
    
    return None

# Determine if the query is complex or simple
def is_complex_query(prompt):
    return any(keyword in prompt.lower() for keyword in ["explain", "how", "why", "describe", "what is the process"])

# Generate response based on user query
def generate_response(client, mode, messages, is_complex):
    system_prompt = system_prompt_complex if is_complex else system_prompt_simple
    stream = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            *[{"role": msg["role"], "content": msg["content"]} for msg in messages]
        ],
        model="llama-3.3-70b",
        stream=True,
        max_tokens=8000,
        temperature=0.2,
        top_p=1
    )

    with st.chat_message("assistant", avatar="🤖"):
        if is_complex:
            thinking_placeholder = st.empty()
            final_answer_placeholder = st.empty()
            final_answer, thinking_process = stream_response(stream, thinking_placeholder, is_complex=True)
            final_answer_placeholder.markdown(final_answer)
            return final_answer, thinking_process
        else:
            response_placeholder = st.empty()
            full_response, _ = stream_response(stream, response_placeholder)
            response_placeholder.markdown(full_response)
            return full_response, None

# Streamlit app
def main():
    # Set wide screen layout
    st.set_page_config(layout="wide")

    # Personalized greeting based on time of the day
    hour = datetime.now().hour
    if hour < 12:
        greeting = "Good Morning!"
    elif hour < 18:
        greeting = "Good Afternoon!"
    else:
        greeting = "Good Evening!"

    st.title(f"🤖 {greeting} AI Chatbot: Simple & Complex Modes")
    st.write("Ask me anything! I'll provide simple answers for easy questions and detailed reasoning for complex ones.")

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "mode" not in st.session_state:
        st.session_state.mode = "auto"  # Options: "auto", "simple", "complex"

    # Sidebar for mode selection and additional content
    with st.sidebar:
        # App description
        st.header("🤖 AI Chatbot")
        st.write(
            "This AI chatbot is designed to provide both **simple** and **complex** answers based on your queries. "
            "You can switch between different response modes for tailored interactions. The chatbot uses advanced reasoning methods for complex questions and straightforward answers for simpler ones."
        )

        # Settings
        st.header("Settings")
        mode = st.radio(
            "Response Mode",
            ["Auto", "Simple", "Complex"],
            index=["auto", "simple", "complex"].index(st.session_state.mode)
        )
        st.session_state.mode = mode.lower()

        if st.button("Clear Chat History"):
            st.session_state.messages = []
            st.success("Chat history cleared!")

        # Information about the chatbot
        st.header("About")
        st.write(
            "This AI was created by **Aniket Kumar**, a passionate developer and AI enthusiast. "
            "He loves to explore the potential of AI and believes in continuous learning. "
            "The chatbot is built using the Cerebras Cloud SDK, providing you with an advanced conversational experience."
        )

        # GitHub Profile
        st.header("GitHub Profile")
        st.markdown("[Visit Aniket Kumar's GitHub](https://github.com/threatthriver) to explore more projects.")

        # Optionally, you could include a contact or feedback form
        st.header("Contact")
        st.write(
            "If you have any questions or feedback, feel free to reach out via GitHub or email. "
            "Let's collaborate and build something amazing!"
        )

        # User Feedback Button
        feedback = st.radio("How was your experience?", ["Good", "Neutral", "Bad"])
        if st.button("Submit Feedback"):
            st.write(f"Thank you for your feedback! You rated it as: {feedback}")

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=message.get("avatar")):
            if message["role"] == "assistant" and "thinking" in message:
                with st.expander("**View Thinking Process**", expanded=False):
                    st.markdown(message["thinking"])
                st.markdown(message["content"])
            else:
                st.markdown(message["content"])

    # User input
    if prompt := st.chat_input("What is your question?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt, "avatar": "👤"})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        # Handle special queries
        special_response = handle_special_queries(prompt)
        if special_response:
            st.session_state.messages.append({
                "role": "assistant",
                "content": special_response,
                "avatar": "🤖"
            })
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(special_response)
            return

        # Determine mode (simple or complex)
        is_complex = (
            st.session_state.mode == "complex" or
            (st.session_state.mode == "auto" and is_complex_query(prompt))
        )

        # Generate response
        with st.spinner("Generating response..."):
            try:
                client = initialize_client()
                response, thinking_process = generate_response(client, st.session_state.mode, st.session_state.messages, is_complex)

                # Add assistant's response to chat history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "thinking": thinking_process,
                    "avatar": "🤖"
                })

            except Exception as e:
                logger.error(f"Error generating response: {e}")
                st.error("An error occurred while generating the response. Please try again.")
                if st.button("Retry"):
                    st.rerun()

# Run the app
if __name__ == "__main__":
    main()