from instagrapi import Client
from pymongo import MongoClient
from datetime import datetime
import time
import signal
import sys

# MongoDB connection
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["instagram_db"]
likes_collection = db["likes"]
comments_collection = db["comments"]

# Instagram connection
cl = Client()
username = "test_acccount123"
password = "testaccaunt123!"
session_file = "session.json"

running = True

def signal_handler(sig, frame):
    """Handler for graceful script termination"""
    global running
    print("\nTerminating monitoring...")
    running = False
    cl.logout()
    mongo_client.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def ensure_login():
    """Function to check and refresh authentication"""
    try:
        if not cl.user_id:
            print("Logging into the account...")
            cl.login(username, password)
            cl.dump_settings(session_file)
            print("Successfully logged in")
        return True
    except Exception as e:
        print(f"Login error: {e}")
        try:
            print("Retrying login...")
            cl.login(username, password)
            cl.dump_settings(session_file)
            print("Retry login successful")
            return True
        except Exception as e:
            print(f"Retry login error: {e}")
            return False

def save_initial_likers(media_id):
    """Saves initial likes"""
    print("Saving existing likes...")
    try:
        if not ensure_login():
            return set()
        
        likers = cl.media_likers(media_id)
        saved_likers = set()
        for user in likers:
            user_data = {
                "username": user.username,
                "full_name": user.full_name,
                "user_id": user.pk,
                "liked_at": datetime.now().isoformat(),
                "media_id": media_id
            }
            if not likes_collection.find_one({"user_id": user.pk, "media_id": media_id}):
                likes_collection.insert_one(user_data)
                print(f"User saved: {user.username}")
            else:
                print(f"User {user.username} already exists in the database.")
            saved_likers.add(user.pk)
            time.sleep(2)
        return saved_likers
    except Exception as e:
        print(f"Error saving likes: {e}")
        return set()

def save_initial_comments(media_id):
    """Saves initial comments"""
    print("Saving existing comments...")
    try:
        if not ensure_login():
            return None
            
        comments = cl.media_comments(media_id)
        last_comment_id = 0
        for comment in comments:
            try:
                comment_id = int(str(comment.pk))
                user_data = {
                    "username": comment.user.username,
                    "full_name": comment.user.full_name,
                    "user_id": comment.user.pk,
                    "comment_text": comment.text,
                    "comment_id": comment_id,
                    "media_id": media_id,
                    "commented_at": datetime.now().isoformat()
                }
                if not comments_collection.find_one({"comment_id": comment_id, "media_id": media_id}):
                    comments_collection.insert_one(user_data)
                    print(f"Comment saved from user: {comment.user.username}")
                else:
                    print(f"Comment from {comment.user.username} already exists in the database.")
                last_comment_id = max(last_comment_id, comment_id)
            except ValueError as e:
                print(f"Error processing comment ID: {e}")
                continue
            time.sleep(2)
        return last_comment_id
    except Exception as e:
        print(f"Error saving comments: {e}")
        return 0

def check_new_likers(media_id, known_likers):
    """Checks and saves new likers"""
    try:
        if not ensure_login():
            return known_likers
            
        current_likers = cl.media_likers(media_id)
        new_likers = []
        
        for user in current_likers:
            if user.pk not in known_likers:
                user_data = {
                    "username": user.username,
                    "full_name": user.full_name,
                    "user_id": user.pk,
                    "liked_at": datetime.now().isoformat(),
                    "media_id": media_id
                }
                if not likes_collection.find_one({"user_id": user.pk, "media_id": media_id}):
                    likes_collection.insert_one(user_data)
                    print(f"New like from user: {user.username}")
                new_likers.append(user.pk)
                
        return known_likers.union(set(new_likers))
    except Exception as e:
        print(f"Error checking new likes: {e}")
        return known_likers

def check_new_comments(media_id, last_comment_id):
    """Checks and saves new comments"""
    try:
        if not ensure_login():
            return last_comment_id
            
        comments = cl.media_comments(media_id)
        new_last_comment_id = last_comment_id
        
        for comment in comments:
            try:
                comment_id = int(str(comment.pk)) 
                if comment_id > new_last_comment_id:
                    user_data = {
                        "username": comment.user.username,
                        "full_name": comment.user.full_name,
                        "user_id": comment.user.pk,
                        "comment_text": comment.text,
                        "comment_id": comment_id,
                        "media_id": media_id,
                        "commented_at": datetime.now().isoformat()
                    }
                    if not comments_collection.find_one({"comment_id": comment_id, "media_id": media_id}):
                        comments_collection.insert_one(user_data)
                        print(f"New comment from user: {comment.user.username}")
                    new_last_comment_id = comment_id
            except ValueError as e:
                print(f"Error processing comment ID: {e}")
                continue
                
        return new_last_comment_id
    except Exception as e:
        print(f"Error checking new comments: {e}")
        return last_comment_id

def main():
    """Main function"""
    if not ensure_login():
        print("Failed to log in. Exiting.")
        return

    post_url = input("Enter Instagram post URL: ")
    try:
        media_id = cl.media_pk_from_url(post_url)
        
        # Save initial data
        existing_likers = save_initial_likers(media_id)
        last_comment_id = save_initial_comments(media_id)
        
        print("\nStarting monitoring of new likes and comments...")
        while running:
            existing_likers = check_new_likers(media_id, existing_likers)
            last_comment_id = check_new_comments(media_id, last_comment_id)
            time.sleep(30)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        cl.logout()
        mongo_client.close()

if __name__ == "__main__":
    main()
