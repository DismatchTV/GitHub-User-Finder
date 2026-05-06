import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
import requests
import json
import os

# Путь к файлу для сохранения избранных пользователей
FAVORITES_FILE = "favorites.json"


def load_favorites():
    """Загружает избранных пользователей из JSON-файла."""
    if os.path.exists(FAVORITES_FILE):
        try:
            with open(FAVORITES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_favorites(favorites):
    """Сохраняет избранных пользователей в JSON-файл."""
    try:
        with open(FAVORITES_FILE, 'w', encoding='utf-8') as f:
            json.dump(favorites, f, ensure_ascii=False, indent=2)
    except IOError as e:
        messagebox.showerror("Ошибка", f"Не удалось сохранить избранные: {e}")


def search_github_user(event=None):  # Добавлен параметр event для привязки к Enter
    """Выполняет поиск пользователя GitHub через API."""
    username = entry_search.get().strip()

    if not username:
        messagebox.showwarning("Предупреждение", "Поле поиска не должно быть пустым!")
        return

    try:
        response = requests.get(f"https://api.github.com/users/{username}",
                                headers={'Accept': 'application/vnd.github.v3+json'})

        if response.status_code == 200:
            user_data = response.json()
            display_user(user_data)
        elif response.status_code == 404:
            messagebox.showerror("Ошибка", "Пользователь не найден!")
            listbox_results.delete(0, tk.END)
            btn_favorite.config(text="Добавить в избранное", state="disabled")
        elif response.status_code == 403:
            messagebox.showerror("Ошибка", "Превышен лимит запросов к GitHub API. Попробуйте позже.")
        else:
            messagebox.showerror("Ошибка", f"Ошибка API: {response.status_code}")
            listbox_results.delete(0, tk.END)

    except requests.RequestException as e:
        messagebox.showerror("Ошибка сети", f"Не удалось подключиться к GitHub API: {e}")


def display_user(user_data):
    """Отображает информацию о найденном пользователе."""
    listbox_results.delete(0, tk.END)

    login = user_data.get('login', 'N/A')
    name = user_data.get('name', 'N/A')
    user_info = f"{login} | {name}"
    listbox_results.insert(tk.END, user_info)

    # Сохраняем текущий логин для последующего использования
    global current_displayed_user
    current_displayed_user = login

    update_favorite_status(login)


def add_to_favorites():
    """Добавляет выбранного пользователя в избранное."""
    # Сначала пробуем получить из результатов поиска
    selection = listbox_results.curselection()
    username = None

    if selection:
        user_info = listbox_results.get(selection[0])
        username = user_info.split(' | ')[0]
    elif current_displayed_user:
        username = current_displayed_user
    else:
        messagebox.showwarning("Предупреждение", "Нет пользователя для добавления в избранное!")
        return

    favorites = load_favorites()

    if any(fav['login'] == username for fav in favorites):
        messagebox.showinfo("Информация", "Пользователь уже в избранном!")
        return

    try:
        response = requests.get(f"https://api.github.com/users/{username}")
        if response.status_code == 200:
            user_data = response.json()
            favorites.append({
                'login': user_data['login'],
                'name': user_data.get('name', 'N/A'),
                'avatar_url': user_data.get('avatar_url', ''),
                'url': user_data.get('html_url', '')
            })
            save_favorites(favorites)
            messagebox.showinfo("Успех", "Пользователь добавлен в избранное!")
            update_favorite_list()
            update_favorite_status(username)
        else:
            messagebox.showerror("Ошибка", "Не удалось получить данные пользователя!")
    except requests.RequestException as e:
        messagebox.showerror("Ошибка", f"Ошибка при добавлении в избранное: {e}")


def update_favorite_list():
    """Обновляет список избранных пользователей."""
    listbox_favorites.delete(0, tk.END)
    favorites = load_favorites()
    for fav in favorites:
        listbox_favorites.insert(tk.END, f"{fav['login']} | {fav['name']}")


def update_favorite_status(username):
    """Обновляет статус избранного для текущего пользователя."""
    if not username:
        btn_favorite.config(text="Добавить в избранное", state="disabled")
        return

    favorites = load_favorites()
    is_favorite = any(fav['login'] == username for fav in favorites)
    btn_favorite.config(
        text="Удалить из избранного" if is_favorite else "Добавить в избранное",
        state="normal"
    )


def toggle_favorite():
    """Переключает статус пользователя в избранном (добавить/удалить)."""
    username = current_displayed_user if current_displayed_user else None

    if not username:
        selection = listbox_results.curselection()
        if selection:
            user_info = listbox_results.get(selection[0])
            username = user_info.split(' | ')[0]

    if not username:
        messagebox.showwarning("Предупреждение", "Нет выбранного пользователя!")
        return

    favorites = load_favorites()
    is_favorite = any(fav['login'] == username for fav in favorites)

    if is_favorite:
        # Удаляем из избранного
        favorites = [fav for fav in favorites if fav['login'] != username]
        save_favorites(favorites)
        messagebox.showinfo("Успех", "Пользователь удалён из избранного!")
    else:
        # Добавляем в избранное
        try:
            response = requests.get(f"https://api.github.com/users/{username}")
            if response.status_code == 200:
                user_data = response.json()
                favorites.append({
                    'login': user_data['login'],
                    'name': user_data.get('name', 'N/A'),
                    'avatar_url': user_data.get('avatar_url', ''),
                    'url': user_data.get('html_url', '')
                })
                save_favorites(favorites)
                messagebox.showinfo("Успех", "Пользователь добавлен в избранное!")
            else:
                messagebox.showerror("Ошибка", "Не удалось получить данные пользователя!")
                return
        except requests.RequestException as e:
            messagebox.showerror("Ошибка", f"Ошибка сети: {e}")
            return

    update_favorite_list()
    update_favorite_status(username)


def remove_from_favorites():
    """Удаляет выбранного пользователя из избранного."""
    selection = listbox_favorites.curselection()
    if not selection:
        messagebox.showwarning("Предупреждение", "Выберите пользователя из списка избранного!")
        return

    favorite_info = listbox_favorites.get(selection[0])
    username = favorite_info.split(' | ')[0]

    favorites = load_favorites()
    favorites = [fav for fav in favorites if fav['login'] != username]
    save_favorites(favorites)
    messagebox.showinfo("Успех", "Пользователь удалён из избранного!")
    update_favorite_list()

    # Обновляем статус кнопки, если этот пользователь сейчас отображается
    if current_displayed_user == username:
        update_favorite_status(None)


def on_favorite_select(event):
    """Обработчик выбора пользователя из списка избранного."""
    selection = listbox_favorites.curselection()
    if not selection:
        return

    favorite_info = listbox_favorites.get(selection[0])
    username = favorite_info.split(' | ')[0]

    # Загружаем актуальные данные пользователя
    try:
        response = requests.get(f"https://api.github.com/users/{username}")
        if response.status_code == 200:
            user_data = response.json()
            display_user(user_data)
            entry_search.delete(0, tk.END)
            entry_search.insert(0, username)
    except requests.RequestException as e:
        messagebox.showerror("Ошибка сети", f"Не удалось загрузить данные: {e}")


# Глобальная переменная для отслеживания текущего отображаемого пользователя
current_displayed_user = None

# Создание главного окна
root = tk.Tk()
root.title("GitHub User Finder")
root.geometry("850x650")

# Настройка расширения виджетов при изменении размера окна
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

# Основной фрейм
main_frame = ttk.Frame(root, padding="10")
main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
main_frame.columnconfigure(1, weight=1)
main_frame.rowconfigure(2, weight=1)
main_frame.rowconfigure(5, weight=1)

# Поле поиска
ttk.Label(main_frame, text="Поиск пользователя GitHub:").grid(row=0, column=0, sticky=tk.W)
entry_search = ttk.Entry(main_frame, width=40)
entry_search.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
entry_search.bind('<Return>', search_github_user)  # Привязка клавиши Enter

btn_search = ttk.Button(main_frame, text="Найти", command=search_github_user)
btn_search.grid(row=0, column=2, padx=5)

# Результаты поиска
ttk.Label(main_frame, text="Результаты поиска:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))

# Frame для listbox с scrollbar
results_frame = ttk.Frame(main_frame)
results_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
results_frame.columnconfigure(0, weight=1)
results_frame.rowconfigure(0, weight=1)

listbox_results = tk.Listbox(results_frame, height=8)
listbox_results.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

scrollbar_results = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=listbox_results.yview)
scrollbar_results.grid(row=0, column=1, sticky=(tk.N, tk.S))
listbox_results['yscrollcommand'] = scrollbar_results.set

# Кнопка переключения избранного (универсальная)
btn_favorite = ttk.Button(main_frame, text="Добавить в избранное", command=toggle_favorite, state="disabled")
btn_favorite.grid(row=3, column=0, columnspan=3, pady=10, sticky=tk.EW)

# Список избранных пользователей
ttk.Label(main_frame, text="Избранные пользователи:").grid(row=4, column=0, sticky=tk.W, pady=(10, 0))

# Frame для favorites listbox с scrollbar
favorites_frame = ttk.Frame(main_frame)
favorites_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
favorites_frame.columnconfigure(0, weight=1)
favorites_frame.rowconfigure(0, weight=1)

listbox_favorites = tk.Listbox(favorites_frame, height=8)
listbox_favorites.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
listbox_favorites.bind('<<ListboxSelect>>', on_favorite_select)  # Клик по избранному загружает пользователя

scrollbar_favorites = ttk.Scrollbar(favorites_frame, orient=tk.VERTICAL, command=listbox_favorites.yview)
scrollbar_favorites.grid(row=0, column=1, sticky=(tk.N, tk.S))
listbox_favorites['yscrollcommand'] = scrollbar_favorites.set

# Кнопка удаления из избранного
btn_remove_favorite = ttk.Button(main_frame, text="Удалить выбранное из избранного", command=remove_from_favorites)
btn_remove_favorite.grid(row=6, column=0, columnspan=3, pady=5, sticky=tk.EW)

# Загрузка начальных данных
update_favorite_list()

# Запуск приложения
root.mainloop()