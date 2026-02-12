# 📤 Test Upload Portfolio - Prompts Claude Desktop

Voici les **3 façons** d'uploader un portfolio dans Claude Desktop avec WealthPoint Analysis.

---

## ✅ Méthode 1 : Chemin de fichier (RECOMMANDÉE)

**Meilleure méthode pour les PDFs de toute taille** - Pas de limite, pas d'encodage base64

### Prompt :
```
Upload et analyse mon portfolio PDF situé ici :
/Users/kevintan/Documents/portfolios/valuation_november_2025.pdf
```

### Ce que Claude va faire :
1. Appeler `upload_portfolio(pdf_path="/Users/kevintan/Documents/portfolios/valuation_november_2025.pdf")`
2. Le serveur lit directement le fichier (pas d'encodage base64)
3. Parse avec Claude Vision
4. Retourne session_id + résumé

**Avantages** :
- ✅ Fonctionne avec n'importe quelle taille de PDF
- ✅ Plus rapide (pas d'encodage/décodage)
- ✅ Ne consomme pas de tokens pour l'encodage base64

---

## ⚠️ Méthode 2 : Glisser-déposer (Petits PDFs uniquement)

**Limite** : PDFs < 500KB seulement (sinon le prompt devient trop long)

### Étape 1 : Glisse ton PDF dans le chat
[Glisse `valuation.pdf` dans la zone de chat]

### Étape 2 : Demande l'analyse
```
Parse ce PDF et analyse le portefeuille
```

### Ce que Claude va faire :
1. Encoder automatiquement le PDF en base64
2. Appeler `upload_portfolio(pdf_base64="<very long string>")`
3. Parse avec Claude Vision
4. Retourne session_id + résumé

**Avantages** :
- ✅ Interface visuelle simple

**Inconvénients** :
- ❌ Limite de taille (~500KB max)
- ❌ Consomme beaucoup de tokens
- ❌ Risque "prompt too long" pour les gros PDFs

---

## 🧪 Méthode 3 : Portfolio Mock (Pour tester sans PDF)

**Utile pour tester les tools sans avoir de vrai PDF**

### Prompt :
```
Créé un portfolio de test avec ces positions :
- AAPL (Apple) : 100 actions à $175
- NVDA (Nvidia) : 50 actions à $480
- SPY (S&P 500 ETF) : 200 actions à $450

Sauvegarde-le avec upload_portfolio et donne-moi le session_id
```

### Ce que Claude va faire :
1. Générer des données mock au format attendu
2. Encoder en base64 (ou créer un fichier temporaire)
3. Appeler `upload_portfolio`
4. Retourne session_id

**Avantages** :
- ✅ Test rapide sans avoir de vrai PDF
- ✅ Données contrôlées

---

## 📊 Après l'upload : Que faire ?

Une fois que tu as le `session_id`, tu peux :

### 1. Voir les données marché live
```
Récupère les données de marché en temps réel pour toutes les positions
du portefeuille <session_id>
```

### 2. Analyser le risque
```
Analyse le risque de Apple (AAPL) dans le portefeuille <session_id>
```

### 3. Analyser le momentum
```
Analyse les indicateurs momentum pour Nvidia (NVDA) dans le portefeuille <session_id>
```

### 4. Matrice de corrélation
```
Calcule la matrice de corrélation entre toutes les positions cotées
du portefeuille <session_id>
```

---

## 🐛 Dépannage

### Erreur : "Prompt too long"
**Cause** : Le PDF encodé en base64 est trop gros

**Solution** :
1. Utilise la **Méthode 1** (chemin de fichier) au lieu du glisser-déposer
2. Ou compresse le PDF d'abord

### Erreur : "File not found"
**Cause** : Le chemin de fichier est incorrect

**Solution** :
1. Vérifie que le chemin est absolu (commence par `/` sur Mac/Linux)
2. Vérifie que le fichier existe : `ls -l /path/to/file.pdf`

### Erreur : "No PDF provided"
**Cause** : Ni `pdf_base64` ni `pdf_path` n'ont été fournis

**Solution** :
- Spécifie explicitement le chemin : `pdf_path="/path/to/file.pdf"`
- Ou fournis le base64

---

## 💡 Recommandation

Pour **tous les tests avec de vrais PDFs**, utilise la **Méthode 1** (chemin de fichier).
C'est plus fiable, plus rapide, et n'a pas de limite de taille.

Exemple de prompt complet :
```
Upload mon portfolio situé à :
/Users/kevintan/Documents/portfolios/valuation_november_2025.pdf

Puis :
1. Montre-moi un résumé du portefeuille
2. Récupère les données marché live pour toutes les positions cotées
3. Analyse le risque de la position avec le plus gros poids
```
