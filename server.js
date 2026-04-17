const express = require('express');
const https = require('https');
const app = express();
app.use(express.json());

app.post('/translate', async (req, res) => {
    const { prompt, password } = req.body;

    if (password !== process.env.HUD_PASSWORD) {
        return res.status(403).json({ text: "Erreur: Pass" });
    }

    const apiKey = process.env.GEMINI_API_KEY;
    const data = JSON.stringify({
        contents: [{ parts: [{ text: prompt }] }]
    });

    const options = {
        hostname: 'generativelanguage.googleapis.com',
        path: `/v1beta/models/gemini-1.5-flash:generateContent?key=${apiKey}`,
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    };

    const request = https.request(options, (response) => {
        let str = '';
        response.on('data', (chunk) => { str += chunk; });
        response.on('end', () => {
            try {
                const json = JSON.parse(str);
                
                // Si Google renvoie une erreur officielle
                if (json.error) {
                    return res.status(500).json({ text: "GOOGLE DIT: " + json.error.message });
                }

                // Si tout va bien
                if (json.candidates && json.candidates[0].content) {
                    res.json({ text: json.candidates[0].content.parts[0].text });
                } else {
                    res.status(500).json({ text: "Réponse vide (Filtre de sécurité ?)" });
                }
            } catch (e) {
                res.status(500).json({ text: "Erreur lecture JSON" });
            }
        });
    });

    request.on('error', (e) => {
        res.status(500).json({ text: "Erreur Connexion: " + e.message });
    });

    request.write(data);
    request.end();
});

const PORT = process.env.PORT || 8080;
app.listen(PORT, '0.0.0.0', () => {
    console.log("Serveur Diagnostic Final prêt.");
});
