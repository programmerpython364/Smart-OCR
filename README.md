# Smart OCR: AI-Powered Media Processing Toolkit

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.0%2B-green)
![AI](https://img.shields.io/badge/AI-Gemini--1.5--Flash-orange)

An intelligent web application for extracting and enhancing text from images and videos using state-of-the-art OCR and generative AI.

## Key Features ✨

- **Image & Video OCR**: Extract text from uploaded images (PNG, JPG, JPEG, WEBP) and videos (MP4).
- **AI-Powered Enhancement**: Refine extracted text using Google's Gemini LLM with conversational memory.
- **Frame Selection**: Choose specific video frames for text processing.
- **Session Management**: Automatic cleanup after 30 minutes of inactivity.
- **Error Reporting**: Detailed error pages with traceback for debugging.
- **Multi-Language Support**: Arabic/English OCR capabilities.


## Tech Stack 🛠️

- **Backend**: Flask, LangChain
- **OCR**: EasyOCR
- **AI**: Google Gemini 1.5 Flash
- **Computer Vision**: OpenCV
- **Session Handling**: UUID-based user sessions


## 📦 Installation

### ✅ Prerequisites
Ensure you have **Python 3.9+** installed. You also need `pip` to install dependencies.

### 📌 Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/3liodeh/Smart-OCR.git
   cd Smart-OCR
   ```

2. **Create a virtual environment and activate it:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   - Create a `.env` file in the root directory and add:
     ```ini
     AI_API_TOKEN=your_api_key_here
     ```
   - Replace `your_api_key_here` with your **Google Gemini API key**.

5. **Run the application:**
   ```bash
   python app.py
   ```

6. **Access the application:**
   Open your browser and go to [`http://localhost:10000`](http://localhost:10000)

## 🎯 Usage

### 1️⃣ Upload an Image
- Navigate to `/image` and **upload an image**.
- The extracted text is displayed along with an option to **improve it using AI**.

### 2️⃣ Upload a Video
- Navigate to `/video` and **upload a video** (`MP4`, max `20MB`).
- Select a frame to process **OCR** and improve extracted text.

### 3️⃣ Chat with AI
- The `/chat` page allows users to **interact with the AI model** to refine extracted text.

## 📁 File Structure

```plaintext
smart-ocr/
├── model/                # OCR model
├── app.py                # Flask application core
├── LLM.py                # Gemini integration & memory
├── OCR.py                # EasyOCR wrappers
├── run.py                # Processing pipelines
├── templates/            # Jinja2 templates
│   ├── index.html        # Landing page
│   ├── video.html        # video ORC interface
│   ├── image.html        # image OCR interface
│   └── result.html       # Chat interface
├── uploads/              # Ephemeral file storage
├── requirements.txt      # Dependency list
└── .env                  # API configuration
```

## 📜 Dependencies

Refer to `requirements.txt`:

```plaintext
Flask==2.2.5
werkzeug==2.2.3
easyocr==1.7.2
numpy==1.26.4
Pillow==10.3.0
opencv-python==4.9.0.80
python-dotenv==1.0.1
google-generativeai==0.8.4
langchain==0.3.17
langchain-core==0.3.33
```

## 📄 License

This project is licensed under the **MIT License**. Feel free to modify and use it as needed.

## 🙏 Acknowledgments

- **Google Gemini AI** for language modeling
- **EasyOCR** for text recognition
- **Flask** for web application framework
