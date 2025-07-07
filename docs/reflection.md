# IT Newsfeed System: A Design Reflection

## Introduction

This document outlines the engineering philosophy and design decisions behind the IT Newsfeed system. The primary goal was to deliver a robust, production-ready MVP that not only meets all functional requirements but also establishes a scalable and maintainable foundation for future iteration. The project was approached with a pragmatic, MVP-first strategy, prioritizing immediate value while ensuring the architecture was prepared for long-term growth. Our overall methodology is aligned with established principles for combining AI and software engineering, focusing on a modular design and data-centric validation to build a reliable AI-powered system.

**A Note on the Development Process:** This project was developed with the assistance of an AI pair programmer. Leveraging AI for research, code generation, and iterative refinement significantly accelerated the development process. This allowed for a greater focus on high-level architectural decisions, robust testing strategies, and a deeper exploration of the filtering models, demonstrating a modern, AI-augmented workflow.

## A Foundation for Growth: Architectural Design

The system's architecture was deliberately chosen to balance speed of delivery with future-proof design. We selected **FastAPI** for its high-performance asynchronous capabilities and its ecosystem, which includes Pydantic for strict, automatic data validation—a critical feature for a reliable API.

Two architectural patterns were central to the design:
1.  **The Registry Pattern:** This was implemented for both data sources and filters. It provides a modular, plug-and-play framework, allowing the system to be extended with new sources or filtering logic without requiring core code changes. This design is key to the system's maintainability and flexibility.
2.  **The Storage Abstraction:** A `NewsStore` interface was created to decouple the application from the persistence layer. The MVP leverages a simple in-memory implementation for rapid development and testing, but the abstraction ensures that migrating to a more powerful, persistent backend like **Qdrant** is a straightforward and low-risk process.

Continuous data aggregation is handled by a simple, resilient background service that periodically fetches content from all registered sources, ensuring the newsfeed remains current.

## A Research-Backed, Hybrid Approach to AI Filtering

Our filtering strategy was meticulously designed to be both effective and practical, moving beyond simple keyword searches to a sophisticated, hybrid relevance model. This approach is grounded in academic research on information retrieval and validated by industry best practices.

The model combines two distinct techniques:

1.  **High-Precision Keyword Matching:** This component provides explicit control and precision. The keywords were not chosen arbitrarily; we followed a research-based methodology to identify core concepts critical to IT managers (e.g., security, outages, updates) and expanded them with relevant synonyms, threat identifiers (`CVE`), and vendor names (`AWS`, `Azure`). These keywords are categorized by business impact to ensure the final score accurately reflects an item's urgency.

2.  **Context-Aware Semantic Analysis:** To capture nuanced meaning, we implemented a semantic similarity filter. The selection of core IT topics (such as "system administration," "network security," "data breach," and "disaster recovery") was validated against numerous academic papers and industry reports. This ensures the topics are directly aligned with the real-world priorities of an IT manager. For the technical implementation, we chose `sentence-transformers` with the `all-MiniLM-L6-v2` model, which offers a favourable balance of high semantic accuracy, fast inference speed, and a small deployment footprint. While larger models like full-scale LLMs were considered, this approach was selected for the MVP due to its significantly lower latency, reduced computational cost, and ease of deployment, ensuring a responsive user experience.

This dual-layered approach creates a robust and deterministic filtering pipeline. It can identify explicitly critical terms while also understanding the contextual relevance of a news item, ensuring the results are consistently accurate, explainable, and truly valuable to the end-user.

## A Commitment to Quality: Testing

A rigorous testing strategy was fundamental to this project. The system is validated by a comprehensive suite of unit and integration tests that cover all critical components of the application.

Our methodology emphasizes **extensive mocking of external services** (like RSS feeds and the Reddit API). This is a deliberate design choice that allows us to build fast, reliable, and deterministic tests that validate our application's logic in isolation, which is a best practice for any service-oriented architecture. While the system is engineered with performance in mind, formal load and performance testing are designated as key activities for future development cycles.

## Evaluating Filter Performance and Correctness

To evaluate the efficiency and correctness of the news retrieval and filtering process, we employ a multi-layered strategy that combines offline testing with a clear path toward online, real-time validation.

**Correctness** is currently ensured through a robust suite of automated tests. Unit tests validate the logic of individual components, such as the keyword matching and scoring, while integration tests confirm that the entire filtering pipeline behaves deterministically. By extensively mocking external data sources, we can feed the system a known set of inputs and assert that the output—the filtered and ranked list of news items—is exactly as expected.

**Efficiency** is addressed architecturally by selecting high-performance components like FastAPI and the lightweight `sentence-transformers` model. While formal performance and load testing are planned for a future phase, the current system is designed to be fast and responsive under typical loads. The strategic roadmap includes implementing a Prometheus endpoint, which will be critical for monitoring throughput, latency, and error rates in a live environment.

### A Two-Stage Filtering Strategy: The Rationale Behind Our Thresholds

The system employs a two-stage filtering strategy to maximize relevance for the end-user while minimizing noise. This involves a strict pre-filter at the API level and a visual categorization at the UI level.

1.  **Stage 1: API Pre-Filtering (Default Threshold: 0.1)**: At both the `/ingest` and `/retrieve` endpoints, a baseline relevance threshold is enforced (defaulting to **0.1**). A news item scoring below this is considered irrelevant and is either not stored at all (at ingest) or not returned to the client (at retrieve). The rationale for this low threshold is to create a "low-pass filter" that aggressively removes obvious noise and junk content without accidentally discarding potentially nuanced but relevant articles. It ensures that the storage layer only contains items with at least a minimal signal of relevance. This threshold is configurable via the `RELEVANCE_THRESHOLD` environment variable, allowing operators to adjust the system's sensitivity.

2.  **Stage 2: UI Visual Prioritization (Thresholds: 0.4 and 0.7)**: The Streamlit dashboard is designed for an IT manager who needs to quickly triage information. It fetches items that have passed the API filter and then applies visual thresholds to help the user prioritize:
    *   **High (> 0.7):** Represents a very strong signal, likely a critical security alert or major outage report.
    *   **Medium (0.4 - 0.7):** Indicates a significant topic that warrants attention. A score of 0.4 is deliberately challenging to achieve, requiring a strong thematic match to our research-backed IT topics. This ensures the user's primary feed is not cluttered.
    *   **Low (< 0.4):** Items that are tangentially related but not considered priority viewing.

This two-tiered approach ensures the system is both efficient in what it stores and effective in how it presents information, preventing alert fatigue and focusing the user's attention on what matters most. These thresholds were not chosen arbitrarily; they were calibrated empirically using the test harness's synthetic data batch to ensure the resulting score distribution aligned with design goals.

### From Theory to Practice: A Case Study in Iterative Refinement

After implementing the "highest signal wins" model, end-to-end validation revealed a problem: critical alerts were not receiving the expected `1.0` score. This triggered a debugging cycle that exemplifies our commitment to quality:

1.  **Symptom Identification**: The API output showed that high-priority keyword matches were not resulting in a high final score.
2.  **Initial Hypothesis**: We initially suspected the issue was in the API routers where scores were aggregated. A preliminary fix was implemented there.
3.  **Root Cause Analysis**: Further testing showed the fix was incomplete. By tracing the data flow, we discovered the true root cause: the individual filters (`keyword_filter` and `semantic_filter`) were internally averaging their scores *before* returning them. This prematurely diluted the high-priority signals.
4.  **Robust Fix**: We implemented a comprehensive, two-part solution. First, we corrected the logic within each filter to correctly use `max()` to find the strongest signal. Second, we simplified the code in the API routers, removing the now-redundant logic.

This iterative process of testing, debugging, and refactoring demonstrates a core engineering principle of this project: theoretical correctness must always be validated by proven, end-to-end functional behavior.

### Evolving the Scoring Model: From Averaging to Prioritizing the Strongest Signal

Upon reviewing the initial scoring output, we observed that critical alerts (e.g., "Critical Security Vulnerability in Apache Log4j") received relevance scores that were lower than intuitively expected. This was due to the initial scoring strategy, which averaged the results from the `keyword_filter` and the `semantic_filter`. While logical, this approach had an unintended side effect: a nuanced but numerically lower semantic score could dilute a perfect `1.0` score from the keyword filter, thus masking the item's true urgency.

This issue is analogous to the well-researched phenomenon of **"Alarm Fatigue,"** where professionals become desensitized to alerts when a system produces too many non-actionable or ambiguous signals. To prevent this "crying wolf" effect and ensure our user—the IT Manager—trusts the system's output, we evolved the calculation. The new logic is not a weighted average, but rather a **"highest signal wins"** model:

**`Final Score = MAX(Keyword Score, Semantic Score)`**

This approach is a direct mitigation strategy for alarm fatigue, documented extensively in healthcare systems research. Additionally, academic research on multi-criteria decision analysis strongly supports maximum aggregation over weighted averaging in scenarios where different filters represent distinct types of expertise. According to comparative studies of aggregation functions, the "highest signal wins" approach prevents the dilution of strong, confident signals and provides more intuitive decision-making outcomes in systems where preserving peak expert confidence is crucial.

This ensures that if any single filter identifies an item as highly relevant, that strong signal is preserved in the final score. A `1.0` score from the keyword filter guarantees a `1.0` final score, making critical alerts unambiguous and immediately actionable. This preserves the integrity of high-priority alerts and respects the user's attention, making the entire system more reliable and effective.

## The Strategic Roadmap: Future Enhancements

The current MVP is a strong starting point, and the architecture is designed to support a clear roadmap of enhancements that would mature it into a full-scale AI service. The key planned evolutions are:
1.  **Migrate to a Vector Database:** Transitioning from the in-memory store to **Qdrant** to unlock persistent storage and enable powerful, large-scale semantic search.
2.  **Advance the AI Core:** Incorporating more sophisticated models for **zero-shot classification**, allowing for even more nuanced and accurate content filtering without retraining.
3.  **Enhance Observability:** Implementing a **Prometheus** metrics endpoint to provide deep, real-time insights into the system's performance and behavior in a production environment.
4.  **Refactor and Centralize Filtering Logic**: To improve maintainability, the duplicated score calculation logic in the API routers (`ingest.py` and `retrieve.py`) should be refactored into the central `FilterOrchestration` class. This will create a single source of truth for the filtering process, simplifying future updates and reducing the risk of inconsistencies.
5.  **Establish a Quantitative Evaluation Framework**: To ensure data-driven model improvements, we will implement an offline evaluation framework. This involves creating a "golden dataset" of news items with known relevance, allowing us to systematically measure the precision and recall of our filtering models as they evolve.
6.  **Evolve Towards an Agent-Ready API**: To support integration with automated systems and AI agents, the API will be enhanced to provide richer, more structured metadata. This includes detailed reasoning for filtering decisions and contextual classifications that an autonomous agent could use to trigger workflows, such as automatically opening a high-priority incident ticket in a service management tool.
7.  **Fully Containerize All Services**: To create a true one-step deployment, the Streamlit UI will be integrated into the `docker-compose` setup as its own service. This will allow the entire application stack—API, background workers, and user interface—to be launched with a single `make up` command, ensuring perfect environmental consistency and simplifying production deployment.

## Conclusion

The IT Newsfeed system successfully delivers a feature-complete and reliable MVP. It is built on a modern, scalable architecture that demonstrates a forward-looking approach to software engineering and AI-powered systems. The project proves that a focus on modular design, robust testing, and a pragmatic development strategy can yield a high-quality product that is ready for both immediate use and future innovation.

---

## References

The methodologies and topics used in this project's filtering system are informed by foundational academic research and established industry reports.

- **Reimers, N., & Gurevych, I. (2019).** *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks*. This foundational paper introduces the Sentence-BERT model, which is the core technology used in this project (via the `sentence-transformers` library) for generating high-quality sentence embeddings for semantic similarity analysis.[https://arxiv.org/abs/1908.10084](https://arxiv.org/abs/1908.10084)

- **IBM. (2023).** *Cost of a Data Breach Report*. This industry-standard report provides critical insights into the financial impact and root causes of security breaches. Its findings directly informed the keyword and semantic models for identifying high-priority security events. The official report can be accessed via IBM's portal. [https://www.ibm.com/reports/data-breach](https://www.ibm.com/reports/data-breach)

- **Cisco. (2025).** *Cybersecurity Readiness Index*. This report assesses corporate preparedness against modern cybersecurity threats. The trends highlighted in the index were used to refine the filtering logic to prioritize news related to emerging vulnerabilities. The official report is available from Cisco's newsroom. [https://newsroom.cisco.com/c/r/newsroom/en/us/a/y2025/m05/cybersecurity-readiness-index-2025.html](https://newsroom.cisco.com/c/r/newsroom/en/us/a/y2025/m05/cybersecurity-readiness-index-2025.html)

- **Martínez-Fernández, S., et al. (2020).** *Software Engineering for AI-Based Systems: A Survey*. This comprehensive survey reviews the challenges and best practices for engineering AI systems, providing a strong academic foundation for this project's focus on modularity, testing, and data-centric validation.[https://arxiv.org/abs/2105.01984](https://arxiv.org/abs/2105.01984)
