# AI Doc Bot

An intelligent document chat interface that allows you to have natural conversations with your PDF documents using OpenAI's GPT models. Upload your documents and ask questions in plain language - AI Doc Bot will provide accurate answers with source references.

![Screenshot 2025-01-13 164110](https://github.com/user-attachments/assets/c9fa31ce-21aa-4b9f-a942-73c93dcb4423)


## 🔗 Quick Links
- **Live Demo**: [AI Doc Bot on Streamlit](https://ai-doc-bot.streamlit.app/)
- **GitHub Repository**: [tathyum-gits/AI-Doc-Bot](https://github.com/tathyum-gits/AI-Doc-Bot)

## ✨ Features

### Current Features
- **Smart PDF Processing**
  - Upload and process PDF documents of upto 100 MB
  - Advanced text chunking for optimal context
  - Fast similarity search for accurate responses
  - Source attribution with page references

- **Intuitive Chat Interface**
  - Natural language questioning
  - Real-time response generation
  - Source highlighting for transparency
  - Clean, professional UI


### Coming Soon
- **Multi-Model Support**
  - Anthropic Claude integration
  - Google Gemini integration
  - Model switching through UI

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- OpenAI API key
- 4GB+ RAM

### Installation

1. Clone the repository
```bash
git clone https://github.com/tathyum-gits/AI-Doc-Bot.git
cd AI-Doc-Bot
```

2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate  # Unix
# or
.\venv\Scripts\activate  # Windows
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables
Create a `.env` file:
```env
OPENAI_API_KEY=your_openai_key_here
ENCRYPTION_KEY=your_secure_encryption_key
SESSION_EXPIRY=3600
```

5. Run the application
```bash
streamlit run main.py
```

## 📂 Project Structure
```
AI-Doc-Bot/
├── main.py
├── requirements.txt
├── .env
├── src/
│   ├── config.py
│   ├── components/
│   │   ├── pdf_processor.py
│   │   ├── embedding_manager.py
│   │   ├── chat_manager.py
│   │   └── ui_components.py
│   └── utils/
│       ├── security.py
│       └── session.py
```

## 🔒 Security Features
- End-to-end encryption for file handling
- Secure session management
- Automatic file cleanup
- No permanent storage of user data

## 💫 Performance Features
- Optimized chunk processing
- Efficient embedding search
- Concurrent request handling

## 📝 Usage Guide

1. **Document Upload**
   - Click "Upload PDF Documents" in sidebar
   - Select PDF file(s)
   - Wait for processing completion

2. **Asking Questions**
   - Type your question in the chat input
   - View AI-generated response with source references
   - Use follow-up questions for clarity

![Screenshot 2025-01-13 164241](https://github.com/user-attachments/assets/1fc504e7-f7bd-4859-80dd-de196c2643a9)


## ⚠️ Limitations
- Maximum file size: 100MB per PDF
- File type supported: PDF only
- Session timeout: 1 hour
- Rate limits based on OpenAI API limits

## 🤝 Support & Contact
- Developer: Pooja @ Tathyum
- Email: tathyum01@gmail.com
- Issues & Feature Requests: [GitHub Issues](https://github.com/tathyum-gits/AI-Doc-Bot/issues)

## 📄 License
This project is licensed under the MIT License.

---

Created with ❤️ by [Pooja @ Tathyum](https://github.com/tathyum-gits)
