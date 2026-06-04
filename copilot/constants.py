"""One Qdrant collection per source; router merges and reranks."""

VECTOR_SIZE = 1024  # BAAI/bge-m3 dense

COLLECTION_PDFS = "source_pdfs"
COLLECTION_SELENIUM = "source_selenium"
COLLECTION_PLAYWRIGHT = "source_playwright"
COLLECTION_VWO_TESTS = "source_vwo_tests"

ALL_COLLECTIONS = (
    COLLECTION_PDFS,
    COLLECTION_SELENIUM,
    COLLECTION_PLAYWRIGHT,
    COLLECTION_VWO_TESTS,
)

SOURCE_LABELS = {
    COLLECTION_PDFS: "PDFs, Markdown (e.g. data/MD), summaries",
    COLLECTION_SELENIUM: "Selenium repo",
    COLLECTION_PLAYWRIGHT: "Playwright repo",
    COLLECTION_VWO_TESTS: "app.vwo.com tests",
}
