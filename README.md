## Open AI Assistant Agent StreamLit

This is a StreamLit example that uses threads and OpenAI's assistant API. 

This StreamLit bot uses the assistants API with threads.

### Supports

- Webscraping
- youtube transcript scraping
- File upload
- gpt-4o Vision (Image upload)
- private Keying and assistant switching
- thread clearing

A note that uploading files or vision will add to your openAI storage. 

### Configuration

When running cloud this can be configured for a secret key and assistant API or the user can insert there own keys and assistant IDs

This is set in the code with `isKeyed = False` setting this to false will allow users to input their own keys


the secrets section should be setup like this if `isKeyed = true`

```
[openai]
api_key = "OPENAI KEY"
assistant_id = "ASSISTANT"
```
## Local Running
- Download this repo
```
 pip install -r requirements. txt
```

```
 python -m streamlit run PATH:\\AssistantChatStreamLit.py
```

Upload your app to streamlit using https://streamlit.io/gallery

