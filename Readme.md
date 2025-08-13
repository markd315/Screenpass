# Screenpass

### you give me screen, I pass screen

### we give trucker screen, we decide if they pass screen.

## Run instructions:
```
pip install -r requirements.txt
anvil-app-server --app ScreenpassChat --port 8080

visit:
http://localhost:8080/#leadSource=google&company=companyB
```


#### claude prompt

Build a single-page LLM chat app using Python Anvil on port 8080.

We only need four components on the page, a large text area for chat responses, 
Immediately below, a very long text box for adding queries.

a green submit button and a red "end chat" button.

Use the bootstrap material theme for the site.

On page load, consume from the 2 query parameters:
"leadSource" and "company". Hit the "init" endpoint for this conversation with these details.

Populate the system prompts in server_config.json with the two placeholder values for YOE and nights_per

When the green submit button is pressed on the frontend, the "prompt" endpoint is hit and the content submitted is added to the text area, prepended with ">Trucker: " to designate the speaker.

The chatbox is refreshed with the contents of any 200 response, prepended with ">Screenpass: " to designate the speaker.

When the red "end chat" button is pressed, the "summarize" endpoint is hit.

The "summarize" endpoint does 3 things:
1) Triggers a write of the full conversation with a filename of the start and end timestamps to the results/audit folder.
2) Calls the LLM again to summarize the conversation in 150 words or less using our same AI tool. Summary written to results/summary
3) Triggers a sentiment analysis on the LLM where the conversation is indexed 1-5 to look at customer satisfaction data. A row is added to results/sentiment.csv
4) Triggers a decision on if the driver met the qualifying criteria. Result is written to results/decisions.csv

Any time an LLM would be called, log to the console with "LLM:". For now assume the API key is 1234.