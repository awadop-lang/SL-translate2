const express = require('express');
const { GoogleGenerativeAI } = require("@google/generative-ai");
const app = express();
app.use(express.json());

// Initialisation de l'IA
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

app.post('/translate', async (req, res) => {
    try {
        const { prompt, password } = req.body;

        if (password !== process.env.HUD_PASSWORD) {
            return res.status(403).json({ error: "Interdit" });
        }

        const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });
        
        // On envoie une requête simple
        const result = await model.generateContent(prompt);
        const response = await result.response;
        const text = response.text();

        res.json({ text: text });
    } catch (error) {
        // CE LOG EST CRUCIAL : Il s'affichera dans Railway
        console.error("ERREUR GEMINI DETECTEE :");
        console.error(error.message); 
        res.status(500).json({ error: "L'IA a crashé : " + error.message });
    }
});

const PORT = process.env.PORT || 8080;
app.listen(PORT, '0.0.0.0', () => {
    console.log("Serveur en ligne sur le port " + PORT);
});
