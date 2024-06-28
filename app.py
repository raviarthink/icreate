from flask import Flask, render_template, request, flash
from PIL import Image
import io
import base64
import requests
import os
from dotenv import load_dotenv
import markdown
import json

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

def convert_to_jpeg(uploaded_file):
    try:
        img = Image.open(uploaded_file)
        img = img.convert("RGB")
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG")
        base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return base64_image
    except Exception as e:
        flash(f"Error converting image to JPEG: {e}", 'error')
        return None

def request_openai_api(images, prompt):
    api_key = os.getenv('OPENAI_API_KEY')  # Retrieve OpenAI API key from environment variable
    if all(images):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        content = [{"type": "text", "text": prompt}]
        for image in images:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image}"}
            })

        payload = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": content}],
            "max_tokens": 300
        }

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        try:
            response.raise_for_status()  # Raise an HTTPError if the HTTP request returned an unsuccessful status code
            return response.json()["choices"][0]["message"]["content"]
        except requests.exceptions.HTTPError as http_err:
            flash(f"HTTP error occurred: {http_err}", 'error')
        except requests.exceptions.RequestException as req_err:
            flash(f"Request error occurred: {req_err}", 'error')
        except json.JSONDecodeError as json_err:
            flash(f"JSON decode error: {json_err} - Response text: {response.text}", 'error')
        except Exception as err:
            flash(f"An error occurred: {err}", 'error')

    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/icreate')
def icreate():
    return render_template('icreate.html')

@app.route('/icreate/personal', methods=['GET', 'POST'])
def personal():
    if request.method == 'POST':
        operation = request.form.get('operation')
        prompt = request.form.get('prompt')

        if operation == 'explore':
            image = request.files.get('image')
            if image:
                base64_image = convert_to_jpeg(image)
                if base64_image:
                    response = request_openai_api([base64_image], prompt)
                    if response:
                        response_html = markdown.markdown(response)
                        return render_template('personal.html', explore_response=response_html, explore_image=base64_image)

        elif operation == 'compare':
            image1 = request.files.get('image1')
            image2 = request.files.get('image2')
            if image1 and image2:
                base64_image1 = convert_to_jpeg(image1)
                base64_image2 = convert_to_jpeg(image2)
                if base64_image1 and base64_image2:
                    response = request_openai_api([base64_image1, base64_image2], prompt)
                    if response:
                        response_html = markdown.markdown(response)
                        return render_template('personal.html', compare_response=response_html, compare_images=[base64_image1, base64_image2])

    return render_template('personal.html')

@app.route('/icreate/industries')
def industries():
    carousel_images = [
        'images/anniversary_img.png',
        'images/Onam_img.png',
        'images/sankranthi_img.png',
    ]
    return render_template('industries.html', carousel_images=carousel_images)



if __name__ == '__main__':
    app.run(debug=True)