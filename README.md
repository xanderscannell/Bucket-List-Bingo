# Bucket List Bingo - Flask Backend Edition

A family-friendly bucket list bingo application with Flask backend for multi-device sync!

## Features

- 🎯 **Create Custom Bingo Cards** - Add 24 personalized bucket list items
- 🎲 **Visual Randomizer** - Fun animated randomization of your bingo card
- 👥 **Multi-User Support** - Create and manage multiple users/family members
- 📊 **Statistics & Leaderboards** - Track progress with:
  - Items completed leaderboard
  - Bingos achieved leaderboard
  - Visual overview of all users' cards
- 💾 **Automatic Sync** - Access your cards from any device on your network
- 🏆 **Bingo Detection** - Automatically counts rows, columns, and diagonals
- 🖨️ **Print Support** - Print your bingo cards

## What's New?

This version replaces localStorage with a Flask backend and SQLite database, enabling:
- ✅ Access your bingo cards from any device
- ✅ Automatic sync across all devices
- ✅ Centralized family data storage
- ✅ No more losing data when clearing browser cache
- ✅ Real-time statistics and leaderboards

## Quick Start

### 1. Install Python

Make sure you have Python 3.8 or higher installed. Check with:
```bash
python --version
```

### 2. Install Dependencies

Open a terminal in this folder and run:
```bash
pip install -r requirements.txt
```

### 3. Run the Server

Start the Flask server:
```bash
python app.py
```

You should see:
```
* Running on http://0.0.0.0:5000
```

### 4. Access the Application

Open your browser and go to:
```
http://localhost:5000
```

That's it! Your family can now access the bingo app from any device on your local network.

## Migrating Old Data

If you have data from the old localStorage version:

1. Make sure the Flask server is running
2. Open the old HTML file (`bucket_list_bingo.html`) in your browser
3. Open `migrate_localStorage.html` in another tab
4. Follow the migration instructions on the page

## Accessing from Other Devices

### On Your Local Network

1. Find your computer's IP address:
   - **Windows**: Open Command Prompt and run `ipconfig`, look for "IPv4 Address"
   - **Mac/Linux**: Open Terminal and run `ifconfig` or `ip addr`

2. On other devices (phones, tablets, other computers), open a browser and go to:
   ```
   http://YOUR_IP_ADDRESS:5000
   ```
   For example: `http://192.168.1.100:5000`

### Hosting on the Internet

To make this accessible from anywhere (not just your local network), you can deploy it to:

- **PythonAnywhere** (Free tier available): https://www.pythonanywhere.com/
- **Render** (Free tier available): https://render.com/
- **Heroku** (Paid): https://www.heroku.com/
- **Your own server** with a static IP

## How to Use

1. **Create a User** - Click "Create New Card" and fill in your name and 24 bucket list items
2. **Randomize** - Click the "Randomize!" button to shuffle your card (one-time only)
3. **Mark Progress** - Click on cells as you complete items
4. **View Statistics** - Check the "Leaderboard" tab to see:
   - Rankings by items completed
   - Rankings by bingos achieved
   - Visual overview of all users' progress
5. **Switch Users** - Use the "Switch User" tab to view or manage different family members

## Project Structure

```
bucket_list_bingo/
├── app.py                        # Flask application with API endpoints
├── models.py                     # Database models (Users, BingoData, Progress)
├── config.py                     # Configuration settings
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── migrate_localStorage.html     # Migration tool for old data
├── bingo.db                      # SQLite database (created automatically)
├── static/
│   └── index.html               # Frontend application
└── bucket_list_bingo.html       # Old version (for reference/migration)
```

## API Endpoints

The Flask backend provides these REST API endpoints:

- `GET /api/users` - Get all users
- `POST /api/users` - Create new user with bingo data
- `GET /api/users/<user_id>` - Get specific user
- `DELETE /api/users/<user_id>` - Delete user and all data
- `GET /api/users/<user_id>/data` - Get user's bingo items
- `PUT /api/users/<user_id>/data` - Update user's bingo items
- `GET /api/users/<user_id>/progress` - Get user's progress
- `PUT /api/users/<user_id>/progress` - Update user's progress
- `POST /api/users/<user_id>/randomize` - Mark card as randomized
- `POST /api/users/<user_id>/reset-progress` - Reset user's progress

## Database

The application uses SQLite (stored in `bingo.db`) with three tables:

- **users** - User information (id, name, created_at)
- **bingo_data** - Bingo card items for each user
- **progress** - Marked cells and randomization status

## Troubleshooting

### Port 5000 already in use?

Change the port in `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Change to 5001 or any available port
```

### Can't connect from another device?

1. Make sure your firewall allows connections on port 5000
2. Verify both devices are on the same network
3. Try using your computer's IP address instead of `localhost`

### Database errors?

Delete `bingo.db` and restart the server - it will create a fresh database.

## Development

### Debug Mode

The server runs in debug mode by default. For production, change in `app.py`:
```python
app.run(debug=False, host='0.0.0.0', port=5000)
```

### Secret Key

For production, set a secure secret key as an environment variable:
```bash
export SECRET_KEY="your-super-secret-random-key-here"
```

## Credits

Built with Flask, SQLAlchemy, and lots of family fun! 🎉
