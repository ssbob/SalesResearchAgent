# SalesResearchAgent

## Why does it exist?

Part of my day-to-day is helping my Account Execs (AE) with account research (on the technical side primarily). They find out what the company has been up to recently and what open jobs they have (specifically, what technologies they are hiring for). What does the annual report (10-K) say about what the company focuses on, what do they think of the market (both micro and macro), and where do they see their company in that market?

In addition to the company view, they search similarly for each contact, stakeholder, and key person they will interface with. They will check LinkedIn, look at where they went to school, what they post on LI, Twitter (X now, I guess), etc.

All of this is pretty manual; why not take the opportunity to automate it and make it smarter simultaneously?

## What does it do?

SalesResearchAgent is pretty simple, actually; it uses a number of technologies, including OpenAI API, Langchain, tool(s), and some general Python stuff to get a reasonable answer to the question "Who is X? and what do they do?" or "What does company Y do?". Behind the scenes, it's doing some Google searches, walking links, finding information, then putting it together in a summary with the supporting links. You can set the limit of the # of links it will crawl down on line 234:

`7/ After scraping and searching, you should consider "if there are new things I should search and scrape based on the data I collected to increase research quality?" If yes, then continue, But don't do more than five iterations
`

The original author set 3 iterations; I tried 5, thinking I may get better/more complete information. I am not convinced this change provided more value, as that is a subjective measurement. I may put it back to 3 and do some more testing.

## How do I use it?

Like any Python app, you need to do the following:

1. Create a virtual environment (though technically you don't really, but it makes things a bit cleaner if you can)
2. Set up a .env file with your API keys. You will need the following:
   1. OpenAI API key should look like `OPENAI_API_KEY = "sk-..."`
   2. Serper.dev API key should look like `SERP_API_KEY = "..."`
   3. Browserless API key should look like `BROWSERLESS_API_KEY = "..."`

If you do not have these accounts, sign up for them. OpenAI is super cheap to get API access, and it's worth it if you are playing with AI. Serper.dev has a free tier, I did not go past that tier in my testing, and I doubt you will either. Browserless also has a free tier, which I used and had no trouble with.
3. Install the dependencies in the requirements.txt; you can do this by using `pip -r requirements.txt`
4. Run the Streamlit script to start the Python application `streamlit run app.py`
5. It will spawn a browser session and run the app

## What do I like and not like about it?

I will start with what I like about it. It automates a lot of the research one would do about a company and individual. However, it is better for the individual than the entity. It does a much better job finding nuggets than I would; that's where the value comes from, freeing up my time for more value add activities.

Now the negative, knowing what I know about LLMs in general, I wonder how much information it finds or if the summaries it provides are hallucinations or made up. It's hard to know, and even though I tell it to not make anything up, it still does. Secondly, it's not particularly deterministic, meaning you could run the same query 3x times, and it will give you different results and different formatting all three times. I realize this is indicative of an LLM, but it's not great at it. I am sure there are ways to improve the output and logic, but I don't know what they are and do not have the time to investigate.

I have also been having a hard time getting it to find the annual report for a given publicly traded company; it seems like it doesn't understand the request and ignores it. There is usually good information in that 10-K, and it bothers me that it doesn't find it or understand what I am asking. I even added a tool to parse PDFs, but no go. I think this is probably just an LLM thing, it finds enough winners and runs with it rather than following instructions to the letter.

## What's next?

For starters, gotta fix that annual report thing; it's a problem that needs to be solved. I will have time to play with it, I am sure.

Secondly, I need to figure out a way to get a more deterministic output from the LLM; I am sure there is a way, I would wager a number of ways, but I haven't had the time to dig deeper. For now, it runs and does a good job; that's good enough for now.

After that, I will ask my AEs to provide feedback and give me some ideas of feature enhancements they would like to see. Maybe a way to add/remove things to look for in the left-hand nav of Streamlit.
