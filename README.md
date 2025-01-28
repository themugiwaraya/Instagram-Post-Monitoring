# Instagram-Post-Monitoring
This script monitors likes and comments on a specific Instagram post in real time. It saves initial likes and comments to a MongoDB database and continuously updates the database with new likes and comments.

## Features
- Saves initial likes and comments for a given Instagram post.
- Periodically checks for new likes and comments.
- Stores all data in MongoDB for further analysis.
- Handles authentication and session management for Instagram.
- Gracefully handles script termination.

---

## Prerequisites

1. **Python 3.8+**
   - Install Python from [python.org](https://www.python.org/downloads/).

2. **MongoDB**
   - Install and run a local MongoDB server. You can download it from [mongodb.com](https://www.mongodb.com/try/download/community).

3. **Python Dependencies**
   Install the required Python packages using `pip`:

   ```bash
   pip install instagrapi pymongo
   ```

---

## Installation

1. Clone or download this repository.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Ensure your MongoDB server is running locally.

---

## Configuration

1. **MongoDB Connection**:
   Ensure your MongoDB instance is accessible at `mongodb://localhost:27017/`.

2. **Instagram Credentials**:
   Replace the placeholders in the script with your Instagram credentials:
   ```python
   username = "test_acccount123"
   password = "testaccaunt123!"
   ```

3. **Session File**:
   The script uses a `session.json` file to store session data for Instagram. Make sure the script has write permissions in the directory to create this file.

---

## Usage

1. Run the script:
   ```bash
   python script_name.py
   ```

2. Enter the Instagram post URL when prompted.
3. The script will begin monitoring the post for likes and comments. Press `Ctrl+C` to stop the script.

---

## Data Structure

### MongoDB Collections

1. **`likes` Collection**:
   Stores data about users who liked the post.
   - Example document:
     ```json
     {
       "username": "example_user",
       "full_name": "Example Name",
       "user_id": 123456789,
       "liked_at": "2025-01-27T12:34:56",
       "media_id": "1234567890123456789"
     }
     ```

2. **`comments` Collection**:
   Stores data about comments on the post.
   - Example document:
     ```json
     {
       "username": "example_user",
       "full_name": "Example Name",
       "user_id": 123456789,
       "comment_text": "Nice post!",
       "comment_id": 987654321,
       "media_id": "1234567890123456789",
       "commented_at": "2025-01-27T12:34:56"
     }
     ```

---

## Script Details

### Main Functions

- **`ensure_login`**: Manages Instagram login and session.
- **`save_initial_likers`**: Saves initial likes for the post to MongoDB.
- **`save_initial_comments`**: Saves initial comments for the post to MongoDB.
- **`check_new_likers`**: Checks and saves new likes.
- **`check_new_comments`**: Checks and saves new comments.
- **`signal_handler`**: Handles graceful termination of the script.

### Execution Flow

1. The script authenticates with Instagram.
2. It saves initial likes and comments to MongoDB.
3. It enters a loop, checking for new likes and comments every 30 seconds.
4. The loop can be terminated with `Ctrl+C`.
