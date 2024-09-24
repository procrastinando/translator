# translator
### CSV Translation Application Overview

This code implements a CSV translation application using **Streamlit**, which allows users to translate the contents of a CSV file into different languages through various translation methods. Here's a breakdown of its key components:

#### Libraries Used
- **`os`, `csv`, `io`, `requests`, `time`, `pandas`**: For handling file operations, HTTP requests, and data manipulation.
- **`openai`**: To interact with OpenAI's translation models.
- **`streamlit`**: For building the web interface.

#### Main Functions
- **`address_changed()`**: Updates the list of available languages when the address input changes.
- **`list_lang(address)`**: Fetches available languages from a specified address using an HTTP GET request.
- **`list_models(address)`**: Retrieves available models from a server endpoint, handling errors gracefully.
- **`run_openai(text, model, prompt, api_key)`**: Calls the OpenAI API to translate the provided text using the specified model.
- **`run_ollama(text, model, prompt, address)`**: Uses the Ollama API to perform translations.
- **`run_lt(text, address, api_key, source, target)`**: Sends translation requests to LibreTranslate, managing the input and output format.
- **`translate_csv(csv_content, method_choice, model_choice, prompt, address, api_key, source, target)`**: Reads CSV content, applies the selected translation method to each cell, and updates a progress bar in the Streamlit interface.
- **`success(csv_data)`**: Displays a success message and offers a download button for the translated CSV file.

#### User Interface
The application sets up a web page where users can select the translation method (OpenAI, Ollama, or Libre Translate), input their translation prompt, API keys, and upload a CSV file for translation. It processes the uploaded file based on the user's chosen method and provides feedback through progress indicators and success messages.

1. Install requirements
```
conda create --name translator python=3.10 -y
conda activate translator
git clone https://github.com/procrastinando/translator
cd translator
pip install -r requirements.txt
```
2. Run
`streamlit run app.py`