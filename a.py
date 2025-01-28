from instagrapi import Client
from pymongo import MongoClient
from datetime import datetime
import time
import signal
import sys

# Подключение к MongoDB
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["instagram_db"]
likes_collection = db["likes"]
comments_collection = db["comments"]

# Подключение к Instagram
cl = Client()
username = "test_acccount123"
password = "testaccaunt123!"
session_file = "session.json"

running = True

def signal_handler(sig, frame):
    """Обработчик для корректного завершения скрипта"""
    global running
    print("\nЗавершение мониторинга...")
    running = False
    cl.logout()
    mongo_client.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def ensure_login():
    """Функция для проверки и обновления авторизации"""
    try:
        if not cl.user_id:
            print("Выполняем вход в аккаунт...")
            cl.login(username, password)
            cl.dump_settings(session_file)
            print("Успешный вход в аккаунт")
        return True
    except Exception as e:
        print(f"Ошибка при входе: {e}")
        try:
            print("Пробуем войти повторно...")
            cl.login(username, password)
            cl.dump_settings(session_file)
            print("Повторный вход успешен")
            return True
        except Exception as e:
            print(f"Ошибка при повторном входе: {e}")
            return False

def save_initial_likers(media_id):
    """Сохраняет начальные лайки"""
    print("Сохранение существующих лайков...")
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
                print(f"Сохранен пользователь: {user.username}")
            else:
                print(f"Пользователь {user.username} уже существует в базе данных.")
            saved_likers.add(user.pk)
            time.sleep(2)
        return saved_likers
    except Exception as e:
        print(f"Ошибка при сохранении лайков: {e}")
        return set()

def save_initial_comments(media_id):
    """Сохраняет начальные комментарии"""
    print("Сохранение существующих комментариев...")
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
                    print(f"Сохранен комментарий от пользователя: {comment.user.username}")
                else:
                    print(f"Комментарий от {comment.user.username} уже существует в базе данных.")
                last_comment_id = max(last_comment_id, comment_id)
            except ValueError as e:
                print(f"Ошибка при обработке ID комментария: {e}")
                continue
            time.sleep(2)
        return last_comment_id
    except Exception as e:
        print(f"Ошибка при сохранении комментариев: {e}")
        return 0

def check_new_likers(media_id, known_likers):
    """Проверяет и сохраняет новых лайкеров"""
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
                    print(f"Новый лайк от пользователя: {user.username}")
                new_likers.append(user.pk)
                
        return known_likers.union(set(new_likers))
    except Exception as e:
        print(f"Ошибка при проверке новых лайков: {e}")
        return known_likers

def check_new_comments(media_id, last_comment_id):
    """Проверяет и сохраняет новые комментарии"""
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
                        print(f"Новый комментарий от пользователя: {comment.user.username}")
                    new_last_comment_id = comment_id
            except ValueError as e:
                print(f"Ошибка при обработке ID комментария: {e}")
                continue
                
        return new_last_comment_id
    except Exception as e:
        print(f"Ошибка при проверке новых комментариев: {e}")
        return last_comment_id

def main():
    """Основная функция"""
    if not ensure_login():
        print("Не удалось войти в аккаунт. Завершение работы.")
        return

    post_url = input("Введите ссылку на пост Instagram: ")
    try:
        media_id = cl.media_pk_from_url(post_url)
        
        # Сохранение начальных данных
        existing_likers = save_initial_likers(media_id)
        last_comment_id = save_initial_comments(media_id)
        
        print("\nНачинаем мониторинг новых лайков и комментариев...")
        while running:
            existing_likers = check_new_likers(media_id, existing_likers)
            last_comment_id = check_new_comments(media_id, last_comment_id)
            time.sleep(30)

    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        cl.logout()
        mongo_client.close()

if __name__ == "__main__":
    main()
