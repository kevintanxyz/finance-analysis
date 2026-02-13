/**
 * Message Blocks - Rich content types for Claude responses
 */

export interface NewsItem {
  title: string;
  url: string;
  summary: string;
  source?: string;
  date?: string;
}

export interface ChartConfig {
  xKey?: string;
  yKey?: string;
  xLabel?: string;
  yLabel?: string;
  nameKey?: string;
  valueKey?: string;
  colors?: string[];
}

export interface ChartDataPoint {
  [key: string]: string | number;
}

// Block types
export interface TextBlock {
  type: 'text';
  content: string; // Markdown text
}

export interface NewsBlock {
  type: 'news';
  items: NewsItem[];
}

export interface TableBlock {
  type: 'table';
  caption?: string;
  headers: string[];
  rows: (string | number)[][];
}

export interface ChartBlock {
  type: 'chart';
  chartType: 'line' | 'pie' | 'bar';
  title?: string;
  data: ChartDataPoint[];
  config?: ChartConfig;
}

export type MessageBlock = TextBlock | NewsBlock | TableBlock | ChartBlock;

export interface StructuredMessage {
  blocks: MessageBlock[];
}

// Type guards
export function isStructuredMessage(content: string): boolean {
  try {
    const parsed = JSON.parse(content);
    return parsed && Array.isArray(parsed.blocks);
  } catch {
    return false;
  }
}

export function parseStructuredMessage(content: string): StructuredMessage | null {
  try {
    let jsonContent = content.trim();

    // Try multiple strategies to extract JSON

    // Strategy 1: Check if wrapped in code blocks (```json ... ``` or ``` ... ```)
    const codeBlockRegex = /```(?:json)?\s*\n?([\s\S]*?)\n?```/;
    const codeBlockMatch = jsonContent.match(codeBlockRegex);
    if (codeBlockMatch) {
      jsonContent = codeBlockMatch[1].trim();
    }

    // Strategy 2: Look for JSON object anywhere in the content
    // Match { ... } with proper nesting
    const jsonObjectRegex = /(\{[\s\S]*"blocks"[\s\S]*\})/;
    const jsonMatch = jsonContent.match(jsonObjectRegex);
    if (jsonMatch) {
      jsonContent = jsonMatch[1].trim();
    }

    // Try to parse
    const parsed = JSON.parse(jsonContent);
    if (parsed && Array.isArray(parsed.blocks)) {
      console.log('✅ Structured message detected with', parsed.blocks.length, 'blocks');
      return parsed as StructuredMessage;
    }

    return null;
  } catch (e) {
    console.log('⚠️ Failed to parse as structured message:', e);
    return null;
  }
}
