const express = require("express");

const app = express();

app.get("/", (req, res) => {
  res.json({
    status: "ok",
    message: "API running"
  });
});

app.get("/process", (req, res) => {
  const input = req.query.input || null;
  res.json({
    status: "processed",
    input
  });
});

const port = process.env.PORT || 3000;
app.listen(port, () => {
  console.log(`API listening on port ${port}`);
});
