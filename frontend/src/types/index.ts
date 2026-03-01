export interface NewsTask {
  id: string;
  user_id: string;
  name: string;
  prompt: string;
  active: boolean;
  created_at: string;
  updated_at: string;
  sources_count: number;
}

export interface NewsTaskCreate {
  name: string;
  prompt: string;
  active: boolean;
}

export interface NewsTaskUpdate {
  name?: string;
  prompt?: string;
  active?: boolean;
}

export interface Source {
  id: string;
  user_id: string;
  name: string;
  type: 'RSS' | 'Telegram';
  source: string;
  active: boolean;
  last_fetched_at: string | null;
  created_at: string;
}

export interface SourceCreate {
  name: string;
  type: 'RSS' | 'Telegram';
  source: string;
  active: boolean;
}

export interface SourceUpdate {
  name?: string;
  source?: string;
  active?: boolean;
}

export interface SourceNewsTaskAssociation {
  source_id: number;
  news_task_id: number;
  created_at?: string;
}

export interface NewsItem {
  id: number;
  source_id: number;
  title: string | null;
  content: string | null;
  url: string | null;
  external_id: string | null;
  published_at: string | null;
  fetched_at: string;
  settings: any | null;
  raw_data: any | null;
  created_at: string;
  updated_at: string;
  processing_results?: NewsItemNewsTask[];
}

export interface NewspaperItem {
  title: string | null;
  content: string | null;
  url: string | null;
  source_id: number;
  published_at: string;
}

export interface Newspaper {
  id: number;
  news_task_id: number;
  title: string;
  body: Record<string, NewspaperItem[]>;
  updated_at: string;
}

export interface NewsItemNewsTask {
  news_item_id: number;
  news_task_id: number;
  processed: boolean;
  result: boolean | null;
  processed_at: string | null;
  ai_response: any | null;
  created_at: string;
  updated_at: string;
}
