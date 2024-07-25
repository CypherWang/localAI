
# LocalAI Chat Application

This is a simple chat application built with Flask, simulating a ChatGPT-like interface. It uses a local language model API
to generate responses and stores chat history in an SQLite database.

## Project Structure

```
LocalAI/
├── app.py
├── static/
│   ├── images/
│   │   ├── user-avatar.png
│   │   └── assistant-avatar.png
│   ├── styles.css
│   ├── script.js
│   └── admin.js
├── templates/
│   ├── index.html
│   └── admin.html
├── chat.db
```

## Features

- Chat with a local language model.
- Store chat history in an SQLite database.
- View and manage chat sessions.
- Create new chat sessions and modify session names.

## Installation

1. **Clone the repository**
    ```bash
    git clone https://github.com/CypherWang/localAI.git
    cd localAI
    ```

2. **Create a virtual environment and activate it**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. **Install the dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4. **Initialize the database**
    ```python
    python -c "from app import init_db; init_db()"
    ```

## Usage

1. **Start the Flask server**
    ```bash
    python app.py
    ```

2. **Access the application in your web browser**
    - Chat interface: `http://127.0.0.1:5000`
    - Admin interface: `http://127.0.0.1:5000/admin`

## API Endpoints

- `/`: Home page, chat interface.
- `/chat`: Endpoint for sending and receiving chat messages.
- `/sessions`: Retrieve all chat sessions.
- `/history/<int:session_id>`: Retrieve chat history for a specific session.
- `/admin`: Admin page, view all chat history.
- `/admin/data`: Endpoint to get all chat history data.
- `/session`: Endpoint to create a new chat session.
- `/session/<int:session_id>`: Endpoint to update the name of a chat session.

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any changes.

## Acknowledgments

- Flask: [Flask](https://flask.palletsprojects.com/)
- SQLite: [SQLite](https://www.sqlite.org/index.html)
- Language Model API: [Local Language Model API](http://localhost:1234)
```
