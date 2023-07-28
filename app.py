# Original credit for this idea comes from me the author, however,
# a similar use case was created by https://github.com/JayZeeDesign/researcher-gpt/tree/main,
# based on a YouTube video https://youtu.be/ogQUlS7CkYA
#
# This implementation of this project is heavily inspired by the above, and tweaked
# for this use case


import json
import os
from typing import Type

import requests
import streamlit as st
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fastapi import FastAPI
from langchain import PromptTemplate
from langchain.agents import AgentType, Tool, initialize_agent
from langchain.chains.summarize import load_summarize_chain
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import PyPDFLoader
from langchain.memory import ConversationSummaryBufferMemory
from langchain.prompts import MessagesPlaceholder
from langchain.schema import SystemMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

# load_dotenv()
browserless_api_key = os.getenv("BROWSERLESS_API_KEY")
serper_api_key = os.getenv("SERP_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")


# 1. Setup search tool(s)
def search(query):
    url = "https://google.serper.dev/search"

    payload = json.dumps({"q": query})

    headers = {"X-API-KEY": serper_api_key, "Content-Type": "application/json"}

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)

    return response.text


# Test search tool
# search("what is the weather in London today?")


# 2. Setup scraping tool(s)
def scrape_web(objective: str, url: str):
    # using the objective defined, will scrape the URL, and summarize it if the content is large
    # the objective is based on the original objective and task that the user gives to the agent, the URL is the URL of the website to be scraped
    print("Scraping site...")

    # Define the headers to be sent in the request
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
    }

    # Define the data to be sent in the request
    data = {"url": url}

    # Convert the Python object to a JSON string
    data_json = json.dumps(data)

    # Send the POST request
    post_url = f"https://chrome.browserless.io/content?token={browserless_api_key}"
    response = requests.post(post_url, headers=headers, data=data_json)

    # Check if we get a 200 status code (200 = Good)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        text = soup.get_text()
        print("CONTENT:", text)

        # Sends to the summary function if the length of the scraped
        # text is very large (>10000 tokens), else just return the text
        if len(text) > 10000:
            output = summary(objective, text)
            return output
        else:
            return text

    else:
        print(f"HTTP request failed with status code {response.status_code}")


def scrape_pdf(objective: str, filename: str):
    loader = PyPDFLoader(filename)
    pages = loader.load_and_split()

    if len(pages) > 10000:
        output = summary(objective, pages)
        # print(output)
        return output
    else:
        # print(pages)
        return pages


# Create a summary of the content provided an objective
def summary(objective, content):
    # Create the LLM object
    llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo-16k-0613")

    # Split the text based on chunk_size and chunk_overlay, this allows
    # us to parse very large sites
    text_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n"], chunk_size=10000, chunk_overlap=500
    )

    # Create the docs object
    docs = text_splitter.create_documents([content])

    # Create the prompt
    map_prompt = """
    Write a summary of the following text for {objective}:
    "{text}"
    SUMMARY: 
    """
    map_prompt_template = PromptTemplate(
        template=map_prompt, input_variables=["text", "objective"]
    )

    # Using map_reduce to summarize our documents allowing for it
    # to keep under token limits, this is versus Vector search (for
    # larger data sets)
    summary_chain = load_summarize_chain(
        llm=llm,
        chain_type="map_reduce",
        map_prompt=map_prompt_template,
        combine_prompt=map_prompt_template,
        verbose=True,
    )

    output = summary_chain.run(input_documents=docs, objective=objective)

    return output


# Class to define inputs for the scrape_web function,
# we need this for the agent to know what information to pass
# to the function
class ScrapedWebsiteInput(BaseModel):
    """Inputs for scrape_web"""

    objective: str = Field(
        description="The objective & task that users give to the agent"
    )
    url: str = Field(description="The URL of the site to be scraped")


# Class to define the tool so that the agent knows when and how to use the
# scrape_web function, all tools with more than one input will need these
# two classes (the definition with fields, and the tool class)
class ScrapeWebsiteTool(BaseTool):
    name = "scrape_site"
    description = "useful when you need to get data from a website URL, passing both a URL and an objective to the function; DO NOT make up any URL, the URL should only be from the search results"
    args_schema: Type[BaseModel] = ScrapedWebsiteInput

    # What happens when the tool is run
    def _run(self, objective: str, url: str):
        return scrape_web(objective, url)

    # What happens when there is an error with the tool
    def _arun(self, url: str):
        raise NotImplementedError("error here")


# Class to define inputs for the scrape_pdf function,
# we need this for the agent to know what information to pass
# to the function
class ScrapePDFInput(BaseModel):
    """Inputs for scrape_pdf"""

    objective: str = Field(
        description="The objective & task that users give to the agent"
    )
    filename: str = Field(description="The file to be scraped")


# Class to define the tool so that the agent knows when and how to use the
# scrape_pdf function, all tools with more than one input will need these
# two classes (the definition with fields, and the tool class)
class ScrapePDFTool(BaseTool):
    name = "scrape_site"
    description = "useful when you need to get data from a PDF, passing both a URL and an objective to the function; DO NOT make up any URL, the URL should only be from the search results"
    args_schema: Type[BaseModel] = ScrapePDFInput

    # What happens when the tool is run
    def _run(self, objective: str, filename: str):
        return scrape_pdf(objective, filename)

    # What happens when there is an error with the tool
    def _arun(self, filename: str):
        raise NotImplementedError("error here")


# 3. Create agent

# Create the list of tools for the agent
tools = [
    Tool(
        name="Search",
        func=search,
        description="useful when you neeed to answer questions about current events and data. You should ask targeted questions",
    ),
    ScrapeWebsiteTool(),
    Tool(
        name="Search_PDF",
        func=scrape_pdf,
        description="useful when you need to answer questions about a PDF document. You should ask targeted questions",
    ),
    ScrapePDFTool(),
]

system_message = SystemMessage(
    content="""You are a world class sales development representative, you can do detailed research on any person and company, and produce facts based results; you do not make things up, you will try as hard as possible to gather facts and data to back up your research
            
            Please make sure you complete the objective above with the following rules:
            1/ You are doing research about an individual and company, for purposes of sales outreach, find out what the person is talking about on Twitter and LinkedIn
            2/ You should find useful pieces of information that would be great hooks to engage them in a conversation
            3/ You should find where they worked prior to their current company, and where they went to college
            4/ You should find the annual report for their current employer and highlight forward thinking strategies and thought leadership 
            5/ You should do sufficient research to gather as much information as possible about the objective
            6/ If there are URLs of relevant links and articles , you will scrape it to gather additional information
            7/ After scraping and searching, you should consider "if there are new things I should search and scrape based on the data I collected to increase research quality?" If yes, then continue; But don't do this more than 5 iterations
            8/ You should not make things up, you should only write facts and data that you have gathered
            9/ In the final output, You should include all reference data & links to back up your research; You should include all reference data & links to back up your research
            10/ In the final output, You should include all reference data & links to back up your research; You should include all reference data & links to back up your research"""
)
agent_kwargs = {
    "extra_prompt_messages": [MessagesPlaceholder(variable_name="memory")],
    "system_message": system_message,
}

llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo-16k-0613")
memory = ConversationSummaryBufferMemory(
    memory_key="memory", return_messages=True, llm=llm, max_token_limit=10000
)

agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True,
    agent_kwargs=agent_kwargs,
    memory=memory,
)


def main():
    st.set_page_config(page_title="AI research agent", page_icon=":bird:")

    st.header("AI research agent :bird:")
    query = st.text_input("Research goal")

    if query:
        st.write("Doing research for ", query)

        result = agent({"input": query})

        st.write(result["output"])


if __name__ == "__main__":
    main()

# 4. Deploy agent


# 5. Integrate
