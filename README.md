# Multi-Modal AI Agent with Chain of Thought Reasoning 🤖

A sophisticated AI agent that performs mathematical computations, creates visual outputs, and sends email notifications using LLM-powered chain of thought methodology with modular architecture.

## 🌟 Features

- **Chain of Thought Reasoning**: Step-by-step problem solving with detailed reasoning
- **Multi-Modal Output**: Text, Image, and Email generation capabilities
- **Mathematical Tools**: 18+ mathematical functions including ASCII conversion and exponential calculations
- **Visual Output**: Mac-compatible image creation with text wrapping and formatting
- **Email Integration**: Automated email notifications with Gmail SMTP
- **LLM Integration**: Powered by Google Gemini 2.5 Flash Lite and Gemini 2.0 Flash
- **Modular Architecture**: Clean separation of concerns with Perception, Decision, Action, and Memory modules
- **Error Handling**: Robust error handling with detailed logging and debugging
- **Cross-Platform**: Works on Mac, Windows, and Linux

## 🏗️ Architecture

```
session6/
├── main.py              # Main orchestration and iteration loop
├── perception.py        # LLM-based fact extraction and analysis
├── decision.py          # Response parsing and function call routing
├── action.py            # Tool execution and mathematical operations
├── memory.py            # User preferences and context storage
├── models.py            # Pydantic schemas for validation
├── logs/               # Application logs
│   └── cot_process.log
└── README.md           # This file
```

## 🛠️ Available Tools

### Mathematical Operations
- `add(a, b)` - Add two numbers
- `subtract(a, b)` - Subtract b from a
- `multiply(a, b)` - Multiply two numbers
- `divide(a, b)` - Divide a by b
- `power(a, b)` - Raise a to the power of b
- `sqrt(a)` - Calculate square root
- `cbrt(a)` - Calculate cube root
- `factorial(a)` - Calculate factorial
- `log(a)` - Calculate natural logarithm
- `remainder(a, b)` - Calculate remainder of division

### Trigonometric Functions
- `sin(a)` - Calculate sine (radians)
- `cos(a)` - Calculate cosine (radians)
- `tan(a)` - Calculate tangent (radians)

### Specialized Functions
- `strings_to_chars_to_int(text)` - Convert string to ASCII values
- `int_list_to_exponential_sum(int_list)` - Calculate sum of exponentials
- `fibonacci_numbers(n)` - Generate Fibonacci sequence
- `add_list(numbers)` - Sum a list of numbers

### Reasoning & Verification
- `show_reasoning(steps)` - Display step-by-step reasoning
- `calculate(expression)` - Evaluate mathematical expressions
- `verify(expression, expected)` - Verify calculation results

### Output & Communication
- `create_image_with_text(text, filename)` - Create formatted images with text wrapping
- `open_image_in_preview(filename)` - Open images in Mac Preview
- `send_email(text)` - Send email notifications via Gmail

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- UV package manager
- Google Gemini API key
- Gmail App Password (for email functionality)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd session6
   ```

2. **Install dependencies**
   ```bash
   uv add google-genai python-dotenv rich mcp pillow
   ```

3. **Set up environment variables**
   ```bash
   # Create .env file
   echo "GEMINI_API_KEY=your_gemini_api_key_here" >> .env
   echo "GMAIL_APP_PASSWORD=your_gmail_app_password_here" >> .env
   ```

4. **Run the application**
   ```bash
   uv run main.py
   ```

## 🎯 Usage Examples

### Basic Mathematical Problem
The agent will automatically:
1. Extract ASCII values from "INDIA": `[73, 78, 68, 73, 65]`
2. Calculate sum of exponentials: `e^73 + e^78 + e^68 + e^73 + e^65`
3. Create a formatted image with the result
4. Open the image in Preview (Mac)
5. Send an email with the final answer

### Sample Output
```
╭──────────────────────────────────────────────────────────╮
│ Starting main execution...                               │
╰──────────────────────────────────────────────────────────╯

--- Iteration 1 ---
LLM Response: FUNCTION_CALL: strings_to_chars_to_int|INDIA
Result: [73, 78, 68, 73, 65]

--- Iteration 2 ---
LLM Response: FUNCTION_CALL: int_list_to_exponential_sum|[73, 78, 68, 73, 65]
Result: 7.59982224609308e+33

--- Iteration 3 ---
LLM Response: FUNCTION_CALL: create_image_with_text|7.59982224609308e+33
Image created successfully: final_answer.png

--- Iteration 4 ---
LLM Response: FUNCTION_CALL: send_email|The sum of exponentials is 7.59982224609308e+33
Email sent successfully!
```

## 🔧 Configuration

### Email Setup (Gmail)
1. Enable 2-Factor Authentication on your Gmail account
2. Generate an App Password: Google Account → Security → App Passwords
3. Use the App Password in your `.env` file

### Customizing the Query
Modify the query in `main.py`:
```python
query = """Your custom mathematical problem here"""
```

## 📊 Logging

The application provides comprehensive logging:
- **Console Output**: Real-time progress and results
- **File Logging**: Detailed logs saved to `logs/cot_process.log`
- **Debug Information**: Function calls, parameters, and results
- **Error Tracking**: Detailed error messages and stack traces

## 🎨 Image Generation

The agent creates beautifully formatted images with:
- **Smart Text Wrapping**: Automatically fits text within image bounds
- **Multiple Font Sizes**: Title, main content, and supplementary information
- **Color Coding**: Visual hierarchy with different colors
- **Mac System Fonts**: Uses Arial/Helvetica for consistent appearance
- **Decorative Borders**: Professional-looking frame
- **Context Information**: Shows ASCII breakdown and mathematical formula

## 📧 Email Integration

Automated email notifications include:
- **Professional Subject**: "Email tool sent via Action Module | EAG V2 Assignment 6"
- **Formatted Body**: Clear presentation of results
- **SMTP Security**: SSL encryption for secure transmission
- **Error Handling**: Graceful failure handling with detailed error messages

## 🔍 Error Handling

The application includes robust error handling:
- **Parameter Validation**: Automatic type conversion and validation
- **Timeout Protection**: Prevents hanging on API calls
- **Iteration Limits**: Prevents infinite loops
- **Graceful Degradation**: Continues operation despite individual tool failures
- **Detailed Logging**: Comprehensive error tracking and debugging

## 🏛️ Architecture Details

### Perception Module
- Extracts key facts from user queries
- Provides structured analysis for decision making
- Integrates with Gemini 2.0 Flash for advanced reasoning

### Decision Module
- Parses LLM responses into actionable function calls
- Handles both `FUNCTION_CALL:` and `FINAL_ANSWER:` formats
- Robust error handling for malformed responses

### Action Module
- Executes mathematical and utility functions
- Handles parameter conversion and validation
- Supports both synchronous and asynchronous operations

### Memory Module
- Stores user preferences and context
- Maintains conversation state across iterations
- Supports preference-based customization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Google Gemini API for LLM capabilities
- Rich library for beautiful console output
- Pillow (PIL) for image generation
- MCP (Model Context Protocol) for tool integration
- UV package manager for dependency management

## 📞 Support

For support, email avinash.ai2022@gmail.com or create an issue in the GitHub repository.

---

**Built with ❤️ using Python, Google Gemini, and modern AI agent architecture patterns.**