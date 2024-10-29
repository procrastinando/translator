import os
import csv
import openai
import streamlit as st
import io
from io import StringIO
import requests
import pandas as pd
from deep_translator import GoogleTranslator

def address_changed():
    try:
        address = st.session_state["address_input"]
        lang_list = list_lang(address)
        st.session_state["lang_list"] = lang_list
    except:
        pass

def list_lang(address):
    try:
        url = f"http://{address}/languages"
        response = requests.get(url)

        # Check if the request was successful
        if response.status_code == 200:
            languages = response.json()
            return list(lang['code'] for lang in languages)
        else:
            return ('No languages available!')
            print(f"Failed to retrieve languages. Status code: {response.status_code}")
    except Exception as e:
        st.error(f"Error: {e}")

def list_models(address):
    try:
        url = f"http://{address}/api/tags"
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        models = response.json().get("models", [])

        lista = []
        for model in models:
            lista.append(model['name'])
        return tuple(lista)

    except Exception as e:  # Catching any exception
        st.error(f"Error: {e}")
        return ('No models available!')

def run_openai(text, model, prompt, contexto, api_key):
    try:
        client = openai.OpenAI(api_key=api_key)  # Initialize the client inside the function
        messages = []
        messages.append({"role": "system", "content": contexto})
        messages.append({"role": "user", "content": f"{prompt}: {text}"})

        response = client.chat.completions.create(
            model=model,
            messages=messages
        )

        # Extract the translated text from the API response
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error: {e}")
        return text

def run_ollama(text, model, prompt, address):
    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": text
            }
        ],
        "stream": False  # Disable streaming for easier handling of the response
    }
    
    url = f"http://{address}/api/chat"
    try:
        response = requests.post(url, json=data, headers=headers)
        result = response.json()
        print(result["message"]["content"])
        return result["message"]["content"]
    except Exception as e:
        st.error(f"Error: {e}")
        return text

def run_lt(text, address, api_key, source, target):
    payload = {
        "q": text,
        "source": source,
        "target": target,
        "format": "text",
        "alternatives": 1,
        "api_key": api_key
    }
    headers = {
        "Content-Type": "application/json"
    }

    url = f"https://{address}/translate"
    try:
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            return response.json()['alternatives'][0]
        else:
            url = f"http://{address}/translate"
            response = requests.post(url, json=payload, headers=headers)
            return response.json()['alternatives'][0]
    except Exception as e:
        st.error(f"Error: {e}")
        return text

def run_google(text, source, target):
    try:
        return GoogleTranslator(source=source, target=target).translate(text=text)
    except Exception as e:
        st.error(f"Error: {e}")
        return text

def translate_csv(csv_content, delimiter, method_choice, model_choice, prompt, context, address, api_key, source, target):
    # Check if csv_content is already a StringIO object
    if isinstance(csv_content, StringIO):
        stringio = csv_content
    else:
        # If it's a string, create a StringIO object
        stringio = StringIO(csv_content)

    # Reset the position of the StringIO object to the beginning
    stringio.seek(0)
    csv_reader = csv.reader(stringio, delimiter=delimiter)

    # Get the total number of rows to process for the progress bar
    csv_lines = list(csv_reader)  # Convert the reader to a list of rows
    total_rows = len(csv_lines)
    
    # Create a progress bar in Streamlit
    progress_bar = st.progress(0)
    progress_text = st.empty()  # Placeholder to show completed row count

    translated_rows = []
    for index, row in enumerate(csv_lines):

        if context != 0:
            # Get the previous 5 rows, starting from the max(0, index-5)
            previous_context = csv_lines[max(0, index - context):index]
            # Get the next 5 rows, stopping at the min(total_rows, index+5)
            next_context = csv_lines[index + 1:min(total_rows, index + context + 1)]
            
            # Flatten the previous and next rows and join into a string
            contexto_list = [cell for sublist in previous_context + next_context for cell in sublist]
            contexto = ", ".join(contexto_list)
        else:
            contexto = ""            

        if method_choice == 'OpenAI':
            translated_row = [run_openai(cell, model_choice, prompt, contexto, api_key) if cell != '' else '' for cell in row]
        elif method_choice == 'Ollama':
            translated_row = [run_ollama(cell, model_choice, prompt, address) if cell != '' else '' for cell in row]
        elif method_choice == 'Google':
            translated_row = [run_google(cell, source, target) if cell != '' else '' for cell in row]
        else:
            translated_row = [run_lt(cell, address, api_key, source, target) if cell != '' else '' for cell in row]
        translated_rows.append(translated_row)

        # Update the progress bar and progress text after each row
        progress = (index + 1) / total_rows
        progress_bar.progress(progress)  # Update progress bar
        progress_text.text(f"Completed: {index + 1}/{total_rows}")  # Update progress text

    csv_data = pd.DataFrame(translated_rows)
    csv_data = csv_data.to_csv(sep=delimiter).encode("utf-8-sig")

    # Ensure output is encoded in UTF-8
    return csv_data

def success(csv_data):
    st.success("Translation complete! Download the file below.")
    st.download_button(
        label="Download translated CSV",
        data=csv_data,
        file_name="translated_output.csv",
        mime='text/csv'
    )

# Streamlit UI
def main():
    st.title("CSV translator App")

    st.sidebar.markdown("""
    ### CSV Translation Application Overview

    ## [Original repository](https://github.com/procrastinando/translator)

    This code implements a CSV translation application using **Streamlit**, which allows users to translate the contents of a CSV file into different languages through various translation methods. Here's a breakdown of its key components:

    #### Libraries Used
    - **`os`, `csv`, `io`, `requests`, `pandas`**: For handling file operations, HTTP requests, and data manipulation.
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

    Overall, this code enables seamless translation of CSV files by leveraging different APIs, with a user-friendly interface built using Streamlit.
    """)

    method_choice = st.selectbox("Choose translation method", ("OpenAI", "Ollama", "Google", "Libre translate"))

    if method_choice == "OpenAI":
        prompt = st.text_area("Enter your translation prompt", value="Translate the following into English without giving any explanations. If for some reason you can't translate this, simply reply: I can't translate that")
        api_key = st.text_input("Enter your API Key", type="password")
        context = st.slider('Select a context size', min_value=0, max_value=20, value=5)

        models_list = ("gpt-4o-mini", "gpt-4o")
        model_choice = st.selectbox("Choose a model", models_list)

    elif method_choice == "Ollama":
        prompt = st.text_area("Enter your translation prompt", value="Translate the following into English without giving any explanations. If for some reason you can't translate this, simply reply: I can't translate that")
        address = st.text_area("Enter Ollama address", value="localhost:11434")

        models_list = list_models(address)
        model_choice = st.selectbox("Choose a model", models_list)
    
    elif method_choice == "Google":
        google_list = [
            'af', 'sq', 'am', 'ar', 'hy', 'az', 'eu', 'be', 'bn', 'bs', 'bg', 'ca',
            'ceb', 'ny', 'zh-cn', 'zh-tw', 'co', 'hr', 'cs', 'da', 'nl', 'en', 'eo',
            'et', 'tl', 'fi', 'fr', 'fy', 'gl', 'ka', 'de', 'el', 'gu', 'ht', 'ha',
            'haw', 'iw', 'hi', 'hmn', 'hu', 'is', 'ig', 'id', 'ga', 'it', 'ja', 'jw',
            'kn', 'kk', 'km', 'rw', 'ko', 'ku', 'ky', 'lo', 'la', 'lv', 'lt', 'lb',
            'mk', 'mg', 'ms', 'ml', 'mt', 'mi', 'mr', 'mn', 'my', 'ne', 'no', 'or',
            'ps', 'fa', 'pl', 'pt', 'pa', 'ro', 'ru', 'sm', 'gd', 'sr', 'st', 'sn',
            'sd', 'si', 'sk', 'sl', 'so', 'es', 'su', 'sw', 'sv', 'tg', 'ta', 'tt',
            'te', 'th', 'tr', 'tk', 'uk', 'ur', 'ug', 'uz', 'vi', 'cy', 'xh', 'yi',
            'yo', 'zu'
        ]
        source = st.selectbox("From:", ['auto'] + google_list)
        target = st.selectbox("To:", google_list)

    else:
        if "lang_list" not in st.session_state:
            st.session_state["lang_list"] = []  # Initialize language list as empty
        address = st.text_area("Enter LibreTranslate address", value="localhost:5000", key="address_input", on_change=address_changed)
        api_key = st.text_input("Enter your API Key", type="password")
        try:
            source = st.selectbox("From:", ['auto'] + st.session_state["lang_list"])
        except:
            source = st.selectbox("From:", st.session_state["lang_list"])
        target = st.selectbox("To:", st.session_state["lang_list"])

    # File uploader
    input_file = st.file_uploader("Upload a CSV file", type="csv")
    if input_file:
        delimiter = st.text_input("Delimiter", value=",")

    # Run button
    if st.button("Run"):
        if input_file is not None:
            # Read the CSV file content
            bytes_data = input_file.getvalue()
            try:
                csv_content = StringIO(input_file.getvalue().decode("utf-8"))
            except UnicodeDecodeError:
                csv_content = StringIO(input_file.getvalue().decode("windows-1252"))

            if method_choice == "OpenAI":
                csv_data = translate_csv(csv_content, delimiter=delimiter, method_choice=method_choice, model_choice=model_choice, prompt=prompt, context=context, address='', api_key=api_key, source='', target='')
                success(csv_data)
            elif method_choice == "Ollama":
                csv_data = translate_csv(csv_content, delimiter=delimiter, method_choice=method_choice, model_choice=model_choice, prompt=prompt, context=0, address=address, api_key='', source='', target='')
                success(csv_data)
            elif method_choice == "Google":
                csv_data = translate_csv(csv_content, delimiter=delimiter, method_choice=method_choice, model_choice='', prompt='', context=0, address='', api_key='', source=source, target=target)
                success(csv_data)
            else:
                csv_data = translate_csv(csv_content, delimiter=delimiter, method_choice=method_choice, model_choice='', prompt='', context=0, address=address, api_key=api_key, source=source, target=target)
                success(csv_data)
        else:
            st.error("Please upload a file")

if __name__ == "__main__":
    main()
