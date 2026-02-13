/**
 * Chat Page - MCP Chat Interface
 * Conversational interface for portfolio analysis
 */

import { useState } from "react";
import { ChatContainer } from "@/components/chat/ChatContainer";
import { Button } from "@/components/ui/button";
import { FileText } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { mcpClient } from "@/services/mcp-client";
import type { ChatMessage, ToolResult } from "@/services/mcp-types";
import { PDFUploadDialog } from "@/components/portfolio/PDFUploadDialog";

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [streamingStatus, setStreamingStatus] = useState<string | null>(null);
  const { toast } = useToast();

  // Handle sending a message
  async function handleSendMessage(content: string) {
    // Add user message
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setStreamingStatus(null);

    // Create placeholder for assistant message
    const assistantMessageId = crypto.randomUUID();
    const assistantMessage: ChatMessage = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, assistantMessage]);

    try {
      // Build conversation history for Claude API
      const history = messages.map((msg) => ({
        role: msg.role,
        content: msg.content,
      }));

      // Use streaming API to get real-time updates
      await mcpClient.chatStream(
        {
          message: content,
          sessionId: sessionId || undefined,
          history,
        },
        {
          // Update message content as text chunks arrive
          onText: (text) => {
            // Clear status when text starts arriving
            setStreamingStatus(null);
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, content: msg.content + text }
                  : msg
              )
            );
          },
          // Show tool execution status
          onStatus: (status) => {
            setStreamingStatus(status);
            // Add line break before tool execution to separate content
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId && msg.content && !msg.content.endsWith('\n\n')
                  ? { ...msg, content: msg.content + '\n\n' }
                  : msg
              )
            );
          },
          // Clear status when done
          onComplete: () => {
            setStreamingStatus(null);
            setIsLoading(false);
          },
          // Handle errors
          onError: (error) => {
            toast({
              title: "Error",
              description: error.message,
              variant: "destructive",
            });
            setStreamingStatus(null);
            setIsLoading(false);
          },
        }
      );
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to get response",
        variant: "destructive",
      });

      // Update message with error
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                content: "Sorry, I encountered an error processing your request.",
                toolResults: [
                  {
                    toolName: "claude_api",
                    displayType: "error",
                    data: null,
                    error: error instanceof Error ? error.message : "Unknown error",
                  } as ToolResult,
                ],
              }
            : msg
        )
      );
    } finally {
      setStreamingStatus(null);
      setIsLoading(false);
    }
  }

  // Handle successful PDF upload
  function handleUploadSuccess(newSessionId: string, filename: string) {
    setSessionId(newSessionId);
    // Store session ID in localStorage for Dashboard access
    localStorage.setItem("activeSessionId", newSessionId);
    toast({
      title: "Portfolio uploaded",
      description: `${filename} analyzed successfully`,
    });

    // Add welcome message with capabilities
    const welcomeMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "assistant",
      content: `✅ **Portfolio chargé avec succès!**

Je suis Thiago, votre assistant d'analyse de portefeuille. J'ai accès à l'ensemble de vos données et à des outils d'analyse avancés.

### 📊 **Données de marché**
- Actualiser les prix en temps réel pour toutes les positions
- Variations: 1 jour, 5 jours, 1 mois
- Prix actuel, ouverture, clôture, volume
- Market cap et données fondamentales

### ⚠️ **Analyse de risque**
- **VaR (Value at Risk)**: Perte potentielle maximale à 95%/99% de confiance
- **Maximum Drawdown**: Plus grande perte historique depuis un pic
- **Volatilité**: Écart-type annualisé des rendements
- **Stress Tests**: Scénarios de crise (-10%, -20%, -30%, -40%)
- **Sharpe Ratio**: Rendement ajusté au risque vs benchmark
- **Beta**: Sensibilité au marché

### 📈 **Analyse technique**
- **RSI**: Survente (<30) / Surachat (>70)
- **MACD**: Convergence/divergence des moyennes mobiles
- **Signal**: Signaux d'achat/vente automatiques
- **Tendance**: Identification des tendances haussières/baissières

### 🔗 **Corrélation**
- Matrice de corrélation entre plusieurs positions
- Détection de diversification ou concentration
- Heatmap visuelle des corrélations

### 🎯 **Optimisation de portefeuille**
- **Max Sharpe**: Maximiser le ratio rendement/risque
- **Min Volatility**: Minimiser la volatilité
- **Max Return**: Maximiser le rendement
- **Frontière efficiente**: Calcul de la frontière d'efficience

### 💰 **Options & Dérivés**
- Valorisation Black-Scholes pour calls et puts
- **Greeks**: Delta, Gamma, Theta, Vega, Rho
- Prix théorique d'option
- Analyse de sensibilité

### 💵 **Revenus et dividendes**
- Rendement dividende annuel pour toutes les positions
- Projection des revenus futurs (ex-dates, montants)
- Total des dividendes attendus sur 12 mois

### 📊 **Allocation**
- Répartition par classe d'actifs (Actions, Obligations, Cash, Structurés, Fonds)
- Exposition par devise (CHF, USD, EUR, etc.)
- Exposition régionale (Suisse, Europe, Amérique du Nord, etc.)
- Exposition sectorielle (Tech, Finance, Healthcare, etc.)

### ✅ **Conformité**
- Vérification concentration max par position (défaut: 20%)
- Vérification concentration max par classe d'actifs (défaut: 70%)
- Vérification concentration max par devise (défaut: 80%)
- Alertes réglementaires automatiques

### 🔄 **Recommandations de rééquilibrage**
- Analyse écart allocation actuelle vs allocation cible
- Recommandations d'achat/vente pour rééquilibrer
- Calcul des montants précis à acheter/vendre

### 👤 **Profil d'investisseur**
- Inférence automatique du profil (Conservateur, Équilibré, Dynamique, Agressif)
- Calcul du score de risque (0-100)
- Analyse de l'horizon d'investissement

### 🔍 **Analyse approfondie d'un titre**
- Analyse technique complète (RSI, MACD, tendances)
- Données fondamentales (PE, market cap, volumes)
- Prix historiques et performance

### 📄 **Rapport complet**
- Rapport exhaustif avec toutes les analyses
- Vue d'ensemble du portefeuille
- Tops & Flops performers
- Historique de performance
- Expositions détaillées (devise, région, secteur)
- Analyse P&L (profit & loss)

---

## 🎨 **Exemples de questions:**

**Analyse de risque:**
- "Analyse le risque de Roche - VaR, drawdown et volatilité"
- "Quel est le stress test à -30% sur Apple?"
- "Compare le risque de Nestlé vs le marché suisse"

**Analyse technique:**
- "Le RSI de Novartis indique-t-il surachat ou survente?"
- "Analyse le momentum de Microsoft sur 90 jours"
- "Quelle est la tendance actuelle d'UBS?"

**Corrélation et diversification:**
- "Corrélation entre Apple et Microsoft?"
- "Mon portefeuille est-il bien diversifié?"
- "Quelles positions sont fortement corrélées?"

**Optimisation:**
- "Optimise mon portefeuille pour maximiser le Sharpe ratio"
- "Quelle est la frontière efficiente de mes positions?"
- "Optimise pour minimiser la volatilité"

**Allocation et rééquilibrage:**
- "Quelle est mon allocation actuelle par classe d'actifs?"
- "Recommande un rééquilibrage vers 60% actions / 30% obligations / 10% cash"
- "Comment rééquilibrer pour réduire l'exposition USD?"

**Conformité:**
- "Mon portefeuille respecte-t-il les limites de concentration?"
- "Ai-je des positions trop importantes?"
- "Vérifie la conformité réglementaire"

**Dividendes et revenus:**
- "Quels dividendes vais-je recevoir cette année?"
- "Quel est le rendement dividende de mon portefeuille?"
- "Projette mes revenus sur 12 mois"

**Actualités et recherche:**
- "Cherche les dernières actualités sur Roche"
- "Quelle est la couverture médiatique de Nestlé?"
- "Recherche des informations sur le secteur pharma suisse"

**Rapports:**
- "Génère un rapport complet de mon portefeuille"
- "Analyse mon profil d'investisseur"
- "Résumé global de ma situation"

---

**Que souhaitez-vous analyser?** 🚀`,
      timestamp: new Date(),
    };

    setMessages([welcomeMessage]);
  }

  return (
    <div className="container mx-auto py-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Portfolio Chat</h1>
          <p className="text-muted-foreground">
            Ask questions about your portfolio using natural language
          </p>
        </div>
        <div className="flex gap-2">
          <PDFUploadDialog onUploadSuccess={handleUploadSuccess} />
          {sessionId && (
            <Button variant="outline" disabled>
              <FileText className="mr-2 h-4 w-4" />
              Session: {sessionId.slice(0, 8)}...
            </Button>
          )}
        </div>
      </div>

      {/* Chat container */}
      <ChatContainer
        messages={messages}
        isLoading={isLoading}
        streamingStatus={streamingStatus}
        onSendMessage={handleSendMessage}
        disabled={!sessionId}
        placeholder={
          !sessionId
            ? "📤 Uploadez d'abord votre portfolio PDF pour commencer..."
            : "Posez votre question sur le portfolio..."
        }
      />
    </div>
  );
}
