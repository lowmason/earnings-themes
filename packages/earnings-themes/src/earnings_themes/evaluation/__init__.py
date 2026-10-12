"""Stage 11's evaluation: scoring the pilot, the user's support labels, and
calibration (the Stage 11 spec, A3–A5).

Pure: it reads no file, sends no request, loads no model and prints nothing. It
imports pure Stage 7–9 code and never ingestion, httpx, an NLI runtime or a concrete
adapter, and no gold-drafting module imports it (D19-4).
"""
