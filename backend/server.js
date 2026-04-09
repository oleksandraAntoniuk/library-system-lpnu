const db = require("./db");
const express = require("express");
const app = express();
const PORT = 5001;

app.use(express.json());

// Локальні тестові користувачі для входу
// login залишаємо простим, щоб не ламати авторизацію
const loginUsers = [
  { id: 1, name: "Іван Петренко", email: "reader@library.local", password: "1234", student_id: "AB14589631", role: "reader" },
  { id: 2, name: "Марія Іванова", email: "maria.ivanova.pp.2023@lpnu.ua", password: "1234", student_id: "CD25874196", role: "reader" },
  { id: 3, name: "Олег Сидоров", email: "oleh.sydorov.pp.2022@lpnu.ua", password: "1234", student_id: "EF36985214", role: "reader" },
  { id: 4, name: "Анна Ковальчук", email: "admin@library.local", password: "admin", role: "admin" },
  { id: 5, name: "Павло Лисенко", email: "pavlo.lysenko.pp.2021@lpnu.ua", password: "1234", student_id: "GH74125896", role: "reader" }
];

// Допоміжна функція для нормалізації статусів
function normalizeStatus(status) {
  if (status === "cancelled") return "canceled";
  return status;
}

// Перевірка API + БД
app.get("/api/health", (req, res) => {
  db.query("SELECT 1", (err) => {
    if (err) {
      return res.status(500).json({
        status: "error",
        db: false,
        error: err.message
      });
    }

    res.json({
      status: "ok",
      db: true,
      port: PORT
    });
  });
});

// Головна сторінка
app.get("/", (req, res) => {
  res.send("Library API server is running");
});

// Авторизація
app.post("/api/login", (req, res) => {
  const { email, password } = req.body;

  const user = loginUsers.find(u => u.email === email && u.password === password);

  if (!user) {
    return res.status(401).json({ error: "Невірний логін або пароль" });
  }

  res.json({
    id: user.id,
    name: user.name,
    email: user.email,
    role: user.role,
    student_id: user.student_id || null
  });
});

// Книги — MySQL
app.get("/api/books", (req, res) => {
  const search = (req.query.search || "").toLowerCase().trim();

  let query = `
    SELECT
      book_id AS id,
      title,
      author,
      publish_year AS year,
      category,
      description,
      available
    FROM books
  `;
  let params = [];

  if (search) {
    query += `
      WHERE LOWER(title) LIKE ?
         OR LOWER(author) LIKE ?
         OR LOWER(category) LIKE ?
    `;
    const s = `%${search}%`;
    params = [s, s, s];
  }

  query += " ORDER BY book_id";

  db.query(query, params, (err, results) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    res.json(results);
  });
});

app.get("/api/books/:id", (req, res) => {
  db.query(
    `
    SELECT
      book_id AS id,
      title,
      author,
      publish_year AS year,
      category,
      description,
      available
    FROM books
    WHERE book_id = ?
    `,
    [req.params.id],
    (err, results) => {
      if (err) {
        return res.status(500).json({ error: err.message });
      }

      if (results.length === 0) {
        return res.status(404).json({ error: "Книгу не знайдено" });
      }

      res.json(results[0]);
    }
  );
});

app.post("/api/books", (req, res) => {
  const { title, author, year, category } = req.body;

  if (!title || !author || !year || !category) {
    return res.status(400).json({ error: "Не всі поля книги заповнені" });
  }

  const sql = `
    INSERT INTO books (title, author, publish_year, category, available)
    VALUES (?, ?, ?, ?, ?)
  `;

  db.query(sql, [title, author, Number(year), category, true], (err, result) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }

    res.status(201).json({
      id: result.insertId,
      title,
      author,
      year: Number(year),
      category,
      available: true
    });
  });
});

app.patch("/api/books/:id", (req, res) => {
  if (typeof req.body.available !== "boolean") {
    return res.status(400).json({ error: "Поле available має бути true або false" });
  }

  db.query(
    "UPDATE books SET available = ? WHERE book_id = ?",
    [req.body.available, req.params.id],
    (err, result) => {
      if (err) {
        return res.status(500).json({ error: err.message });
      }

      if (result.affectedRows === 0) {
        return res.status(404).json({ error: "Книгу не знайдено" });
      }

      db.query(
        `
        SELECT
          book_id AS id,
          title,
          author,
          publish_year AS year,
          category,
          description,
          available
        FROM books
        WHERE book_id = ?
        `,
        [req.params.id],
        (err2, results) => {
          if (err2) {
            return res.status(500).json({ error: err2.message });
          }
          res.json(results[0]);
        }
      );
    }
  );
});

// Користувачі — MySQL
app.get("/api/users", (req, res) => {
  db.query(
    `
    SELECT
      user_id AS id,
      full_name AS name,
      email,
      student_id,
      role
    FROM users
    ORDER BY user_id
    `,
    (err, results) => {
      if (err) {
        return res.status(500).json({ error: err.message });
      }
      res.json(results);
    }
  );
});

app.get("/api/users/:id", (req, res) => {
  db.query(
    `
    SELECT
      user_id AS id,
      full_name AS name,
      email,
      student_id,
      role
    FROM users
    WHERE user_id = ?
    `,
    [req.params.id],
    (err, results) => {
      if (err) {
        return res.status(500).json({ error: err.message });
      }

      if (results.length === 0) {
        return res.status(404).json({ error: "Користувача не знайдено" });
      }

      res.json(results[0]);
    }
  );
});

// Бронювання — MySQL
app.get("/api/reservations", (req, res) => {
  const userId = req.query.user_id;

  let query = `
    SELECT
      reservation_id AS id,
      user_id,
      book_id,
      status
    FROM reservations
  `;
  let params = [];

  if (userId) {
    query += " WHERE user_id = ?";
    params.push(userId);
  }

  query += " ORDER BY reservation_id";

  db.query(query, params, (err, results) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }

    const normalized = results.map(r => ({
      ...r,
      status: normalizeStatus(r.status)
    }));

    res.json(normalized);
  });
});

app.post("/api/reservations", (req, res) => {
  const { user_id, book_id } = req.body;

  if (!user_id || !book_id) {
    return res.status(400).json({ error: "Потрібно передати user_id та book_id" });
  }

  db.query(
    "SELECT user_id FROM users WHERE user_id = ?",
    [user_id],
    (errUser, userResults) => {
      if (errUser) {
        return res.status(500).json({ error: errUser.message });
      }

      if (userResults.length === 0) {
        return res.status(404).json({ error: "Користувача не знайдено" });
      }

      db.query(
        `
        SELECT
          book_id AS id,
          title,
          available
        FROM books
        WHERE book_id = ?
        `,
        [book_id],
        (errBook, bookResults) => {
          if (errBook) {
            return res.status(500).json({ error: errBook.message });
          }

          if (bookResults.length === 0) {
            return res.status(404).json({ error: "Книгу не знайдено" });
          }

          const book = bookResults[0];

          if (!book.available) {
            return res.status(400).json({ error: "Книга недоступна для бронювання" });
          }

          db.query(
            `
            SELECT reservation_id
            FROM reservations
            WHERE user_id = ? AND book_id = ? AND status = 'active'
            `,
            [user_id, book_id],
            (errExisting, existingResults) => {
              if (errExisting) {
                return res.status(500).json({ error: errExisting.message });
              }

              if (existingResults.length > 0) {
                return res.status(400).json({ error: "Ця книга вже заброньована цим користувачем" });
              }

              db.query(
                `
                INSERT INTO reservations (user_id, book_id, status)
                VALUES (?, ?, 'active')
                `,
                [user_id, book_id],
                (errInsert, insertResult) => {
                  if (errInsert) {
                    return res.status(500).json({ error: errInsert.message });
                  }

                  db.query(
                    "UPDATE books SET available = false WHERE book_id = ?",
                    [book_id],
                    (errUpdateBook) => {
                      if (errUpdateBook) {
                        return res.status(500).json({ error: errUpdateBook.message });
                      }

                      db.query(
                        `
                        INSERT INTO notifications (user_id, message, is_read)
                        VALUES (?, ?, false)
                        `,
                        [user_id, `Книгу "${book.title}" успішно заброньовано`],
                        (errNotification) => {
                          if (errNotification) {
                            return res.status(500).json({ error: errNotification.message });
                          }

                          res.status(201).json({
                            id: insertResult.insertId,
                            user_id: Number(user_id),
                            book_id: Number(book_id),
                            status: "active"
                          });
                        }
                      );
                    }
                  );
                }
              );
            }
          );
        }
      );
    }
  );
});

// Видачі — MySQL
app.get("/api/loans", (req, res) => {
  const userId = req.query.user_id;

  let query = `
    SELECT
      loan_id AS id,
      user_id,
      book_id,
      borrow_date,
      due_date,
      return_date,
      status
    FROM loans
  `;
  let params = [];

  if (userId) {
    query += " WHERE user_id = ?";
    params.push(userId);
  }

  query += " ORDER BY loan_id";

  db.query(query, params, (err, results) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    res.json(results);
  });
});

app.post("/api/loans", (req, res) => {
  const { user_id, book_id } = req.body;

  if (!user_id || !book_id) {
    return res.status(400).json({ error: "Потрібно передати user_id та book_id" });
  }

  db.query(
    "SELECT user_id FROM users WHERE user_id = ?",
    [user_id],
    (errUser, userResults) => {
      if (errUser) {
        return res.status(500).json({ error: errUser.message });
      }

      if (userResults.length === 0) {
        return res.status(404).json({ error: "Користувача не знайдено" });
      }

      db.query(
        `
        SELECT
          book_id AS id,
          title,
          available
        FROM books
        WHERE book_id = ?
        `,
        [book_id],
        (errBook, bookResults) => {
          if (errBook) {
            return res.status(500).json({ error: errBook.message });
          }

          if (bookResults.length === 0) {
            return res.status(404).json({ error: "Книгу не знайдено" });
          }

          const book = bookResults[0];

          if (!book.available) {
            return res.status(400).json({ error: "Книга недоступна для видачі" });
          }

          db.query(
            `
            INSERT INTO loans (user_id, book_id, borrow_date, due_date, return_date, status)
            VALUES (?, ?, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY), NULL, 'borrowed')
            `,
            [user_id, book_id],
            (errInsert, insertResult) => {
              if (errInsert) {
                return res.status(500).json({ error: errInsert.message });
              }

              db.query(
                "UPDATE books SET available = false WHERE book_id = ?",
                [book_id],
                (errUpdateBook) => {
                  if (errUpdateBook) {
                    return res.status(500).json({ error: errUpdateBook.message });
                  }

                  db.query(
                    `
                    INSERT INTO notifications (user_id, message, is_read)
                    VALUES (?, ?, false)
                    `,
                    [user_id, `Ви отримали книгу "${book.title}"`],
                    (errNotification) => {
                      if (errNotification) {
                        return res.status(500).json({ error: errNotification.message });
                      }

                      res.status(201).json({
                        id: insertResult.insertId,
                        user_id: Number(user_id),
                        book_id: Number(book_id),
                        status: "borrowed"
                      });
                    }
                  );
                }
              );
            }
          );
        }
      );
    }
  );
});

app.patch("/api/loans/:id/return", (req, res) => {
  db.query(
    `
    SELECT
      loan_id AS id,
      user_id,
      book_id,
      status
    FROM loans
    WHERE loan_id = ?
    `,
    [req.params.id],
    (errLoan, loanResults) => {
      if (errLoan) {
        return res.status(500).json({ error: errLoan.message });
      }

      if (loanResults.length === 0) {
        return res.status(404).json({ error: "Видачу не знайдено" });
      }

      const loan = loanResults[0];

      if (loan.status === "returned") {
        return res.status(400).json({ error: "Книга вже повернена" });
      }

      db.query(
        `
        UPDATE loans
        SET status = 'returned',
            return_date = CURDATE()
        WHERE loan_id = ?
        `,
        [req.params.id],
        (errUpdateLoan) => {
          if (errUpdateLoan) {
            return res.status(500).json({ error: errUpdateLoan.message });
          }

          db.query(
            "UPDATE books SET available = true WHERE book_id = ?",
            [loan.book_id],
            (errUpdateBook) => {
              if (errUpdateBook) {
                return res.status(500).json({ error: errUpdateBook.message });
              }

              db.query(
                `
                SELECT fine_id
                FROM fines
                WHERE loan_id = ? AND status = 'unpaid'
                `,
                [loan.id],
                (errFineCheck, fineCheckResults) => {
                  if (errFineCheck) {
                    return res.status(500).json({ error: errFineCheck.message });
                  }

                  const addFineIfNeeded = (callback) => {
                    if (fineCheckResults.length > 0) {
                      return callback();
                    }

                    db.query(
                      `
                      INSERT INTO fines (user_id, loan_id, amount, reason, status)
                      VALUES (?, ?, ?, ?, 'unpaid')
                      `,
                      [loan.user_id, loan.id, 50, "late return"],
                      (errFineInsert) => {
                        if (errFineInsert) {
                          return res.status(500).json({ error: errFineInsert.message });
                        }
                        callback();
                      }
                    );
                  };

                  addFineIfNeeded(() => {
                    db.query(
                      `
                      INSERT INTO notifications (user_id, message, is_read)
                      VALUES (?, ?, false)
                      `,
                      [loan.user_id, "Книгу повернуто. Перевірте інформацію щодо штрафу."],
                      (errNotification) => {
                        if (errNotification) {
                          return res.status(500).json({ error: errNotification.message });
                        }

                        res.json({
                          id: loan.id,
                          user_id: loan.user_id,
                          book_id: loan.book_id,
                          status: "returned"
                        });
                      }
                    );
                  });
                }
              );
            }
          );
        }
      );
    }
  );
});

// Штрафи — MySQL
app.get("/api/fines", (req, res) => {
  const userId = req.query.user_id;

  let query = `
    SELECT
      fine_id AS id,
      user_id,
      loan_id,
      amount,
      reason,
      status
    FROM fines
  `;
  let params = [];

  if (userId) {
    query += " WHERE user_id = ?";
    params.push(userId);
  }

  query += " ORDER BY fine_id";

  db.query(query, params, (err, results) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    res.json(results);
  });
});

// Сповіщення — MySQL
app.get("/api/notifications", (req, res) => {
  const userId = req.query.user_id;

  let query = `
    SELECT
      notification_id AS id,
      user_id,
      message,
      is_read AS read
    FROM notifications
  `;
  let params = [];

  if (userId) {
    query += " WHERE user_id = ?";
    params.push(userId);
  }

  query += " ORDER BY notification_id";

  db.query(query, params, (err, results) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    res.json(results);
  });
});

app.patch("/api/notifications/:id/read", (req, res) => {
  db.query(
    "UPDATE notifications SET is_read = true WHERE notification_id = ?",
    [req.params.id],
    (err, result) => {
      if (err) {
        return res.status(500).json({ error: err.message });
      }

      if (result.affectedRows === 0) {
        return res.status(404).json({ error: "Сповіщення не знайдено" });
      }

      db.query(
        `
        SELECT
          notification_id AS id,
          user_id,
          message,
          is_read AS read
        FROM notifications
        WHERE notification_id = ?
        `,
        [req.params.id],
        (err2, results) => {
          if (err2) {
            return res.status(500).json({ error: err2.message });
          }
          res.json(results[0]);
        }
      );
    }
  );
});

// Admin actions — MySQL
app.get("/api/admin_actions", (req, res) => {
  db.query(
    `
    SELECT
      action_id AS id,
      admin_id,
      action_type AS action,
      target_table,
      target_id,
      description,
      action_time
    FROM admin_actions
    ORDER BY action_id
    `,
    (err, results) => {
      if (err) {
        return res.status(500).json({ error: err.message });
      }
      res.json(results);
    }
  );
});

app.listen(PORT, () => {
  console.log(`Server started on http://localhost:${PORT}`);
});