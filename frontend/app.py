import tkinter as tk
from tkinter import ttk, messagebox
import requests

API_DEFAULT = "http://localhost:5001/api"
APP_TITLE = 'ІС "Національна бібліотека Львівська політехніка"'


class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def _extract_error(self, response):
        try:
            data = response.json()
            if isinstance(data, dict) and "error" in data:
                return data["error"]
        except Exception:
            pass
        return f"{response.status_code} {response.reason}"

    def get(self, endpoint: str, **params):
        r = requests.get(f"{self.base_url}{endpoint}", params=params, timeout=5)
        if not r.ok:
            raise Exception(self._extract_error(r))
        return r.json()

    def post(self, endpoint: str, payload: dict):
        r = requests.post(f"{self.base_url}{endpoint}", json=payload, timeout=5)
        if not r.ok:
            raise Exception(self._extract_error(r))
        return r.json()

    def patch(self, endpoint: str, payload: dict):
        r = requests.patch(f"{self.base_url}{endpoint}", json=payload, timeout=5)
        if not r.ok:
            raise Exception(self._extract_error(r))
        return r.json()

    def login(self, email: str, password: str):
        return self.post("/login", {"email": email, "password": password})

    def health(self):
        return self.get("/health")

    def books(self, search: str = ""):
        if search:
            return self.get("/books", search=search)
        return self.get("/books")

    def reservations(self, user_id: int):
        return self.get("/reservations", user_id=user_id)

    def reserve(self, user_id: int, book_id: int):
        return self.post("/reservations", {"user_id": user_id, "book_id": book_id})

    def loans(self, user_id: int):
        return self.get("/loans", user_id=user_id)

    def return_loan(self, loan_id: int):
        return self.patch(f"/loans/{loan_id}/return", {})

    def fines(self, user_id: int):
        return self.get("/fines", user_id=user_id)

    def notifications(self, user_id: int):
        return self.get("/notifications", user_id=user_id)

    def mark_notification_read(self, notification_id: int):
        return self.patch(f"/notifications/{notification_id}/read", {})

    def add_book(self, title: str, author: str, year: int, category: str):
        return self.post("/books", {
            "title": title,
            "author": author,
            "year": year,
            "category": category
        })

    def toggle_book_availability(self, book_id: int, available: bool):
        return self.patch(f"/books/{book_id}", {"available": available})


class LibraryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1320x860")
        self.minsize(1100, 760)
        self.configure(bg="#eef4fb")

        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass
        self.setup_styles()

        self.client = None
        self.user = None
        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Не авторизовано")
        self.book_map = {}

        self.bind("<Return>", lambda e: self.refresh_books() if self.user else self.do_login())

        self.build_login_screen()

    def setup_styles(self):
        self.option_add("*Font", ("Segoe UI", 10))
        self.style.configure("TNotebook", background="#eef4fb", borderwidth=0)
        self.style.configure("TNotebook.Tab", padding=(16, 10), font=("Segoe UI", 10, "bold"))
        self.style.configure("Treeview", rowheight=30, font=("Segoe UI", 10))
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        self.style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"))

    def clear_root(self):
        for widget in self.winfo_children():
            widget.destroy()

    def build_login_screen(self):
        self.clear_root()
        self.geometry("620x420")

        outer = tk.Frame(self, bg="#eef4fb")
        outer.pack(fill="both", expand=True, padx=24, pady=24)

        card = tk.Frame(outer, bg="white", highlightthickness=1, highlightbackground="#d7e3f4")
        card.pack(fill="both", expand=True)

        tk.Label(
            card,
            text="Вхід до бібліотечної системи",
            font=("Segoe UI", 18, "bold"),
            bg="white",
            fg="#183b63"
        ).pack(pady=(24, 20))

        form = tk.Frame(card, bg="white")
        form.pack(fill="x", padx=28)

        self.email_var = tk.StringVar(value="reader@library.local")
        self.password_var = tk.StringVar(value="1234")
        self.api_var = tk.StringVar(value=API_DEFAULT)

        fields = [
            ("Email", self.email_var, ""),
            ("Пароль", self.password_var, "*"),
            ("API URL", self.api_var, "")
        ]

        for i, (label, var, show) in enumerate(fields):
            tk.Label(
                form,
                text=label,
                bg="white",
                fg="#24496f",
                font=("Segoe UI", 11, "bold")
            ).grid(row=i * 2, column=0, sticky="w", pady=(0, 6))

            entry = ttk.Entry(form, textvariable=var, show=show, font=("Segoe UI", 11))
            entry.grid(row=i * 2 + 1, column=0, sticky="ew", pady=(0, 14), ipady=6)

        form.grid_columnconfigure(0, weight=1)

        ttk.Button(card, text="Увійти", command=self.do_login).pack(fill="x", padx=28, pady=(6, 8), ipady=8)

        hint = "Тестові входи:\nreader@library.local / 1234\nadmin@library.local / admin"
        tk.Label(
            card,
            text=hint,
            bg="white",
            fg="#5a6f86",
            justify="left",
            font=("Segoe UI", 10)
        ).pack(anchor="w", padx=28, pady=(8, 24))

    def do_login(self):
        email = self.email_var.get().strip()
        password = self.password_var.get().strip()
        api_url = self.api_var.get().strip()

        if not email or not password or not api_url:
            messagebox.showwarning("Увага", "Заповни всі поля.")
            return

        try:
            self.client = ApiClient(api_url)
            self.client.health()
            self.user = self.client.login(email, password)
            self.build_main_ui()
            self.refresh_all()
        except Exception as exc:
            messagebox.showerror("Помилка входу", f"Не вдалося увійти:\n{exc}")

    def build_main_ui(self):
        self.clear_root()
        self.geometry("1320x860")

        self.build_header()
        self.build_stats()
        self.build_tabs()
        self.build_footer()

    def build_header(self):
        header = tk.Frame(self, bg="#17324d")
        header.pack(fill="x")

        left = tk.Frame(header, bg="#17324d")
        left.pack(side="left", padx=18, pady=14)

        tk.Label(left, text=APP_TITLE, bg="#17324d", fg="white",
                 font=("Segoe UI", 18, "bold")).pack(anchor="w")
        tk.Label(left, text="Клієнтський застосунок на Python Tkinter",
                 bg="#17324d", fg="#c8d8ea", font=("Segoe UI", 10)).pack(anchor="w")

        right = tk.Frame(header, bg="#17324d")
        right.pack(side="right", padx=18, pady=14)

        role_text = "Адміністратор" if self.user.get("role") == "admin" else "Читач"
        tk.Label(right, text=self.user.get("name", "Користувач"),
                 bg="#17324d", fg="white", font=("Segoe UI", 11, "bold")).pack(anchor="e")
        tk.Label(right, text=f"Роль: {role_text}",
                 bg="#17324d", fg="#c8d8ea", font=("Segoe UI", 10)).pack(anchor="e")

        center = tk.Frame(header, bg="#17324d")
        center.pack(side="right", padx=(0, 20), pady=14)
        ttk.Button(center, text="Оновити все", command=self.refresh_all).pack()

    def build_stats(self):
        self.stats_wrap = tk.Frame(self, bg="#eef4fb")
        self.stats_wrap.pack(fill="x", padx=14, pady=(14, 8))

    def stat_card(self, parent, title, value, note):
        card = tk.Frame(parent, bg="white", highlightthickness=1, highlightbackground="#d7e3f4")
        card.pack(side="left", fill="both", expand=True, padx=6)
        tk.Label(card, text=title, bg="white", fg="#5b6d80",
                 font=("Segoe UI", 10)).pack(anchor="w", padx=16, pady=(14, 4))
        tk.Label(card, text=value, bg="white", fg="#17324d",
                 font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=16)
        tk.Label(card, text=note, bg="white", fg="#8697aa",
                 font=("Segoe UI", 9)).pack(anchor="w", padx=16, pady=(2, 14))

    def build_tabs(self):
        wrap = tk.Frame(self, bg="#eef4fb")
        wrap.pack(fill="both", expand=True, padx=14, pady=8)

        self.nb = ttk.Notebook(wrap)
        self.nb.pack(fill="both", expand=True)

        self.tab_books = ttk.Frame(self.nb)
        self.tab_res = ttk.Frame(self.nb)
        self.tab_loans = ttk.Frame(self.nb)
        self.tab_notes = ttk.Frame(self.nb)
        self.nb.add(self.tab_books, text="Каталог")
        self.nb.add(self.tab_res, text="Бронювання")
        self.nb.add(self.tab_loans, text="Видачі та штрафи")
        self.nb.add(self.tab_notes, text="Сповіщення")

        if self.user.get("role") == "admin":
            self.tab_admin = ttk.Frame(self.nb)
            self.nb.add(self.tab_admin, text="Адміністрування")
            self.build_admin_tab()

        self.build_books_tab()
        self.build_res_tab()
        self.build_loans_tab()
        self.build_notes_tab()

    def build_footer(self):
        footer = tk.Frame(self, bg="#17324d")
        footer.pack(fill="x", side="bottom")
        tk.Label(footer, textvariable=self.status_var, bg="#17324d",
                 fg="#c8d8ea").pack(side="left", padx=12, pady=8)

    def build_books_tab(self):
        outer = tk.Frame(self.tab_books, bg="#eef4fb")
        outer.pack(fill="both", expand=True)

        top = tk.Frame(outer, bg="#eef4fb")
        top.pack(fill="x", padx=10, pady=10)
        ttk.Entry(top, textvariable=self.search_var).pack(side="left", fill="x", expand=True)
        ttk.Button(top, text="Пошук", command=self.refresh_books).pack(side="left", padx=8)
        ttk.Button(top, text="Забронювати", command=self.reserve_selected,
                   style="Accent.TButton").pack(side="right")

        body = tk.PanedWindow(outer, orient="horizontal", sashrelief="flat", bg="#eef4fb")
        body.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        left = tk.Frame(body, bg="white", highlightthickness=1, highlightbackground="#d7e3f4")
        right = tk.Frame(body, bg="white", highlightthickness=1, highlightbackground="#d7e3f4")
        body.add(left, minsize=580)
        body.add(right, minsize=260)

        cols = ("id", "title", "author", "year", "category", "available")
        self.books_tree = ttk.Treeview(left, columns=cols, show="headings")
        headers = {
            "id": "ID",
            "title": "Назва",
            "author": "Автор",
            "year": "Рік",
            "category": "Категорія",
            "available": "Статус"
        }
        widths = {"id": 50, "title": 300, "author": 200, "year": 70, "category": 130, "available": 110}
        for c in cols:
            self.books_tree.heading(c, text=headers[c])
            self.books_tree.column(c, width=widths[c], anchor="center")
        self.books_tree.column("title", anchor="w")
        self.books_tree.column("author", anchor="w")
        self.books_tree.pack(fill="both", expand=True, padx=8, pady=8)
        self.books_tree.bind("<<TreeviewSelect>>", self.show_book_details)

        tk.Label(right, text="Інформація про книгу", bg="white", fg="#17324d",
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=14, pady=(14, 8))
        self.book_details = tk.Text(right, wrap="word", relief="flat", bg="white",
                                    font=("Segoe UI", 10))
        self.book_details.pack(fill="both", expand=True, padx=14, pady=(0, 14))

    def build_res_tab(self):
        outer = tk.Frame(self.tab_res, bg="#eef4fb")
        outer.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Button(outer, text="Оновити", command=self.refresh_reservations).pack(anchor="ne", pady=(0, 8))

        box = tk.Frame(outer, bg="white", highlightthickness=1, highlightbackground="#d7e3f4")
        box.pack(fill="both", expand=True)

        cols = ("id", "title", "status")
        self.res_tree = ttk.Treeview(box, columns=cols, show="headings")
        for col, name, width, anchor in [
            ("id", "ID", 80, "center"),
            ("title", "Назва книги", 420, "w"),
            ("status", "Статус", 160, "center")
        ]:
            self.res_tree.heading(col, text=name)
            self.res_tree.column(col, width=width, anchor=anchor)
        self.res_tree.pack(fill="both", expand=True, padx=8, pady=8)

    def build_loans_tab(self):
        outer = tk.Frame(self.tab_loans, bg="#eef4fb")
        outer.pack(fill="both", expand=True, padx=10, pady=10)

        top = tk.Frame(outer, bg="#eef4fb")
        top.pack(fill="x")
        ttk.Button(top, text="Оновити", command=self.refresh_loans_and_fines).pack(side="left")
        ttk.Button(top, text="Повернути книгу", command=self.return_selected_loan).pack(side="right")

        content = tk.PanedWindow(outer, orient="vertical", sashrelief="flat", bg="#eef4fb")
        content.pack(fill="both", expand=True, pady=(10, 0))

        loans_box = tk.Frame(content, bg="white", highlightthickness=1, highlightbackground="#d7e3f4")
        fines_box = tk.Frame(content, bg="white", highlightthickness=1, highlightbackground="#d7e3f4")
        content.add(loans_box, minsize=240)
        content.add(fines_box, minsize=220)

        tk.Label(loans_box, text="Видачі", bg="white", fg="#17324d",
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=12, pady=(12, 0))

        loan_table_wrap = tk.Frame(loans_box, bg="white")
        loan_table_wrap.pack(fill="both", expand=True, padx=8, pady=8)

        loan_scroll_y = ttk.Scrollbar(loan_table_wrap, orient="vertical")
        loan_scroll_y.pack(side="right", fill="y")

        self.loan_tree = ttk.Treeview(
            loan_table_wrap,
            columns=("id", "title", "status"),
            show="headings",
            height=8,
            yscrollcommand=loan_scroll_y.set
        )
        loan_scroll_y.config(command=self.loan_tree.yview)

        for col, name, width, anchor in [
            ("id", "ID", 80, "center"),
            ("title", "Назва книги", 420, "w"),
            ("status", "Статус", 180, "center")
        ]:
            self.loan_tree.heading(col, text=name)
            self.loan_tree.column(col, width=width, anchor=anchor)
        self.loan_tree.pack(side="left", fill="both", expand=True)

        tk.Label(fines_box, text="Штрафи", bg="white", fg="#17324d",
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=12, pady=(12, 0))

        fine_table_wrap = tk.Frame(fines_box, bg="white")
        fine_table_wrap.pack(fill="both", expand=True, padx=8, pady=8)

        fine_scroll_y = ttk.Scrollbar(fine_table_wrap, orient="vertical")
        fine_scroll_y.pack(side="right", fill="y")

        self.fine_tree = ttk.Treeview(
            fine_table_wrap,
            columns=("id", "amount", "reason", "status"),
            show="headings",
            height=7,
            yscrollcommand=fine_scroll_y.set
        )
        fine_scroll_y.config(command=self.fine_tree.yview)

        for col, name, width, anchor in [
            ("id", "ID", 80, "center"),
            ("amount", "Сума", 100, "center"),
            ("reason", "Причина", 360, "w"),
            ("status", "Статус", 120, "center")
        ]:
            self.fine_tree.heading(col, text=name)
            self.fine_tree.column(col, width=width, anchor=anchor)
        self.fine_tree.pack(side="left", fill="both", expand=True)

    def build_notes_tab(self):
        outer = tk.Frame(self.tab_notes, bg="#eef4fb")
        outer.pack(fill="both", expand=True, padx=10, pady=10)

        top = tk.Frame(outer, bg="#eef4fb")
        top.pack(fill="x")
        ttk.Button(top, text="Оновити", command=self.refresh_notifications).pack(side="left")
        ttk.Button(top, text="Позначити вибране як прочитане",
                   command=self.mark_selected_note).pack(side="right")

        box = tk.Frame(outer, bg="white", highlightthickness=1, highlightbackground="#d7e3f4")
        box.pack(fill="both", expand=True, pady=(10, 0))

        self.note_tree = ttk.Treeview(box, columns=("id", "message", "read"), show="headings")
        for col, name, width, anchor in [
            ("id", "ID", 80, "center"),
            ("message", "Повідомлення", 760, "w"),
            ("read", "Статус", 120, "center")
        ]:
            self.note_tree.heading(col, text=name)
            self.note_tree.column(col, width=width, anchor=anchor)
        self.note_tree.pack(fill="both", expand=True, padx=8, pady=8)

    def build_admin_tab(self):
        outer = tk.Frame(self.tab_admin, bg="#eef4fb")
        outer.pack(fill="both", expand=True, padx=10, pady=10)

        card = tk.Frame(outer, bg="white", highlightthickness=1, highlightbackground="#d7e3f4")
        card.pack(fill="both", expand=True)

        tk.Label(card, text="Додати нову книгу", bg="white", fg="#17324d",
                 font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=16, pady=(16, 12))

        form = tk.Frame(card, bg="white")
        form.pack(fill="x", padx=16, pady=(0, 16))

        self.admin_title = tk.StringVar()
        self.admin_author = tk.StringVar()
        self.admin_year = tk.StringVar()
        self.admin_category = tk.StringVar()

        fields = [
            ("Назва", self.admin_title),
            ("Автор", self.admin_author),
            ("Рік", self.admin_year),
            ("Категорія", self.admin_category),
        ]
        for i, (label, var) in enumerate(fields):
            tk.Label(form, text=label, bg="white", fg="#24496f",
                     font=("Segoe UI", 10, "bold")).grid(row=i, column=0, sticky="w", pady=6)
            ttk.Entry(form, textvariable=var).grid(row=i, column=1, sticky="ew", pady=6, padx=(12, 0), ipady=5)
        form.grid_columnconfigure(1, weight=1)

        ttk.Button(form, text="Додати книгу", command=self.add_book,
                   style="Accent.TButton").grid(row=len(fields), column=1, sticky="w", pady=(12, 0))

        tk.Label(card, text="Список книг", bg="white", fg="#17324d",
                 font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=16, pady=(20, 10))

        admin_table_wrap = tk.Frame(card, bg="white")
        admin_table_wrap.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self.admin_books_tree = ttk.Treeview(
            admin_table_wrap,
            columns=("id", "title", "author", "year", "available"),
            show="headings",
            height=8
        )
        for col, name, width, anchor in [
            ("id", "ID", 60, "center"),
            ("title", "Назва", 280, "w"),
            ("author", "Автор", 180, "w"),
            ("year", "Рік", 80, "center"),
            ("available", "Статус", 120, "center")
        ]:
            self.admin_books_tree.heading(col, text=name)
            self.admin_books_tree.column(col, width=width, anchor=anchor)

        self.admin_books_tree.pack(fill="both", expand=True)

        ttk.Button(
            card,
            text="Змінити доступність вибраної книги",
            command=self.toggle_selected_book_availability
        ).pack(anchor="w", padx=16, pady=(0, 16))

    def clear_tree(self, tree):
        for item in tree.get_children():
            tree.delete(item)

    def get_book_title_by_id(self, book_id):
        try:
            row = self.book_map.get(int(book_id))
            if row:
                return row.get("title", f"Книга #{book_id}")
        except Exception:
            pass
        return f"Книга #{book_id}"

    def translate_status(self, status):
        status_map = {
            "active": "Активне",
            "canceled": "Скасовано",
            "cancelled": "Скасовано",
            "borrowed": "Видано",
            "returned": "Повернено",
            "unpaid": "Не сплачено",
            "paid": "Сплачено"
        }
        return status_map.get(str(status).lower(), status)

    def toggle_selected_book_availability(self):
        selected = self.admin_books_tree.selection()
        if not selected:
            messagebox.showwarning("Увага", "Оберіть книгу.")
            return

        item = self.admin_books_tree.item(selected[0], "values")
        book_id = int(item[0])
        current_available = item[4] == "Доступна"

        if not messagebox.askyesno(
            "Підтвердження",
            f"Змінити статус книги на {'Недоступна' if current_available else 'Доступна'}?"
        ):
            return

        try:
            self.client.toggle_book_availability(book_id, not current_available)
            messagebox.showinfo("Готово", "Статус книги оновлено.")
            self.refresh_all()
        except Exception as exc:
            messagebox.showerror("Помилка", str(exc))

    def refresh_all(self):
        self.refresh_stats()
        self.refresh_books()
        self.refresh_reservations()
        self.refresh_loans_and_fines()
        self.refresh_notifications()
        if self.user.get("role") == "admin":
            self.refresh_admin_books()

    def refresh_stats(self):
        for w in self.stats_wrap.winfo_children():
            w.destroy()

        books = self.client.books()
        res = self.client.reservations(self.user["id"])
        loans = self.client.loans(self.user["id"])
        fines = self.client.fines(self.user["id"])
        unpaid = sum(float(f.get("amount", 0)) for f in fines if f.get("status") == "unpaid")

        self.stat_card(self.stats_wrap, "Усього книг", str(len(books)), "каталог бібліотеки")
        self.stat_card(self.stats_wrap, "Доступні", str(sum(1 for b in books if b.get("available"))), "можна бронювати")
        self.stat_card(self.stats_wrap, "Бронювання", str(sum(1 for r in res if r.get("status") == "active")), "активні")
        self.stat_card(self.stats_wrap, "Видачі", str(sum(1 for l in loans if l.get("status") == "borrowed")), "неповернуті")
        self.stat_card(self.stats_wrap, "Штрафи", f"{int(unpaid)} грн", "несплачені")
        self.status_var.set(f"Підключено до API: {self.client.base_url}")

    def refresh_books(self):
        self.clear_tree(self.books_tree)
        self.book_map.clear()
        rows = self.client.books(self.search_var.get().strip())

        for row in rows:
            self.book_map[int(row["id"])] = row
            self.books_tree.insert("", "end", values=(
                row.get("id"),
                row.get("title", ""),
                row.get("author", ""),
                row.get("year", ""),
                row.get("category", ""),
                "Доступна" if row.get("available") else "Недоступна",
            ))

        self.book_details.delete("1.0", tk.END)

    def show_book_details(self, _event=None):
        selected = self.books_tree.selection()
        if not selected:
            return

        values = self.books_tree.item(selected[0], "values")
        book_id = int(values[0])
        row = self.book_map.get(book_id, {})

        txt = (
            f"Назва: {row.get('title', '-')}\n"
            f"Автор: {row.get('author', '-')}\n"
            f"Рік: {row.get('year', '-')}\n"
            f"Категорія: {row.get('category', '-')}\n"
            f"Опис: {row.get('description', '-')}\n"
            f"Статус: {'доступна' if row.get('available') else 'недоступна'}\n"
        )
        self.book_details.delete("1.0", tk.END)
        self.book_details.insert(tk.END, txt)

    def reserve_selected(self):
        selected = self.books_tree.selection()
        if not selected:
            messagebox.showwarning("Увага", "Оберіть книгу.")
            return

        book_id = int(self.books_tree.item(selected[0], "values")[0])
        book_title = self.get_book_title_by_id(book_id)

        if not messagebox.askyesno("Підтвердження", f'Забронювати книгу "{book_title}"?'):
            return

        try:
            self.client.reserve(self.user["id"], book_id)
            messagebox.showinfo("Готово", "Книгу успішно заброньовано.")
            self.refresh_all()
        except Exception as exc:
            messagebox.showerror("Помилка", str(exc))

    def refresh_reservations(self):
        self.clear_tree(self.res_tree)
        for row in self.client.reservations(self.user["id"]):
            self.res_tree.insert("", "end", values=(
                row.get("id", "-"),
                self.get_book_title_by_id(row.get("book_id", "-")),
                self.translate_status(row.get("status", "-")),
            ))

    def refresh_loans_and_fines(self):
        self.clear_tree(self.loan_tree)
        self.clear_tree(self.fine_tree)

        for row in self.client.loans(self.user["id"]):
            self.loan_tree.insert("", "end", values=(
                row.get("id", "-"),
                self.get_book_title_by_id(row.get("book_id", "-")),
                self.translate_status(row.get("status", "-")),
            ))

        for row in self.client.fines(self.user["id"]):
            self.fine_tree.insert("", "end", values=(
                row.get("id", "-"),
                row.get("amount", "-"),
                row.get("reason", "-"),
                self.translate_status(row.get("status", "-")),
            ))

    def return_selected_loan(self):
        selected = self.loan_tree.selection()
        if not selected:
            messagebox.showwarning("Увага", "Оберіть видачу.")
            return

        loan_id = int(self.loan_tree.item(selected[0], "values")[0])
        book_title = self.loan_tree.item(selected[0], "values")[1]

        if not messagebox.askyesno("Підтвердження", f'Повернути книгу "{book_title}"?'):
            return

        try:
            self.client.return_loan(loan_id)
            messagebox.showinfo("Готово", "Книгу повернуто.")
            self.refresh_all()
        except Exception as exc:
            messagebox.showerror("Помилка", str(exc))

    def refresh_notifications(self):
        self.clear_tree(self.note_tree)
        for row in self.client.notifications(self.user["id"]):
            self.note_tree.insert("", "end", values=(
                row.get("id", "-"),
                row.get("message", "-"),
                "Прочитано" if row.get("read") else "Непрочитано",
            ))

    def mark_selected_note(self):
        selected = self.note_tree.selection()
        if not selected:
            messagebox.showwarning("Увага", "Оберіть сповіщення.")
            return

        nid = int(self.note_tree.item(selected[0], "values")[0])
        try:
            self.client.mark_notification_read(nid)
            self.refresh_notifications()
        except Exception as exc:
            messagebox.showerror("Помилка", str(exc))

    def add_book(self):
        title = self.admin_title.get().strip()
        author = self.admin_author.get().strip()
        year = self.admin_year.get().strip()
        category = self.admin_category.get().strip()

        if not title or not author or not year or not category:
            messagebox.showwarning("Увага", "Заповни всі поля.")
            return

        if not year.isdigit():
            messagebox.showwarning("Увага", "Рік має бути числом.")
            return

        try:
            self.client.add_book(title, author, int(year), category)
            self.admin_title.set("")
            self.admin_author.set("")
            self.admin_year.set("")
            self.admin_category.set("")
            messagebox.showinfo("Готово", "Книгу додано.")
            self.refresh_all()
        except Exception as exc:
            messagebox.showerror("Помилка", str(exc))

    def refresh_admin_books(self):
        if not hasattr(self, "admin_books_tree"):
            return

        self.clear_tree(self.admin_books_tree)
        for row in self.client.books():
            self.admin_books_tree.insert("", "end", values=(
                row.get("id", "-"),
                row.get("title", ""),
                row.get("author", ""),
                row.get("year", ""),
                "Доступна" if row.get("available") else "Недоступна"
            ))


if __name__ == "__main__":
    app = LibraryApp()
    app.mainloop()