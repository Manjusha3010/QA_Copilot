export type Meta = {
  version?: string;
  embed_model: string;
  reranker_model: string;
  groq_model: string;
  collections: { id: string; label: string }[];
  paths: {
    pdfs: string | null;
    markdown: string | null;
    selenium: string | null;
    playwright: string | null;
    vwo_tests: string | null;
  };
};

export type Citation = {
  collection: string;
  vector_score: number;
  rerank_score: number;
  text: string;
  path?: string;
  page?: number;
  source_type?: string;
  doc_quality?: string;
};

export type HitSummary = {
  point_id?: string | number;
  collection?: string;
  hybrid_rrf_score?: number;
  text_preview?: string;
  text_length?: number;
  path?: string;
  page?: number;
  tc_id?: string;
  jira_id?: string;
  rerank_score?: number;
  full_text?: string;
};

export type RagExploreTrace = {
  query_original: string;
  query_rewritten: string;
  router_collections: string[];
  router_raw_llm: string;
  router_fallback_all_collections: boolean;
  per_collection_hits: Record<string, HitSummary[]>;
  rerank_scores_table: {
    point_id?: string | number;
    collection?: string;
    hybrid_rrf_score?: number;
    rerank_score?: number;
    path?: string;
  }[];
  final_chunks: HitSummary[];
  prompt_system: string;
  prompt_user: string;
  answer: string;
  citations: Citation[];
  counts: Record<string, number>;
  pipeline_steps_explained: string[];
  groq_model?: string;
};
