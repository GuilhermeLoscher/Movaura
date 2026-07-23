# Catálogo Online Movaura

O catálogo usa um manifesto JSON hospedado em qualquer servidor HTTPS.
Cada item aponta para um wallpaper e pode incluir um hash SHA-256 para impedir
arquivos corrompidos ou substituídos.

```json
{
  "wallpapers": [
    {
      "name": "Cidade Neon",
      "kind": "video",
      "download_url": "https://exemplo.com/wallpapers/cidade-neon.mp4",
      "sha256": "HASH_SHA256_DO_ARQUIVO",
      "description": "Loop noturno em 1080p."
    }
  ]
}
```

Formatos aceitos: `.mp4`, `.webm`, `.gif`, `.png`, `.jpg`, `.jpeg`, `.bmp`
e `.webp`.

Para publicar um marketplace completo, use este manifesto como API inicial e
adicione autenticação, moderação, avaliações e armazenamento externo.
