# AI-Powered Finance Tracker

A modern web application for tracking personal finances with AI-powered insights and predictions.

## Features

- User authentication and secure data storage
- Expense tracking with categories
- Interactive visualizations of spending patterns
- AI-powered spending predictions
- Modern and responsive UI
- Real-time expense analysis

## Setup 

### Docker

1. Clone the repository:
```bash
git clone https://github.com/Hudater/exec-2024.git
cd exec-2024
```

2. Docker compose up
```bash
docker compose up -d
```

3. Enjoy (kind of, very lame app so not much to enjoy :)

visit http://localhost:8080

### Baremetal

1. Clone the repository:
```bash
git clone https://github.com/Hudater/exec-2024.git
cd exec-2024
```

1. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

1. Install the required packages:
```bash
pip install -r requirements.txt
```

1. Initialize the database:
```bash
python app.py
```

1. Open your browser and navigate to `http://localhost:5000`

## Usage

1. Register a new account or login with existing credentials
2. Add your expenses with categories and descriptions
3. View your spending patterns in the dashboard
4. Check the analytics page for visualizations and AI predictions
5. Use the insights to make better financial decisions

## Technologies Used

- Flask (Python web framework)
- SQLAlchemy (Database ORM)
- scikit-learn (Machine Learning)
- Plotly (Interactive visualizations)
- Bootstrap 5 (UI framework)
- Font Awesome (Icons)

## Security Notes

- Change the `SECRET_KEY` in `app.py` before deploying to production
- Use environment variables for sensitive information
- Implement proper password hashing (already included)
- Consider adding rate limiting for production use

## Contributing

Feel free to submit issues and enhancement requests! 