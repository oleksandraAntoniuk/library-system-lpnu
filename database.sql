CREATE DATABASE IF NOT EXISTS library_selfservice
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE library_selfservice;

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    student_id VARCHAR(50) UNIQUE,
    role ENUM('reader', 'librarian', 'admin') NOT NULL DEFAULT 'reader',
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE books (
    book_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    publish_year INT,
    category VARCHAR(100),
    description TEXT,
    available BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE reservations (
    reservation_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    book_id INT NOT NULL,
    reservation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('active', 'cancelled', 'completed') NOT NULL DEFAULT 'active',
    CONSTRAINT fk_reservation_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_reservation_book
        FOREIGN KEY (book_id) REFERENCES books(book_id)
        ON DELETE CASCADE
);
CREATE TABLE loans (
    loan_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    book_id INT NOT NULL,
    borrow_date DATE NOT NULL,
    due_date DATE NOT NULL,
    return_date DATE NULL,
    status ENUM('borrowed', 'returned', 'overdue') NOT NULL DEFAULT 'borrowed',
    CONSTRAINT fk_loan_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_loan_book
        FOREIGN KEY (book_id) REFERENCES books(book_id)
        ON DELETE CASCADE
);

CREATE TABLE fines (
    fine_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    loan_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    reason VARCHAR(255) NOT NULL,
    status ENUM('unpaid', 'paid') NOT NULL DEFAULT 'unpaid',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_fine_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_fine_loan
        FOREIGN KEY (loan_id) REFERENCES loans(loan_id)
        ON DELETE CASCADE
);

CREATE TABLE notifications (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    message TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_notification_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE
);

CREATE TABLE admin_actions (
    action_id INT AUTO_INCREMENT PRIMARY KEY,
    admin_id INT NOT NULL,
    action_type VARCHAR(100) NOT NULL,
    target_table VARCHAR(100) NOT NULL,
    target_id INT,
    description TEXT,
    action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_admin_action_user
        FOREIGN KEY (admin_id) REFERENCES users(user_id)
        ON DELETE CASCADE
);

USE library_selfservice;

INSERT INTO users (full_name, email, student_id, role, password_hash) VALUES
('Іван Петренко', 'ivan.petrenko@lpnu.ua', 'AB14589631', 'reader', 'hashedpass1'),
('Марія Іванова', 'maria.ivanova@lpnu.ua', 'CD25874196', 'reader', 'hashedpass2'),
('Олег Сидоров', 'oleh.sydorov@lpnu.ua', 'EF36985214', 'reader', 'hashedpass3'),
('Анна Ковальчук', 'anna.kovalchuk@lpnu.ua', NULL, 'admin', 'hashedpass4'),
('Павло Лисенко', 'pavlo.lysenko@lpnu.ua', 'GH74125896', 'reader', 'hashedpass5');

INSERT INTO books (title, author, publish_year, category, description, available) VALUES
('Database Systems', 'Ramez Elmasri', 2016, 'Databases', 'Підручник з баз даних', TRUE),
('Artificial Intelligence: A Modern Approach', 'Stuart Russell', 2021, 'Artificial Intelligence', 'Книга зі штучного інтелекту', TRUE),
('Computer Networks', 'Andrew S. Tanenbaum', 2019, 'Networking', 'Книга з комп’ютерних мереж', TRUE),
('Introduction to Algorithms', 'Thomas H. Cormen', 2022, 'Algorithms', 'Підручник з алгоритмів', TRUE),
('Operating System Concepts', 'Abraham Silberschatz', 2018, 'Operating Systems', 'Книга з операційних систем', FALSE);

INSERT INTO reservations (user_id, book_id, status) VALUES
(1, 3, 'active'),
(2, 1, 'active'),
(3, 4, 'cancelled');

INSERT INTO loans (user_id, book_id, borrow_date, due_date, return_date, status) VALUES
(1, 2, '2026-03-01', '2026-03-15', NULL, 'borrowed'),
(3, 4, '2026-03-02', '2026-03-16', '2026-03-14', 'returned'),
(5, 1, '2026-03-03', '2026-03-17', NULL, 'borrowed');

INSERT INTO fines (user_id, loan_id, amount, reason, status) VALUES
(1, 1, 50.00, 'late return', 'unpaid'),
(3, 2, 20.00, 'book damage', 'paid');

INSERT INTO notifications (user_id, message, is_read) VALUES
(1, 'Нагадування: поверніть книгу до 15.03.2026', FALSE),
(2, 'Книга доступна для отримання після бронювання', TRUE),
(3, 'Вам нараховано штраф за прострочення', FALSE);

INSERT INTO admin_actions (admin_id, action_type, target_table, target_id, description) VALUES
(4, 'add_book', 'books', 5, 'Додано нову книгу в каталог'),
(4, 'update_book_status', 'books', 5, 'Змінено статус доступності книги'),
(4, 'issue_fine', 'fines', 1, 'Нараховано штраф користувачу');

SELECT * FROM users;

SELECT * FROM books;
SELECT * FROM reservations;
SELECT * FROM loans;
SELECT * FROM fines;
SELECT * FROM notifications;
SELECT * FROM admin_actions;

INSERT INTO books (title, author, publish_year, category, description, available)
VALUES ('TEST BOOK', 'TEST AUTHOR', 2026, 'TEST', 'перевірка підключення', true);
