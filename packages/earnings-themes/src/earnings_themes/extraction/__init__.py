"""Stage 7's extractor: pointer selection over every eligible element, keeping only
the spans code verifies (the Stage 7 spec, §Plan B).

A model sees a window of enumerated units and returns their labels with a claim in
its own words. Code maps each label to its element, slices the canonical text, and
runs Stage 2's exactness checks. The modules are plain functions behind a small
adapter protocol, with no framework and no provider SDK (ES10). The one local
adapter, ``local``, sits behind the ``local-model`` extra, and nothing here imports
it, so no other module loads an HTTP client (ES15).
"""
