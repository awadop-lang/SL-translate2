const express = require('express');
const { GoogleGenerativeAI } = require("@google/generative-ai");

const app = express();
app.use(express.json());

app.post('/translate', async (req, res) => {
    try {
        const { prompt, password } = req.body;

        if (password !== process.env.HUD_PASSWORD) {
            return res.status(403).json({ text: "Erreur: Mot de passe incorrect." });
        }

        const apiKey = process.env.GEMINI_API_KEY;
        const genAI = new GoogleGenerativeAI(apiKey);

        // CHANGEMENT ICI : On utilise "gemini-1.5-flash" mais avec une initialisation simplifiée
        const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });

        // Utilisation de la méthode la plus compatible
        const result = await model.generateContent(prompt);
        const response = await result.response;
        const text = response.text();

        res.json({ text: text });

    } catch (err) {
        console.error(err);
        // Si gemini-1.5-flash échoue, on tente le fallback gemini-pro
        res.status(500).json({ text: "ERREUR GOOGLE: " + err.message });
    }
});

const PORT = process.env.PORT || 8080;
app.listen(PORT, '0.0.0.0', () => {
    console.log("Serveur corrigé prêt.");
});
