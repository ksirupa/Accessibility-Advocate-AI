import streamlit as st
import os
from toolhouse import Toolhouse
from llms import llms, llm_call
from http_exceptions.client_exceptions import NotFoundException

st.set_page_config(
    page_title="Intelligence AI",
)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "user" not in st.session_state:
    st.session_state.user = ""

if "stream" not in st.session_state:
    st.session_state.stream = True

if "provider" not in st.session_state:
    st.session_state.provider = llms.get(next(iter(llms))).get("provider")
    
if "bundle" not in st.session_state:
    st.session_state.bundle = "default"

if "previous_bundle" not in st.session_state:
    st.session_state.previous_bundle = "default"

from utils import print_messages, append_and_print
import dotenv

dotenv.load_dotenv()

st.logo("logo.svg")

with st.sidebar:
    t = Toolhouse(provider=st.session_state.provider)
    st.title("Accessibility Adovcate")
    with st.expander("Advanced"):
        llm_choice = st.selectbox("Model", tuple(llms.keys()))
        st.session_state.stream = st.toggle("Stream responses", True)
        user = st.text_input("User", "daniele")
        st.session_state.bundle = st.text_input("Bundle", "default")
        st.session_state.tools = t.get_tools(bundle=st.session_state.bundle)

    try:
        available_tools = t.get_tools(bundle=st.session_state.bundle)
    except NotFoundException:
        available_tools = None

    if not available_tools:
        st.subheader("No tools installed")
        st.caption(
            "Go to the [Tool Store](https://app.toolhouse.ai/store) to install your tools, or visit [Bundles](https://app.toolhouse.ai/bundles) to check if the selected bundle exists."
        )
    else:
        st.subheader("Installed tools")
        for tool in available_tools:
            tool_name = tool.get("name")
            if st.session_state.provider != "anthropic":
                tool_name = tool["function"].get("name")
            st.page_link(f"https://app.toolhouse.ai/store/{tool_name}", label=tool_name)

        st.caption(
            "\n\nManage your tools in the [Tool Store](https://app.toolhouse.ai/store) or your [Bundles](https://app.toolhouse.ai/bundles)."
        )

for i in range(4):
    with st.sidebar:
        side_bar_selection = "sidebar" + str(i)
        st.button(label=side_bar_selection)
        st.markdown("---")



llm = llms.get(llm_choice)
st.session_state.provider = llm.get("provider")
model = llm.get("model")

th = Toolhouse(provider=llm.get("provider"))

if st.session_state.bundle != st.session_state.previous_bundle:
    st.session_state.tools = th.get_tools(bundle=st.session_state.bundle)
    st.session_state.previous_bundle = st.session_state.bundle

th.set_metadata("timezone", -7)
if user:
    th.set_metadata("id", user)

print_messages(st.session_state.messages, st.session_state.provider)

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with llm_call(
        provider=llm_choice,
        model=model,
        messages=st.session_state.messages,
        stream=st.session_state.stream,
        tools=st.session_state.tools,
        max_tokens=4096,
        temperature=0.1,
    ) as response:
        completion = append_and_print(response)
        tool_results = th.run_tools(
            completion, append=False
        )

        while tool_results:
            st.session_state.messages += tool_results
            with llm_call(
                provider=llm_choice,
                model=model,
                messages=st.session_state.messages,
                stream=st.session_state.stream,
                tools=st.session_state.tools,
                max_tokens=4096,
                temperature=0.1,
            ) as after_tool_response:
                after_tool_response = append_and_print(after_tool_response)
                tool_results = th.run_tools(
                    after_tool_response, append=False
                )