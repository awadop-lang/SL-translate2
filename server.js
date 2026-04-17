const express = require('express');
const { GoogleGenerativeAI } = require("@google/generative-ai");
const app = express();
app.use(express.json());

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

app.post('/translate', async (req, res) => {
    try {
        const { prompt, password } = req.body;
        if (password !== process.env.HUD_PASSWORD) {
            return res.status(403).json({ error: "Accès refusé" });
        }
        const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });
        const result = await model.generateContent(prompt);
        const response = await result.response;
        res.json({ text: response.text() });
    } catch (error) {
        res.status(500).json({ error: "Erreur IA" });
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Serveur prêt sur port ${PORT}`));
