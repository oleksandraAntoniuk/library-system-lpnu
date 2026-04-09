const mysql = require("mysql2");

const db = mysql.createConnection({
  host: "127.0.0.1",
  user: "root",
  password: "root",
  database: "library_selfservice",
  port: 3307
});

db.connect((err) => {
  if (err) {
    console.log("Помилка підключення до MySQL:", err.message);
  } else {
    console.log("Підключення до MySQL успішне");
  }
});

module.exports = db;