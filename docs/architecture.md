# Architecture

`computer_vision` emits observations and event candidates matching `shared/data_contracts`. `backend` owns API and database configuration; `analytics` only consumes validated observations/events. A later identity/AI service may enrich records, but must preserve track IDs, confidence, timestamps, source references, and candidate status.
