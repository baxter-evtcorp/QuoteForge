# QuoteForge

QuoteForge is a web-based application designed to generate and manage professional-looking quotes and purchase orders. It features a database to save, view, edit, and delete your documents.

## Features

- Create professional quotes and purchase orders.
- Save documents to a database for future access.
- View a list of all existing documents.
- Edit and update saved documents.
- Generate PDFs for any document.
- Dynamically add sections and line items to quotes.
- Upload a company logo to be included in the documents.


## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.x
- Pip (Python package installer)
- WeasyPrint and its dependencies (including Pango). For detailed installation instructions, refer to the [WeasyPrint documentation](https://weasyprint.readthedocs.io/en/stable/install.html).

### Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/QuoteForge.git
    cd QuoteForge
    ```

2.  **Install the required Python packages:**

    ```bash
    pip install -r requirements.txt
    ```

### Running the Application

To start the Flask development server, run the following command:

```bash
python app.py
```

The application will be accessible at `http://127.0.0.1:5001`.

## How to Use

1.  **Create a Document:** Fill out the form for either a quote or a purchase order.
2.  **Save the Document:** Click the "Save Document" button. The new document will appear in the "Existing Documents" list on the right.
3.  **Manage Documents:**
    -   **Generate PDF:** Click the "PDF" button next to any document in the list to generate the PDF.
    -   **Edit:** Click the "Edit" button to load a document's data back into the form for modification.
    -   **Delete:** Click the "Del" button to permanently remove a document.

## Project Structure

- `app.py`: The main Flask application with all the API endpoints.
- `database.py`: Initializes the SQLAlchemy database object.
- `models.py`: Defines the database models for quotes and line items.
- `quotes.db`: The SQLite database file where all data is stored.
- `templates/`: HTML templates for the web interface and PDF output.
- `static/`: CSS and JavaScript files for the frontend.
- `uploads/`: Directory for uploaded company logos.
- `requirements.txt`: Python dependencies.

## Contributing

Contributions are welcome! If you have suggestions for improvements or new features, please feel free to fork the repository and submit a pull request.
