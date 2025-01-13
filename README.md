# Enterprise Document Chat

A production-grade Streamlit-based AI chatbot for document interaction, leveraging OpenAI, Claude, and Gemini APIs. This application enables users to upload PDF documents and engage in context-aware conversations about their content.

## 🌟 Features

- **Multi-Model Support**
  - OpenAI GPT-4
  - Anthropic Claude
  - Google Gemini
  - Easy model switching through UI

- **Document Processing**
  - PDF text extraction with chunk optimization
  - Advanced embedding generation
  - Fast similarity search
  - Source reference tracking

- **Enterprise-Grade Security**
  - Secure file handling
  - Session management
  - Encrypted storage
  - Automatic cleanup

- **Professional UI**
  - Intuitive document management
  - Real-time chat interface
  - Progress tracking
  - System metrics
  - Source attribution

- **Performance Features**
  - Concurrent request handling
  - Optimized memory usage
  - Fast response times
  - Scalable architecture

## 📋 Requirements

- Python 3.8+
- Virtual environment (recommended)
- API keys for:
  - OpenAI
  - Anthropic
  - Google (Gemini)
- System requirements:
  - 4GB+ RAM
  - 2GB+ free disk space

## 🚀 Quick Start

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-org/document-chat.git
   cd document-chat
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Unix
   # or
   .\venv\Scripts\activate  # Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your_openai_key
   ANTHROPIC_API_KEY=your_anthropic_key
   GOOGLE_API_KEY=your_google_key
   ENCRYPTION_KEY=your_secure_encryption_key
   SESSION_EXPIRY=3600
   ```

5. **Run the Application**
   ```bash
   streamlit run src/main.py
   ```

## 🛠️ Development Setup

### Project Structure
```
pdf_chatbot/
├── requirements.txt
├── .env
├── README.md
├── Dockerfile
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── components/
│   │   ├── __init__.py
│   │   ├── pdf_processor.py
│   │   ├── embedding_manager.py
│   │   ├── chat_manager.py
│   │   └── ui_components.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── security.py
│   │   ├── session.py
│   │   └── logging_config.py
│   └── models/
│       ├── __init__.py
│       └── response.py
└── tests/
    ├── __init__.py
    ├── test_pdf_processor.py
    ├── test_embedding_manager.py
    └── test_chat_manager.py
```

### Testing
Run the test suite:
```bash
pytest tests/
```

## 🚢 Deployment

### Docker Deployment
1. **Build the Docker Image**
   ```bash
   docker build -t document-chat .
   ```

2. **Run the Container**
   ```bash
   docker run -p 8501:8501 --env-file .env document-chat
   ```

### Cloud Deployment

#### Streamlit Cloud
1. Connect your GitHub repository
2. Add environment variables in Streamlit Cloud settings
3. Deploy from the main branch

#### AWS Deployment
1. **ECR Setup**
   ```bash
   aws ecr create-repository --repository-name document-chat
   aws ecr get-login-password | docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com
   ```

2. **Push to ECR**
   ```bash
   docker tag document-chat:latest $AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com/document-chat:latest
   docker push $AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com/document-chat:latest
   ```

3. **Deploy to ECS**
   - Create ECS cluster
   - Define task definition
   - Configure service
   - Set up load balancer

## 🔒 Security Considerations

### Data Protection
- All uploaded files are encrypted at rest
- Temporary files are securely deleted after session expiry
- No permanent storage of user data
- Secure communication with API endpoints

### Session Management
- Automatic session expiry
- Secure session token generation
- Resource cleanup on session end

### API Security
- Secure API key management
- Rate limiting
- Request validation
- Error handling

## 🔧 Configuration Options

### Environment Variables
```env
# API Keys
OPENAI_API_KEY=required
ANTHROPIC_API_KEY=required
GOOGLE_API_KEY=required

# Security
ENCRYPTION_KEY=required
SESSION_EXPIRY=3600

# Vector Database
VECTOR_DB_PROVIDER=faiss
PINECONE_API_KEY=optional
PINECONE_ENVIRONMENT=optional

# Application Settings
MAX_FILE_SIZE=104857600  # 100MB
```

### Advanced Settings
Configurable through the UI:
- Chunk size
- Chunk overlap
- Max context chunks
- Temperature
- Response length

## 📈 Performance Optimization

### Memory Management
- Efficient chunk processing
- Automatic garbage collection
- Memory usage monitoring

### Response Time
- Asynchronous processing
- Efficient embedding search
- Request caching

## 📝 Usage Guide

1. **Upload Documents**
   - Click "Upload PDF Documents" in sidebar
   - Select one or more PDF files
   - Wait for processing completion

2. **Chat Interface**
   - Type questions in the chat input
   - View source references in responses
   - Switch AI models as needed

3. **Document Management**
   - View uploaded documents in sidebar
   - Remove documents when needed
   - Monitor document statistics

4. **Advanced Features**
   - Adjust settings for optimal performance
   - Monitor system metrics
   - View session information

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to the branch
5. Create a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Limitations

- Maximum file size: 100MB per PDF
- Supported file type: PDF only
- Session timeout: 1 hour (configurable)
- Rate limits based on API provider limits

## 🆘 Troubleshooting

Common issues and solutions:
1. **File Upload Errors**
   - Check file size limit
   - Verify PDF format
   - Ensure sufficient memory

2. **API Issues**
   - Verify API keys
   - Check rate limits
   - Monitor API status

3. **Performance Issues**
   - Adjust chunk settings
   - Monitor memory usage
   - Check system resources

## 📞 Support

For enterprise support:
- Email: support@your-org.com
- Documentation: docs.your-org.com
- Issue Tracker: GitHub Issues