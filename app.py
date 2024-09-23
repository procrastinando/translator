import os
import csv
import openai
import streamlit as st
import io
from io import StringIO
import requests
import time
import pandas as pd


def list_models(address='localhost:11434'):
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
        print(f"An error occurred: {e}")
        return ()

def run_openai(text, model, prompt, api_key):
    try:
        client = openai.OpenAI(api_key=api_key)  # Initialize the client inside the function
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": f"{prompt}: {text}"}
            ]
        )
        # Extract the translated text from the API response
        print(response.choices[0].message.content)
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error: {e}")
        return text

def run_ollama(text, model, prompt, address='localhost:11434'):
    url = f"http://{address}/api/chat"
    
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
    
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(result["message"]["content"])
        return result["message"]["content"]
    else:
        st.error(f"Error: {response.status_code}, {response.text}")
        return text

def translate_csv(csv_content, model_choice, prompt, api_key, models_list):
    # Check if csv_content is already a StringIO object
    if isinstance(csv_content, StringIO):
        stringio = csv_content
    else:
        # If it's a string, create a StringIO object
        stringio = StringIO(csv_content)

    # Reset the position of the StringIO object to the beginning
    stringio.seek(0)
    csv_reader = csv.reader(stringio)

    # Get the total number of rows to process for the progress bar
    csv_lines = list(csv_reader)  # Convert the reader to a list of rows
    total_rows = len(csv_lines)
    
    # Create a progress bar in Streamlit
    progress_bar = st.progress(0)
    progress_text = st.empty()  # Placeholder to show completed row count

    translated_rows = []
    for index, row in enumerate(csv_lines):
        if model_choice in models_list:
            translated_row = [run_openai(cell, model_choice, prompt, api_key) if cell != '' else '' for cell in row]
        else:
            translated_row = [run_ollama(cell, model_choice, prompt, 'localhost:11434') if cell != '' else '' for cell in row]
        translated_rows.append(translated_row)

        # Update the progress bar and progress text after each row
        progress = (index + 1) / total_rows
        progress_bar.progress(progress)  # Update progress bar
        progress_text.text(f"Completed: {index + 1}/{total_rows}")  # Update progress text

    print(translated_rows)
    csv_data = pd.DataFrame(translated_rows)
    csv_data = csv_data.to_csv().encode("utf-8-sig")

    # Ensure output is encoded in UTF-8
    return csv_data


# Streamlit UI
st.set_page_config(page_title="CSV translator", page_icon="icon.webp")
st.title("CSV translator App")

models_tuple = list_models('localhost:11434')

def main():
    # Model choice
    models_list = ("gpt-4o-mini", "gpt-4o")
    model_choice = st.selectbox("Choose a model", models_list + models_tuple)

    # OpenAI API Key input
    if model_choice in model_choice:
        openai_api_key = st.text_input("Enter your OpenAI API Key", type="password")

    # Prompt input
    prompt = st.text_area("Enter your translation prompt, for example:\nTranslate the following into English without giving explanations")

    # File uploader
    input_file = st.file_uploader("Upload a CSV file", type="csv")

    # Run button
    if st.button("Run"):
        if input_file is not None:
            # Read the CSV file content
            bytes_data = input_file.getvalue()
            csv_content = StringIO(input_file.getvalue().decode("utf-8"))

            # Translate the CSV content
            if model_choice in models_list and not openai_api_key:
                st.error("Please insert API")
            else:
                csv_data = translate_csv(csv_content, model_choice, prompt, openai_api_key, models_list)

                # Provide download link for the translated file
                st.success("Translation complete! Download the file below.")
                st.download_button(
                    label="Download translated CSV",
                    data=csv_data,
                    file_name="translated_output.csv",
                    mime='text/csv'
                )
        else:
            st.error("Please upload a file")

if __name__ == "__main__":
    if models_tuple == ():
        st.error("Could not connect to OLLAMA.")
    main()
