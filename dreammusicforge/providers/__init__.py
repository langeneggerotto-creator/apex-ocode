"""Namespace for provider-specific compiler packages (spec section 5's
`providers/` directory: `kling/`, `veo/`, `runway/`, `generic/`).

Nothing is re-exported at this level -- only `providers.kling` exists so
far (Release 0.7). Spec section 14's provider-neutral `VideoRenderer`
interface (`capabilities()`/`compile_request()`/`submit()`/`status()`/
`collect()`) is not implemented anywhere in this repository yet: no
release has named it as a required deliverable, and building it now
would mean inventing `ProviderRequest`/`ProviderJob`/`ProviderJobStatus`/
`RenderedAsset` shapes with no spec example to ground them in. See
`providers/kling/README` notes (in `providers/kling/__init__.py`'s
docstring) for what this release builds instead.
"""
from __future__ import annotations
