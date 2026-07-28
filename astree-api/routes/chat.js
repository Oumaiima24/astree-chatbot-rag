const express = require("express");
const axios = require("axios");

const router = express.Router();

const RAG_SERVICE_URL = process.env.RAG_SERVICE_URL || "http://localhost:8000";

// ─────────────────────────────────────────
// POST /api/chat
// Body : { "message": "Comment déclarer un sinistre ?" }
// ─────────────────────────────────────────
router.post("/", async (req, res) => {
  const { message } = req.body;

  // ── Validation ──────────────────────────
  if (!message || typeof message !== "string" || !message.trim()) {
    return res.status(400).json({
      error: "Le champ 'message' est requis et doit être une chaîne non vide."
    });
  }

  try {
    // ── Appel au micro-service Python (RAG) ──
    const response = await axios.post(
      `${RAG_SERVICE_URL}/rag`,
      { message: message.trim() },
      { timeout: 30000 }
    );

    const data = response.data;
    console.log("Réponse FastAPI :", JSON.stringify(data)); // ← ajoute cette ligne

    // ── Cas où le service Python a renvoyé une erreur ──
    if (data.error) {
      return res.status(502).json({
        error: "Erreur du service IA : " + data.error
      });
    }

    // ── Réponse normale ──
    return res.json({
      reponse: data.reponse,
      sources: data.sources || []
    });

  } catch (err) {
    // ── Service Python injoignable ──
    if (err.code === "ECONNREFUSED") {
      return res.status(503).json({
        error: "Le service IA (RAG) est indisponible. Veuillez réessayer plus tard."
      });
    }

    // ── Timeout ──
    if (err.code === "ECONNABORTED") {
      return res.status(504).json({
        error: "Le service IA a mis trop de temps à répondre."
      });
    }

    // ── Autre erreur ──
    console.error("Erreur /api/chat :", err.message);
    return res.status(500).json({
      error: "Une erreur interne est survenue."
    });
  }
});

module.exports = router;