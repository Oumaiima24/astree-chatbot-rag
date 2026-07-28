require("dotenv").config();
const express = require("express");
const cors = require("cors");
const chatRoutes = require("./routes/chat");

const app = express();

app.use(cors());
app.use(express.json());

// ─────────────────────────────────────────
// Routes
// ─────────────────────────────────────────
app.use("/api/chat", chatRoutes);

app.get("/", (req, res) => {
  res.json({ status: "ok", service: "Astree Chatbot API" });
});

// ─────────────────────────────────────────
// Gestion des erreurs globales
// ─────────────────────────────────────────
app.use((req, res) => {
  res.status(404).json({ error: "Route non trouvée" });
});

app.use((err, req, res, next) => {
  console.error(err);
  res.status(500).json({ error: "Erreur interne du serveur" });
});

// ─────────────────────────────────────────
// Lancement du serveur
// ─────────────────────────────────────────
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(` API démarrée sur http://localhost:${PORT}`);
});