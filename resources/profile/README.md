# Homepage photograph

Add your portrait here as `photo.jpg`:

```
resources/profile/photo.jpg
```

The next Hugo build (or local preview rebuild) replaces the homepage placeholder with
the photograph. No template or configuration edits are needed. Use a square image with
your face near the centre; Hugo generates a 640 × 640 WebP for display.

For a PNG or WebP instead, place it in this folder and update `manlog.avatar` in
`config/_default/params.toml` to `profile/photo.png` or `profile/photo.webp`.

This folder contains source files and should be kept in git. Only `resources/_gen/`
is disposable Hugo output; do not delete the whole `resources/` directory.
