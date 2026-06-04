"""Five Qdrant collections (Chapter 9 naming)."""

VECTOR_SIZE = 1024
DENSE_NAME = "dense"
SPARSE_NAME = "sparse"

SELENIUM_CODE = "selenium_code"
PLAYWRIGHT_CODE = "playwright_code"
VWO_TESTCASES = "vwo_testcases"
VWO_DOCS = "vwo_docs"
VWO_BUGS = "vwo_bugs"

ALL_COLLECTIONS = (
    SELENIUM_CODE,
    PLAYWRIGHT_CODE,
    VWO_TESTCASES,
    VWO_DOCS,
    VWO_BUGS,
)

SOURCE_LABELS = {
    SELENIUM_CODE: "Selenium TestNG Java",
    PLAYWRIGHT_CODE: "Playwright TS/JS",
    VWO_TESTCASES: "VWO test cases (CSV)",
    VWO_DOCS: "VWO PRDs / PDFs",
    VWO_BUGS: "VWO JIRA exports (Markdown)",
}
